"""
控制台信息显示组件
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import QTimer

from utils import loggings

qt_handler = loggings.log_handlers.qt_handler()


class ConsoleWidget(QWidget):
    """控制台信息显示组件"""

    def __init__(self):
        super().__init__()
        self.max_lines = 500
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header_layout = QHBoxLayout()
        title_label = QLabel("控制台")
        title_label.setStyleSheet("font-weight: bold;")

        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.clear)
        self.clear_btn.setMaximumWidth(60)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_btn)

        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")

        layout.addLayout(header_layout)
        layout.addWidget(self.console_text)

        QTimer.singleShot(100, self.connect_signal)

    def connect_signal(self):
        """延迟连接信号"""
        try:
            qt_handler.log_signal.connect(self.append)
        except:
            pass

    def append(self, text: str):
        """追加日志信息"""
        if not hasattr(self, 'max_lines'):
            return
        self.console_text.append(text)

        lines = self.console_text.toPlainText().split('\n')
        if len(lines) > self.max_lines:
            self.console_text.setPlainText('\n'.join(lines[-self.max_lines:]))

    def clear(self):
        """清空日志"""
        self.console_text.clear()

    def get_text(self):
        """获取日志内容"""
        return self.console_text.toPlainText()
