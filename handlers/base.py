#!/usr/bin/env python
# coding: utf-8

import os
import re
import time
import datetime

import tornado.web
import tornado.database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ext.parser import parse_mysql_config, TornadoConfigParser


def none_to_empty_str(obj):
    if obj is None:
        return ""
    else:
        return obj


class BaseHandler(tornado.web.RequestHandler):
    @property
    def backend(self):
        return Backend.instance()

    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        return self.get_secure_cookie("username")

    def fetch_all_regions(self):
        entries = self.db.query("select id, region_name from md_region")
        dataset = {}
        for e in entries:
            dataset.setdefault(e.id, e.region_name)
        return dataset

    def fetch_all_tags(self):
        '''读取所有脸型、发量、发质的tag'''
        return self.db.query("select id, tag_name from md_tag")

    def fetch_provinces(self):
        '''读取全部省份信息'''
        return self.db.query("select id, region_name from md_region where level = 1")

    def fetch_cities(self):
        '''读取全部城市信息'''
        return self.db.query("select id, region_name from md_region where level = 2")

    def fetch_domains(self):
        '''读取全部区域信息'''
        return self.db.query("select id, region_name from md_region where level = 3")

    def fetch_cities_by_province_id(self, province_id):
        '''读取指定省份的城市列表'''
        return self.db.query("select * from md_region where level = 2 and parent_id = %s", province_id)

    def fetch_domains_by_city_id(self, city_id):
        '''读取制定城市的区域列表'''
        return self.db.query("select * from md_region where level = 3 and parent_id = %s", city_id)

    def fetch_stylists(self):
        '''读取发型师信息'''
        return self.db.query("select id, username, email from md_member where member_type = 2")

    def fetch_packages(self):
        '''读取当前有效的发型包列表'''
        return self.db.query("select id, package_name from md_hairpackage where actived = 1")

    def path_to_url(self, path):
        '''将文件路径转换为URL地址'''
        return path.replace("assets", "/static")

    def url_to_path(self, url):
        '''将图片URL地址转换为文件路径'''
        return url.replace("/static", "assets")

    def default_image_path(self):
        '''默认图片的文件路径'''
        return "assets/default.jpg"

    def default_image_url(self):
        return self.path_to_url(self.default_image_path())

    def get_subject_path_prefix(self):
        '''DIY课堂图片和当季主题图片的URL地址前缀'''
        parser = TornadoConfigParser()
        root_path = parser.get("uploader", "root_path")
        subject_path = parser.get("uploader", "subject_path")
        return (root_path + "/" + subject_path).replace("//", "/")

    def get_avatar_path_prefix(self):
        '''用户头像的URL地址前缀'''
        parser = TornadoConfigParser()
        root_path = parser.get("uploader", "root_path")
        subject_path = parser.get("uploader", "avatar_path")
        return (root_path + "/" + subject_path).replace("//", "/")

    def get_salon_path_prefix(self):
        '''沙龙图片的URL地址前缀'''
        parser = TornadoConfigParser()
        root_path = parser.get("uploader", "root_path")
        subject_path = parser.get("uploader", "salon_path")
        return (root_path + "/" + subject_path).replace("//", "/")

    def get_twitter_path_prefix(self):
        '''用户图片的URL地址前缀'''
        parser = TornadoConfigParser()
        root_path = parser.get("uploader", "root_path")
        subject_path = parser.get("uploader", "twitter_path")
        return (root_path + "/" + subject_path).replace("//", "/")

    def get_hairpackage_path_prefix(self):
        '''发行包的URL地址前缀'''
        parser = TornadoConfigParser()
        root_path = parser.get("uploader", "root_path")
        subject_path = parser.get("uploader", "hairpackage_path")
        return (root_path + "/" + subject_path).replace("//", "/")

    def pic_url(self, pic_id):
        '''获取图片的url地址'''
        pic = self.db.get("select * from md_theme_picture where id = %s", pic_id)
        if pic is not None:
            pic_url = pic.img_path + "/" + pic.pic_url + "." + pic.img_type
        else:
            pic_url = ""
        return pic_url

    def _avatar_path(self, id, type=0):
        '''返回用户头像的文件路径，若不存在则返回None'''
        path = "assets/pictures/avatar"
        id = "%09d" % int(id)
        filename = id[0:3] + '/' + id[3:5] + '/' + id[5:7] + '/' + id[7:9]

        if type == 0:
            filename = filename + '_big'
        elif type == 1:
            filename = filename + '_middle'
        elif type == 2:
            filename = filename + '_small'

        url = path + '/' + filename + '.jpg'
        return url

    def get_avatar_pic(self, id):
        '''返回用户头像的url地址，若不存在则返回默认头像的url地址'''
        filename = self._avatar_path(id)
        if os.path.isfile(filename):
            return "/" + filename.replace("assets", "static")
        else:
            return "/static/default.jpg"

    def convert_to_timestamp(self, str):
        '''将datetime格式字符串转换为timestamp'''
        date_time = datetime.datetime.strptime(str, "%Y-%m-%d %H:%M:%S")
        return time.mktime(date_time.timetuple())

    def convert_date_to_timestamp(self, str):
        '''将datetime格式字符串转换为timestamp'''
        date_time = datetime.datetime.strptime(str, "%Y-%m-%d")
        return time.mktime(date_time.timetuple())


