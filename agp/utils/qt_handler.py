"""
Qt日志处理器
将Python logging日志发送到Qt界面
"""

import logging
from PySide6.QtCore import QObject, Signal


class QtHandler(logging.Handler, QObject):
    """
    Qt日志处理器
    继承自 logging.Handler 和 QObject，可以发送信号到Qt界面
    """

    log_signal = Signal(str)

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)

    def emit(self, record: logging.LogRecord):
        """发送日志记录到Qt界面"""
        try:
            msg = self.format(record)
            self.log_signal.emit(msg)
        except Exception:
            self.handleError(record)
