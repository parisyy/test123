#!/usr/bin/env python
# coding: utf-8

import re
import urlparse
import tornado.web


class UserQueryModule(tornado.web.UIModule):
    def render(self):
        query_params = dict(
            member_type=self.handler.get_argument("member_type", None),
            actived=self.handler.get_argument("actived", None),
            province_id=self.handler.get_argument("province_id", None),
            city_id=self.handler.get_argument("city_id", None),
            username=self.handler.get_argument("username", ""),
            email=self.handler.get_argument("email", ""),
            mobile=self.handler.get_argument("mobile", ""),
            regtime_from=self.handler.get_argument("regtime_from", ""),
            regtime_to=self.handler.get_argument("regtime_to", ""),
            lastlogintime_from=self.handler.get_argument("lastlogintime_from", ""),
            lastlogintime_to=self.handler.get_argument("lastlogintime_to", ""),
        )
        params = dict(
            provinces=self.handler.fetch_provinces(),
            cities=self.handler.fetch_cities(),
            query_params=query_params,
            config=self.handler.config,
        )
        return self.render_string("modules/user_query/_query.html", **params)


class PictureListModule(tornado.web.UIModule):
    def render(self, pics, path_prefix):
        pics = [pic for pic in pics if pic.img_path is not None and pic.pic_url is not None]
        params = dict(
            pics=pics,
            path_prefix=path_prefix,
        )
        return self.render_string("modules/pic_list/_list.html", **params)


class PaginationModule(tornado.web.UIModule):
    def uri_without_keyword(self, key):
        parsed = urlparse.urlparse(self.handler.request.uri)
        query = [e for e in parsed.query.split('&') if e != "" and not re.match("%s=" % key, e)]
        return parsed.path + '?' + '&'.join(query)

    def render(self, page_count):
        base_url = self.uri_without_keyword("page")
        page = self.handler.get_argument("page", 1)

        params = dict(
            base_url=base_url,
            page=page,
            page_count=page_count,
        )
        return self.render_string("modules/_pagination.html", **params)