class BaseApplication(tornado.web.Application):
    def db_conn(self):
        db_user, db_password, db_host, db_database = parse_mysql_config()
        return tornado.database.Connection(host=db_host, database=db_database, user=db_user, password=db_password)


class Backend(object):
    def __init__(self):
        db_user, db_password, db_host, db_database = parse_mysql_config()
        engine = create_engine("mysql://%s:%s@%s/%s?charset=utf8" % (db_user, db_password, db_host, db_database))
        self._session = sessionmaker(bind=engine)

    def get_session(self):
        return self._session()

    @classmethod
    def instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance


class Validator(object):
    def test_max_len(self, maxlen, obj):
        '''最大长度'''
        if len(obj) > maxlen:
            return False
        else:
            return True

    def test_min_len(self, minlen, obj):
        '''最小长度'''
        if len(obj) < minlen:
            return False
        else:
            return True

    def test_none(self, obj):
        '''是否None类型'''
        if obj is None:
            return True
        else:
            return False

    def test_zero(self, obj):
        '''是否等于0'''
        if obj == 0:
            return True
        else:
            return False

    def test_empty_str(self, obj):
        '''是否空字符串'''
        if obj == "":
            return True
        else:
            return False

    def test_email(self, obj):
        '''是否邮件地址'''
        pattern = r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        if re.match(pattern, obj) is None:
            return False
        else:
            return True

    def test_mobile(self, obj):
        '''是否手机号码'''
        pass

    def test_datetime(self, obj):
        '''是否日期时间格式（2012-01-01 00:00:00）'''
        # 参考这里：http://blog.csdn.net/lxcnn/article/details/4362500
        pattern = r'^(?:(?!0000)[0-9]{4}-(?:(?:0[1-9]|1[0-2])-(?:0[1-9]|1[0-9]|2[0-8])|(?:0[13-9]|1[0-2])-(?:29|30)|(?:0[13578]|1[02])-31)|(?:[0-9]{2}(?:0[48]|[2468][048]|[13579][26])|(?:0[48]|[2468][048]|[13579][26])00)-02-29)\s+([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$'
        if re.match(pattern, obj) is None:
            return False
        else:
            return True

    def test_date(self, obj):
        '''是否日期格式（2012-01-01）'''
        pattern = r'^(?:(?!0000)[0-9]{4}([-/.]?)(?:(?:0?[1-9]|1[0-2])\1(?:0?[1-9]|1[0-9]|2[0-8])|(?:0?[13-9]|1[0-2])\1(?:29|30)|(?:0?[13578]|1[02])\1(?:31))|(?:[0-9]{2}(?:0[48]|[2468][048]|[13579][26])|(?:0[48]|[2468][048]|[13579][26])00)([-/.]?)0?2\2(?:29))$'
        if re.match(pattern, obj) is None:
            return False
        else:
            return True


if __name__ == "__main__":
    val = Validator()
    print val.test_datetime('2000-02-29 00:00:00')
    print val.test_date('2000-02-29')
