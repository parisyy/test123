#!/usr/bin/env python
# coding: utf-8

import os
#import logging

import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
import tornado.database
from tornado.options import define, options

define('port', default=8000, help='run on the given port', type=int)
define('environment', default='development', help='run on the specific environment')

from handlers.base import BaseApplication
from handlers.home import HomeHandler
from handlers.user import UserHandler, UserDetailHandler, UserEditHandler, UserEditBasicModule, UserQueryModule
from handlers.lesson import LessonHandler, LessonNewHandler, LessonEditHandler
from handlers.uploader import ImageUploaderHandler
from handlers.season import SeasonHandler
from handlers.star import StarHandler


class Application(BaseApplication):
    def __init__(self):
        handlers = [
            (r'/', HomeHandler),

            # 用户管理
            (r'/users[\/]*', UserHandler),
            (r'/users/show/([0-9]+)', UserDetailHandler),
            (r'/users/edit/([0-9]+)', UserEditHandler),

            # 星光巨匠
            (r'/stars[\/]*', StarHandler),

            # DIY课堂
            (r'/lessons[\/]*', LessonHandler),
            (r'/lessons/new', LessonNewHandler),
            (r'/lessons/edit/([0-9]+)', LessonEditHandler),

            # 图片上传
            (r'/uploader', ImageUploaderHandler),

            # 当季主题
            (r'/seasons[\/]*', SeasonHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'assets'),
            ui_modules={
                'UserEditBasicModule': UserEditBasicModule,
                'UserQueryModule': UserQueryModule,
            },
            autoescape=None,
            cookie_secret='74f51c2f337676d9d6491aaa013624cb3c2226c0',
            xsrf_cookies=True,
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = self.db_conn()


def run_server():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    run_server()
