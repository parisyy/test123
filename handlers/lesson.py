#!/usr/bin/env python
# coding: utf-8

import time
import datetime
import tornado.web
from handlers.base import BaseHandler
from ext.informer import BootstrapInformer, Informer
from ext.pagination import Pagination


class LessonBaseHandler(BaseHandler):
    def fetch_all_lessons(self, page):
        sql = '''select d.id, subject_name, username, from_unixtime(createtime) as createtime,
                date(from_unixtime(start_time)) as start_time, date(from_unixtime(end_time)) as end_time,
                d.actived from md_diy_subject d left join md_member m on d.member_id = m.id
                order by createtime desc'''
        sql = Pagination.add_limit_clause(sql, page)
        return self.db.query(sql)

    def fetch_all_lessons_size(self):
        entry = self.db.get("select count(*) as cnt from md_diy_subject")
        if entry is None:
            return 0
        else:
            return entry.cnt

    def fetch_lesson(self, id):
        return self.db.get("select d.id, subject_name, username, content, member_id, "
                "from_unixtime(createtime) as createtime, "
                "date(from_unixtime(start_time)) as start_time, date(from_unixtime(end_time)) as end_time, "
                "d.actived from md_diy_subject d left join md_member m on d.member_id = m.id "
                "where d.id = %s", id)

    def fetch_all_pics(self, id):
        return self.db.query("select * from md_diy_subject_content d, md_theme_picture p "
                "where d.theme_pic_id = p.id and subject_id = %s", id)


class LessonHandler(LessonBaseHandler):
    @tornado.web.authenticated
    def get(self):
        page = self.get_argument("page", 1)
        lessons = self.fetch_all_lessons(page)
        count = self.fetch_all_lessons_size()
        page_count = Pagination.page_count(count)

        params = dict(
            lessons=lessons,
            informer=BootstrapInformer("success", "共 %s 条记录" % len(lessons), "查询结果："),
            page_count=page_count,
        )
        self.render("lessons/index.html", **params)


class LessonNewHandler(LessonBaseHandler):
    @tornado.web.authenticated
    def get(self):
        params = dict(
            stylists=self.fetch_stylists(),
        )
        self.render("lessons/new.html", **params)

    @tornado.web.authenticated
    def post(self):
        try:
            name = self.get_argument("name", "未命名课程名称")
            member_id = self.get_argument("member_id", 0)
            content = self.get_argument("content", "")
            start_date = self.get_argument("start_date", "2012-01-01")
            end_date = self.get_argument("end_date", "2012-01-01")
            createtime = time.mktime(datetime.datetime.now().timetuple())

            pics = self.get_arguments("pics")

            # 创建主题
            # md_diy_subject
            start_date = self.convert_date_to_timestamp(start_date)
            end_date = self.convert_date_to_timestamp(end_date)
            subject_id = self.db.execute("insert into md_diy_subject(subject_name, member_id, content, actived, "
                    "createtime, start_time, end_time) "
                    "values(%s, %s, %s, %s, %s, %s, %s)",
                    name, member_id, content, 'N', createtime, start_date, end_date)
            for pic in pics:
                pic_id, pic_url = pic.split("|")
                self.db.execute("insert into md_diy_subject_content(subject_id, theme_pic_id, "
                        "thme_pic_url, sort, actived) values(%s, %s, %s, %s, %s)",
                        subject_id, pic_id, pic_url, 0, 'N')
        except Exception, e:
            print e
            params = dict(
                stylists=self.fetch_stylists(),
                informer=BootstrapInformer("error", e),
            )
            self.render("lessons/new.html", **params)
            return

        # 设置数据库中图片相关参数
        # md_diy_subject_content
        '''
        self.db.execute("insert into md_diy_subject_content(subject_id, theme_pic_id, theme_pic_url, actived) "
                "values(%s, %s, %s, %s, %s)", subject_id, theme_pic_id, theme_pic_url, 'Y')
        '''

        self.redirect("/lessons")


class LessonEditHandler(LessonBaseHandler):
    @tornado.web.authenticated
    def get(self, id):
        lesson = self.fetch_lesson(id)
        if lesson is None:
            raise tornado.web.HTTPError(404)

        pics = self.fetch_all_pics(id)

        params = dict(
            lesson=lesson,
            stylists=self.fetch_stylists(),
            pics=pics,
            path_prefix=self.path_to_url(self.get_subject_path_prefix()),
        )
        self.render("lessons/edit.html", **params)

    @tornado.web.authenticated
    def post(self, id):
        name = self.get_argument("name", None)
        member_id = self.get_argument("member_id", 0)
        content = self.get_argument("content", "")
        start_date = self.get_argument("start_date", "")
        end_date = self.get_argument("end_date", "")
        pics = self.get_arguments("pics")

        lesson = self.fetch_lesson(id)
        stylists = self.fetch_stylists()

        try:
            new_start_date = self.convert_date_to_timestamp(start_date)
            new_end_date = self.convert_date_to_timestamp(end_date)
            self.db.execute("update md_diy_subject set subject_name = %s, member_id = %s, content = %s, "
                    "start_time = %s, end_time = %s where id = %s",
                    name, member_id, content, new_start_date, new_end_date, id)
            for pic in pics:
                pic_id, pic_url = pic.split("|")
                self.db.execute("insert into md_diy_subject_content(subject_id, theme_pic_id, "
                        "thme_pic_url, sort, actived) values(%s, %s, %s, %s, %s)",
                        lesson.id, pic_id, pic_url, 0, 'N')
            self.redirect("/lessons")
        except Exception, e:
            lesson.subject_name = name
            lesson.member_id = member_id
            lesson.content = content
            lesson.start_time = start_date
            lesson.end_date = end_date
            pics = self.fetch_all_pics(id)
            params = dict(
                lesson=lesson,
                informer=Informer("error", str(e)),
                stylists=stylists,
                pics=pics,
                path_prefix=self.path_to_url(self.get_subject_path_prefix()),
            )
            self.render("lessons/edit.html", **params)
