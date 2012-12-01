#!/usr/bin/env python
# coding: utf-8

import json
import time
import datetime
import tornado.web
from handlers.base import BaseHandler
from ext.informer import BootstrapInformer
from ext.pagination import Pagination


class SeasonBaseHandler(BaseHandler):
    def fetch_all_seasons(self, page):
        sql = '''select *, date(from_unixtime(createtime)) as createtime_str
                from md_season_period order by createtime desc'''
        sql = Pagination.add_limit_clause(sql, page)
        return self.db.query(sql)

    def fetch_all_seasons_size(self):
        entry = self.db.get("select count(*) as cnt from md_season_period")
        if entry is None:
            return 0
        else:
            return entry.cnt

    def fetch_season(self, id):
        return self.db.get("select *, date(from_unixtime(start_time)) as start_time_str, "
                "date(from_unixtime(end_time)) as end_time_str "
                "from md_season_period where id = %s", id)

    def fetch_all_users(self):
        return self.db.query("select id, username, email from md_member")

    def fetch_season_pics(self, period_id):
        return self.db.query("select * from md_theme_picture p, md_season_picture s "
                "where p.id = s.tid and s.period_id = %s", period_id)


class SeasonHandler(SeasonBaseHandler):
    @tornado.web.authenticated
    def get(self):
        page = self.get_argument("page", 1)
        seasons = self.fetch_all_seasons(page)
        count = self.fetch_all_seasons_size()
        page_count = Pagination.page_count(count)

        params = dict(
            seasons=seasons,
            informer=BootstrapInformer("success", "共 %s 条记录" % len(seasons), "查询结果："),
            page_count=page_count,
        )
        self.render("seasons/index.html", **params)


class SeasonNewHandler(SeasonBaseHandler):
    @tornado.web.authenticated
    def get(self):
        params = dict(
            pics=[],
            packages=self.fetch_packages(),
            path_prefix=self.path_to_url(self.get_subject_path_prefix()),
        )
        self.render("seasons/new.html", **params)

    @tornado.web.authenticated
    def post(self):
        try:
            period_name = self.get_argument("period_name", "未知主题名称")
            content = self.get_argument("content", "")
            package_id = self.get_argument("package_id", 0)
            start_time = self.get_argument("start_time", "2012-01-01")
            end_time = self.get_argument("end_time", "2012-01-01")
            theme_pic_id = self.get_argument("theme_pic_id", 0)
            theme_pic_url = self.get_argument("theme_pic_url", "")
            pic_ids = self.get_argument("pic_ids", "")

            if isinstance(start_time, str) or isinstance(start_time, unicode):
                start_time = self.convert_date_to_timestamp(start_time)
            if isinstance(end_time, str) or isinstance(end_time, unicode):
                end_time = self.convert_date_to_timestamp(end_time)
            createtime = time.mktime(datetime.datetime.now().timetuple())

            id = self.db.execute("insert into md_season_period(period_name, content, package_id, "
                    "start_time, end_time, createtime, theme_pic_id, theme_pic_url, actived) "
                    "values(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    period_name, content, package_id, start_time, end_time, createtime,
                    theme_pic_id, theme_pic_url, "N")

            pic_ids = pic_ids.split(",")
            for pic_id in pic_ids:
                if pic_id:
                    self.db.execute("insert into md_season_picture(period_id, tid, actived) "
                            "values(%s, %s, %s)", id, pic_id, 'Y')

            self.redirect("/seasons")
        except Exception, e:
            params = dict(
                pics=[],
                packages=self.fetch_packages(),
                informer=BootstrapInformer("error", e),
                path_prefix=self.path_to_url(self.get_subject_path_prefix()),
            )
            self.render("seasons/new.html", **params)


class SeasonEditHandler(SeasonBaseHandler):
    @tornado.web.authenticated
    def get(self, id):
        season = self.fetch_season(id)
        pics = self.fetch_season_pics(id)
        path_prefix = self.path_to_url(self.get_subject_path_prefix())
        pic_url = path_prefix + "/" + self.pic_url(season.theme_pic_id)

        params = dict(
            season=season,
            packages=self.fetch_packages(),
            pic_url=pic_url,
            pics=pics,
            path_prefix=path_prefix,
        )
        self.render("seasons/edit.html", **params)

    @tornado.web.authenticated
    def post(self, id):
        season = self.fetch_season(id)

        season["period_name"] = self.get_argument("period_name", season.period_name)
        season["content"] = self.get_argument("content", season.content)
        season["package_id"] = self.get_argument("package_id", season.package_id)
        season["start_time"] = self.get_argument("start_time", season.start_time)
        season["end_time"] = self.get_argument("end_time", season.end_time)
        season["theme_pic_id"] = self.get_argument("theme_pic_id", season.theme_pic_id)
        season["theme_pic_url"] = self.get_argument("theme_pic_url", season.theme_pic_url)

        pic_ids = self.get_argument("pic_ids", "")

        try:
            if isinstance(season.start_time, str) or isinstance(season.start_time, unicode):
                season["start_time"] = self.convert_date_to_timestamp(season.start_time)
            if isinstance(season.end_time, str) or isinstance(season.end_time, unicode):
                season["end_time"] = self.convert_date_to_timestamp(season.end_time)

            self.db.execute("update md_season_period set period_name = %s, content = %s, "
                    "package_id = %s, start_time = %s, end_time = %s, "
                    "theme_pic_id = %s, theme_pic_url = %s where id = %s",
                    season.period_name, season.content, season.package_id, season.start_time,
                    season.end_time, season.theme_pic_id, season.theme_pic_url, season.id)

            pic_ids = pic_ids.split(",")
            for pic_id in pic_ids:
                if pic_id:
                    self.db.execute("insert into md_season_picture(period_id, tid, actived) "
                            "values(%s, %s, %s)", id, pic_id, 'Y')

            self.redirect("/seasons")
        except Exception, e:
            path_prefix = self.path_to_url(self.get_subject_path_prefix())
            pic_url = path_prefix + "/" + self.pic_url(season.theme_pic_id)
            params = dict(
                season=season,
                packages=self.fetch_packages(),
                informer=BootstrapInformer("error", e),
                pic_url=pic_url,
                pics=self.fetch_season_pics(id),
                path_prefix=path_prefix,
            )
            self.render("seasons/edit.html", **params)


class PictureSelectorHandler(SeasonBaseHandler):
    @tornado.web.authenticated
    def get(self):
        members = self.fetch_all_users()

        params = dict(
            members=members,
            path_prefix=self.path_to_url(self.get_subject_path_prefix()),
        )
        self.render("seasons/selector.html", **params)

    @tornado.web.authenticated
    def post(self):
        pic_id = self.get_argument("pic_id", 0)
        member_id = self.get_argument("member_id", 0)
        
        if pic_id == 0 and member_id == 0:
            entries = []

        if pic_id != 0:
            entries = self.db.get("select * from md_theme_picture where id = %s", pic_id)

        if entries is None or entries == []:
            self.write(json.dumps({'code': -1}))
        else:
            self.write(json.dumps({
                'code': 0,
                'pics': entries,
            }))
