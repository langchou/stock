#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Windows 本地定时调度器
交易时段每30分钟自动爬取选股数据+股票实时行情数据
用法: uv run python scheduler.py
"""

import time
import datetime
import logging
import os
import sys

cpath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cpath)
os.environ.setdefault('PYTHONPATH', cpath)

log_path = os.path.join(cpath, 'instock', 'log')
if not os.path.exists(log_path):
    os.makedirs(log_path)

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_path, 'scheduler.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logging.getLogger().setLevel(logging.INFO)

# 交易时段: 9:30-11:30, 13:00-15:00
TRADING_PERIODS = [
    (datetime.time(9, 25), datetime.time(11, 35)),
    (datetime.time(12, 55), datetime.time(15, 5)),
]

INTERVAL_MINUTES = 30


def is_trading_time(now=None):
    """判断当前是否在交易时段"""
    if now is None:
        now = datetime.datetime.now()
    # 周末不交易
    if now.weekday() >= 5:
        return False
    t = now.time()
    for start, end in TRADING_PERIODS:
        if start <= t <= end:
            return True
    return False


def next_trading_time(now=None):
    """计算距离下一个交易时段的秒数"""
    if now is None:
        now = datetime.datetime.now()
    today = now.date()

    # 今天剩余的交易时段
    if now.weekday() < 5:
        for start, end in TRADING_PERIODS:
            slot_start = datetime.datetime.combine(today, start)
            if now < slot_start:
                return (slot_start - now).total_seconds()

    # 找下一个工作日
    d = today + datetime.timedelta(days=1)
    while d.weekday() >= 5:
        d += datetime.timedelta(days=1)
    next_start = datetime.datetime.combine(d, TRADING_PERIODS[0][0])
    return (next_start - now).total_seconds()


def run_basic_data_job():
    """执行股票实时行情数据爬取"""
    try:
        from instock.job.basic_data_daily_job import main
        logging.info("开始爬取股票实时行情数据...")
        main()
        logging.info("股票实时行情数据爬取完成")
    except Exception as e:
        logging.error(f"股票实时行情数据爬取失败: {e}")


def run_selection_job():
    """执行选股数据爬取"""
    try:
        from instock.job.selection_data_daily_job import main
        logging.info("开始爬取选股数据...")
        main()
        logging.info("选股数据爬取完成")
    except Exception as e:
        logging.error(f"选股数据爬取失败: {e}")


def run_daily_job():
    """执行完整的每日任务(盘后)"""
    try:
        from instock.job.execute_daily_job import main
        logging.info("开始执行每日全量任务...")
        main()
        logging.info("每日全量任务完成")
    except Exception as e:
        logging.error(f"每日全量任务失败: {e}")


def main():
    logging.info("=" * 50)
    logging.info("InStock 定时调度器已启动")
    logging.info(f"调度策略: 交易时段每{INTERVAL_MINUTES}分钟执行行情数据+选股数据爬取")
    logging.info("=" * 50)

    last_run = None
    last_daily_date = None

    while True:
        now = datetime.datetime.now()

        if is_trading_time(now):
            # 交易时段: 每隔 INTERVAL_MINUTES 分钟跑一次行情数据+选股数据
            if last_run is None or (now - last_run).total_seconds() >= INTERVAL_MINUTES * 60:
                run_basic_data_job()
                run_selection_job()
                last_run = datetime.datetime.now()

            time.sleep(60)  # 每分钟检查一次

        else:
            # 盘后15:05-15:30执行一次全量任务
            t = now.time()
            today = now.date()
            if (now.weekday() < 5
                    and datetime.time(15, 5) <= t <= datetime.time(15, 30)
                    and last_daily_date != today):
                run_daily_job()
                last_daily_date = today

            # 非交易时段, 计算等待时间
            wait = next_trading_time(now)
            if wait > 300:
                logging.info(f"非交易时段, {wait/3600:.1f}小时后进入下一交易时段, 休眠中...")
                time.sleep(min(wait - 60, 300))  # 最多睡5分钟, 避免错过
            else:
                time.sleep(30)


if __name__ == '__main__':
    main()
