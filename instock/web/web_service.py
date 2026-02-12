#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import logging
import os.path
import sys
from abc import ABC

import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado import gen

# 在项目运行时，临时将项目路径添加到环境变量
cpath_current = os.path.dirname(os.path.dirname(__file__))
cpath = os.path.abspath(os.path.join(cpath_current, os.pardir))
sys.path.append(cpath)
log_path = os.path.join(cpath_current, 'log')
if not os.path.exists(log_path):
    os.makedirs(log_path)
logging.basicConfig(format='%(asctime)s %(message)s', filename=os.path.join(log_path, 'stock_web.log'))
logging.getLogger().setLevel(logging.ERROR)
import instock.lib.torndb as torndb
import instock.lib.database as mdb
import instock.lib.version as version
import instock.web.dataTableHandler as dataTableHandler
import instock.web.dataIndicatorsHandler as dataIndicatorsHandler
import instock.web.base as webBase
import instock.web.chatHandler as chatHandler

__author__ = 'myh '
__date__ = '2023/3/10 '


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            # 登录/登出
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            # 设置路由
            (r"/", HomeHandler),
            (r"/instock/", HomeHandler),
            # 使用datatable 展示报表数据模块。
            (r"/instock/api_data", dataTableHandler.GetStockDataHandler),
            (r"/instock/data", dataTableHandler.GetStockHtmlHandler),
            # 获得股票指标数据。
            (r"/instock/data/indicators", dataIndicatorsHandler.GetDataIndicatorsHandler),
            # 加入关注
            (r"/instock/control/attention", dataIndicatorsHandler.SaveCollectHandler),
            # AI 助手
            (r"/instock/chat", chatHandler.ChatPageHandler),
            (r"/instock/api_chat", chatHandler.ChatApiHandler),
        ]
        settings = dict(  # 配置
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=False,  # True,
            # cookie加密
            cookie_secret="027bb1b670eddf0392cdda8709268a17b58b7",
            login_url="/login",
            debug=True,
        )
        super(Application, self).__init__(handlers, **settings)
        # Have one global connection to the blog DB across all handlers
        self.db = torndb.Connection(**mdb.MYSQL_CONN_TORNDB)


# 登录handler。
class LoginHandler(webBase.BaseHandler, ABC):
    def get(self):
        if self.current_user:
            self.redirect(self.get_argument("next", "/"))
            return
        self.render("login.html", error=None)

    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        if (username == webBase.INSTOCK_USERNAME and
                webBase.hash_password(password) == webBase.hash_password(webBase.INSTOCK_PASSWORD)):
            self.set_secure_cookie("user", username, expires_days=30)
            self.redirect(self.get_argument("next", "/"))
        else:
            self.render("login.html", error="用户名或密码错误")


# 登出handler。
class LogoutHandler(webBase.BaseHandler, ABC):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/login")


# 首页handler。
class HomeHandler(webBase.BaseHandler, ABC):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        self.render("index.html",
                    stockVersion=version.__version__,
                    leftMenu=webBase.GetLeftMenu(self.request.uri))


def main():
    # tornado.options.parse_command_line()
    tornado.options.options.logging = None

    http_server = tornado.httpserver.HTTPServer(Application())
    port = 9988
    http_server.listen(port)

    print(f"服务已启动，web地址 : http://localhost:{port}/")
    logging.error(f"服务已启动，web地址 : http://localhost:{port}/")

    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
