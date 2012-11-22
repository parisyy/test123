#!/usr/bin/env python
# coding: utf-8

import time
import datetime
import tornado.web
from handlers.base import BaseHandler
from ext.informer import BootstrapInformer, Informer


class LessonBaseHandler(BaseHandler):
    def all_lessons(self):
        return self.db.query("select d.id, subject_name, username, from_unixtime(createtime) as createtime, "
                "date(from_unixtime(start_time)) as start_time, date(from_unixtime(end_time)) as end_time, "
                "d.actived from md_diy_subject d left join md_member m on d.member_id = m.id")

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
    def get(self):
        lessons = self.all_lessons()

        params = dict(
            lessons=lessons,
            informer=BootstrapInformer("success", "共 %s 条记录" % len(lessons), "查询结果："),
        )
        self.render("lessons/index.html", **params)


class LessonNewHandler(LessonBaseHandler):
    def get(self):
        params = dict(
            stylists=self.fetch_stylists(),
        )
        self.render("lessons/new.html", **params)

    def post(self):
        name = self.get_argument("name", None)
        member_id = self.get_argument("member_id", 0)
        content = self.get_argument("content", "")
        start_date = self.get_argument("start_date", "")
        end_date = self.get_argument("end_date", "")
        createtime = time.mktime(datetime.datetime.now().timetuple())

        pics = self.get_arguments("pics")

        # 创建主题
        # md_diy_subject
        try:
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
    def get(self, id):
        lesson = self.fetch_lesson(id)
        if lesson is None:
            raise tornado.web.HTTPError(404)

        pics = self.fetch_all_pics(id)
        #pic_urls = [(e.img_path + "/" + e.pic_url).replace("assets", "static") for e in pics]

        params = dict(
            lesson=lesson,
            stylists=self.fetch_stylists(),
            #pic_urls=pic_urls,
            pics=pics,
        )
        self.render("lessons/edit.html", **params)

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
            #pic_urls = [(e.img_path + "/" + e.pic_url).replace("assets", "static") for e in pics]
            params = dict(
                lesson=lesson,
                informer=Informer("error", str(e)),
                stylists=stylists,
                pics=pics,
            )
            self.render("lessons/edit.html", **params)
