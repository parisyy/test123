#!/usr/bin/env python
# coding: utf-8

import json
from handlers.base import BaseHandler
from handlers.user import UserBaseHandler
from ext.informer import BootstrapInformer
from ext.pagination import Pagination


class StarBaseHandler(UserBaseHandler):
    def query_users_where_clause(self, **args):
        query = ["recommend = 2"]  # 保存SQL查询条件
        params = []  # 保存SQL查询参数

        if args["member_type"] is not None:
            query.append("member_type = %s")
            params.append(args["member_type"])

        if args["actived"] is not None:
            query.append("actived = %s")
            params.append(args["actived"])

        if args["province_id"] is not None:
            query.append("province_id = %s")
            params.append(args["province_id"])

        if args["city_id"] is not None:
            query.append("city_id = %s")
            params.append(args["city_id"])

        if args["username"]:
            query.append("username like %s")
            params.append('%' + args["username"] + '%')

        if args["email"]:
            query.append("email = %s")
            params.append(args["email"])

        if args["regtime_from"] and args["regtime_to"]:
            datetime_start = self.convert_to_timestamp(args["regtime_from"] + " 00:00:00")
            datetime_end = self.convert_to_timestamp(args["regtime_to"] + " 23:59:59")
            # 数据库里保存的是TIMESTAMP类型
            query.append("regtime >= %s and regtime <= %s")
            params.append(datetime_start)
            params.append(datetime_end)

        if args["lastlogintime_from"] and args["lastlogintime_to"]:
            datetime_start = self.convert_to_timestamp(args["lastlogintime_from"] + " 00:00:00")
            datetime_end = self.convert_to_timestamp(args["lastlogintime_to"] + " 23:59:59")
            # 数据库里保存的是TIMESTAMP类型
            query.append("lastlogintime >= %s and lastlogintime <= %s")
            params.append(datetime_start)
            params.append(datetime_end)

        # 拼接SQL的where查询条件
        if query != []:
            query_str = "where " + " and ".join(query)
        else:
            query_str = ""

        return query_str, params


class StarHandler(StarBaseHandler):
    def get(self):
        query_params = dict(
            member_type=self.get_argument("member_type", None),
            actived=self.get_argument("actived", None),
            province_id=self.get_argument("province_id", None),
            city_id=self.get_argument("city_id", None),
            username=self.get_argument("username", ""),
            email=self.get_argument("email", ""),
            regtime_from=self.get_argument("regtime_from", ""),
            regtime_to=self.get_argument("regtime_to", ""),
            lastlogintime_from=self.get_argument("lastlogintime_from", ""),
            lastlogintime_to=self.get_argument("lastlogintime_to", ""),
            page=self.get_argument("page", 1)
        )

        try:
            entries = self.query_users(**query_params)
            count = self.query_users_size(**query_params)
            page_count = Pagination.page_count(count)
        except Exception, e:
            print e
            self.redirect("/stars")
            return

        params = dict(
            provinces=self.fetch_provinces(),
            entries=entries,
            query_params=query_params,
            config=self.config,
            informer=BootstrapInformer("success", "共 %s 条记录" % count, "查询结果："),
            page_count=page_count,
        )

        self.render("stars/index.html", **params)

    def delete(self, id):
        try:
            self.db.execute("update md_member set recommend = 0 where id = %s", id)
            self.write(json.dumps({'code': 0}))
        except Exception, e:
            self.write(json.dumps({
                'code': -1,
                'error': str(e),
            }))


class StarRecommendHandler(BaseHandler):
    def get(self, id):
        pics = self.db.query("select t.id, t.member_id, t.actived, p.tid, tp.* "
                "from md_talent t, md_talent_picture p, md_theme_picture tp "
                "where t.id = p.talent_id and p.tid = tp.id and t.member_id = %s", id)
        self.render("stars/recommend.html", pics=pics)
