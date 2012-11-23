#!/usr/bin/env python
# coding: utf-8

import os
import re
import sys
import time
import base64
import hashlib
import datetime
import tempfile
from PIL import Image

import sqlalchemy
import tornado.web
import tornado.database
from tornado.options import options
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.parser import TornadoConfigParser


def parse_mysql_config():
    '''读取MySQL数据库配置'''
    options.parse_command_line()

    parser = TornadoConfigParser()
    db_host = parser.get(options.environment, 'host')
    db_database = parser.get(options.environment, 'database')
    db_user = parser.get(options.environment, 'user')
    db_password = parser.get(options.environment, 'password')

    return (db_user, db_password, db_host, db_database)


def parse_upload_config():
    '''读取图片上传功能的配置'''
    parser = TornadoConfigParser()
    base_dir = parser.get('upload', 'base_dir')
    return base_dir


def none_to_empty_str(obj):
    if obj is None:
        return ""
    else:
        return obj


def without_none(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if obj[k] is None:
                obj[k] = ""
    elif isinstance(obj, list):
        for i in xrange(len(obj)):
            if obj[i] is None:
                obj[i] = ""
    return obj


class Backend(object):
    def __init__(self):
        tornado.options.parse_command_line()
        engine = sqlalchemy.create_engine("mysql://{0}:{1}@{2}/{3}?charset=utf8".format(
            *parse_mysql_config()), pool_recycle=3600, echo=False, echo_pool=False)
        self._session = sessionmaker(bind=engine)

    @classmethod
    def instance(cls):
        if not hasattr(Backend, "_instance"):
            cls._instance = Backend()
        return cls._instance

    def get_session(self):
        return self._session()


class BaseHandler(tornado.web.RequestHandler):
    config = {
        'member_type': {
            0: '普通用户',
            1: '发型师',
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
        'price': {
            1: '小于100',
            2: '100~300',
            3: '300~500',
            4: '大于500',
        },
        'recommend': {
            0: '否',
            1: '是',
        },
    }

    @property
    def backend(self):
        return Backend.instance()

    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        return self.get_secure_cookie("username")

    def fetch_provinces(self):
        '''读取全部省份信息'''
        return self.db.query("select id, region_name from md_region where level = 1")

    def fetch_cities(self):
        '''读取全部城市信息'''
        return self.db.query("select id, region_name from md_region where level = 2")

    def fetch_stylists(self):
        '''读取发型师信息'''
        return self.db.query("select id, username, email from md_member where member_type = 2")

    def fetch_packages(self):
        '''读取当前有效的发型包列表'''
        return self.db.query("select id, package_name from md_hairpackage where actived = 1")

    def convert_to_timestamp(self, str):
        '''将datetime格式字符串转换为timestamp'''
        date_time = datetime.datetime.strptime(str, "%Y-%m-%d %H:%M:%S")
        return time.mktime(date_time.timetuple())

    def convert_date_to_timestamp(self, str):
        '''将datetime格式字符串转换为timestamp'''
        date_time = datetime.datetime.strptime(str, "%Y-%m-%d")
        return time.mktime(date_time.timetuple())

    def create_image_file(self, fd):
        '''创建图片'''
        # 数据库记录
        pic_id = self.db.execute("insert into md_theme_picture "
                "(pic_url, img_path, img_type, width, height) values('', '', '', 0, 0)")

        # 文件名称
        postfix = fd.filename.split(".").pop()
        if len(postfix) > 4:
            postfix = postfix[:4]
        if not postfix in ["jpg", "jpeg", "png"]:
            self.db.execute("delete from md_theme_picture where id = %s", pic_id)
            raise Exception("不支持该文件格式")

        # prefix = md5(base64(pic_id + microsecond))
        microsecond = datetime.datetime.now().microsecond
        prefix = hashlib.md5(base64.b64encode(str(pic_id) + str(microsecond))).hexdigest()

        dstname = str(prefix) + "." + postfix
        
        # 目录名称
        # format: theme/2012/11/17/16/30
        tmp_datetime = datetime.datetime.now()
        dstdir = "assets/pictures/theme/%s/%s/%s/%s" % (tmp_datetime.year, tmp_datetime.month,
                tmp_datetime.day, tmp_datetime.hour)
        if not os.path.exists(dstdir):
            os.makedirs(dstdir)

        # 创建临时文件
        tmpf = tempfile.NamedTemporaryFile()
        tmpf.write(fd['body'])
        tmpf.seek(0)

        # 保存图片
        img = Image.open(tmpf.name)
        tmpf.close()
        #img.thumbnail((400, 400), resample=1)
        img.save(dstdir + "/" + dstname)  # 文件保存在pictures目录下
        img_width, img_height = img.size

        # 设置数据库
        dstdir = dstdir.replace('assets', 'static')
        self.db.execute("update md_theme_picture set pic_url = %s, img_path = %s, "
                "img_type = %s, width = %s, height = %s where id = %s",
                dstname, dstdir, postfix, img_width, img_height, pic_id)
        return pic_id, dstname, dstdir + "/" + dstname


class BaseApplication(tornado.web.Application):
    def db_conn(self):
        db_user, db_password, db_host, db_database = parse_mysql_config()
        return tornado.database.Connection(host=db_host, database=db_database, user=db_user, password=db_password)


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
