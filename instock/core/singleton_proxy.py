#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import sys
import random
import configparser
from instock.lib.singleton_type import singleton_type

# 在项目运行时，临时将项目路径添加到环境变量
cpath_current = os.path.dirname(os.path.dirname(__file__))
cpath = os.path.abspath(os.path.join(cpath_current, os.pardir))
sys.path.append(cpath)
proxy_filename = os.path.join(cpath_current, 'config', 'proxy.txt')
config_filename = os.path.join(cpath, 'config.ini')

__author__ = 'myh '
__date__ = '2025/1/6 '


# 读取代理
class proxys(metaclass=singleton_type):
    def __init__(self):
        self.data = []
        self.tunnel_proxy = None

        # 优先尝试隧道代理
        self._init_tunnel_proxy()

        # 如果隧道代理未启用，回退到 proxy.txt
        if self.tunnel_proxy is None:
            try:
                with open(proxy_filename, "r") as file:
                    self.data = list(set(line.strip() for line in file.readlines() if line.strip()))
            except Exception:
                pass

    def _init_tunnel_proxy(self):
        """从 config.ini 读取隧道代理配置"""
        try:
            config = configparser.ConfigParser()
            config.read(config_filename, encoding='utf-8')
            if 'proxy' not in config:
                return
            if not config['proxy'].getboolean('enable_proxy', False):
                return

            host = config['proxy'].get('tunnel_host', '').strip()
            port = config['proxy'].get('tunnel_port', '').strip()
            username = config['proxy'].get('tunnel_username', '').strip()
            password = config['proxy'].get('tunnel_password', '').strip()

            if not host or not port:
                return

            if username and password:
                self.tunnel_proxy = f"http://{username}:{password}@{host}:{port}"
            else:
                self.tunnel_proxy = f"http://{host}:{port}"

            print(f"隧道代理已启用: {host}:{port}")
        except Exception as e:
            print(f"隧道代理配置读取失败: {e}")

    def get_data(self):
        return self.data

    def get_proxies(self):
        # 优先使用隧道代理
        if self.tunnel_proxy:
            return {"http": self.tunnel_proxy, "https": self.tunnel_proxy}

        # 回退到 proxy.txt 列表
        if self.data is None or len(self.data) == 0:
            return None

        proxy = random.choice(self.data)
        return {"http": proxy, "https": proxy}
