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
from handlers.login import LoginHandler, LogoutHandler
from handlers.home import HomeHandler

from handlers.region import RegionHandler

from handlers.ui_module import UserQueryModule, PictureListModule, PaginationModule
from handlers.user import UserHandler, UserDetailHandler, UserEditHandler, UserEditBasicModule
from handlers.lesson import LessonHandler, LessonNewHandler, LessonEditHandler
from handlers.uploader import ImageUploaderHandler, AvatarUploaderHandler
from handlers.season import SeasonHandler, SeasonNewHandler, SeasonEditHandler, PictureSelectorHandler
from handlers.star import StarHandler, StarRecommendHandler, StarRecommendEditHandler
from handlers.salon import SalonHandler


class Application(BaseApplication):
    def __init__(self):
        handlers = [
            (r'/', HomeHandler),

            # 登录
            (r'/login', LoginHandler),
            (r'/logout', LogoutHandler),

            # 用户管理
            (r'/users[\/]*', UserHandler),
            (r'/users/show/([0-9]+)', UserDetailHandler),
            (r'/users/edit/([0-9]+)', UserEditHandler),

            # 星光巨匠
            (r'/stars[\/]*', StarHandler),
            (r'/stars/delete/([0-9]+)', StarHandler),
            (r'/stars/recommend_pics/([0-9]+)', StarRecommendHandler),
            (r'/stars/recommend_pics/edit/([0-9]+)', StarRecommendEditHandler),

            # DIY课堂
            (r'/lessons[\/]*', LessonHandler),
            (r'/lessons/new', LessonNewHandler),
            (r'/lessons/edit/([0-9]+)', LessonEditHandler),

            # 图片上传
            (r'/uploader', ImageUploaderHandler),
            (r'/avatar_uploader', AvatarUploaderHandler),

            # 图片选择
            (r'/selector', PictureSelectorHandler),

            # 省市区信息
            (r'/region', RegionHandler),

            # 当季主题
            (r'/seasons[\/]*', SeasonHandler),
            (r'/seasons/new', SeasonNewHandler),
            (r'/seasons/edit/([0-9]+)', SeasonEditHandler),

            # 沙龙管理
            (r'/salons', SalonHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'assets'),
            ui_modules={
                'UserEditBasicModule': UserEditBasicModule,
                'UserQueryModule': UserQueryModule,
                'PictureListModule': PictureListModule,
                'PaginationModule': PaginationModule,
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
