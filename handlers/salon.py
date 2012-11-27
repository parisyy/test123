#!/usr/bin/env python
# coding: utf-8

from handlers.base import BaseHandler
from ext.pagination import Pagination


class SalonBaseHandler(BaseHandler):
    config = {
        "recommend": {
            0: '未推荐',
            1: '已推荐',
        },
    }

    def fetch_all_salons(self, page):
        sql = '''
            select m.*, s.salon_pic_url from md_salon m left outer join md_salon_picture s
            on m.id = s.salon_id and s.is_logo = 'Y'
        '''
        sql = Pagination.add_limit_clause(sql, page)
        return self.db.query(sql)

    def fetch_all_salons_size(self):
        entry = self.db.get("select count(*) as cnt from md_salon")
        if entry is None:
            return 0
        else:
            return entry.cnt


class SalonHandler(SalonBaseHandler):
    def get(self):
        page = self.get_argument("page", 1)

        salons = self.fetch_all_salons(page)
        page_count = Pagination.page_count(self.fetch_all_salons_size())

        params = dict(
            salons=salons,
            regions=self.fetch_all_regions(),
            page_count=page_count
        )
        self.render("salons/index.html", **params)
