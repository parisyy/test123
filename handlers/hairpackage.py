#!/usr/bin/env python
# coding: utf-8

import json
import tornado
from handlers.base import BaseHandler
from ext.pagination import Pagination
from ext.informer import BootstrapInformer
from models.models import HairPackage, Member


class HairPackageBaseHandler(BaseHandler):
    config = {
        "actived": {
            0: "未审核",
            1: "正常",
            2: "已下架",
        },
    }

    @property
    def params(self):
        dataset = {}
        for k, v in self.request.arguments.items():
            dataset.setdefault(k, v[-1])
        return dataset


class HairPackageHandler(HairPackageBaseHandler):
    def delete(self, id):
        self.db.execute("delete from md_hairpackage where id = %s", id)
        self.db.execute("delete from md_hairpackage_member where package_id = %s", id)
        self.write(json.dumps({'code': 0}))

    def post(self, id):
        package = self.db.get("select * from md_hairpackage where id = %s", id)
        if not package:
            self.write(json.dumps({'code': -1, 'error': '发型包不存在'}))
            return

        actived = self.get_argument("actived", package.actived)
        try:
            self.db.execute("update md_hairpackage set actived = %s where id = %s",
                    actived, id)
            self.write(json.dumps({'code': 0}))
        except Exception, e:
            self.write(json.dumps({'code': -1, 'error': e}))


class HairPackageListHandler(HairPackageBaseHandler):
    def get(self):
        session = self.backend.get_session()

        # 查询
        package_name = self.get_argument("package_name", "")
        if package_name:
            hairpackages = session.query(HairPackage).filter(HairPackage.package_name.like("%" + package_name + "%"))
        else:
            hairpackages = session.query(HairPackage)
        hairpackages = hairpackages.order_by(HairPackage.modifytime.desc())

        # 分页
        count = hairpackages.count()
        page_count = Pagination.page_count(count)

        params = dict(
            hairpackages=hairpackages.all(),
            config=self.config,
            page_count=page_count,
            informer=BootstrapInformer("success", "共 %s 条记录" % count, "查询结果："),
            package_name=package_name,
        )
        self.render("hairpackages/index.html", **params)

        session.close()


class HairPackageNewHandler(HairPackageBaseHandler):
    def get(self):
        session = self.backend.get_session()
        params = dict(
            config=self.config,
            stylists=session.query(Member).filter_by(member_type=2),
        )
        self.render("hairpackages/new.html", **params)
        session.close()

    def post(self):
        hairpackage = HairPackage(**self.params)

        try:
            session = self.backend.get_session()
            session.add(hairpackage)
            session.commit()

            hairpackage.set_package_url()
            session.commit()

            self.redirect("/hairpackages")
        except Exception, e:
            print e
            session.rollback()
        finally:
            session.close()


class HairPackageEditHandler(HairPackageBaseHandler):
    def get(self, id):
        session = self.backend.get_session()

        hairpackage = session.query(HairPackage).get(id)
        if not hairpackage:
            raise tornado.web.HTTPError(404)
        
        params = dict(
            hairpackage=hairpackage,
            stylists=session.query(Member).filter_by(member_type=2).all(),
            config=self.config,
        )
        self.render("hairpackages/edit.html", **params)
        session.close()

    def post(self, id):
        session = self.backend.get_session()

        hairpackage = session.query(HairPackage).get(id)
        if not hairpackage:
            raise tornado.web.HTTPError(404)

        try:
            hairpackage.set(**self.params)
            session.commit()
            self.redirect("/hairpackages")
        except Exception, e:
            print e
            session.rollback()

            params = dict(
                hairpackage=hairpackage,
                stylists=session.query(Member).filter_by(member_type=2).all(),
                config=self.config,
                informer=BootstrapInformer("error", e, "更新失败：")
            )
            self.render("hairpackages/edit.html", **params)
        finally:
            session.close()
