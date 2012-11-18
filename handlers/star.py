#!/usr/bin/env python
# coding: utf-8

from handlers.base import BaseHandler
from ext.informer import BootstrapInformer


class StarBaseHandler(BaseHandler):
    def query_users(self, **args):
        sql = '''
            select m.id, m.username, m.email, m.member_type, m.regtime,
                m.actived, s.works_count, s.lastlogintime, s.twitter_num, s.emotion_num,
                from_unixtime(m.regtime) as regtime_str,
                from_unixtime(s.lastlogintime) as lastlogintime_str
            from md_member m left outer join md_member_statistics s on m.id = s.member_id
        '''

        query = ["recommend = 1"]  # 保存SQL查询条件
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
            query.append("username = %s")
            params.append(args["username"])

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

        sql = sql + query_str

        return self.db.query(sql, *params)


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
        )

        try:
            entries = self.query_users(**query_params)
        except:
            self.redirect("/users")

        params = dict(
            provinces=self.fetch_provinces(),
            entries=entries,
            query_params=query_params,
            config=self.config,
            informer=BootstrapInformer("success", "共%s条记录" % len(entries), "查询结果：")
        )

        self.render("stars/index.html", **params)
