#!/usr/bin/env python
# coding: utf-8

import os
import json
import datetime
import hashlib
import base64
import tempfile
from PIL import Image
from handlers.base import BaseHandler
from ext.parser import TornadoConfigParser


class UploaderBaseHandler(BaseHandler):
    def create_image_file(self, fd):
        '''创建图片'''
        # 创建一条新的数据库记录，因为后续操作需要指定的pic_id
        pic_id = self.db.execute("insert into md_theme_picture "
                "(pic_url, img_path, img_type, width, height) values('', '', '', 0, 0)")

        # 生成文件名称
        postfix = fd.filename.split(".").pop()
        if len(postfix) > 4:
            postfix = postfix[:4]
        if not postfix in ["jpg", "jpeg", "png"]:
            self.db.execute("delete from md_theme_picture where id = %s", pic_id)
            raise Exception("不支持该文件格式")

        # 从配置文件中读取目录前缀
        parser = TornadoConfigParser()
        root_path = parser.get("uploader", "root_path")
        subject_path = parser.get("uploader", "subject_path")
        prefix_path = root_path + "/" + subject_path

        # 获取按照指定规则生成的目录名和文件名
        dirname, filename = self.gen_subject_path(pic_id)

        # 本地文件的路径，不存在则自动创建
        real_dirname = prefix_path + "/" + dirname
        if not os.path.exists(real_dirname):
            os.makedirs(real_dirname)

        img = self.create_file(fd, real_dirname + "/" + filename + "." + postfix)
        img_width, img_height = img.size

        # 设置数据库
        #dstdir = dstdir.replace('assets', 'static')
        self.db.execute("update md_theme_picture set pic_url = %s, img_path = %s, "
                "img_type = %s, width = %s, height = %s where id = %s",
                filename, dirname, postfix, img_width, img_height, pic_id)

        return pic_id, filename + "." + postfix, self.path_to_url(real_dirname + "/" + filename + "." + postfix)

    # TODO: 需要重构
    def create_avatar_file(self, fd, uid):
        '''创建用户头像'''
        # 创建临时文件
        tmpf = tempfile.NamedTemporaryFile()
        tmpf.write(fd['body'])
        tmpf.seek(0)

        # 保存图片
        img = Image.open(tmpf.name)
        tmpf.close()
        #img.thumbnail((400, 400), resample=1)

        # 文件名
        filename = self._avatar_path(uid)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        img.save(filename)  # 文件保存在pictures目录下

        return filename.replace("assets", "static")

    def create_file(self, fd, filename):
        '''保存上传文件
        @fd 文件数据
        @filename 保存文件时的文件名（包含目录路径）
        '''
        tmpf = tempfile.NamedTemporaryFile()
        tmpf.write(fd['body'])
        tmpf.seek(0)

        img = Image.open(tmpf.name)
        tmpf.close()
        img.save(filename)

        return img

    def set_table_md_theme_picture(self):
        '''在md_theme_picture表中创建图片文件的记录'''
        session = self.backend.get_session()
        try:
            session.execute("insert into md_theme_picture(pic_url, img_path, img_type, width, height) "
                    "values(%s, %s, %s, %s, %s)")
            session.commit()
            session.close()
        except Exception, e:
            session.rollback()
            raise e

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
        dirname = "%s/%s/%s/%s" % (now.year, now.month, now.day, now.hour)
        return dirname, filename

    def gen_salon_path(self, id):
        '''沙龙图片的文件名生产规则：
        01. 目录名：ID补足9位；假设ID为123456789，则目录为：123/45/67/89
        02. 文件名：md5(base64(salon_id + microsecond)).hexdigest()
        '''
        now = datetime.datetime.now()
        filename = hashlib.md5(base64.b64encode(str(id)) + str(now.microsecond)).hexdigest()
        id = "%09d" % id
        dirname = "%s/%s/%s/%s" % (id[:3], id[3:5], id[5:7], id[7:9])
        return dirname, filename

    def gen_subject_path(self, id):
        '''DIY课堂和当季主题中，图片的文件名生成规则：
        01. 目录名：2012/11/17/16（即：年/月/日/时）
        02. 文件名：md5(base64(pic_id + microsecond)).hexdigest()
        '''
        now = datetime.datetime.now()
        filename = hashlib.md5(base64.b64encode(str(id) + str(now.microsecond))).hexdigest()
        dirname = "%s/%s/%s/%s" % (now.year, now.month, now.day, now.hour)
        return dirname, filename


class ImageUploaderHandler(UploaderBaseHandler):
    def get(self):
        self.write("Hello, world!")

    def post(self):
        if self.request.files:
            for f in self.request.files["userfile"]:
                try:
                    pic_id, pic_name, pic_url = self.create_image_file(f)
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


class TestUploaderHandler(UploaderBaseHandler):
    def get(self):
        self.test_gen_avatar_path()
        self.test_gen_salon_path()
        self.test_gen_twitter_path()
        self.test_gen_subject_path()

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
