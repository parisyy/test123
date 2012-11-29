#!/usr/bin/env python
# coding: utf-8

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
    }

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
            query_str.append("client_createtime >= %s")
            start_date = self.convert_date_to_timestamp(args.get("start_date")[0])
            params.append(start_date)

        if args.get("end_date"):
            query_str.append("client_createtime <= %s")
            end_date = self.convert_date_to_timestamp(args.get("end_date")[0])
            params.append(end_date)

        if args.get("description"):
            query_str.append("description like %s")
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
            select m.id, m.share_type, m.client_createtime,
                m.actived, s.description, s.comment_num,
                p.pic_url, p.img_path, p.img_type,
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


class TwitterHandler(TwitterBaseHandler):
    def get(self):
        entries = self.query_twitters(**self.request.arguments)
        count = self.query_twitters_count(**self.request.arguments)
        page_count = Pagination.page_count(count)
        informer = BootstrapInformer("success", "共 %s 条记录" % count, "查询结果")

        # 图片的URL地址
        for entry in entries:
            path_prefix = self.get_twitter_path_prefix()
            entry["real_pic_url"] = path_prefix + "/" + entry.img_path + "/" + entry.pic_url + "." + entry.img_type
            entry["real_pic_url"].replace("//", "/")
            entry["real_pic_url"] = self.path_to_url(entry["real_pic_url"])

        params = dict(
            entries=entries,
            config=self.config,
            page_count=page_count,
            informer=informer,
            args=self.request.arguments,
        )
        self.render("twitters/index.html", **params)
