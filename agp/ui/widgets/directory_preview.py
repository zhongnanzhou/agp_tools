"""目录预览组件 - 左侧栏。"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QSizePolicy
from PySide6.QtCore import Qt, QSize, QTimer
from pathlib import Path

from ..config import DIR_PREVIEW_WIDTH, THUMBNAIL_SIZE
from ..event_bus import event_bus
from .thumbnail_item import ThumbnailItem
from .thumbnail_loader import scan_image_files, load_visible_thumbnails

import logging
logger = logging.getLogger(__name__)


class DirectoryPreviewWidget(QWidget):
    """目录预览组件 - 左侧栏"""

    def __init__(self):
        super().__init__()
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
        self.visible_load_timer.timeout.connect(self._on_load_visible_thumbnails)

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

        # 4. 缩略图列表 widget（QListWidget 自带滚动，无需外层 QScrollArea）
        self.list_widget = QListWidget()
        self.list_widget.setMinimumWidth(DIR_PREVIEW_WIDTH)
        self.list_widget.setVisible(False)  # 初始隐藏，加载目录后显示
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

        # 5. 拖拽提示标签 （初始显示）
        self.drop_label = QLabel("拖拽目录到此处")
        self.drop_label.setAlignment(Qt.AlignCenter)  # 居中显示
        self.drop_label.setStyleSheet("color: gray; font-size: 10px;")  # 提示文本样式
        self.drop_label.setMinimumHeight(80)  # 最小高度，确保显示完整
        
        # 6. 添加组件到布局
        layout.addWidget(title_label)  # 标题标签
        layout.addWidget(self.list_widget)  # 缩略图列表
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
        """加载目录，使用 scan_image_files 扫描图片文件"""
        self.current_dir = Path(dir_path)
        self.image_files = scan_image_files(dir_path)
        self.thumbnail_items = {}

        self.list_widget.setUpdatesEnabled(False)
        self.list_widget.clear()

        for file_path in self.image_files:
            item = ThumbnailItem(str(file_path))
            self.list_widget.addItem(item)
            self.thumbnail_items[str(file_path)] = item

        self.list_widget.setUpdatesEnabled(True)

        logger.debug(f"列表项总数：{self.list_widget.count()}")
        self.drop_label.setVisible(False)  # 拖拽提示标签隐藏
        self.list_widget.setVisible(True)  # 缩略图列表显示

        logger.info(f"✅ 加载目录：{self.current_dir.name}，共 {len(self.image_files)} 张图片")

        # 通过 EventBus 广播目录加载完成
        event_bus.directory_loaded.emit(dir_path)

        # 延迟加载缩略图，先让Qt完成初始布局
        self.list_widget.scheduleDelayedItemsLayout()
        self.schedule_visible_thumbnail_load(80)

    def schedule_visible_thumbnail_load(self, delay_ms: int = 0):
        """调度可见区域缩略图加载。"""
        if self.list_widget.count() == 0 or not self.list_widget.isVisible():
            return

        self.visible_load_timer.start(max(delay_ms, 0))

    def _on_load_visible_thumbnails(self):
        """缩略图加载定时器回调，委托给 thumbnail_loader 模块执行。"""
        result = load_visible_thumbnails(self.list_widget)

        if result == -1:
            # 布局未就绪，重新调度
            self.schedule_visible_thumbnail_load(30)
            return

        if result > 0:
            # 有新加载的缩略图，触发布局刷新
            self.list_widget.scheduleDelayedItemsLayout()
            self.list_widget.viewport().update()

    def on_scroll(self):
        """滚动事件 - 延迟加载可见区域的缩略图"""
        self.schedule_visible_thumbnail_load(80)

    def on_item_clicked(self, item):
        """图片项点击事件，通过 EventBus 广播选中图片"""
        if item and isinstance(item, ThumbnailItem):
            file_path = item.file_path
            if file_path:
                event_bus.image_selected.emit(file_path)

    def _do_update_layout(self):
        """实际执行布局更新（节流后调用，核心方法）"""
        if not self.list_widget.isVisible() or self.list_widget.count() == 0:
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
        if self.list_widget.isVisible():
            # 使用scheduleDelayedItemsLayout让Qt自动重新布局
            self.list_widget.scheduleDelayedItemsLayout()
            self.list_widget.viewport().update()
            self.schedule_visible_thumbnail_load(30)

