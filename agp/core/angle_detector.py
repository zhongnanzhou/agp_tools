"""
角度检测核心模块
"""

import cv2
import numpy as np
import math
from pathlib import Path
from PIL import Image
from typing import Union


class AngleDetector:
    """图片角度检测器"""
    
    def __init__(self, image_input: Union[str, Path, Image.Image]):
        """
        初始化检测器
        
        Args:
            image_input: 图片路径或 PIL Image 对象
        """
        self.image_path = None
        if isinstance(image_input, Image.Image):
            self.img_pil = image_input.copy()
        else:
            self.image_path = Path(image_input)
            if not self.image_path.exists():
                raise FileNotFoundError(f"文件不存在：{image_input}")
            self.img_pil = Image.open(self.image_path)
        self.has_alpha = self.img_pil.mode in ['RGBA', 'LA', 'PA']
        self.img_np = np.array(self.img_pil)
        self.height, self.width = self.img_np.shape[:2]

    def detect_angle(self) -> float:
        hough_result = self.detect_hough_angle()
        hough_angle = hough_result.get('avg_angle', 0)
        if hough_angle and hough_angle > 0:
            return float(hough_angle)
        points = self.detect_isometric_corners()
        if points:
            angle_info = self.calculate_isometric_angle(points)
            if angle_info and angle_info.get('avg_angle'):
                return float(angle_info['avg_angle'])
        return 0.0
    
    def detect_hough_angle(self):
        """
        使用 Hough 直线检测图片角度
        
        Returns:
            字典，包含检测结果
        """
        if len(self.img_np.shape) == 3 and self.img_np.shape[2] == 4:
            gray = cv2.cvtColor(self.img_np[:, :, :3], cv2.COLOR_RGB2GRAY)
        else:
            gray = cv2.cvtColor(self.img_np, cv2.COLOR_RGB2GRAY)
        
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        lines = cv2.HoughLinesP(
            edges,
            1,
            np.pi / 180,
            threshold=100,
            minLineLength=100,
            maxLineGap=10
        )
        
        if lines is None:
            return {
                'total_lines': 0,
                'diagonal_lines': 0,
                'avg_angle': 0,
                'angles': []
            }
        
        diagonal_angles = []
        all_angles = []
        
        for line in lines[:, 0]:
            x1, y1, x2, y2 = line
            dx = x2 - x1
            dy = y2 - y1
            
            if dx == 0:
                continue
            
            angle = abs(math.degrees(math.atan2(dy, dx)))
            if angle > 90:
                angle = 180 - angle
            
            all_angles.append(angle)
            
            if 30 <= angle <= 60:
                diagonal_angles.append(angle)
        
        result = {
            'total_lines': len(lines) if lines is not None else 0,
            'diagonal_lines': len(diagonal_angles),
            'avg_angle': float(np.mean(diagonal_angles)) if diagonal_angles else 0,
            'angles': diagonal_angles,
            'all_angles': all_angles
        }
        
        return result
    
    def detect_isometric_corners(self):
        """
        检测等轴测物体的 6 个特征角点
        
        基于图片坐标系（左上角为原点，y 轴向下）：
        ① 左上角：x 值最小，y 值较小
        ② 左下角：x 值最小，y 值较大
        ③ 上顶角：y 值最小（最上面）
        ④ 下顶角：y 值最大（最下面）
        ⑤ 右上角：x 值最大，y 值较小
        ⑥ 右下角：x 值最大，y 值较大
        
        Returns:
            6 个角点的坐标列表 [(x1,y1), ...]
        """
        if len(self.img_np.shape) == 3 and self.img_np.shape[2] == 4:
            gray = cv2.cvtColor(self.img_np[:, :, :3], cv2.COLOR_RGB2GRAY)
        else:
            gray = cv2.cvtColor(self.img_np, cv2.COLOR_RGB2GRAY)
        
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        kernel = np.ones((3, 3), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=2)
        eroded_edges = cv2.erode(dilated_edges, kernel, iterations=1)
        
        contours, _ = cv2.findContours(eroded_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        largest_contour = max(contours, key=cv2.contourArea)
        
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        hull = cv2.convexHull(largest_contour)
        
        topmost = tuple(hull[hull[:, :, 1].argmin()][0])
        bottommost = tuple(hull[hull[:, :, 1].argmax()][0])
        
        epsilon = 0.01 * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)
        
        corners = {}
        
        for point in approx:
            px, py = point[0]
            
            if px <= x + w * 0.4 and py < y + h * 0.5:
                if 'top_left' not in corners or (px < corners['top_left'][0]):
                    corners['top_left'] = (px, py)
            
            if px <= x + w * 0.4 and py > y + h * 0.5:
                if 'bottom_left' not in corners or (px < corners['bottom_left'][0]):
                    corners['bottom_left'] = (px, py)
            
            if px >= x + w * 0.6 and py < y + h * 0.5:
                if 'top_right' not in corners or (px > corners['top_right'][0]):
                    corners['top_right'] = (px, py)
            
            if px >= x + w * 0.6 and py > y + h * 0.5:
                if 'bottom_right' not in corners or (px > corners['bottom_right'][0]):
                    corners['bottom_right'] = (px, py)
        
        if 'top_left' not in corners:
            corners['top_left'] = (x, y)
        if 'bottom_left' not in corners:
            corners['bottom_left'] = (x, y + h)
        if 'top_right' not in corners:
            corners['top_right'] = (x + w, y)
        if 'bottom_right' not in corners:
            corners['bottom_right'] = (x + w, y + h)
        
        ordered_corners = [
            corners['top_left'],
            corners['bottom_left'],
            topmost,
            bottommost,
            corners['top_right'],
            corners['bottom_right']
        ]
        
        return ordered_corners
    
    def calculate_isometric_angle(self, points):
        """
        计算等轴测角度
        
        Args:
            points: 6 个角点
            
        Returns:
            字典，包含角度信息
        """
        if not points or len(points) < 6:
            return None
        
        p1 = np.array(points[0])
        p3 = np.array(points[2])
        p5 = np.array(points[4])
        
        dx_left = p3[0] - p1[0]
        dy_left = abs(p3[1] - p1[1])
        angle_left = math.degrees(math.atan2(dy_left, dx_left))
        
        dx_right = p5[0] - p3[0]
        dy_right = abs(p5[1] - p3[1])
        angle_right = math.degrees(math.atan2(dy_right, dx_right))
        
        avg_angle = (angle_left + angle_right) / 2
        
        return {
            'left_angle': angle_left,
            'right_angle': angle_right,
            'avg_angle': avg_angle,
            'points': points
        }
    
    def infer_hidden_corners(self, visible_corners):
        """
        推算 2 个隐藏点
        
        Args:
            visible_corners: 6 个可见角点
            
        Returns:
            8 个角点的列表
        """
        if not visible_corners or len(visible_corners) < 6:
            return visible_corners
        
        p1 = np.array(visible_corners[0])
        p2 = np.array(visible_corners[1])
        p3 = np.array(visible_corners[2])
        p4 = np.array(visible_corners[3])
        p5 = np.array(visible_corners[4])
        p6 = np.array(visible_corners[5])
        
        vector_2_to_1 = p1 - p2
        p7 = p4 + vector_2_to_1
        
        vector_5_to_6 = p6 - p5
        p8 = p3 + vector_5_to_6
        
        return visible_corners + [tuple(p7.astype(int)), tuple(p8.astype(int))]
