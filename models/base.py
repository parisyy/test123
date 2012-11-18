#!/usr/bin/env python
# coding: utf-8

from tornado.options import define, options
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

define('environment', default='development', help='run on the specific environment')


class DBAlchemy(object):
    def __init__(self):
        self.engine = self._create_engine()
        self.session = self._create_session(self.engine)

    def _create_engine(self):
        import os
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from config.parser import TornadoConfigParser

        options.parse_command_line()

        parser = TornadoConfigParser()
        db_host = parser.get(options.environment, 'host')
        db_database = parser.get(options.environment, 'database')
        db_user = parser.get(options.environment, 'user')
        db_password = parser.get(options.environment, 'password')

        return create_engine('mysql://%s:%s@%s/%s?charset=utf8' % (db_user, db_password, db_host, db_database))

    def _create_session(self, engine):
        Session = sessionmaker()
        Session.configure(bind=engine)
        return Session()


if __name__ == '__main__':
    db = DBAlchemy()
    print db.engine.execute('select now()').scalar()
