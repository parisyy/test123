#!/usr/bin/env python
# coding: utf-8

from sqlalchemy import Column, String, Integer

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


class Lesson(Base):
    __tablename__ = 'md_diy_subject'

    id = Column('id', Integer, primary_key=True)
    subject_name = Column('subject_name', String(50))
    member_id = Column('member_id', Integer)
    cover_pic_id = Column('cover_pic_id', Integer)
    cover_pic_url = Column('cover_pic_url', String(50))
    content = Column('content', String(256))
    actived = Column('actived', Integer)
    createtime = Column('createtime', Integer)
    start_time = Column('start_time', Integer)
    end_time = Column('end_time', Integer)

    def __init__(self, id, name, member_id, pic_id, pic_url, content, actived, createtime, starttime, endtime):
        self.id = id
        self.subject_name = name
        self.member_id = member_id
        self.cover_pic_id = pic_id
        self.cover_pic_url = pic_url
        self.content = content
        self.actived = actived
        self.createtime = createtime
        self.start_time = starttime
        self.end_time = endtime

    def __str__(self):
        tmpl = "<Lesson(%s,'%s',%s,%s,'%s','%s',%s,%s,%s,%s)>" % self.to_tuple()
        return tmpl

    '''
    def __init__(self, **args):
        self.id = args.get("id", 0)
        self.subject_name = args.get("subject_name", "")
        self.member_id = args.get("member_id", 0)
        self.cover_pic_id = args.get("cover_pic_id", 0)
        self.cover_pic_url = args.get("cover_pic_url", "")
        self.content = args.get("content", "")
        self.actived = args.get("actived", -1)
        self.createtime = args.get("createtime", 0)
        self.start_time = args.get("start_time", 0)
        self.end_time = args.get("end_time", 0)
    '''

    def to_hash(self):
        return dict(
            id=self.id,
            subject_name=self.subject_name,
            member_id=self.member_id,
            cover_pic_id=self.cover_pic_id,
            cover_pic_url=self.cover_pic_url,
            content=self.content,
            actived=self.actived,
            createtime=self.createtime,
            start_time=self.start_time,
            end_time=self.end_time,
        )

    def to_tuple(self):
        return (self.id, self.subject_name, self.member_id, self.cover_pic_id,
                self.cover_pic_url, self.content, self.actived, self.createtime,
                self.start_time, self.end_time)


if __name__ == "__main__":
    from base import DBAlchemy
    db = DBAlchemy()
    print db.session.query(Lesson).all()

    '''
    # 访问有对应关系的对象
    lesson.member
    '''
    pass
