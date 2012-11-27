#!/usr/bin/env python
# coding: utf-8

from handlers.base import BaseHandler
from ext.pagination import Pagination
from ext.parser import get_default_img_path
from ext.informer import BootstrapInformer


class SalonBaseHandler(BaseHandler):
    config = {
        "recommend": {
            0: '未推荐',
            1: '已推荐',
        },
    }

    def fetch_hairstylist_count(self):
        entries = self.db.query("select salon_id, count(*) as cnt from md_member where member_type = 2 "
                "group by salon_id")
        dataset = {}
        for e in entries:
            dataset.setdefault(e.salon_id, e.cnt)
        return dataset

    def fetch_all_logos(self):
        entries = self.db.query("select salon_id, p.img_path, p.pic_url, p.img_type "
                "from md_salon_picture m left outer join md_theme_picture p "
                "on m.salon_pic_id = p.id and m.is_logo = 'Y'")
        dataset = {}
        for e in entries:
            if e.img_path and e.pic_url and e.img_type:
                dataset.setdefault(e.salon_id, e.img_path + "/" + e.pic_url + "." + e.img_type)
        print dataset
        return dataset

    def gen_query_str(self, sql, salon_name, province_id, city_id, domain_id):
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
        sql = '''
            select m.*, s.salon_pic_url from md_salon m left outer join md_salon_picture s
            on m.id = s.salon_id and s.is_logo = 'Y'
        '''
        sql, params = self.gen_query_str(sql, salon_name, province_id, city_id, domain_id)
        sql = Pagination.add_limit_clause(sql, page)
        return self.db.query(sql, *params)

    def fetch_salons_count(self, salon_name, province_id, city_id, domain_id):
        sql = '''
            select count(*) as cnt from md_salon m left outer join md_salon_picture s
            on m.id = s.salon_id and s.is_logo = 'Y'
        '''
        sql, params = self.gen_query_str(sql, salon_name, province_id, city_id, domain_id)
        entry = self.db.get(sql, *params)
        if entry is None:
            return 0
        else:
            return entry.cnt


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
            default_img="/static/" + get_default_img_path(),

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
