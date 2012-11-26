#!/usr/bin/env python
# coding: utf-8

import json
from handlers.base import BaseHandler


class RegionBaseHandler(BaseHandler):
    def fetch_all_provinces(self):
        return self.db.query("select * from md_region where level = 1")

    def fetch_all_cities(self):
        return self.db.query("select * from md_region where level = 2")

    def fetch_all_domains(self):
        return self.db.query("select * from md_region where level = 3")

    def fetch_cities_by_province_id(self, province_id):
        return self.db.query("select * from md_region where level = 2 and parent_id = %s", province_id)

    def fetch_domains_by_city_id(self, city_id):
        return self.db.query("select * from md_region where level = 3 and parent_id = %s", city_id)


class RegionHandler(RegionBaseHandler):
    def get(self):
        try:
            data_type = int(self.get_argument("type"))

            if data_type == 1:
                entries = self.fetch_all_provinces()

            if data_type == 2:
                entries = self.fetch_all_cities()

            if data_type == 3:
                entries = self.fetch_all_domains()

            if data_type == 4:
                print 'aaa'
                province_id = int(self.get_argument("region_id"))
                entries = self.fetch_cities_by_province_id(province_id)

            if data_type == 5:
                city_id = int(self.get_argument("region_id"))
                entries = self.fetch_domains_by_city_id(city_id)

            #tmpl = '''<option value="%s">%s</option>'''
            #data = "\n".join([tmpl % (e.id, e.region_name) for e in entries])

            self.write(json.dumps({
                'code': 0,
                'data': entries,
            }))
        except Exception, e:
            self.write(json.dumps({
                'code': -1,
                'error': str(e),
            }))
