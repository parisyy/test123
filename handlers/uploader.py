#!/usr/bin/env python
# coding: utf-8

import json
from handlers.base import BaseHandler


class ImageUploaderHandler(BaseHandler):
    def get(self):
        self.write("Hello, world!")

    def post(self):
        # 读取参数
        # 创建文件
        # 设置md_theme_picture
        # 返回(pic_id, pic_url)
        if self.request.files:
            for f in self.request.files["userfile"]:
                try:
                    pic_id, pic_name, pic_url = self.create_image_file(f)
                    self.write(json.dumps({
                        'id': pic_id,
                        'name': pic_name,
                        'url': pic_url
                    }))
                except Exception, e:
                    print e
