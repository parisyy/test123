#!/usr/bin/env python
# coding: utf-8

import tornado.web
from handlers.base import BaseHandler
from ext.pagination import Pagination
from ext.informer import BootstrapInformer


class SalonBaseHandler(BaseHandler):
    config = {
        "recommend": {
            0: '未推荐',
            1: '已推荐',
        },
    }

    def fetch_hairstylists(self, salon_id):
        '''根据沙龙ID，获取属于该沙龙的所有发型师'''
        return self.db.query("select * from md_member where member_type = 2 and salon_id = %s", salon_id)

    def fetch_hairstylist_count(self):
        '''根据沙龙ID，计算各沙龙的发型师数量'''
        entries = self.db.query("select salon_id, count(*) as cnt from md_member where member_type = 2 "
                "group by salon_id")
        dataset = {}
        for e in entries:
            dataset.setdefault(e.salon_id, e.cnt)
        return dataset

    def _logo_url(self, entry):
        filename = self.get_salon_path_prefix()
        filename = str(filename) + "/" + str(entry.img_path) + "/" + str(entry.pic_url) + "." + str(entry.img_type)
        filename = filename.replace("//", "/")
        return self.path_to_url(filename)

    def fetch_all_logos(self):
        '''读取所有的logo'''
        entries = self.db.query("select salon_id, p.img_path, p.pic_url, p.img_type "
                "from md_salon_picture m left outer join md_theme_picture p "
                "on m.salon_pic_id = p.id and m.is_logo = 'Y'")
        dataset = {}
        for e in entries:
            if e.img_path and e.pic_url and e.img_type:
                dataset.setdefault(e.salon_id, self._logo_url(e))
        return dataset

    def fetch_logo_url(self, salon_id):
        '''读取指定沙龙的logo'''
        entry = self.db.query("select salon_id, p.img_path, p.pic_url, p.img_type "
                "from md_salon_picture m, md_theme_picture p "
                "where m.salon_pic_id = p.id and m.is_logo = 'Y' and salon_id = %s",
                salon_id)
        if entry == []:
            return self.default_image_url()
        else:
            entry = entry[0]
            return self._logo_url(entry)

    def gen_query_str(self, sql, salon_name, province_id, city_id, domain_id):
        '''生成查询语句的where子语句'''
        query_str = []
        params = []

        if salon_name:
            query_str.append("salon_name like %s")
            params.append('%' + salon_name + '%')

        if province_id:
            query_str.append("province_id = %s")
            params.append(province_id)

        if city_id:
            query_str.append("city_id = %s")
            params.append(city_id)

        if domain_id:
            query_str.append("domain_id = %s")
            params.append(domain_id)

        if query_str != []:
            query_str = "where " + " and ".join(query_str)
            sql = sql + query_str

        sql = sql + " order by id desc"
        
        return sql, params

    def query_salons(self, salon_name, province_id, city_id, domain_id, page):
        '''查询沙龙'''
        sql = '''
            select * from md_salon
        '''
        sql, params = self.gen_query_str(sql, salon_name, province_id, city_id, domain_id)
        sql = Pagination.add_limit_clause(sql, page)
        return self.db.query(sql, *params)

    def fetch_salons_count(self, salon_name, province_id, city_id, domain_id):
        '''计算该查询条件下的沙龙数量'''
        sql = '''
            select count(*) as cnt from md_salon
        '''
        sql, params = self.gen_query_str(sql, salon_name, province_id, city_id, domain_id)
        entry = self.db.get(sql, *params)
        if entry is None:
            return 0
        else:
            return entry.cnt

    def fetch_salon_by_id(self, id):
        entry = self.db.query("select m.*, s.salon_pic_url from md_salon m "
                "left outer join md_salon_picture s on m.id = s.salon_id and s.is_logo = 'Y' "
                "where m.id = %s", id)
        if entry == []:
            return None
        else:
            return entry[0]

    def update_salon(self, id, **args):
        # 删除NoneType的数据项
        for k in args.keys():
            if args.get(k) is None:
                args.pop(k)
        # 更新数据库
        setters = map(lambda x: x + ' = %s', args.keys())
        if len(setters) == 0:
            return
        else:
            tmpl = "update md_salon set " + ", ".join(setters) + " where id = %s"
            params = args.values()
            params.append(id)
            self.db.execute(tmpl, *params)

    def create_salon(self, **args):
        # 删除NoneType数据项
        for k in args.keys():
            if args.get(k) is None:
                args.pop(k)
        # 更新数据库
        setters = map(lambda x: '%s', args.keys())
        if setters:
            tmpl = "insert into md_salon(" + ",".join(args.keys()) + ") values(" + ",".join(setters) + ")"
            self.db.execute(tmpl, *args.values())

    def fetch_salon_pics(self, salon_id):
        entries = self.db.query("select p.img_path, p.pic_url, p.img_type "
                "from md_salon_picture s, md_theme_picture p "
                "where s.salon_pic_id = p.id and s.is_logo = 'N' "
                "and salon_id = %s", salon_id)
        for e in entries:
            e["real_pic_url"] = self._logo_url(e)
        return entries


