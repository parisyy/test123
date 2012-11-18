#!/usr/bin/env python
# coding: utf-8

import hashlib
import datetime

h = hashlib.sha1()
h.update(str(datetime.datetime.now()))
print h.hexdigest()
