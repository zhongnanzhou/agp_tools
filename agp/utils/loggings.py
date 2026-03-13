#!/usr/bin/env python
# @Char: coding: utf-8
# @FileName：loggings.py
# @Date: 2023/10/26 15:16
# @Author: hans
# @SoftWare：PyCharm

import os
import sys
import logging
from logging import handlers


class log_handlers:
    """
    日志处理器工具类
    """

    @staticmethod
    def console_handler(level: int = logging.WARNING):
        """
        输出到控制台（标准输出）
        :param level: 日志级别，默认 WARNING
        :return: handler
        """
        # fmt = logging.Formatter("[%(asctime)s]-[%(filename)s]-[%(funcName)s:%(lineno)s]:%(message)s")
        fmt = logging.Formatter("[%(asctime)s]-[%(filename)s]-[%(name)s.%(funcName)s:%(lineno)s]:%(message)s", datefmt='%H:%M:%S')
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(fmt)
        return handler

    @staticmethod
    def file_handler(name, path, level: int = logging.INFO):
        """
        输出到文件
        :param name: 日志文件名
        :param path: 日志存储路径
        :param level: 日志级别，默认 INFO
        :return: handler
        """
        LOG_PATH = os.path.abspath(os.path.join(path, 'logs'))
        if not os.path.exists(LOG_PATH): os.makedirs(LOG_PATH)
        LOG_FILE_PATH = os.path.abspath(os.path.join(LOG_PATH, f"{name}.log"))

        # 日志文件按天进行保存，每天一个日志文件
        handler = handlers.TimedRotatingFileHandler(filename=LOG_FILE_PATH, when='d', backupCount=24 * 7, encoding='utf-8')
        # 按照大小自动分割日志文件，一旦达到指定的大小重新生成文件
        # handler = handlers.RotatingFileHandler(filename=LOG_FILE_PATH, maxBytes=1*1024*1024*1024, backupCount=1, encoding='utf-8')
        # fmt = logging.Formatter("%(asctime)s - %(pathname)s - %(funcName)s - %(lineno)s - %(levelname)s: %(message)s")
        # fmt = logging.Formatter("%(asctime)s - %(filename)s - %(name)s.%(funcName)s:%(lineno)s - %(levelname)s: %(message)s")
        fmt = logging.Formatter("%(asctime)s - %(name)s.%(funcName)s:%(lineno)s - %(levelname)s: %(message)s")
        handler.setLevel(level)
        handler.setFormatter(fmt)
        return handler

    @staticmethod
    def qt_handler(level: int = logging.INFO):
        """
        输出到 Qt 界面
        :param level: 日志级别，默认 INFO
        :return: handler
        """
        from .qt_handler import QtHandler
        fmt = logging.Formatter('%(message)s')
        handler = QtHandler()
        handler.setLevel(level)
        handler.setFormatter(fmt)
        return handler

    @staticmethod
    def db_handler(level: int = logging.INFO):
        """
        输出到数据库（预留）
        :param level: 日志级别，默认 INFO
        :return: handler
        """
        # TODO: 实现数据库 Handler
        pass

    @staticmethod
    def dingtalk_handler(level: int = logging.ERROR):
        """
        输出到钉钉（预留）
        :param level: 日志级别，默认 ERROR（只有错误才发钉钉）
        :return: handler
        """
        # TODO: 实现钉钉 Handler
        pass

    @staticmethod
    def email_handler(level: int = logging.ERROR):
        """
        输出到邮件（预留）
        :param level: 日志级别，默认 ERROR
        :return: handler
        """
        # TODO: 实现邮件 Handler
        pass


class loggings:

    _logger = None
    _handlers = []

    @classmethod
    def created(cls, handlers: list = None):
        """
        创建日志处理器实例
        :param handlers: handler 列表
        :return: loggings 实例
        """
        instance = cls()
        instance.setHandlers(handlers)
        return instance

    def add_handler(self, handler: logging.Handler):
        """
        为 logger 添加 handler
        :param handler: 日志处理器
        :return:
        """
        if self._logger:
            self._logger.addHandler(handler)

    def add_handlers(self, handlers: list = None):
        """
        为 logger 添加多个 handler
        :param handlers: handler 列表
        :return:
        """
        if handlers:
            self.setHandlers(handlers)
        for handler in self._handlers:
            self.add_handler(handler)

    def setHandlers(self, handlers: list = None):
        """
        设置 handler 列表
        :param handlers: handler 列表
        :return:
        """
        self._handlers = handlers if handlers else []

    def logger(self, name: str = None):
        """
        获取或创建 logger 对象
        :param name: logger 名称
        :return: logger 对象
        """
        self._logger = logging.getLogger(name) if name else logging.getLogger(__name__)
        return self._logger


def getLogger(name=None, handlers: list = None):
    """
    获取 logger 对象
    
    使用示例：
    ```python
    # 只输出到控制台（WARNING 及以上）
    logger = getLogger('agp', [
        log_handlers.console_handler()
    ])
    
    # 输出到控制台和文件
    logger = getLogger('agp', [
        log_handlers.console_handler(logging.WARNING),
        log_handlers.file_handler('agp', './logs')
    ])
    
    # 输出到控制台、文件、Qt界面
    logger = getLogger('agp', [
        log_handlers.console_handler(logging.WARNING),
        log_handlers.file_handler('agp', './logs'),
        log_handlers.qt_handler()
    ])
    ```
    
    :param name: 日志名称
    :param handlers: handler 列表，每个 handler 可以有不同的级别
    :return: logger 对象
    """
    my_logger = loggings()
    logger_obj = my_logger.logger(name)
    my_logger.add_handlers(handlers)
    logger_obj.setLevel(logging.DEBUG)

    return logger_obj
