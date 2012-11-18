#!/usr/bin/env python
# coding: utf-8

from handlers.base import BaseHandler


class SeasonBaseHandler(BaseHandler):
    def fetch_all_seasons(self):
        return self.db.query("select * from md_season_period")


class SeasonHandler(SeasonBaseHandler):
    def get(self):
        seasons = self.fetch_all_seasons()
        self.render("seasons/index.html", seasons=seasons)


class SeasonNewHandler(SeasonBaseHandler):
    def get(self):
        pass

    def post(self):
        pass


class SeasonEditHandler(SeasonBaseHandler):
    def get(self):
        pass

    def post(self):
        pass
