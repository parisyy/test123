#!/usr/bin/env python
# coding: utf-8

import time
import datetime
import tornado.web
from base import BaseHandler, none_to_empty_str
from ext.informer import BootstrapInformer
from ext.pagination import Pagination


class UserBaseHandler(BaseHandler):
    config = {
        'member_type': {
            1: '普通用户',
            2: '发型师',
        },
        'actived': {
            0: '未激活',
            1: '激活',
            2: '已禁用',
            3: '用户未通过审核（仅发型师）',
            4: '等待审核(仅发型师)',
            5: '已通过认证（仅发型师）',
            6: '申请修改资料（仅发型师）',
            7: '小号',
        },
        'gender': {
            0: '男',
            1: '女',
            2: '保密',
        },
        'haircut_price': {
            1: '小于100',
            2: '100~200',
            3: '200~300',
            4: '大于300',
        },
        'price': {
            1: '小于300',
            2: '300~600',
            3: '600~1000',
            4: '大于1000',
        },
        'recommend': {
            0: '否',
            1: '是',
        },
        'recommend_talent': {
            0: '否',
            1: '是',
        },
        'hair_face': {
            1: '圆脸',
            2: '长脸',
            4: '方脸',
            8: '瓜子脸',
        },
        'hair_quality': {
            1: '天然卷',
            2: '粗硬',
            4: '中等',
            8: '细软',
        },
        'hair_volume': {
            1: '多密',
            2: '中等',
            4: '偏少',
        },
    }

    def fetch_user(self, uid):
        user = self.db.get("select m.*, from_unixtime(regtime) as regtime_str, "
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
        setters.append("last_modifytime = %s")
        if len(setters) == 0:
            return
        else:
            tmpl = "update md_member set " + ", ".join(setters) + " where id = %s"
            params = args.values()
            params.append(time.mktime(datetime.datetime.now().timetuple()))
            params.append(uid)
            self.db.execute(tmpl, *params)

    def query_users_where_clause(self, **args):
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

        if args["mobile"]:
            query.append("mobile = %s")
            params.append(args["mobile"])

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

    def query_users_size(self, **args):
        sql = '''
            select count(distinct m.id) as cnt
            from md_member m left outer join md_member_statistics s on m.id = s.member_id
        '''
        query_str, params = self.query_users_where_clause(**args)
        sql = sql + query_str

        entry = self.db.get(sql, *params)
        if entry is None:
            return 0
        else:
            return entry.cnt

    def query_users(self, **args):
        sql = '''
            select m.id, m.username, m.email, m.member_type, m.regtime, m.recommend,
                m.province_id, m.city_id, m.recommend_talent,
                m.actived, s.works_count, s.lastlogintime, s.twitter_num, s.emotion_num,
                from_unixtime(m.regtime) as regtime_str,
                from_unixtime(s.lastlogintime) as lastlogintime_str
            from md_member m left outer join md_member_statistics s on m.id = s.member_id
        '''
        query_str, params = self.query_users_where_clause(**args)
        sql = sql + query_str
        sql = sql + " order by m.id desc "
        sql = Pagination.add_limit_clause(sql, args["page"])
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
            mobile=self.get_argument("mobile", None),
            regtime_from=self.get_argument("regtime_from", ""),
            regtime_to=self.get_argument("regtime_to", str(datetime.date.today())),
            lastlogintime_from=self.get_argument("lastlogintime_from", ""),
            lastlogintime_to=self.get_argument("lastlogintime_to", str(datetime.date.today())),
            page=self.get_argument("page", 1)
        )

        try:
            regions = self.fetch_all_regions()
            entries = self.query_users(**query_params)
            count = self.query_users_size(**query_params)
            page_count = Pagination.page_count(count)
        except Exception, e:
            print e
            self.redirect("/users")
            return

        params = dict(
            regions=regions,
            entries=entries,
            query_params=query_params,
            config=self.config,
            informer=BootstrapInformer("success", "共 %s 条记录" % count, "查询结果："),
            page_count=page_count,
        )
        self.render("users/index.html", **params)


class UserDetailHandler(UserBaseHandler):
    def get(self, id):
        user = self.fetch_user(id)
        self.render("users/show.html", user=user)


class UserEditHandler(UserBaseHandler):
    def get(self, id):
        avatar_pic = self.get_avatar_pic(id)

        params = dict(
            user=self.fetch_user(id),
            config=self.config,
            avatar_pic=avatar_pic,
            tags=self.fetch_all_tags(),
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
            area_id=self.get_argument("domain_id", None),
            sign_text=self.get_argument("sign_text", None),
            avatar_id=self.get_argument("avatar_id", None),

            # common users
            hair_face=self.get_argument("hair_face", None),
            hair_quality=self.get_argument("hair_quality", None),
            hair_volume=self.get_argument("hair_volume", None),

            # stylists
            recommend=self.get_argument("recommend", None),
            recommend_talent=self.get_argument("recommend_talent", None),
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
        if user.province_id:
            cities = self.handler.fetch_cities_by_province_id(user.province_id)
        else:
            cities = self.handler.fetch_cities()

        if user.city_id:
            domains = self.handler.fetch_domains_by_city_id(user.city_id)
        else:
            domains = self.handler.fetch_domains()

        params = dict(
            user=user,
            config=self.handler.config,
            provinces=self.handler.fetch_provinces(),
            cities=cities,
            domains=domains,
            avatar_pic=self.handler.get_avatar_pic(user.id),
        )
        return self.render_string("users/_basic.html", **params)
