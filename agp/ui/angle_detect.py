"""
角度检测面板
"""

import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QGroupBox, QRadioButton)
from PySide6.QtCore import Qt
from pathlib import Path
import sys
import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))

from ..core.angle_detector import AngleDetector

logger = logging.getLogger(__name__)


class AngleDetectPanel(QWidget):
    """角度检测面板"""
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.detector = None
        self.current_file = None
        self.init_ui()
        
        if main_window:
            main_window.panel_activated.connect(self.on_panel_activated)
    
    def on_panel_activated(self, panel, file_path: str):
        """面板激活时加载图片 - 观察者模式"""
        if panel == self:
            self.on_image_changed(file_path)
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        detect_group = QGroupBox("检测设置")
        detect_layout = QVBoxLayout(detect_group)
        
        detect_type_layout = QHBoxLayout()
        self.hough_radio = QRadioButton("Hough 直线检测")
        self.hough_radio.setChecked(True)
        self.isometric_radio = QRadioButton("等轴测角点检测")
        
        detect_type_layout.addWidget(self.hough_radio)
        detect_type_layout.addWidget(self.isometric_radio)
        
        detect_layout.addLayout(detect_type_layout)
        
        btn_layout = QHBoxLayout()
        self.detect_btn = QPushButton("开始检测")
        self.detect_btn.clicked.connect(self.detect_angle)
        self.detect_btn.setEnabled(False)
        
        self.viz_btn = QPushButton("可视化角点")
        self.viz_btn.clicked.connect(self.visualize_corners)
        self.viz_btn.setEnabled(False)
        
        btn_layout.addWidget(self.detect_btn)
        btn_layout.addWidget(self.viz_btn)
        
        detect_layout.addLayout(btn_layout)
        
        layout.addWidget(detect_group)
        layout.addStretch()
    
    def on_image_changed(self, file_path: str):
        """图片变化回调"""
        if file_path:
            self.current_file = file_path
            self.detect_btn.setEnabled(True)
            logger.info(f"已加载图片: {Path(file_path).name}")
        else:
            self.current_file = None
            self.detect_btn.setEnabled(False)
            self.viz_btn.setEnabled(False)
    
    def detect_angle(self):
        """检测角度"""
        if not self.current_file:
            logger.error("没有可处理的图片")
            return
        
        logger.info("=" * 50)
        logger.info("开始角度检测...")
        
        try:
            self.detector = AngleDetector(self.current_file)
            
            if self.hough_radio.isChecked():
                result = self.detector.detect_hough_angle()
                logger.info("[Hough直线检测]")
                logger.info(f"  检测到直线数：{result['total_lines']}")
                logger.info(f"  30-60°范围直线数：{result['diagonal_lines']}")
                if result['diagonal_lines'] > 0:
                    logger.info(f"  ★ 平均角度：{result['avg_angle']:.2f}°")
                else:
                    logger.warning("未检测到有效角度的直线")
            
            elif self.isometric_radio.isChecked():
                points = self.detector.detect_isometric_corners()
                
                if points:
                    angle_info = self.detector.calculate_isometric_angle(points)
                    
                    logger.info("[等轴测角点检测]")
                    logger.info(f"  检测到 6 个角点：")
                    for i, p in enumerate(points, 1):
                        logger.info(f"    {i}. ({p[0]}, {p[1]})")
                    
                    logger.info("  ★ 角度信息：")
                    logger.info(f"    左侧顶部（①-③）：{angle_info['left_angle']:.2f}°")
                    logger.info(f"    右侧顶部（③-⑤）：{angle_info['right_angle']:.2f}°")
                    logger.info(f"    ★ 平均角度：{angle_info['avg_angle']:.2f}°")
                    
                    self.viz_btn.setEnabled(True)
                else:
                    logger.warning("未检测到等轴测角点")
            
            logger.info("=" * 50)
        
        except Exception as e:
            logger.error(f"检测失败: {str(e)}")
    
    def visualize_corners(self):
        """可视化角点"""
        if not self.current_file or not self.detector:
            return
        
        try:
            img = cv2.imread(self.current_file)
            
            points = self.detector.detect_isometric_corners()
            if not points:
                logger.warning("可视化失败：无法检测到角点")
                return
            
            hidden_points = self.detector.infer_hidden_corners(points)
            
            all_points = points + hidden_points[6:]
            
            for i, (x, y) in enumerate(all_points, 1):
                color = (0, 255, 0) if i <= 6 else (128, 128, 128)
                cv2.circle(img, (int(x), int(y)), 8, color, -1)
                cv2.putText(img, str(i), (int(x) + 10, int(y) - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            edges = [
                (0, 1), (0, 2), (0, 6), (1, 3), (1, 7), (3, 5),
                (3, 6), (6, 4), (5, 4), (5, 7), (4, 2), (2, 7),
            ]
            
            for idx1, idx2 in edges:
                pt1 = (int(all_points[idx1][0]), int(all_points[idx1][1]))
                pt2 = (int(all_points[idx2][0]), int(all_points[idx2][1]))
                cv2.line(img, pt1, pt2, (0, 255, 0), 2)
            
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(img_rgb)
            
            if self.main_window:
                self.main_window.preview_widget.set_image(pil_image, "角点可视化")
            
            logger.info("✓ 角点可视化已显示在预览区域")
        
        except Exception as e:
            logger.error(f"可视化失败: {str(e)}")
