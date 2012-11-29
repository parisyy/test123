#!/usr/bin/env python
# coding: utf-8

from handlers.base import BaseHandler


class TwitterBaseHandler(BaseHandler):
    config = {
        "from_type": {
            0: "用户发布",
            1: "发型师发布",
            2: "杂志发布",
            3: "发品公司发布",
        },
        "share_type": {
            1: "秀发型",
            2: "我要美发",
            3: "洗护问题",
            4: "沙龙优惠",
        },
        "actived": {
            0: "未审核",
            1: "已经审核",
            2: "用户已删除",
            3: "系统已强制删除",
            4: "未上传完成",
            5: "隐藏",
            6: "屏蔽",
            9: "隐藏",
        },
    }
    pass


class TwitterHandler(TwitterBaseHandler):
    def get(self):
        params = dict(
            entries=[""],
            config=self.config,
        )
        self.render("twitters/index.html", **params)
