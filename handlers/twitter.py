#!/usr/bin/env python
# coding: utf-8

import json
import tornado.web
from handlers.base import BaseHandler
from ext.pagination import Pagination
from ext.informer import BootstrapInformer


class TwitterBaseHandler(BaseHandler):
    config = {
        "from_type": {
            0: "用户发布",
            1: "发型师发布",
            2: "杂志发布",
            3: "发品公司发布",
        },
        "share_type": {
            1: "秀发型",
            2: "我要美发",
            3: "洗护问题",
            4: "沙龙优惠",
        },
        "actived": {
            0: "未审核",
            1: "已经审核",
            2: "用户已删除",
            3: "系统已强制删除",
            4: "未上传完成",
            5: "隐藏",
            6: "屏蔽",
            9: "隐藏",
        },
        'member_type': {
            1: '普通用户',
            2: '发型师',
        },
        'love_type': {
            0: '不喜欢',
            1: '喜欢',
            -1: '无状态',
        },
        'hair_face': {
            1: '圆脸',
            2: '长脸',
            4: '方脸',
            8: '瓜子脸',
        },
        'hair_volume': {
            1: '多密',
            2: '中等',
            4: '偏少',
        },
        'easy_style': {
            0: '可居家打理',
            1: '需专业打理',
        },
    }

    def stylist_type_id(self):
        return 2

    def user_type_id(self):
        return 1

    def gen_query_str(self, sql, **args):
        query_str = []
        params = []

        if args.get("share_type"):
            query_str.append("share_type = %s")
            params.append(args.get("share_type")[0])

        if args.get("actived"):
            query_str.append("m.actived = %s")
            params.append(args.get("actived")[0])

        if args.get("start_date"):
            query_str.append("m.createtime >= %s")
            start_date = self.convert_date_to_timestamp(args.get("start_date")[0])
            params.append(start_date)

        if args.get("end_date"):
            query_str.append("m.createtime <= %s")
            end_date = self.convert_date_to_timestamp(args.get("end_date")[0])
            params.append(end_date)

        if args.get("description"):
            query_str.append("m.description like %s")
            params.append("%" + args.get("description")[0] + "%")

        if args.get("member_type"):
            query_str.append("member_type = %s")
            params.append(args.get("member_type")[0])

        if args.get("username"):
            query_str.append("username = %s")
            params.append(args.get("username")[0])

        if args.get("email"):
            query_str.append("email = %s")
            params.append(args.get("email")[0])

        if query_str:
            query_str = " and ".join(query_str)
            sql = sql + " and " + query_str

        return sql, params

    def query_twitters(self, **args):
        sql = '''
            select m.id, m.share_type, m.createtime, from_unixtime(m.createtime) as createtime_str,
                m.actived, s.description, s.comment_num,
                p.id as pic_id, p.pic_url, p.img_path, p.img_type,
                u.id as uid, u.username, u.member_type
            from md_twitter m, md_twitter_show s, md_twitter_picture p, md_member u
            where m.id = s.tid and s.pic_id = p.id and m.member_id = u.id
        '''
        sql, params = self.gen_query_str(sql, **args)

        page = args.get("page", [1])[0]
        sql = Pagination.add_limit_clause(sql, page)

        return self.db.query(sql, *params)

    def query_twitters_count(self, **args):
        sql = '''
            select count(*) as cnt
            from md_twitter m, md_twitter_show s, md_twitter_picture p, md_member u
            where m.id = s.tid and s.pic_id = p.id and m.member_id = u.id
        '''
        sql, params = self.gen_query_str(sql, **args)
        entry = self.db.get(sql, *params)
        if entry:
            return entry.cnt
        else:
            return 0

    def fetch_twitter_by_id(self, id):
        sql = '''
            select m.id, m.share_type, m.createtime, from_unixtime(m.createtime) as createtime_str,
                m.actived, s.description, s.comment_num, s.hair_face, s.hair_volume, s.easy_style,
                p.pic_url, p.img_path, p.img_type,
                u.id as uid, u.username, u.member_type, u.email
            from md_twitter m, md_twitter_show s, md_twitter_picture p, md_member u
            where m.id = s.tid and s.pic_id = p.id and m.member_id = u.id and m.id = %s
        '''
        return self.db.get(sql, id)

    def fetch_comments_by_twitter_id(self, twitter_id):
        return self.db.query("select c.id, c.member_type, c.createtime, "
                "from_unixtime(c.createtime) as createtime_str, c.content, "
                "c.love_type, m.username, m.email "
                "from md_twitter_comment c, md_member m "
                "where c.member_id = m.id and tid = %s", twitter_id)

    def real_pic_url(self, entry):
        path_prefix = self.get_twitter_path_prefix()
        url = path_prefix + "/" + entry.img_path + "/" + entry.pic_url + "_small." + entry.img_type
        url = url.replace("//", "/")
        return self.path_to_url(url)

    def check_hair_config(self, entry, attr):
        '''检查缩略图的发型特征，返回发行特征的配置项列表
        注意，self.config配置项名称需要与数据库字段名称保持一致
        例如，md_twitter_show.hair_face对应self.config['hair_face']
        '''
        dataset = {}
        for k, v in self.config[attr].items():
            if entry[attr] & k == k:
                dataset.setdefault(k, v)
        return dataset


