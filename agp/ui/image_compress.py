"""
图片压缩面板
"""

import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFileDialog, QGroupBox, QComboBox)
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from ..core.image_compressor import ImageCompressor

logger = logging.getLogger(__name__)


class ImageCompressPanel(QWidget):
    """图片压缩面板"""
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.compressor = None
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
        
        file_group = QGroupBox("当前图片")
        file_layout = QVBoxLayout(file_group)
        
        self.file_label = QLabel("请先在预览区域加载图片")
        self.file_label.setStyleSheet("color: #666;")
        
        file_layout.addWidget(self.file_label)
        
        compress_group = QGroupBox("压缩设置")
        compress_layout = QVBoxLayout(compress_group)
        
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("压缩级别："))
        
        self.level_combo = QComboBox()
        self.level_combo.addItems(["1 (低)", "3", "5", "7", "9 (高)"])
        self.level_combo.setCurrentIndex(4)
        
        level_layout.addWidget(self.level_combo)
        
        compress_layout.addLayout(level_layout)
        
        self.compress_btn = QPushButton("开始压缩")
        self.compress_btn.clicked.connect(self.compress_image)
        self.compress_btn.setEnabled(False)
        
        compress_layout.addWidget(self.compress_btn)
        
        layout.addWidget(file_group)
        layout.addWidget(compress_group)
        layout.addStretch()
    
    def on_image_changed(self, file_path: str):
        """预览区域图片改变"""
        if file_path and Path(file_path).exists():
            self.current_file = file_path
            self.file_label.setText(Path(file_path).name)
            self.compress_btn.setEnabled(True)
            
            try:
                self.compressor = ImageCompressor(file_path)
                info = self.compressor.get_compression_info()
                logger.info(f"已加载图片: {Path(file_path).name}")
                logger.info(f"  尺寸: {info['width']} x {info['height']}")
                logger.info(f"  模式: {info['mode']}")
                logger.info(f"  原始大小: {info['original_size'] / 1024:.2f} KB")
            except Exception as e:
                logger.error(f"加载失败: {str(e)}")
        else:
            self.current_file = None
            self.file_label.setText("请先在预览区域加载图片")
            self.compress_btn.setEnabled(False)
            self.compressor = None
    
    def compress_image(self):
        if not self.compressor:
            logger.error("没有可处理的图片")
            return
        
        compress_level = int(self.level_combo.currentText().split()[0])
        
        logger.info("=" * 50)
        logger.info(f"开始压缩，级别: {compress_level}")
        
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存压缩后的图片",
            "",
            "PNG 图片 (*.png)"
        )
        
        if output_path:
            try:
                compressed_size = self.compressor.compress_png(output_path, compress_level)
                original_size = self.compressor.original_size
                saved = original_size - compressed_size
                saved_percent = saved / original_size * 100
                
                logger.info("✓ 压缩完成")
                logger.info(f"  原始大小: {original_size / 1024:.2f} KB")
                logger.info(f"  压缩后: {compressed_size / 1024:.2f} KB")
                logger.info(f"  节省: {saved / 1024:.2f} KB ({saved_percent:.1f}%)")
                logger.info(f"  保存位置: {output_path}")
                logger.info("=" * 50)
                
            except Exception as e:
                logger.error(f"压缩失败: {str(e)}")
