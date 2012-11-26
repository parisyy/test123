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

        # prefix = md5(base64(pic_id + microsecond)).hexdigest()
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
                prefix, dstdir, postfix, img_width, img_height, pic_id)
        return pic_id, dstname, dstdir + "/" + dstname


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
