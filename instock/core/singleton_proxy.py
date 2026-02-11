#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import sys
import random
import logging
import time
import configparser
import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from instock.lib.singleton_type import singleton_type

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        """读取隧道代理配置，优先级: 环境变量 > config.ini"""
        # 1. 优先从环境变量读取 (Docker 部署用)
        proxy_url = os.environ.get('PROXY_URL', '').strip()
        if proxy_url:
            self.tunnel_proxy = proxy_url
            print(f"隧道代理已启用(环境变量): {proxy_url.split('@')[-1] if '@' in proxy_url else proxy_url}")
            return

        # 2. 从 config.ini 读取
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

    def _get_session(self):
        """获取带重试策略的 requests Session"""
        if not hasattr(self, '_session'):
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[403, 429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "POST", "OPTIONS"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            self._session = session
        return self._session

    def request_get(self, url, headers=None, params=None, retry=3, timeout=15):
        """带重试的 GET 请求"""
        session = self._get_session()
        for i in range(retry):
            try:
                resp = session.get(url, proxies=self.get_proxies(), headers=headers,
                                   params=params, timeout=timeout, verify=False)
                resp.raise_for_status()
                return resp
            except requests.exceptions.RequestException as e:
                logging.warning(f"GET请求失败({i+1}/{retry}): {url} - {e}")
                if i < retry - 1:
                    time.sleep(random.uniform(2, 5))
                else:
                    raise

    def request_post(self, url, headers=None, json=None, data=None, retry=3, timeout=15):
        """带重试的 POST 请求"""
        session = self._get_session()
        for i in range(retry):
            try:
                resp = session.post(url, proxies=self.get_proxies(), headers=headers,
                                    json=json, data=data, timeout=timeout, verify=False)
                resp.raise_for_status()
                return resp
            except requests.exceptions.RequestException as e:
                logging.warning(f"POST请求失败({i+1}/{retry}): {url} - {e}")
                if i < retry - 1:
                    time.sleep(random.uniform(2, 5))
                else:
                    raise
