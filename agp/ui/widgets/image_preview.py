"""
图片预览组件 - 支持编辑功能
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QMessageBox, QButtonGroup, QRadioButton
from PySide6.QtCore import Qt, Signal, QPoint, QRect
from PySide6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent, QPainter, QPen, QColor, QCursor
import numpy as np
from PIL import Image

import logging
logger = logging.getLogger(__name__)


class EditableImageLabel(QLabel):
    """可编辑的图片标签"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        self.setText("拖拽图片到此处\n或通过菜单打开图片")
        self.setCursor(QCursor(Qt.CrossCursor))

        self.drawing = False
        self.start_point = None
        self.end_point = None
        self.draw_mode = None
        self.drawings = []

    def set_draw_mode(self, mode):
        """设置绘制模式: 'line', 'rect', None"""
        self.draw_mode = mode
        if mode:
            self.setCursor(QCursor(Qt.CrossCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))

    def clear_drawings(self):
        """清除所有绘制"""
        self.drawings = []
        self.update()

    def mousePressEvent(self, event):
        """鼠标按下"""
        if self.draw_mode and event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = event.pos()
            self.end_point = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动"""
        if self.drawing and self.draw_mode:
            self.end_point = event.pos()
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        if self.drawing and self.draw_mode and event.button() == Qt.LeftButton:
            self.drawing = False
            self.end_point = event.pos()

            if self.start_point and self.end_point:
                self.drawings.append({
                    'mode': self.draw_mode,
                    'start': (self.start_point.x(), self.start_point.y()),
                    'end': (self.end_point.x(), self.end_point.y())
                })

            self.start_point = None
            self.end_point = None
            self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)

        if not self.drawing and not self.drawings:
            return

        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 0, 0), 2))

        for drawing in self.drawings:
            mode = drawing['mode']
            start = drawing['start']
            end = drawing['end']

            if mode == 'line':
                painter.drawLine(start[0], start[1], end[0], end[1])
            elif mode == 'rect':
                painter.drawRect(
                    min(start[0], end[0]),
                    min(start[1], end[1]),
                    abs(end[0] - start[0]),
                    abs(end[1] - start[1])
                )

        if self.drawing and self.start_point and self.end_point:
            painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.DashLine))
            if self.draw_mode == 'line':
                painter.drawLine(
                    self.start_point.x(), self.start_point.y(),
                    self.end_point.x(), self.end_point.y()
                )
            elif self.draw_mode == 'rect':
                painter.drawRect(
                    min(self.start_point.x(), self.end_point.x()),
                    min(self.start_point.y(), self.end_point.y()),
                    abs(self.end_point.x() - self.start_point.x()),
                    abs(self.end_point.y() - self.start_point.y())
                )


class ImagePreviewWidget(QWidget):
    """图片预览组件"""

    image_changed = Signal(str)
    pil_image_changed = Signal(object)
    request_switch_image = Signal(str)

    def __init__(self, main_window=None):
        super().__init__()
        self.current_file = None
        self.original_file = None
        self.scale_factor = 1.0
        self.current_pil_image = None
        self.original_pil_image = None
        self.is_modified = False
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAcceptDrops(True)
        self.scroll_area.setMinimumSize(400, 400)

        self.image_label = EditableImageLabel()

        self.scroll_area.setWidget(self.image_label)

        control_layout = QHBoxLayout()

        self.zoom_in_btn = QPushButton("放大")
        self.zoom_in_btn.clicked.connect(self.zoom_in)

        self.zoom_out_btn = QPushButton("缩小")
        self.zoom_out_btn.clicked.connect(self.zoom_out)

        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_zoom)

        self.remove_btn = QPushButton("移除")
        self.remove_btn.clicked.connect(self.remove_image)
        self.remove_btn.setEnabled(False)

        self.edit_group = QButtonGroup(self)
        self.select_btn = QRadioButton("选择")
        self.select_btn.setChecked(True)
        self.line_btn = QRadioButton("画线")
        self.rect_btn = QRadioButton("框选")
        self.clear_btn = QPushButton("清除")
        self.clear_btn.clicked.connect(self.clear_drawings)

        self.edit_group.addButton(self.select_btn)
        self.edit_group.addButton(self.line_btn)
        self.edit_group.addButton(self.rect_btn)

        self.select_btn.toggled.connect(lambda: self.set_edit_mode(None))
        self.line_btn.toggled.connect(lambda: self.set_edit_mode('line'))
        self.rect_btn.toggled.connect(lambda: self.set_edit_mode('rect'))

        control_layout.addWidget(self.select_btn)
        control_layout.addWidget(self.line_btn)
        control_layout.addWidget(self.rect_btn)
        control_layout.addWidget(self.clear_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.zoom_in_btn)
        control_layout.addWidget(self.zoom_out_btn)
        control_layout.addWidget(self.reset_btn)
        control_layout.addWidget(self.remove_btn)

        layout.addWidget(self.scroll_area)
        layout.addLayout(control_layout)

        self.scroll_area.dragEnterEvent = self.dragEnterEvent
        self.scroll_area.dropEvent = self.dropEvent

        self.original_pixmap = None

    def set_edit_mode(self, mode):
        """设置编辑模式"""
        if mode:
            self.is_modified = True
        self.image_label.set_draw_mode(mode)

    def clear_drawings(self):
        """清除绘制"""
        self.image_label.clear_drawings()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        files = event.mimeData().urls()
        if files:
            file_path = files[0].toLocalFile()
            if file_path:
                self.load_image(file_path)
                event.acceptProposedAction()

    def load_image(self, file_path: str):
        """加载图片"""
        self.current_file = file_path
        self.image_label.clear_drawings()

        self.original_pixmap = QPixmap(file_path)

        self.current_pil_image = Image.open(file_path)
        self.original_pil_image = self.current_pil_image.copy()

        self.update_display()

        self.remove_btn.setEnabled(True)

        self.image_changed.emit(file_path)
        self.pil_image_changed.emit(self.current_pil_image)

        self.log_image_info(file_path)

    def log_image_info(self, file_path: str):
        """记录图片信息到控制台"""
        from utils.image_loader import ImageLoader
        from utils.file_helper import FileHelper

        try:
            info = ImageLoader.get_image_info(file_path)
            logger.info("=" * 50)
            logger.info("图片信息")
            logger.info(f"  文件名: {info['name']}")
            logger.info(f"  尺寸: {info['width']} x {info['height']}")
            logger.info(f"  模式: {info['mode']}")
            logger.info(f"  格式: {info['format']}")
            logger.info(f"  大小: {FileHelper.format_size(info['size_bytes'])}")
            logger.info(f"  透明通道: {'有' if info['has_alpha'] else '无'}")
            logger.info("=" * 50)
        except Exception as e:
            logger.error(f"无法读取图片信息: {str(e)}")

    def set_image(self, pil_image: Image.Image, title: str = "处理结果"):
        """设置内存中的PIL图片到预览区域"""
        self.current_pil_image = pil_image
        self.image_label.clear_drawings()

        img_array = np.array(pil_image)

        if len(img_array.shape) == 2:
            img_array = np.stack([img_array, img_array, img_array], axis=-1)

        if img_array.shape[2] == 4:
            img_array = img_array[:, :, :3]

        height, width, channel = img_array.shape
        bytes_per_line = 3 * width
        q_image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)

        self.original_pixmap = QPixmap.fromImage(q_image)

        self.update_display()

        self.remove_btn.setEnabled(True)

        self.pil_image_changed.emit(pil_image)

    def mark_modified(self):
        """标记图片已修改"""
        self.is_modified = True

    def mark_saved(self):
        """标记图片已保存"""
        self.is_modified = False
        if self.current_file:
            self.original_pil_image = self.current_pil_image.copy()

    def is_image_modified(self):
        """检查图片是否被修改"""
        if not self.is_modified or not self.current_pil_image or not self.original_pil_image:
            return False

        current_array = np.array(self.current_pil_image)
        original_array = np.array(self.original_pil_image)

        return not np.array_equal(current_array, original_array)

    def check_and_switch_image(self, new_file_path: str) -> bool:
        """检查是否需要提示用户保存图片，返回是否允许切换"""
        if self.is_image_modified() and self.current_file:
            reply = QMessageBox.question(
                self,
                "图片已修改",
                f"当前图片已进行过修改，是否放弃修改？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.load_image(new_file_path)
                return True
            else:
                return False

        self.load_image(new_file_path)
        return True

    def switch_to_image(self, new_file_path: str):
        """切换到新图片（带修改检查）"""
        if not self.check_and_switch_image(new_file_path):
            logger.info("已取消切换图片")

    def update_display(self):
        """更新显示"""
        if self.original_pixmap:
            scaled_size = self.original_pixmap.size() * self.scale_factor
            scaled_pixmap = self.original_pixmap.scaled(
                scaled_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.resize(scaled_size)

    def zoom_in(self):
        """放大"""
        self.scale_factor *= 1.2
        self.update_display()

    def zoom_out(self):
        """缩小"""
        self.scale_factor /= 1.2
        self.update_display()

    def reset_zoom(self):
        """重置缩放"""
        self.scale_factor = 1.0
        self.update_display()

    def wheelEvent(self, event):
        """鼠标滚轮缩放"""
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        event.accept()

    def remove_image(self):
        """移除图片"""
        self.current_file = None
        self.original_pixmap = None
        self.current_pil_image = None
        self.original_pil_image = None
        self.scale_factor = 1.0
        self.is_modified = False
        self.image_label.clear()
        self.image_label.setText("拖拽图片到此处\n或通过菜单打开图片")
        self.image_label.resize(400, 400)
        self.image_label.clear_drawings()
        self.remove_btn.setEnabled(False)
        self.image_changed.emit("")
        self.pil_image_changed.emit(None)

    def get_current_file(self):
        """获取当前文件路径"""
        return self.current_file

    def get_current_pil_image(self):
        """获取当前PIL图片对象"""
        return self.current_pil_image
