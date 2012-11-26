#!/usr/bin/env python
# coding: utf-8

from parser import TornadoConfigParser


class Pagination(object):
    @classmethod
    def add_limit_clause(cls, sql, page):
        parser = TornadoConfigParser()
        page_size = parser.get('pagination', 'page_size')
        start_pos = (int(page) - 1) * int(page_size)  # 起始位置
        sql += " limit %s, %s" % (start_pos, page_size)
        return sql

    @classmethod
    def page_count(cls, entries_count):
        parser = TornadoConfigParser()
        page_size = int(parser.get('pagination', 'page_size'))
        if entries_count % page_size == 0:
            return entries_count / page_size
        else:
            return entries_count / page_size + 1
        

if __name__ == "__main__":
    print Pagination.add_limit_clause('', 2)
    print Pagination.page_count(50)
    print Pagination.page_count(51)
