#!/usr/bin/env python
# coding: utf-8

import os
import json
import time
import datetime
import hashlib
import base64
import tempfile
from PIL import Image
import tornado.web
from handlers.base import BaseHandler


class UploaderBaseHandler(BaseHandler):
    support_img_types = ["jpg", "jpeg", "png"]

    def create_subject_file(self, fd):
        '''创建图片'''
        # 创建一条新的数据库记录，因为后续操作需要指定的pic_id
        pic_id = self.db.execute("insert into md_theme_picture "
                "(pic_url, img_path, img_type, width, height) values('', '', '', 0, 0)")

        # 生成文件名称
        postfix = self.get_img_type(fd)
        if not postfix in self.support_img_types:
            self.db.execute("delete from md_theme_picture where id = %s", pic_id)
            raise Exception("不支持该文件格式")

        # 从配置文件中读取目录前缀
        prefix_path = self.url_to_path(self.get_subject_path_prefix())

        # 获取按照指定规则生成的目录名和文件名
        dirname, filename = self.gen_subject_path(pic_id)

        # 本地文件的路径，不存在则自动创建
        real_dirname = prefix_path + "/" + dirname
        if not os.path.exists(real_dirname):
            os.makedirs(real_dirname)

        img = self.create_file(fd, real_dirname + "/" + filename + "." + postfix)
        img_width, img_height = img.size

        # 设置数据库
        self.update_table_md_theme_picture(dirname, filename, postfix, img_width, img_height, pic_id)

        return pic_id, filename, self.path_to_url(real_dirname + "/" + filename + "." + postfix)

    # TODO: 需要重构
    def create_avatar_file(self, fd, uid):
        '''创建用户头像'''
        self.create_file(fd, self._avatar_path(uid, 0), (128, 128))
        self.create_file(fd, self._avatar_path(uid, 1), (64, 64))
        self.create_file(fd, self._avatar_path(uid, 2), (32, 32))

        # 更新数据库设置
        import uuid
        avatar_id = str(uuid.uuid1())
        avatar_id += str(datetime.datetime.now().microsecond)
        avatar_id = hashlib.md5(base64.b64encode(avatar_id)).hexdigest()
        self.db.execute("update md_member set avatar_id = %s where id = %s", avatar_id, uid)

        filename = self._avatar_path(uid, 0)
        return filename.replace("assets", "static")

    def create_salon_logo_file(self, fd, salon_id):
        img_type = self.get_img_type(fd)
        if not img_type in self.support_img_types:
            raise Exception("不支持该文件格式")

        dirname, filename = self.gen_salon_path(salon_id)
        prefix_path = self.get_salon_path_prefix()
        real_dirname = prefix_path + "/" + dirname
        if not os.path.exists(real_dirname):
            os.makedirs(real_dirname)

        img = self.create_file(fd, real_dirname + "/" + filename + "." + img_type)
        img = self.create_file(fd, real_dirname + "/" + filename + "_192x192." + img_type, (192, 192))
        img_width, img_height = img.size

        # 更新数据库
        pic_id = self.insert_table_md_theme_picture(dirname, filename, img_type, img_width, img_height)
        self.remove_salon_logo_file(salon_id)
        now = datetime.datetime.now()
        self.db.execute("update md_salon set logo_id = %s, logo_url = %s where id = %s", pic_id, filename, salon_id)
        self.db.execute("insert into md_salon_picture(salon_id, salon_pic_id, salon_pic_url, is_logo, createtime, img_type) "
                "values(%s, %s, %s, %s, %s, %s)",
                salon_id, pic_id, filename, 'Y', time.mktime(datetime.datetime.timetuple(now)), img_type)

        # 计算URL地址
        pic_url = prefix_path + "/" + dirname + "/" + filename + "." + img_type
        pic_url = self.path_to_url(pic_url)
        return pic_url.replace("//", "/")

    def create_salon_file(self, fd, salon_id):
        img_type = self.get_img_type(fd)
        if not img_type in self.support_img_types:
            raise Exception("不支持该文件格式")

        dirname, filename = self.gen_salon_path(salon_id)
        prefix_path = self.get_salon_path_prefix()
        real_dirname = prefix_path + "/" + dirname
        if not os.path.exists(real_dirname):
            os.makedirs(real_dirname)

        img = self.create_file(fd, real_dirname + "/" + filename + "." + img_type)
        img = self.create_file(fd, real_dirname + "/" + filename + "_192x192." + img_type, (192, 192))
        img_width, img_height = img.size

        # 更新数据库
        pic_id = self.insert_table_md_theme_picture(dirname, filename, img_type, img_width, img_height)
        now = datetime.datetime.now()
        self.db.execute("insert into md_salon_picture(salon_id, salon_pic_id, salon_pic_url, is_logo, createtime) "
                "values(%s, %s, %s, %s, %s)",
                salon_id, pic_id, filename, 'N', time.mktime(datetime.datetime.timetuple(now)))

        # 计算URL地址
        pic_url = prefix_path + "/" + dirname + "/" + filename + "." + img_type
        pic_url = self.path_to_url(pic_url)
        return pic_url.replace("//", "/")

    def remove_salon_logo_file(self, salon_id):
        # 只删除数据库记录，不删除已上传的图片
        self.db.execute("delete from md_salon_picture where is_logo = 'Y' and salon_id = %s", salon_id)

    def create_hairpackage_file(self, fd, package_id):
        pass

    def create_file(self, fd, filename, size=None):
        '''保存上传文件
        @fd 文件数据
        @filename 保存文件时的文件名（包含目录路径）
        '''
        tmpf = tempfile.NamedTemporaryFile()
        tmpf.write(fd['body'])
        tmpf.seek(0)

        img = Image.open(tmpf.name)
        if size:
            img.thumbnail((size[0], size[1]), resample=1)
        tmpf.close()
        img.save(filename)

        return img

    def update_table_md_theme_picture(self, *args):
        '''在md_theme_picture表中创建图片文件的记录'''
        img_path, pic_url, img_type, width, height, id = args
        self.db.execute("update md_theme_picture set img_path = %s, pic_url = %s, "
                "img_type = %s, width = %s, height = %s where id = %s",
                img_path, pic_url, img_type, width, height, id)

    def insert_table_md_theme_picture(self, *args):
        img_path, pic_url, img_type, width, height = args
        id = self.db.execute("insert into md_theme_picture(img_path, pic_url, img_type, width, height) "
                "values(%s, %s, %s, %s, %s)",
                img_path, pic_url, img_type, width, height)
        return id

    def delete_table_md_theme_picture(self, id):
        self.db.execute("delete from md_theme_picture where id = %s", id)

    def gen_avatar_path(self, id):
        '''用户头像的文件名生成规则：
        01. 若ID不满9位，则补足9位；
        02. 假设ID为123456789，则拆分为：123/45/67/89；其中89为文件名，123/45/67为目录

        返回：（目录名，文件名）
        '''
        id = "%09d" % int(id)
        return (id[0:3] + '/' + id[3:5] + '/' + id[5:7], id[7:9])

    def gen_twitter_path(self, id):
        '''用户发表图片的文件名生成规则：
        01. 目录名：2012/11/17/16（即：年/月/日/时）
        02. 文件名：md5(base64(pic_id + microsecond)).hexdigest()（microsecond表示当前时间的微秒数）

        返回：（目录名，文件名）
        '''
        now = datetime.datetime.now()
        filename = hashlib.md5(base64.b64encode(str(id) + str(now.microsecond))).hexdigest()
        dirname = "%s/%s/%s/%s/" % (now.year, now.month, now.day, now.hour)
        return dirname, filename

    def gen_salon_path(self, id):
        '''沙龙图片的文件名生产规则：
        01. 目录名：ID补足9位；假设ID为123456789，则目录为：123/45/67/89
        02. 文件名：md5(base64(salon_id + microsecond)).hexdigest()
        '''
        now = datetime.datetime.now()
        filename = hashlib.md5(base64.b64encode(str(id)) + str(now.microsecond)).hexdigest()
        id = "%09d" % int(id)
        dirname = "%s/%s/%s/%s/" % (id[:3], id[3:5], id[5:7], id[7:9])
        return dirname, filename

    def gen_subject_path(self, id):
        '''DIY课堂和当季主题中，图片的文件名生成规则：
        01. 目录名：2012/11/17/16（即：年/月/日/时）
        02. 文件名：md5(base64(pic_id + microsecond)).hexdigest()
        '''
        now = datetime.datetime.now()
        filename = hashlib.md5(base64.b64encode(str(id) + str(now.microsecond))).hexdigest()
        dirname = "%s/%s/%s/%s/" % (now.year, now.month, now.day, now.hour)
        return dirname, filename

    def gen_hairpackage_path(self, id):
        '''发型包的文件名生成规则：
        01. 目录名：2012/12/04（年/月/日）
        02. 文件名：md5(uuid)
        03. 必须是zip文件
        '''
        import uuid
        now = datetime.date.today()
        dirname = "%s/%s/%s/" % (now.year, now.month, now.day)
        filename = hashlib.md5(uuid.uuid1()).digest()
        return dirname, filename

    def get_img_type(self, fd):
        postfix = fd.filename.split(".").pop()
        return postfix[:4]


