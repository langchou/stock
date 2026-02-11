#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import os
import hashlib
from abc import ABC
import tornado.web
import instock.core.singleton_stock_web_module_data as sswmd

__author__ = 'myh '
__date__ = '2023/3/10 '

# 登录账号配置，优先从环境变量读取（Docker部署用），默认 admin/admin
INSTOCK_USERNAME = os.environ.get('INSTOCK_USERNAME', 'admin')
INSTOCK_PASSWORD = os.environ.get('INSTOCK_PASSWORD', 'admin')


def hash_password(password):
    """SHA-256哈希密码，带固定盐"""
    return hashlib.sha256(f"instock_{password}_salt".encode('utf-8')).hexdigest()


# 基础handler，主要负责检查mysql的数据库链接。
class BaseHandler(tornado.web.RequestHandler, ABC):
    def get_current_user(self):
        return self.get_secure_cookie("user")

    @property
    def db(self):
        try:
            # check every time。
            self.application.db.query("SELECT 1 ")
        except Exception as e:
            print(e)
            self.application.db.reconnect()
        return self.application.db


class LeftMenu:
    def __init__(self, url):
        self.leftMenuList = sswmd.stock_web_module_data().get_data_list()
        self.current_url = url


# 获得左菜单。
def GetLeftMenu(url):
    return LeftMenu(url)