class SalonHandler(SalonBaseHandler):
    @tornado.web.authenticated
    def get(self):
        salon_name = self.get_argument("salon_name", "")
        province_id = self.get_argument("province_id", 0)
        city_id = self.get_argument("city_id", 0)
        domain_id = self.get_argument("domain_id", 0)
        page = self.get_argument("page", 1)

        salons = self.query_salons(salon_name, province_id, city_id, domain_id, page)
        count = self.fetch_salons_count(salon_name, province_id, city_id, domain_id)
        page_count = Pagination.page_count(count)
        hairstylists = self.fetch_hairstylist_count()
        logos = self.fetch_all_logos()

        params = dict(
            config=self.config,

            # 沙龙列表
            salons=salons,
            hairstylists=hairstylists,
            logos=logos,
            default_img=self.default_image_url(),
            #path_prefix=self.get_salon_path_prefix(),

            # 查询模块
            regions=self.fetch_all_regions(),
            provinces=self.fetch_provinces(),
            cities=self.fetch_cities(),
            domains=self.fetch_domains(),
            arguments=self.request.arguments,

            # 分页
            page_count=page_count,

            # 提示信息
            informer=BootstrapInformer("success", "共 %s 条记录" % count, "查询结果："),
        )
        self.render("salons/index.html", **params)


class SalonEditHandler(SalonBaseHandler):
    @tornado.web.authenticated
    def get(self, id):
        salon = self.fetch_salon_by_id(id)
        if salon:
            pics = self.fetch_salon_pics(salon.id)
            params = dict(
                salon=salon,
                provinces=self.fetch_provinces(),
                cities=self.fetch_cities(),
                domains=self.fetch_domains(),
                config=self.config,
                hairstylists=self.fetch_hairstylists(salon.id),

                # 图片预览
                logo_pic=self.fetch_logo_url(id),
                path_prefix=self.path_to_url(self.get_salon_path_prefix()),
                pics=pics,
            )
            self.render("salons/edit.html", **params)
        else:
            raise tornado.web.HTTPError(404)

    @tornado.web.authenticated
    def post(self, id):
        try:
            args = dict(
                salon_name=self.get_argument("salon_name"),
                recommend=self.get_argument("recommend", 0),
                province_id=self.get_argument("province_id", 0),
                city_id=self.get_argument("city_id", 0),
                area_id=self.get_argument("domain_id", 0),
                address=self.get_argument("address"),
                salon_telephone=self.get_argument("salon_telephone", ""),
                longitude=self.get_argument("longitude", 0),
                latitude=self.get_argument("latitude", 0),
            )
            self.update_salon(id, **args)
            self.redirect("/salons")
        except Exception, e:
            print e
            self.redirect("/salons/edit/%s" % id)


class SalonNewHandler(SalonBaseHandler):
    def get(self):
        params = dict(
            provinces=self.fetch_provinces(),
            cities=self.fetch_cities(),
            domains=self.fetch_domains(),
            config=self.config,
            logo_pic=self.fetch_logo_url(id),
        )
        self.render("salons/new.html", **params)

    def post(self):
        try:
            args = dict(
                salon_name=self.get_argument("salon_name"),
                recommend=self.get_argument("recommend", 0),
                province_id=self.get_argument("province_id", 0),
                city_id=self.get_argument("city_id", 0),
                area_id=self.get_argument("domain_id", 0),
                address=self.get_argument("address"),
                salon_telephone=self.get_argument("salon_telephone", ""),
                longitude=self.get_argument("longitude", 0),
                latitude=self.get_argument("latitude", 0),
            )
            self.create_salon(**args)
            self.redirect("/salons")
        except Exception, e:
            print e
            self.redirect("/salons/new")
