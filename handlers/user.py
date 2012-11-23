#!/usr/bin/env python
# coding: utf-8

import datetime
import tornado.web
from base import BaseHandler, none_to_empty_str
from ext.informer import BootstrapInformer


class UserBaseHandler(BaseHandler):
    # 分页（Pagination）需要考虑的几个问题：
    # <limit m, n>方式的分页在大数据集上的表现不好，基本可以排除；
    # 推荐采用的方式为<where id > 0 limit 10>，即按步长递增ID，通过传入不同的ID实现分页
    # 这个方法仍然存在问题：
    #   ID可能并不是有序的（比如，频繁删除并新增数据的表，可能出现后面的数据使用较小ID的情况）
    #   数据需要按照其它字段排序，然后按照这个排序结果分页，此时，ID几乎不可能是有序的
    # 因此，推荐方法的实质应该是：根据排序的键值进行分页，而非根据ID分页
    # 在这个排序的键值上建立索引（多键值则建立复合索引）
    # 即：需要在SQL的where子句里填充比较操作，并且在order by子句里填充排序操作
    # key = [{'id': (0, 'asc')}, {'regtime': (0, 'desc')}]

    def fetch_user(self, uid):
        user = self.db.get("select *, from_unixtime(regtime) as regtime_str, "
                "from_unixtime(last_modifytime) as last_modifytime_str, "
                "from_unixtime(s.lastlogintime) as lastlogintime_str "
                "from md_member m left outer join md_member_statistics s "
                "on m.id = s.member_id where m.id = %s", uid)
        for k, v in user.items():
            user[k] = none_to_empty_str(user[k])
        return user

    def update_user(self, uid, **args):
        # 删除NoneType的数据项
        for k in args.keys():
            if args.get(k) is None:
                args.pop(k)
        # 更新数据库
        tmpl = "update md_member set %s = %%s where id = %s"
        setters = map(lambda x: x + ' = %s', args.keys())
        if len(setters) == 0:
            return
        else:
            tmpl = "update md_member set " + ", ".join(setters) + " where id = %s"
            params = args.values()
            params.append(uid)
            self.db.execute(tmpl, *params)

    def query_users(self, **args):
        sql = '''
            select m.id, m.username, m.email, m.member_type, m.regtime,
                m.actived, s.works_count, s.lastlogintime, s.twitter_num, s.emotion_num,
                from_unixtime(m.regtime) as regtime_str,
                from_unixtime(s.lastlogintime) as lastlogintime_str
            from md_member m left outer join md_member_statistics s on m.id = s.member_id
        '''

        query = []  # 保存SQL查询条件
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

        sql = sql + query_str

        return self.db.query(sql, *params)


class UserHandler(UserBaseHandler):
    def get(self):
        query_params = dict(
            member_type=self.get_argument("member_type", None),
            actived=self.get_argument("actived", None),
            province_id=self.get_argument("province_id", None),
            city_id=self.get_argument("city_id", None),
            username=self.get_argument("username", ""),
            email=self.get_argument("email", ""),
            regtime_from=self.get_argument("regtime_from", ""),
            regtime_to=self.get_argument("regtime_to", str(datetime.date.today())),
            lastlogintime_from=self.get_argument("lastlogintime_from", ""),
            lastlogintime_to=self.get_argument("lastlogintime_to", str(datetime.date.today())),
        )

        try:
            entries = self.query_users(**query_params)
        except Exception, e:
            print e
            self.redirect("/users")
            return

        params = dict(
            provinces=self.fetch_provinces(),
            entries=entries,
            query_params=query_params,
            config=self.config,
            informer=BootstrapInformer("success", "共 %s 条记录" % len(entries), "查询结果：")
        )
        self.render("users/index.html", **params)


class UserDetailHandler(UserBaseHandler):
    def get(self, id):
        user = self.fetch_user(id)
        self.render("users/show.html", user=user)


class UserEditHandler(UserBaseHandler):
    def get(self, id):
        params = dict(
            user=self.fetch_user(id),
            config=self.config,
        )
        self.render("users/edit.html", **params)

    def post(self, id):
        args = dict(
            # basic info
            username=self.get_argument("username", None),
            actived=self.get_argument("actived", None),
            email=self.get_argument("email", None),
            gender=self.get_argument("gender", None),
            province_id=self.get_argument("province_id", None),
            city_id=self.get_argument("city_id", None),
            sign_text=self.get_argument("sign_text", None),
            avatar_id=self.get_argument("avatar_id", None),

            # common users
            hair_face=self.get_argument("hair_face", None),
            hair_quality=self.get_argument("hair_quality", None),
            hair_volume=self.get_argument("hair_volume", None),

            # stylists
            recommend=self.get_argument("recommend", None),
            salon_id=self.get_argument("salon_id", None),
            mobile=self.get_argument("mobile", None),
            price_haircut=self.get_argument("price_haircut", None),
            price_perm=self.get_argument("price_perm", None),
            price_dye=self.get_argument("price_dye", None),
            price_care=self.get_argument("price_care", None),
        )

        user = self.fetch_user(id)
        try:
            self.update_user(id, **args)
        except Exception, e:
            informer = BootstrapInformer('error', e)
            self.render("users/edit.html", user=user, config=self.config, informer=informer)
            return
        self.redirect("/users")


class UserEditBasicModule(tornado.web.UIModule):
    def render(self, user):
        params = dict(
            user=user,
            config=self.handler.config,
            provinces=self.handler.fetch_provinces(),
            cities=self.handler.fetch_cities(),
        )
        return self.render_string("users/_basic.html", **params)
