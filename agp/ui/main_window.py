"""
AGP 主窗口模块
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QFileDialog, QTabWidget, QStatusBar, QSplitter)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from pathlib import Path
from PIL import Image

from agp import __version__

import logging
logger = logging.getLogger(__name__)

from .config import (
    DIR_PREVIEW_WIDTH,
    FUNCTION_PANEL_WIDTH,
    BUTTON_SIZE,
    MIN_WINDOW_SIZE,
    SPLITTER_HANDLE_WIDTH,
    PREVIEW_MIN_HEIGHT,
    RESULT_MIN_HEIGHT,
)
from .event_bus import event_bus
from .widgets import (
    DirectoryPreviewWidget,
    FunctionPanelWidget,
    ImagePreviewWidget,
    ResultDisplayWidget,
    ConsoleWidget,
)


class MainWindow(QMainWindow):
    """AGP 主窗口"""

    def __init__(self):
        super().__init__()
        self.last_open_dir = ""
        self.init_ui()
        self.connect_events()

        logger.info("AGP 主窗口 初始化完成")

    def connect_events(self):
        """连接 EventBus 事件"""
        event_bus.image_selected.connect(self.on_directory_image_selected)
        event_bus.image_changed.connect(self.on_preview_image_changed)
        event_bus.function_triggered.connect(self.on_function_triggered)
        event_bus.directory_loaded.connect(self.on_directory_loaded)
        event_bus.status_updated.connect(self.update_status)
        event_bus.result_ready.connect(self.on_result_ready)
        event_bus.image_info_requested.connect(self.on_image_info_requested)

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"AGP - Automated Graphic Processing Tools v{__version__}")
        self.setMinimumSize(MIN_WINDOW_SIZE[0], MIN_WINDOW_SIZE[1])

        self.create_menu()
        self.create_central_widget()
        self.create_status_bar()

    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件")

        open_action = file_menu.addAction("打开图片")
        open_action.triggered.connect(self.open_image)

        open_dir_action = file_menu.addAction("打开目录")
        open_dir_action.triggered.connect(self.open_directory)

        file_menu.addSeparator()

        save_action = file_menu.addAction("保存")
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_image)

        save_as_action = file_menu.addAction("另存为")
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_image_as)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)

        help_menu = menubar.addMenu("帮助")
        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)

    def create_central_widget(self):
        """创建中央部件 - 三栏布局"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(SPLITTER_HANDLE_WIDTH)
        self.main_splitter.setStyleSheet("QSplitter::handle { background-color: #666; }")
        self.main_splitter.splitterMoved.connect(self.on_main_splitter_moved)

        self.dir_preview_widget = DirectoryPreviewWidget()
        self.dir_preview_widget.setMinimumWidth(DIR_PREVIEW_WIDTH)
        self.dir_preview_widget.setMaximumWidth(DIR_PREVIEW_WIDTH * 2)

        self.center_widget = QWidget()
        center_layout = QVBoxLayout(self.center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(2)

        self.preview_widget = ImagePreviewWidget()

        self.result_tabs = QTabWidget()

        self.console_widget = ConsoleWidget()
        self.result_display_widget = ResultDisplayWidget()

        self.result_tabs.addTab(self.console_widget, "控制台")
        self.result_tabs.addTab(self.result_display_widget, "执行结果")

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.preview_widget)
        self.splitter.addWidget(self.result_tabs)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setHandleWidth(SPLITTER_HANDLE_WIDTH)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #666; }")

        self.preview_widget.setMinimumHeight(PREVIEW_MIN_HEIGHT)
        self.result_tabs.setMinimumHeight(RESULT_MIN_HEIGHT)

        center_layout.addWidget(self.splitter)

        self.function_panel_widget = FunctionPanelWidget()
        self.function_panel_widget.setMinimumWidth(FUNCTION_PANEL_WIDTH)
        self.function_panel_widget.setMaximumWidth(FUNCTION_PANEL_WIDTH * 2)

        self.main_splitter.addWidget(self.dir_preview_widget)
        self.main_splitter.addWidget(self.center_widget)
        self.main_splitter.addWidget(self.function_panel_widget)
        self.main_splitter.setStretchFactor(0, 2)
        self.main_splitter.setStretchFactor(1, 5)
        self.main_splitter.setStretchFactor(2, 2)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.main_splitter)

    def create_status_bar(self):
        """创建状态栏"""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")

    def open_image(self):
        """打开图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            self.last_open_dir if self.last_open_dir else "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;所有文件 (*.*)"
        )

        if file_path:
            self.last_open_dir = str(Path(file_path).parent)
            self.preview_widget.load_image(file_path)
            logger.info(f"已加载图片: {Path(file_path).name}")

    def open_directory(self):
        """打开目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择目录",
            self.last_open_dir if self.last_open_dir else ""
        )

        if dir_path:
            self.last_open_dir = dir_path
            self.dir_preview_widget.load_directory(dir_path)
            self.statusBar.showMessage(f"已选择目录：{dir_path}")

    def save_image(self):
        """保存当前图片（覆盖原文件）"""
        current_file = self.preview_widget.get_current_file()
        if not current_file:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", "没有可保存的图片或图片来自内存")
            return

        pil_image = self.preview_widget.get_current_pil_image()
        if not pil_image:
            return

        try:
            pil_image.save(current_file)
            self.preview_widget.mark_saved()
            logger.info(f"图片已保存: {Path(current_file).name}")
            self.statusBar.showMessage(f"已保存: {Path(current_file).name}")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def save_image_as(self):
        """另存为图片"""
        pil_image = self.preview_widget.get_current_pil_image()
        if not pil_image:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", "没有可保存的图片")
            return

        current_file = self.preview_widget.get_current_file()
        default_dir = str(Path(current_file).parent) if current_file else ""

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "另存为",
            default_dir,
            "PNG 图片 (*.png);;JPEG 图片 (*.jpg)"
        )

        if file_path:
            try:
                pil_image.save(file_path)
                logger.info(f"图片已另存为: {Path(file_path).name}")
                self.statusBar.showMessage(f"已另存为: {Path(file_path).name}")
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"另存为失败: {str(e)}")

    def show_about(self):
        """显示关于对话框"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "关于 AGP",
            f"AGP - Automated Graphic Processing Tools\n\n"
            f"一个集成化的图片处理工具，支持角度检测、角度校正、图片切分等功能。\n\n"
            f"版本：v{__version__}"
        )

    def add_tab(self, widget, title):
        """添加标签页"""
        self.result_tabs.addTab(widget, title)

    def update_status(self, message: str):
        """更新状态栏"""
        self.statusBar.showMessage(message)

    def get_current_image_path(self):
        """获取当前图片路径"""
        return self.preview_widget.get_current_file()

    def on_directory_image_selected(self, file_path: str):
        """目录中图片被选中"""
        if file_path:
            self.preview_widget.switch_to_image(file_path)
            logger.info(f"已选择图片: {Path(file_path).name}")

    def on_main_splitter_moved(self, pos: int, index: int):
        """主分割器移动时更新缩略图大小"""
        if hasattr(self, 'dir_preview_widget') and self.dir_preview_widget:
            new_width = self.dir_preview_widget.width()
            if new_width > 0:
                self.dir_preview_widget.update_layout()

    def on_preview_image_changed(self, file_path: str):
        """预览区域图片变化回调"""
        if file_path:
            self.setWindowTitle(f"AGP - {Path(file_path).name}")
        else:
            self.setWindowTitle(f"AGP - Automated Graphic Processing Tools v{__version__}")

    def on_directory_loaded(self, dir_path: str):
        """目录加载完成回调"""
        self.last_open_dir = dir_path
        logger.info(f"目录已加载: {dir_path}")

    def on_result_ready(self, pil_image):
        """功能执行结果就绪回调"""
        if pil_image:
            self.result_display_widget.set_result_image(pil_image)
            self.result_tabs.setCurrentIndex(1)

    def on_image_info_requested(self, file_path: str):
        """图片信息请求回调"""
        from agp.utils.image_loader import ImageLoader
        from agp.utils.file_helper import FileHelper
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
            logger.error(f"获取图片信息失败: {str(e)}")

    # 功能ID -> (执行函数, 描述) 映射表
    FUNCTION_MAP = {
        "angle_detect": ("_exec_angle_detect", "角度检测"),
        "angle_correct": ("_exec_angle_correct", "角度校正"),
        "image_crop": ("_exec_image_crop", "图片切分"),
        "image_compress": ("_exec_image_compress", "图片压缩"),
    }

    def on_function_triggered(self, func_id: str):
        """功能按钮被点击，通过映射表分发执行"""
        current_image = self.preview_widget.get_current_pil_image()
        if not current_image:
            logger.warning("请先加载图片")
            return

        entry = self.FUNCTION_MAP.get(func_id)
        if not entry:
            logger.warning(f"未知功能: {func_id}")
            return

        method_name, desc = entry
        logger.info(f"执行功能: {desc}")
        try:
            result = getattr(self, method_name)(current_image)
            if result:
                self._handle_function_result(result, desc)
        except Exception as e:
            logger.error(f"{desc}失败: {str(e)}")

    def _handle_function_result(self, pil_image, desc: str):
        """统一处理功能执行结果，通过 EventBus 广播"""
        self.preview_widget.set_image(pil_image)
        self.preview_widget.mark_modified()
        event_bus.result_ready.emit(pil_image)
        logger.info(f"{desc}完成")

    def _exec_angle_detect(self, pil_image: Image.Image):
        """执行角度检测（仅输出结果，不产生新图片）"""
        from agp.core.angle_detector import AngleDetector
        detector = AngleDetector(pil_image)
        angle = detector.detect_angle()
        logger.info(f"检测到角度: {angle:.2f}°")
        return None

    def _exec_angle_correct(self, pil_image: Image.Image):
        """执行角度校正"""
        from agp.core.isometric_corrector import IsometricCorrector
        corrector = IsometricCorrector(pil_image)
        return corrector.correct()

    def _exec_image_crop(self, pil_image: Image.Image):
        """执行图片切分"""
        from agp.core.image_cropper import ImageCropper
        current_file = self.preview_widget.get_current_file()
        if current_file:
            cropper = ImageCropper(current_file)
            output_files = cropper.split_by_count(4, naming_style="index")
            logger.info(f"图片切分已导出: {Path(output_files[0]).parent}，共 {len(output_files)} 张")
            return cropper.crop(rows=2, cols=2)
        cropper = ImageCropper(pil_image)
        logger.info("当前为内存图片，仅执行切分预览，未导出切片文件")
        return cropper.crop(rows=2, cols=2)

    def _exec_image_compress(self, pil_image: Image.Image):
        """执行图片压缩"""
        from agp.core.image_compressor import ImageCompressor
        compressor = ImageCompressor(pil_image)
        return compressor.compress(quality=85)

    def get_console(self):
        """获取控制台组件"""
        return self.console_widget
