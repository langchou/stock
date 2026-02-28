#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import random
import configparser
from instock.lib.singleton_type import singleton_type

# 在项目运行时，临时将项目路径添加到环境变量
cpath_current = os.path.dirname(os.path.dirname(__file__))
cpath = os.path.abspath(os.path.join(cpath_current, os.pardir))
sys.path.append(cpath)
proxy_filename = os.path.join(cpath_current, 'config', 'proxy.txt')

__author__ = 'myh '
__date__ = '2025/1/6 '


# 读取代理
class proxys(metaclass=singleton_type):
    def __init__(self):
        self.data = []
        self._tunnel_proxy = None

        # 优先级: 环境变量 PROXY_URL > config.ini > proxy.txt
        self._load_from_env()

        if self._tunnel_proxy is None:
            self._load_tunnel_proxy()

        if self._tunnel_proxy is None:
            self._load_proxy_file()

    def _load_from_env(self):
        """从环境变量 PROXY_URL 读取代理（Docker 部署用）"""
        proxy_url = os.environ.get('PROXY_URL', '').strip()
        if proxy_url:
            self._tunnel_proxy = proxy_url
            print(f"代理已配置(环境变量): {proxy_url.split('@')[-1] if '@' in proxy_url else proxy_url}")

    def _load_tunnel_proxy(self):
        """从 config.ini 读取隧道代理配置"""
        config_file = os.path.join(cpath, 'config.ini')

        # 打包后从 exe 目录读取
        if getattr(sys, 'frozen', False):
            config_file = os.path.join(os.path.dirname(sys.executable), 'config.ini')

        if not os.path.exists(config_file):
            return

        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')

        if 'proxy' not in config:
            return

        enabled = config['proxy'].getboolean('enable_proxy', False)
        if not enabled:
            return

        host = config['proxy'].get('tunnel_host', '').strip()
        port = config['proxy'].get('tunnel_port', '').strip()
        username = config['proxy'].get('tunnel_username', '').strip()
        password = config['proxy'].get('tunnel_password', '').strip()

        if host and port:
            if username and password:
                self._tunnel_proxy = f"http://{username}:{password}@{host}:{port}"
            else:
                self._tunnel_proxy = f"http://{host}:{port}"
            print(f"隧道代理已配置: {host}:{port}")

    def _load_proxy_file(self):
        """从 proxy.txt 读取代理列表"""
        try:
            with open(proxy_filename, "r") as file:
                self.data = list(set(line.strip() for line in file.readlines() if line.strip()))
        except Exception:
            pass

    def get_data(self):
        return self.data

    def get_proxies(self):
        # 优先使用隧道代理
        if self._tunnel_proxy:
            return {"http": self._tunnel_proxy, "https": self._tunnel_proxy}

        # 回退到文件代理列表
        if self.data is None or len(self.data) == 0:
            return None

        proxy = random.choice(self.data)
        return {"http": proxy, "https": proxy}
