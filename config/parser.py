#!/usr/bin/env python
# coding: utf-8

import os
from ConfigParser import SafeConfigParser


class TornadoConfigParser(object):
    _config_files = ['database.ini', 'upload.ini']

    def __init__(self):
        self.parser = SafeConfigParser()
        config_files = [os.path.join(os.path.dirname(__file__), e) for e in self._config_files]
        self.parser.read(config_files)

    def get(self, *args):
        return self.parser.get(*args)


def test():
    parser = TornadoConfigParser()
    print parser.get('development', 'host')


if __name__ == '__main__':
    test()
