#!/usr/bin/env python
# coding: utf-8

import hashlib
import time
import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()


class Member(Base):
    __tablename__ = "md_member"

    id = Column("id", Integer, primary_key=True)
    username = Column("username", String(64))
    salon_id = Column("salon_id", Integer)
    actived = Column("actived", Integer)
    member_type = Column("member_type", Integer)


class HairPackage(Base):
    __tablename__ = "md_hairpackage"

    id = Column("id", Integer, primary_key=True)
    package_name = Column("package_name", String(64))
    package_url = Column("package_url", String(32))
    barber_id = Column("barber_id", Integer, ForeignKey("md_member.id"))
    salon_id = Column("salon_id", Integer)
    hair_num = Column("hair_num", Integer)
    description = Column("description", String(255))
    filepath = Column("filepath", String(64))
    filename = Column("filename", String(64))
    filesize = Column("filesize", Integer)
    actived = Column("actived", Integer)
    down_num = Column("down_num", Integer)
    createtime = Column("createtime", Integer)
    modifytime = Column("modifytime", Integer)

    stylist = relationship("Member")

    def __init__(self, **args):
        self.package_name = args.get("package_name", "未知发型包名称")
        self.package_url = args.get("package_url", "")
        self.barber_id = args.get("barber_id", 0)
        self.salon_id = args.get("salone_id", 0)
        self.hair_num = args.get("hair_num", 0)
        self.description = args.get("description", "")
        self.filepath = args.get("filepath", "")
        self.filename = args.get("filename", "")
        self.filesize = args.get("filesize", 0)
        self.actived = args.get("actived", 0)
        self.down_num = args.get("down_num", 0)
        self.createtime = time.mktime(datetime.datetime.now().timetuple())
        self.modifytime = time.mktime(datetime.datetime.now().timetuple())

    def set(self, **args):
        self.package_name = args.get("package_name", self.package_name)
        self.package_url = args.get("package_url", self.package_url)
        self.barber_id = args.get("barber_id", self.barber_id)
        self.salon_id = args.get("salone_id", self.salon_id)
        self.hair_num = args.get("hair_num", self.hair_num)
        self.description = args.get("description", self.description)
        self.filepath = args.get("filepath", self.filepath)
        self.filename = args.get("filename", self.filename)
        self.filesize = args.get("filesize", self.filesize)
        self.actived = args.get("actived", self.actived)
        self.down_num = args.get("down_num", self.down_num)
        self.modifytime = time.mktime(datetime.datetime.now().timetuple())

    def set_package_url(self):
        self.package_url = str(hashlib.md5(str(self.id)).hexdigest())
        #print type(hashlib.md5(self.id).hexdigest())
