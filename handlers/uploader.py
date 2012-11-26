#!/usr/bin/env python
# coding: utf-8

import os
import json
from handlers.base import BaseHandler


class ImageUploaderHandler(BaseHandler):
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
