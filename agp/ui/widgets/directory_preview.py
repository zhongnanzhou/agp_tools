"""目录预览组件 - 左侧栏。"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QSizePolicy, QScrollArea
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QPixmap, QIcon, QImageReader
from pathlib import Path

from ..config import DIR_PREVIEW_WIDTH, THUMBNAIL_SIZE

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

    def load_thumbnail(self):
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


class DirectoryPreviewWidget(QWidget):
    """目录预览组件 - 左侧栏"""

    image_selected = Signal(str)

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.current_dir = None
        self.image_files = []
        self.thumbnail_items = {}

        # ========== 节流定时器（分隔线拖动专用） ==========
        self.layout_timer = QTimer(self)
        self.layout_timer.setSingleShot(True)  # 仅触发一次
        self.layout_timer.setInterval(50)      # 延迟50ms执行，可自定义
        self.layout_timer.timeout.connect(self._do_update_layout)  # 实际执行布局的方法

        # ========== 缩略图加载定时器（滚动/初始渲染防抖） ==========
        self.visible_load_timer = QTimer(self)
        self.visible_load_timer.setSingleShot(True)
        self.visible_load_timer.timeout.connect(self.load_visible_thumbnails)

        # 1. 初始化界面
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        # 1. 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)   # 上下左右边距
        layout.setSpacing(2)                    # 组件间距

        # 2. 允许拖拽到整个 widget
        self.setAcceptDrops(True)

        # 3. 标题标签
        title_label = QLabel("目录预览")
        title_label.setStyleSheet("font-weight: bold; padding: 2px;")
        title_label.setAlignment(Qt.AlignCenter)  # 居中显示
        title_label.setMaximumHeight(25)  # 限制高度

        # 4. 滚动区域（包裹缩略图列表）
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)  # 内容可调整大小
        self.scroll_area.setMinimumWidth(DIR_PREVIEW_WIDTH)  # 最小宽度
        self.scroll_area.setVisible(False)  # 初始隐藏

        # 5. 缩略图列表 widget
        self.list_widget = QListWidget()
        # ========== 设置尺寸策略（核心，解决宽度获取失败） ==========
        self.list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.list_widget.setMinimumSize(QSize(1, 1))  # 避免最小尺寸为0
        # ========== 新增：强制横向排列（Qt6 IconMode 必设，核心修复） ==========
        self.list_widget.setFlow(QListWidget.LeftToRight)  # 核心：强制横向排列
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)  # 图标模式
        self.list_widget.setSpacing(5)  # 项之间的间距
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 显示垂直滚动条按需显示
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 水平滚动条总是隐藏
        self.list_widget.setMovement(QListWidget.Movement.Static)  # 禁止拖动
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)  # 自适应大小
        self.list_widget.setWrapping(True)  # 开启自动换行（核心，必须保留）
        self.list_widget.setGridSize(QSize(-1, -1))  # 核心：取消固定网格，使用-1而不是0
        # ========== 新增：关闭强制统一项尺寸（Qt6 IconMode 最核心坑，必关） ==========
        self.list_widget.setUniformItemSizes(False)
        # ========== 新增：Qt6绘制/布局优化，确保项优先渲染 ==========
        self.list_widget.setLayoutMode(QListWidget.Batched)  # 批量布局，提升效率
        # 设置图标大小为最大缩略图尺寸（这样Qt才能正确计算布局）
        self.list_widget.setIconSize(QSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE))
        
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        # 连接滚动事件，实现延迟加载
        self.list_widget.verticalScrollBar().valueChanged.connect(self.on_scroll)

        # 6. 将 list_widget 放入 scroll_area 组合到一起
        self.scroll_area.setWidget(self.list_widget)

        # 7. 拖拽提示标签 （初始显示）
        self.drop_label = QLabel("拖拽目录到此处")
        self.drop_label.setAlignment(Qt.AlignCenter)  # 居中显示
        self.drop_label.setStyleSheet("color: gray; font-size: 10px;")  # 提示文本样式
        self.drop_label.setMinimumHeight(80)  # 最小高度，确保显示完整
        
        # 8. 添加组件到布局
        layout.addWidget(title_label)  # 标题标签
        layout.addWidget(self.scroll_area)  # 滚动区域
        layout.addWidget(self.drop_label)  # 拖拽提示标签

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        pass

    def dropEvent(self, event):
        """拖拽放下事件"""
        files = event.mimeData().urls()
        if files:
            dir_path = files[0].toLocalFile()
            if dir_path and Path(dir_path).is_dir():
                self.load_directory(dir_path)
                event.acceptProposedAction()

    def load_directory(self, dir_path: str):
        """加载目录"""
        self.current_dir = Path(dir_path)
        self.image_files = []
        self.thumbnail_items = {}

        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}

        for file_path in self.current_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                self.image_files.append(file_path)

        logger.debug(f"筛选到图片数量：{len(self.image_files)}")
        self.list_widget.setUpdatesEnabled(False)
        self.list_widget.clear()

        for file_path in self.image_files:
            item = ThumbnailItem(str(file_path))
            self.list_widget.addItem(item)
            self.thumbnail_items[str(file_path)] = item

        self.list_widget.setUpdatesEnabled(True)

        logger.debug(f"列表项总数：{self.list_widget.count()}")
        self.drop_label.setVisible(False)  # 拖拽提示标签隐藏
        self.scroll_area.setVisible(True)  # 滚动区域显示

        logger.info(f"✅ 加载目录：{self.current_dir.name}，共 {len(self.image_files)} 张图片")

        # 延迟加载缩略图，先让Qt完成初始布局
        self.list_widget.scheduleDelayedItemsLayout()
        self.schedule_visible_thumbnail_load(80)

    def schedule_visible_thumbnail_load(self, delay_ms: int = 0):
        """调度可见区域缩略图加载。"""
        if self.list_widget.count() == 0 or not self.scroll_area.isVisible():
            return

        self.visible_load_timer.start(max(delay_ms, 0))

    def get_buffered_visible_rect(self):
        """获取带缓冲区的可见区域，减少滚动时的空白闪烁。"""
        viewport_rect = self.list_widget.viewport().rect()
        buffer_size = max(THUMBNAIL_SIZE // 2, 40)
        return viewport_rect.adjusted(-buffer_size, -buffer_size, buffer_size, buffer_size)

    def _estimate_visible_range(self):
        """估算可见区域的 item 索引范围，避免遍历全部 item。"""
        total = self.list_widget.count()
        if total == 0:
            return 0, 0

        viewport = self.list_widget.viewport()
        viewport_rect = viewport.rect()

        # 用 indexAt 找到视口左上角对应的 item
        from PySide6.QtCore import QPoint
        first_idx = self.list_widget.indexAt(viewport_rect.topLeft())
        if not first_idx.isValid():
            first_idx = self.list_widget.indexAt(QPoint(5, 5))

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

    def load_visible_thumbnails(self):
        """加载可见区域的缩略图（仅扫描估算的可见范围，非全量遍历）"""
        if self.list_widget.count() == 0 or not self.scroll_area.isVisible():
            return

        first_item = self.list_widget.item(0)
        if first_item and self.list_widget.visualItemRect(first_item).isNull():
            self.schedule_visible_thumbnail_load(30)
            return

        visible_rect = self.get_buffered_visible_rect()
        scan_start, scan_end = self._estimate_visible_range()
        loaded_count = 0

        for i in range(scan_start, scan_end):
            item = self.list_widget.item(i)
            if not item or not isinstance(item, ThumbnailItem) or item.is_loaded:
                continue

            item_rect = self.list_widget.visualItemRect(item)
            if item_rect.isNull() or not visible_rect.intersects(item_rect):
                continue

            if item.load_thumbnail():
                loaded_count += 1

        if loaded_count == 0:
            return

        self.list_widget.scheduleDelayedItemsLayout()
        self.list_widget.viewport().update()
        logger.debug(f"已加载可见区域缩略图：{loaded_count} 张")

    def on_scroll(self):
        """滚动事件 - 延迟加载可见区域的缩略图"""
        self.schedule_visible_thumbnail_load(80)

    def on_item_clicked(self, item):
        """图片项点击事件"""
        if item and isinstance(item, ThumbnailItem):
            file_path = item.file_path
            if file_path:
                self.image_selected.emit(file_path)

    def _do_update_layout(self):
        """实际执行布局更新（节流后调用，核心方法）"""
        if not self.scroll_area.isVisible() or self.list_widget.count() == 0:
            return  # 无内容时直接返回，避免无效操作
        
        # 1. 保存当前滚动位置（关键：避免跳回顶部）
        scroll_bar = self.list_widget.verticalScrollBar()
        current_scroll_pos = scroll_bar.value()
        
        # 2. 强制QListWidget重新计算布局排列
        self.list_widget.scheduleDelayedItemsLayout()
        scroll_bar.setValue(current_scroll_pos)
        self.list_widget.viewport().update()
        self.schedule_visible_thumbnail_load(0)

    def update_layout(self):
        """布局更新入口（节流版），供外部splitterMoved调用"""
        self.layout_timer.start()  # 每次调用重置定时器，拖动停止后50ms执行

    def resizeEvent(self, event):
        """组件尺寸变化时，触发列表重新布局"""
        super().resizeEvent(event)
        if self.scroll_area.isVisible():
            # 使用scheduleDelayedItemsLayout让Qt自动重新布局
            self.list_widget.scheduleDelayedItemsLayout()
            self.list_widget.viewport().update()
            self.schedule_visible_thumbnail_load(30)