class ImageUploaderHandler(UploaderBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.write("Hello, world!")

    @tornado.web.authenticated
    def post(self):
        if self.request.files:
            for f in self.request.files["userfile"]:
                try:
                    pic_id, pic_name, pic_url = self.create_subject_file(f)
                    self.write(json.dumps({
                        'code': 0,
                        'id': pic_id,
                        'name': pic_name,
                        'url': pic_url
                    }))
                except Exception, e:
                    self.write(json.dumps({
                        'code': -1,
                        'error': unicode(e),
                    }))

    @tornado.web.authenticated
    def delete(self):
        pic_id = self.get_argument("pic_id", 0)

        pic = self.db.get("select * from md_theme_picture where id = %s", pic_id)
        if pic is not None:
            filename = pic.img_path + "/" + pic.pic_url
        else:
            self.write(json.dumps({'code': 0}))

        try:
            self.db.execute("delete from md_theme_picture where id = %s", pic_id)
            print filename
            os.remove(filename)
        except Exception, e:
            self.write(json.dumps({
                'code': -1,
                'error': unicode(e),
            }))


class AvatarUploaderHandler(UploaderBaseHandler):
    @tornado.web.authenticated
    def post(self):
        try:
            uid = self.get_argument("uid")
            if self.request.files:
                for f in self.request.files["userfile"]:
                        pic_url = self.create_avatar_file(f, uid)
                        self.write(json.dumps({
                            'code': 0,
                            'url': pic_url
                        }))
        except Exception, e:
            self.write(json.dumps({
                'code': -1,
                'error': unicode(e),
            }))


class SalonLogoUploaderHandler(UploaderBaseHandler):
    @tornado.web.authenticated
    def post(self):
        try:
            salon_id = self.get_argument("salon_id")
            if self.request.files:
                for f in self.request.files["userfile"]:
                        pic_url = self.create_salon_logo_file(f, salon_id)
                        self.write(json.dumps({
                            'code': 0,
                            'url': pic_url
                        }))
        except Exception, e:
            self.write(json.dumps({
                'code': -1,
                'error': unicode(e),
            }))


class SalonUploaderHandler(UploaderBaseHandler):
    @tornado.web.authenticated
    def post(self):
        try:
            salon_id = self.get_argument("salon_id")
            if self.request.files:
                for f in self.request.files["userfile"]:
                        pic_url = self.create_salon_file(f, salon_id)
                        self.write(json.dumps({
                            'code': 0,
                            'url': pic_url
                        }))
        except Exception, e:
            self.write(json.dumps({
                'code': -1,
                'error': unicode(e),
            }))


class HairPackageUploaderHandler(UploaderBaseHandler):
    @tornado.web.authenticated
    def post(self):
        try:
            package_id = self.get_argument("package_id")
            if self.request.files:
                for f in self.request.files["userfile"]:
                        download_url = self.create_hairpackage_file(f, package_id)
                        self.write(json.dumps({
                            'code': 0,
                            'url': download_url
                        }))
        except Exception, e:
            self.write(json.dumps({
                'code': -1,
                'error': unicode(e),
            }))


class TestUploaderHandler(UploaderBaseHandler):
    def get(self):
        self.test_gen_avatar_path()
        self.test_gen_salon_path()
        self.test_gen_twitter_path()
        self.test_gen_subject_path()

    @tornado.web.authenticated
    def test_gen_avatar_path(self):
        dataset = []
        entries = self.db.query("select id from md_member limit 10")
        for i in [e.id for e in entries]:
            dirname, filename = self.gen_avatar_path(i)
            dataset.append(dirname + '/' + filename)
        self.write(json.dumps(dataset))

    def test_gen_twitter_path(self):
        entries = self.db.query("select id from md_salon limit 10")
        dataset = []
        for i in [e.id for e in entries]:
            dirname, filename = self.gen_twitter_path(i)
            dataset.append(dirname + '/' + filename)
        self.write(json.dumps(dataset))

    def test_gen_salon_path(self):
        entries = self.db.query("select id from md_salon limit 10")
        dataset = []
        for i in [e.id for e in entries]:
            dirname, filename = self.gen_salon_path(i)
            dataset.append(dirname + '/' + filename)
        self.write(json.dumps(dataset))

    def test_gen_subject_path(self):
        entries = self.db.query("select id from md_theme_picture order by id desc limit 10")
        dataset = []
        for i in [e.id for e in entries]:
            dirname, filename = self.gen_subject_path(i)
            dataset.append(dirname + '/' + filename)
        self.write(json.dumps(dataset))
