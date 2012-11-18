#!/usr/bin/env python
# coding: utf-8

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Member(Base):
    __tablename__ = 'md_member'

    id = Column('id', Integer, primary_key=True)
    username = Column('username', String(64))
    realname = Column('realname', String(32))
    email = Column('email', String(64))
    password = Column('password', String(64))
    regtime = Column('regtime', Integer)
    mobile = Column('mobile', String(13))
    gender = Column('gender', Integer)
    member_type = Column('member_type', Integer)
    sourcetype = Column('sourcetype', Integer)
    actived = Column('actived', Integer)
    has_avatar = Column('has_avatar', Integer)
    avatar_id = Column('avatar_id', String(50))
    salon_id = Column('salon_id', Integer)
    salon_name = Column('salon_name', String(50))
    salon_address = Column('salon_address', String(50))
    salon_telephone = Column('salon_telephone', String(50))
    province_id = Column('province_id', Integer)
    city_id = Column('city_id', Integer)
    area_id = Column('area_id', Integer)
    last_modifytime = Column('last_modifytime', DateTime)
    sign_text = Column('sign_text', String(280))
    recommend = Column('recommend', Integer)
    bind3rd = Column('bind3rd', Integer)
    push_message = Column('push_message', Integer)
    price_haircut = Column('price_haircut', Integer)
    price_perm = Column('price_perm', Integer)
    price_dye = Column('price_dye', Integer)
    price_care = Column('price_care', Integer)
    hair_face = Column('hair_face', Integer)
    hair_quality = Column('hair_quality', Integer)
    hair_volume = Column('hair_volume', Integer)
    channel = Column('channel', Integer)
    show_mobile = Column('show_mobile', String(1))

    stats = relationship('MemberStats', uselist=False, backref='md_member')

    def __init__(self, last_modifytime, works_count):
        self.last_modifytime = last_modifytime
        self.works_count = works_count


class MemberStats(Base):
    __tablename__ = 'md_member_statistics'
    id = Column('id', Integer, primary_key=True)
    member_id = Column('member_id', Integer, ForeignKey('md_member.id'))
    lastlogintime = Column('lastlogintime', Integer)
    twitter_num = Column('twitter_num', Integer)
    emotion_num = Column('emotion_num', Integer)


if __name__ == "__main__":
    from base import DBAlchemy
    db = DBAlchemy()
    entries = db.session.query(Member).all()
    print entries[0].stats.emotion_num
