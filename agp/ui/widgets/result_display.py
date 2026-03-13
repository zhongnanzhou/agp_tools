"""
结果展示组件 - 显示执行结果图片
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
import numpy as np
from PIL import Image


class ResultDisplayWidget(QWidget):
    """结果展示组件 - 显示执行结果图片"""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("执行结果")
        title_label.setStyleSheet("font-weight: bold; padding: 5px;")

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        self.image_label.setText("执行结果将显示在此处")

        self.scroll_area.setWidget(self.image_label)

        layout.addWidget(title_label)
        layout.addWidget(self.scroll_area)

    def set_result_image(self, pil_image: Image.Image):
        """设置结果图片"""
        img_array = np.array(pil_image)

        if len(img_array.shape) == 2:
            img_array = np.stack([img_array, img_array, img_array], axis=-1)

        if img_array.shape[2] == 4:
            img_array = img_array[:, :, :3]

        height, width, channel = img_array.shape
        bytes_per_line = 3 * width
        q_image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.scroll_area.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.resize(scaled_pixmap.size())

    def clear(self):
        """清空显示"""
        self.image_label.clear()
        self.image_label.setText("执行结果将显示在此处")
