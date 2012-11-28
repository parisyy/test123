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
            print entry
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


class SalonHandler(SalonBaseHandler):
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
    def get(self, id):
        salon = self.fetch_salon_by_id(id)
        if salon:
            params = dict(
                salon=salon,
                provinces=self.fetch_provinces(),
                cities=self.fetch_cities(),
                domains=self.fetch_domains(),
                config=self.config,
                logo_pic=self.fetch_logo_url(id),
            )
            self.render("salons/edit.html", **params)
        else:
            raise tornado.web.HTTPError(404)

    def post(self, id):
        try:
            args = dict(
                salon_name=self.get_argument("salon_name"),
                recommend=self.get_argument("recommend"),
                province_id=self.get_argument("province_id"),
                city_id=self.get_argument("city_id"),
                area_id=self.get_argument("domain_id"),
                address=self.get_argument("address"),
                salon_telephone=self.get_argument("salon_telephone"),
            )
            self.update_salon(id, **args)
            self.redirect("/salons")
        except:
            self.redirect("/salons/edit/%s" % id)
