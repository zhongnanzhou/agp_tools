"""
功能面板组件 - 右侧栏
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QPushButton, QSizePolicy
from PySide6.QtCore import Signal, Qt

from ..config import FUNCTION_PANEL_WIDTH, BUTTON_SIZE


class FunctionPanelWidget(QWidget):
    """功能面板组件 - 右侧栏"""

    function_triggered = Signal(str)

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        title_label = QLabel("功能区")
        title_label.setStyleSheet("font-weight: bold; padding: 5px;")
        title_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)

        button_layout = QGridLayout()
        button_layout.setSpacing(10)
        button_layout.setColumnStretch(0, 1)
        button_layout.setColumnStretch(1, 1)

        functions = [
            ("角度检测", "angle_detect"),
            ("角度校正", "angle_correct"),
            ("图片切分", "image_crop"),
            ("图片压缩", "image_compress"),
        ]

        for i, (name, func_id) in enumerate(functions):
            row = i // 2
            col = i % 2
            btn = QPushButton(name)
            btn.setFixedSize(BUTTON_SIZE[0], BUTTON_SIZE[1])
            btn.clicked.connect(lambda checked, fid=func_id: self.on_button_clicked(fid))
            button_layout.addWidget(btn, row, col, Qt.AlignCenter)

        layout.addLayout(button_layout)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(spacer)

    def on_button_clicked(self, func_id: str):
        """按钮点击事件"""
        self.function_triggered.emit(func_id)
