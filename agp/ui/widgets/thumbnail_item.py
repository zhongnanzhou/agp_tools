"""缩略图项 - 延迟加载的 QListWidgetItem 子类。"""

from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon, QImageReader
from pathlib import Path

from ..config import THUMBNAIL_SIZE

import logging
logger = logging.getLogger(__name__)


class ThumbnailItem(QListWidgetItem):
    """缩略图项 - 延迟加载"""

    def __init__(self, file_path: str):
        super().__init__(str(Path(file_path).name))
        self.file_path = file_path
        self.is_loaded = False
        self.size = QSize(0, 0)  # 存储实际缩放后的缩略图尺寸
        self.setToolTip(file_path)
        # 文字换行（避免长文件名撑宽项）
        self.setTextAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.setFlags(self.flags() & ~Qt.ItemIsEditable)
        # 未加载缩略图时使用统一占位尺寸，保证初始布局稳定
        self.setSizeHint(QSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE + 20))

    def load_thumbnail(self) -> bool:
        """加载缩略图（使用 QImageReader 直接解码到目标尺寸，避免全量加载原图）"""
        # 1. 如果已经加载过，直接返回（避免重复加载）
        if self.is_loaded:
            return False

        # 2. 使用 QImageReader 读取元信息，不加载全部像素
        reader = QImageReader(self.file_path)
        reader.setAutoTransform(True)  # 尊重 EXIF 旋转信息
        original_size = reader.size()

        if not original_size.isValid():
            logger.warning(f"⚠️  无法加载图片：{self.file_path}")
            return False

        # 3. 计算目标缩放尺寸（保持宽高比），让解码器直接输出小图
        scaled_size = original_size.scaled(
            THUMBNAIL_SIZE, THUMBNAIL_SIZE, Qt.KeepAspectRatio
        )
        reader.setScaledSize(scaled_size)

        # 4. 解码：JPEG 等格式会利用 DCT 缩放，内存占用远小于全量加载
        image = reader.read()
        if image.isNull():
            logger.warning(f"⚠️  无法加载图片：{self.file_path}")
            return False

        scaled_pixmap = QPixmap.fromImage(image)
        self.size = scaled_pixmap.size()

        # 5. 设置为图标
        self.setIcon(QIcon(scaled_pixmap))
        # 6. 标记已加载
        self.is_loaded = True
        # 7. 设置项的 sizeHint → 缩略图实际尺寸 + 文字高度（20px）
        hint_size = QSize(self.size.width(), self.size.height() + 20)
        self.setSizeHint(hint_size)

        logger.debug(f"加载缩略图：{self.file_path}, 原始: {original_size}, 缩略图: {self.size}")
        return True

