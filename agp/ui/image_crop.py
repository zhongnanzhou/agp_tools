"""
图片切分面板
"""

import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QGroupBox, QComboBox)
from pathlib import Path

from ..core.image_cropper import ImageCropper

logger = logging.getLogger(__name__)


class ImageCropPanel(QWidget):
    """图片切分面板"""
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.cropper = None
        self.current_file = None
        self.init_ui()
        
        if main_window:
            main_window.panel_activated.connect(self.on_panel_activated)
    
    def on_panel_activated(self, panel, file_path: str):
        """面板激活时加载图片 - 观察者模式"""
        if panel == self:
            self.on_image_changed(file_path)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        group = QGroupBox("图片切分")
        group_layout = QVBoxLayout(group)
        
        self.status_label = QLabel("请先在预览区域加载图片")
        self.status_label.setStyleSheet("color: #666;")
        
        self.split_combo = QComboBox()
        self.split_combo.addItems(["4 份 (2x2)", "6 份 (2x3)", "8 份 (2x4)", "9 份 (3x3)"])
        
        self.crop_btn = QPushButton("开始切分")
        self.crop_btn.clicked.connect(self.split_image)
        self.crop_btn.setEnabled(False)
        
        group_layout.addWidget(self.status_label)
        group_layout.addWidget(self.split_combo)
        group_layout.addWidget(self.crop_btn)
        
        layout.addWidget(group)
        layout.addStretch()
    
    def on_image_changed(self, file_path: str):
        """预览区域图片改变"""
        if file_path and Path(file_path).exists():
            self.current_file = file_path
            self.status_label.setText(f"当前图片：{Path(file_path).name}")
            self.cropper = ImageCropper(file_path)
            self.crop_btn.setEnabled(True)
            logger.info(f"已加载图片: {Path(file_path).name}")
        else:
            self.current_file = None
            self.status_label.setText("请先在预览区域加载图片")
            self.cropper = None
            self.crop_btn.setEnabled(False)
    
    def split_image(self):
        if not self.cropper:
            logger.error("没有可处理的图片")
            return
        
        count = int(self.split_combo.currentText().split()[0])
        
        logger.info("=" * 50)
        logger.info(f"开始切分 {count} 份...")
        
        from PySide6.QtWidgets import QFileDialog
        
        output_dir = QFileDialog.getExistingDirectory(self, "选择输出目录")
        
        if output_dir:
            try:
                output_files = self.cropper.split_by_count(count, output_dir)
                
                logger.info("✓ 切分完成")
                logger.info(f"  输出目录: {output_dir}")
                logger.info(f"  生成文件数: {len(output_files)}")
                logger.info("=" * 50)
                
            except Exception as e:
                logger.error(f"切分失败: {str(e)}")
