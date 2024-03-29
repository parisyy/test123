#!/usr/bin/env python
# coding: utf-8

from handlers.base import BaseHandler


class HomeHandler(BaseHandler):
    def get(self):
        '''
        session = self.backend.get_session()
        entries = session.query(AppID).filter_by(visible=1).order_by(AppID.platform, AppID.name, AppID.version.desc())
        session.close()
        entries = self.db.query("select AppPlatform as platform, AppName as name, AppVer as version, isShow as visible "
                "from bs_appid where isShow = 1 order by AppPlatform, AppName, AppVer desc")
        entries = self.fetch_default_users()
        self.render("index.html", entries=entries)
        '''
        if self.get_current_user():
            self.redirect("/users")
        else:
            self.redirect("/login")
