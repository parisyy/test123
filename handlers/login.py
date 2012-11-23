#!/usr/bin/env python
# coding: utf-8

import hashlib
from handlers.base import BaseHandler
from ext.informer import BootstrapInformer


class LoginHandler(BaseHandler):
    def get(self):
        if self.get_current_user():
            self.redirect("/")
        else:
            next_url = self.get_argument("next", "/")
            self.render("login/login.html", next_url=next_url)

    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        next_url = self.get_argument("next_url", "/")

        print username, password, next_url

        user = self.db.get("select password from md_admin_member where username = %s", username)
        if user is not None and user.password == hashlib.md5(password).hexdigest():
            self.set_secure_cookie("username", username)
            self.set_secure_cookie("password", password)
        else:
            informer = BootstrapInformer("error", "错误的用户名或密码", "认证失败：")
            self.render("login/login.html", informer=informer)

        self.redirect(next_url)


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_all_cookies()
        self.redirect("/")
