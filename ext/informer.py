#!/usr/bin/env python
# coding: utf-8


class Informer(object):
    def __init__(self, type="", info="", heading=""):
        self.type = type
        self.info = info
        self.heading = heading

    def __repr__(self):
        return "<Informer('%s','%s')>" % (self.type, self.info)


class BootstrapInformer(Informer):
    def __repr__(self):
        tmpl = '''
            <div class="alert %s">
                <a class="close" data-dismiss="alert" href="#">x</a>
                <span class="alert-heading">%s</span>
                %s
            </div>
        '''
        if self.type == "info":
            tmpl = tmpl % ('alert-info', self.heading, self.info)
        elif self.type == "warning":
            tmpl = tmpl % ('alert-warning', self.heading, self.info)
        elif self.type == "error":
            tmpl = tmpl % ('alert-error', self.heading, self.info)
        elif self.type == "success":
            tmpl = tmpl % ('alert-success', self.heading, self.info)
        else:
            tmpl = tmpl % ('', self.heading, self.info)
        return tmpl


if __name__ == "__main__":
    informer = Informer()
    print informer

    informer2 = BootstrapInformer('info', 'Hello, world!')
    informer3 = BootstrapInformer('', '')
    print informer2
    print informer3
