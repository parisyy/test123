#!/usr/bin/env python
# coding: utf-8

import os
from ConfigParser import SafeConfigParser
from tornado.options import options


class TornadoConfigParser(object):
    _config_files = ['database.ini', 'pagination.ini', 'uploader.ini']

    def __init__(self):
        self.parser = SafeConfigParser()
        config_files = [os.path.join(os.path.dirname(__file__) + '/../config', e) for e in self._config_files]
        self.parser.read(config_files)

    def get(self, *args):
        return self.parser.get(*args)


def parse_mysql_config():
    '''读取MySQL数据库配置'''
    options.parse_command_line()

    parser = TornadoConfigParser()
    db_host = parser.get(options.environment, 'host')
    db_database = parser.get(options.environment, 'database')
    db_user = parser.get(options.environment, 'user')
    db_password = parser.get(options.environment, 'password')

    return (db_user, db_password, db_host, db_database)