class TwitterHandler(TwitterBaseHandler):
    @tornado.web.authenticated
    def post(self, id):
        args = self.request.arguments
        args.pop('_xsrf')

        setters = []
        for k, v in args.items():
            setters.append("%s = %s" % (k, v[0]))

        if not setters:
            self.write(json.dumps({'code': 0}))
            return

        try:
            self.db.execute("update md_twitter set " + ",".join(setters) + " where id = %s", id)
            self.write(json.dumps({'code': 0}))
        except Exception, e:
            self.write(json.dumps({
                'code': -1,
                'error': e,
            }))


class TwitterListHandler(TwitterBaseHandler):
    @tornado.web.authenticated
    def get(self):
        entries = self.query_twitters(**self.request.arguments)
        count = self.query_twitters_count(**self.request.arguments)
        page_count = Pagination.page_count(count)
        informer = BootstrapInformer("success", "共 %s 条记录" % count, "查询结果")

        # 图片的URL地址
        for entry in entries:
            entry["real_pic_url"] = self.real_pic_url(entry)

        # 查询参数由数组变为数值
        dataset = {}
        for k, v in self.request.arguments.items():
            dataset.setdefault(k, list(v)[0])

        params = dict(
            entries=entries,
            config=self.config,
            page_count=page_count,
            informer=informer,
            args=dataset,
        )
        self.render("twitters/index.html", **params)


class TwitterEditHandler(TwitterBaseHandler):
    @tornado.web.authenticated
    def get(self, id):
        entry = self.fetch_twitter_by_id(id)
        if not entry:
            raise tornado.web.HTTPError(404)

        entry["real_pic_url"] = self.real_pic_url(entry)
        comments = self.fetch_comments_by_twitter_id(id)

        params = dict(
            config=self.config,
            entry=entry,
            comments=comments,

            # 缩略图信息
            hair_face=self.check_hair_config(entry, 'hair_face'),
            hair_volume=self.check_hair_config(entry, 'hair_volume'),
            easy_style=self.check_hair_config(entry, 'easy_style'),
        )
        self.render("twitters/edit.html", **params)

    @tornado.web.authenticated
    def post(self, id):
        try:
            # 去掉_xsrf参数
            args = self.request.arguments
            args.pop('_xsrf')

            setter = []
            easy_style = self.get_argument("easy_style", 0)
            args.pop('easy_style')
            setter.append("easy_style = %s" % easy_style)

            dataset = {}
            for e in args.keys():
                items = e.split('_')
                k = '_'.join(items[:-1])
                v = items[-1]
                dataset[k] = dataset.get(k, 0) + int(v)

            tmpl = "%s = %s"
            for k, v in dataset.items():
                setter.append(tmpl % (k, v))

            sql = "update md_twitter_show set " + ",".join(setter) + " where id = %s"
            self.db.execute(sql, id)
            self.redirect("/twitters/edit/%s" % id)
        except Exception, e:
            print e
            self.redirect("/twitters/edit/%s" % id)


class TwitterCommentDeleteHandler(TwitterBaseHandler):
    @tornado.web.authenticated
    def post(self, id):
        import json
        entry = self.db.get("select tid, member_id from md_twitter_comment where id = %s", id)
        if not entry:
            return
        else:
            tid = entry.tid
            member_id = entry.member_id

        # 计数减1
        try:
            self.db.execute("update md_twitter_show set comment_num = comment_num - 1 "
                    "where tid = %s", tid)
            self.write(json.dumps({
                'code': 0,
            }))
        except Exception, e:
            self.write(json.dumps({
                'code': -1,
                'error': unicode(e),
            }))
            return

        # 删除记录
        try:
            self.db.execute("delete from md_twitter_comment where id = %s", id)
        except Exception, e:
            self.db.execute("update md_twitter_show set comment_num = comment_num + 1 "
                    "where member_id = %s and tid = %s", member_id, tid)
            self.write(json.dumps({
                'code': -1,
                'error': unicode(e),
            }))
