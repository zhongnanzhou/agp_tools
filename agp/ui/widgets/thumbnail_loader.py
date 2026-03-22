"""缩略图加载辅助模块 - 目录扫描与懒加载调度逻辑。"""

from PySide6.QtWidgets import QListWidget
from PySide6.QtCore import QPoint
from pathlib import Path
from ..config import THUMBNAIL_SIZE
from .thumbnail_item import ThumbnailItem

import logging
logger = logging.getLogger(__name__)

# 支持的图片扩展名
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}


def scan_image_files(dir_path: str) -> list[Path]:
    """扫描目录中的图片文件，返回排序后的文件路径列表。"""
    directory = Path(dir_path)
    if not directory.is_dir():
        logger.warning(f"⚠️  无效目录：{dir_path}")
        return []

    image_files = [
        f for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]
    logger.debug(f"筛选到图片数量：{len(image_files)}")
    return image_files


def estimate_visible_range(list_widget: QListWidget) -> tuple[int, int]:
    """估算可见区域的 item 索引范围，避免遍历全部 item。"""
    total = list_widget.count()
    if total == 0:
        return 0, 0

    viewport = list_widget.viewport()
    viewport_rect = viewport.rect()

    # 用 indexAt 找到视口左上角对应的 item
    first_idx = list_widget.indexAt(viewport_rect.topLeft())
    if not first_idx.isValid():
        first_idx = list_widget.indexAt(QPoint(5, 5))

    start_row = first_idx.row() if first_idx.isValid() else 0

    # 估算视口内能容纳多少 item（按缩略图尺寸 + 间距估算）
    item_height = THUMBNAIL_SIZE + 25
    viewport_width = max(viewport_rect.width(), 1)
    items_per_row = max(viewport_width // (THUMBNAIL_SIZE + 10), 1)
    visible_rows = (viewport_rect.height() // item_height) + 3  # +3 行缓冲
    max_visible = items_per_row * visible_rows

    # 前后各留一行缓冲
    scan_start = max(start_row - items_per_row, 0)
    scan_end = min(start_row + max_visible + items_per_row, total)
    return scan_start, scan_end


def get_buffered_visible_rect(list_widget: QListWidget):
    """获取带缓冲区的可见区域，减少滚动时的空白闪烁。"""
    viewport_rect = list_widget.viewport().rect()
    buffer_size = max(THUMBNAIL_SIZE // 2, 40)
    return viewport_rect.adjusted(-buffer_size, -buffer_size, buffer_size, buffer_size)


def load_visible_thumbnails(list_widget: QListWidget) -> int:
    """加载可见区域的缩略图（仅扫描估算的可见范围，非全量遍历）。

    Returns:
        加载的缩略图数量，0 表示无新加载。
    """
    if list_widget.count() == 0 or not list_widget.isVisible():
        return 0

    # 首项布局未就绪时跳过，由调用方决定是否重新调度
    first_item = list_widget.item(0)
    if first_item and list_widget.visualItemRect(first_item).isNull():
        return -1  # -1 表示布局未就绪，需要重新调度

    visible_rect = get_buffered_visible_rect(list_widget)
    scan_start, scan_end = estimate_visible_range(list_widget)
    loaded_count = 0

    for i in range(scan_start, scan_end):
        item = list_widget.item(i)
        if not item or not isinstance(item, ThumbnailItem) or item.is_loaded:
            continue

        item_rect = list_widget.visualItemRect(item)
        if item_rect.isNull() or not visible_rect.intersects(item_rect):
            continue

        if item.load_thumbnail():
            loaded_count += 1

    if loaded_count > 0:
        logger.debug(f"已加载可见区域缩略图：{loaded_count} 张")

    return loaded_count

