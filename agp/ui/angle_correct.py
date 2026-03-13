"""
角度校正面板
"""

import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QGroupBox, QRadioButton, QLineEdit)
from PySide6.QtCore import Qt
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from ..core.isometric_corrector import IsometricCorrector

logger = logging.getLogger(__name__)


class AngleCorrectPanel(QWidget):
    """角度校正面板"""
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.corrector = None
        self.corrected_image = None
        self.current_file = None
        self.current_pil_image = None
        self.init_ui()
        
        if main_window:
            main_window.panel_activated.connect(self.on_panel_activated)
    
    def on_panel_activated(self, panel, file_path: str):
        """面板激活时加载图片 - 观察者模式"""
        if panel == self:
            self.on_image_changed(file_path)
            pil_image = self.main_window.preview_widget.get_current_pil_image()
            if pil_image:
                self.on_pil_image_changed(pil_image)
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        target_group = QGroupBox("目标角度")
        target_layout = QVBoxLayout(target_group)
        
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("手动输入："))
        self.angle_input = QLineEdit()
        self.angle_input.setPlaceholderText("如：26.565, 30, 45")
        manual_layout.addWidget(self.angle_input)
        
        target_layout.addLayout(manual_layout)
        
        standard_layout = QHBoxLayout()
        standard_layout.addWidget(QLabel("标准角度："))
        
        self.btn_26 = QPushButton("26.565°")
        self.btn_26.clicked.connect(lambda: self.set_angle(26.565))
        standard_layout.addWidget(self.btn_26)
        
        self.btn_30 = QPushButton("30°")
        self.btn_30.clicked.connect(lambda: self.set_angle(30))
        standard_layout.addWidget(self.btn_30)
        
        self.btn_45 = QPushButton("45°")
        self.btn_45.clicked.connect(lambda: self.set_angle(45))
        standard_layout.addWidget(self.btn_45)
        
        target_layout.addLayout(standard_layout)
        
        method_group = QGroupBox("校正方式")
        method_layout = QVBoxLayout(method_group)
        
        self.affine_radio = QRadioButton("仿射变换（推荐，保持形状不变）")
        self.affine_radio.setChecked(True)
        self.perspective_radio = QRadioButton("透视变换（可能改变形状）")
        
        method_layout.addWidget(self.affine_radio)
        method_layout.addWidget(self.perspective_radio)
        
        btn_layout = QHBoxLayout()
        self.correct_btn = QPushButton("开始校正")
        self.correct_btn.clicked.connect(self.correct_angle)
        self.correct_btn.setEnabled(False)
        
        self.save_btn = QPushButton("保存结果")
        self.save_btn.clicked.connect(self.save_result)
        self.save_btn.setEnabled(False)
        
        btn_layout.addWidget(self.correct_btn)
        btn_layout.addWidget(self.save_btn)
        
        layout.addWidget(target_group)
        layout.addWidget(method_group)
        layout.addLayout(btn_layout)
        layout.addStretch()
    
    def on_image_changed(self, file_path: str):
        """图片路径变化回调"""
        if file_path:
            self.current_file = file_path
            self.correct_btn.setEnabled(True)
            logger.info(f"已加载图片: {Path(file_path).name}")
        else:
            self.current_file = None
            self.current_pil_image = None
            self.correct_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
    
    def on_pil_image_changed(self, pil_image):
        """PIL图片对象变化回调"""
        self.current_pil_image = pil_image
    
    def set_angle(self, angle: float):
        """设置目标角度"""
        self.angle_input.setText(str(angle))
    
    def correct_angle(self):
        """校正角度"""
        if not self.current_file and not self.current_pil_image:
            logger.error("没有可处理的图片")
            return
        
        angle_text = self.angle_input.text().strip()
        if not angle_text:
            logger.warning("请输入目标角度")
            return
        
        try:
            target_angle = float(angle_text)
        except ValueError:
            logger.warning("请输入有效的角度值")
            return
        
        logger.info("=" * 50)
        logger.info(f"开始校正，目标角度: {target_angle}°")
        
        try:
            self.corrector = IsometricCorrector(self.current_file)
            
            if self.affine_radio.isChecked():
                self.corrected_image = self.corrector.correct_with_affine_transform(target_angle)
                method = "仿射变换"
            else:
                self.corrected_image = self.corrector.correct_with_perspective_transform(target_angle)
                method = "透视变换"
            
            if self.corrected_image:
                logger.info(f"✓ 校正完成 ({method})")
                logger.info(f"  结果尺寸: {self.corrected_image.width} x {self.corrected_image.height}")
                self.save_btn.setEnabled(True)
                
                if self.main_window:
                    self.main_window.preview_widget.set_image(self.corrected_image, "校正结果")
                
                logger.info("✓ 校正后的图片已显示在预览区域")
            else:
                logger.warning("校正失败：无法检测到角点")
            
            logger.info("=" * 50)
        
        except Exception as e:
            logger.error(f"校正失败: {str(e)}")
    
    def save_result(self):
        """保存结果"""
        if not self.corrected_image:
            return
        
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存图片",
            "",
            "PNG 图片 (*.png);;JPEG 图片 (*.jpg)"
        )
        
        if output_path:
            try:
                self.corrector.save(self.corrected_image, output_path)
                logger.info(f"✓ 已保存图片: {Path(output_path).name}")
                QMessageBox.information(self, "成功", f"图片已保存到：{output_path}")
            except Exception as e:
                logger.error(f"保存失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"保存失败：{str(e)}")
