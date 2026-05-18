# -*- coding: utf-8 -*-
"""
日志工具模块

提供统一的日志配置和管理功能。
支持控制台和文件输出、日志轮转、日志级别配置。
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


_loggers = {}


def setup_logger(
    name: str,
    level: str = "INFO",
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    console_output: bool = True,
) -> logging.Logger:
    """配置日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别
        log_format: 日志格式字符串
        log_file: 日志文件路径
        max_bytes: 日志文件最大大小
        backup_count: 保留的日志文件数量
        console_output: 是否输出到控制台

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(log_format)

    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=str(log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _loggers[name] = logger
    return logger


def get_logger(name: str) -> logging.Logger:
    """获取已配置的日志记录器

    如果日志记录器不存在，则创建一个默认配置的新记录器。

    Args:
        name: 日志记录器名称

    Returns:
        logging.Logger: 日志记录器实例
    """
    if name in _loggers:
        return _loggers[name]

    return setup_logger(name)


class LoggerContext:
    """日志上下文管理器

    用于临时改变日志级别或添加日志处理器。
    """

    def __init__(self, logger: logging.Logger, level: Optional[str] = None):
        """初始化日志上下文

        Args:
            logger: 日志记录器
            level: 临时日志级别
        """
        self.logger = logger
        self.temp_level = level
        self.original_level: Optional[int] = None
        self.handlers_backup: list = []

    def __enter__(self) -> logging.Logger:
        """进入上下文"""
        if self.temp_level:
            self.original_level = self.logger.level
            self.logger.setLevel(getattr(logging, self.temp_level.upper()))
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出上下文"""
        if self.original_level is not None:
            self.logger.setLevel(self.original_level)


def get_log_level(env_level: Optional[str] = None) -> str:
    """根据环境变量获取日志级别

    Args:
        env_level: 环境变量名称，默认LOG_LEVEL

    Returns:
        str: 日志级别字符串
    """
    env_name = env_level or "LOG_LEVEL"
    return os.getenv(env_name, "INFO").upper()
