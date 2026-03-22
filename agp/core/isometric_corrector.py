"""
等轴测校正核心模块
"""

import cv2
import numpy as np
import math
from pathlib import Path
from PIL import Image
from typing import Union


class IsometricCorrector:
    """等轴测角度校正器"""
    
    def __init__(self, image_input: Union[str, Path, Image.Image]):
        """
        初始化校正器
        
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
    
    def infer_hidden_corners(self, visible_corners):
        """
        基于 6 个可见点推算 2 个隐藏点
        
        推算方法：
        - ⑦ = ④ + (① - ②)
        - ⑧ = ③ + (⑥ - ⑤)
        
        Args:
            visible_corners: 6 个可见点
            
        Returns:
            8 个点的完整列表
        """
        if len(visible_corners) != 6:
            return visible_corners
        
        p1 = np.array(visible_corners[0])
        p2 = np.array(visible_corners[1])
        p3 = np.array(visible_corners[2])
        p4 = np.array(visible_corners[3])
        p5 = np.array(visible_corners[4])
        p6 = np.array(visible_corners[5])
        
        p7 = p4 + (p1 - p2)
        
        p8 = p3 + (p6 - p5)
        
        all_corners = visible_corners + [
            tuple(p7.astype(int)),
            tuple(p8.astype(int))
        ]
        
        return all_corners
    
    def calculate_isometric_angle(self, points):
        """
        计算等轴测物体的实际角度
        
        Args:
            points: 6 个可见角点
            
        Returns:
            实际角度值（度）
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
        
        return avg_angle
    
    def correct_with_affine_transform(self, target_angle: float):
        """
        使用仿射变换校正角度
        
        Args:
            target_angle: 目标角度
            
        Returns:
            校正后的 PIL Image 对象
        """
        src_points = self.detect_isometric_corners()
        if not src_points:
            return None
        
        original_angle = self.calculate_isometric_angle(src_points)
        
        p1_fixed = np.array(src_points[0])
        p2_fixed = np.array(src_points[1])
        
        original_1_3_length = np.linalg.norm(np.array(src_points[2]) - np.array(src_points[0]))
        
        angle_rad = math.radians(target_angle)
        
        p3_target = (
            p1_fixed[0] + original_1_3_length * math.cos(angle_rad),
            p1_fixed[1] - original_1_3_length * math.sin(angle_rad)
        )
        
        original_3_5_dx = src_points[4][0] - src_points[2][0]
        original_3_5_dy = src_points[4][1] - src_points[2][1]
        p5_target = (
            p3_target[0] + original_3_5_dx,
            p3_target[1] + original_3_5_dy
        )
        
        src_pts = np.array([
            src_points[0],
            src_points[1],
            src_points[4],
        ], dtype=np.float32)
        
        dst_pts = np.array([
            p1_fixed,
            p2_fixed,
            p5_target,
        ], dtype=np.float32)
        
        matrix = cv2.getAffineTransform(src_pts, dst_pts)
        
        if self.has_alpha:
            channels = cv2.split(self.img_np)
            corrected_channels = []
            for channel in channels:
                corrected = cv2.warpAffine(channel, matrix, (self.width, self.height),
                                          borderMode=cv2.BORDER_TRANSPARENT)
                corrected_channels.append(corrected)
            corrected_img = cv2.merge(corrected_channels)
        else:
            if len(self.img_np.shape) == 3:
                corrected_img = cv2.warpAffine(self.img_np, matrix, (self.width, self.height),
                                              borderMode=cv2.BORDER_TRANSPARENT)
            else:
                corrected_img = cv2.warpAffine(self.img_np, matrix, (self.width, self.height),
                                              borderMode=cv2.BORDER_TRANSPARENT)
                corrected_img = cv2.cvtColor(corrected_img, cv2.COLOR_GRAY2RGB)
        
        if len(corrected_img.shape) == 3 and corrected_img.shape[2] == 4:
            corrected_img = cv2.cvtColor(corrected_img, cv2.COLOR_BGRA2RGBA)
            result = Image.fromarray(corrected_img, 'RGBA')
        else:
            result = Image.fromarray(corrected_img)
        
        return result
    
    def correct_with_perspective_transform(self, target_angle: float):
        """
        使用透视变换校正角度
        
        Args:
            target_angle: 目标角度
            
        Returns:
            校正后的 PIL Image 对象
        """
        src_points = self.detect_isometric_corners()
        if not src_points:
            return None
        
        p1_fixed = np.array(src_points[0])
        p2_fixed = np.array(src_points[1])
        
        top_edge_length = np.linalg.norm(np.array(src_points[0]) - np.array(src_points[4]))
        bottom_edge_length = np.linalg.norm(np.array(src_points[1]) - np.array(src_points[5]))
        avg_edge_length = (top_edge_length + bottom_edge_length) / 2
        
        angle_rad = math.radians(target_angle)
        
        p3_target = (
            p1_fixed[0] + avg_edge_length * math.cos(angle_rad),
            p1_fixed[1] - avg_edge_length * math.sin(angle_rad)
        )
        
        p5_target = (
            p3_target[0] + avg_edge_length * math.cos(angle_rad),
            p3_target[1] + avg_edge_length * math.sin(angle_rad)
        )
        
        p4_target = (
            p2_fixed[0] + avg_edge_length * math.cos(angle_rad),
            p2_fixed[1] - avg_edge_length * math.sin(angle_rad)
        )
        
        p6_target = (
            p4_target[0] + avg_edge_length * math.cos(angle_rad),
            p4_target[1] + avg_edge_length * math.sin(angle_rad)
        )
        
        dst_points = [
            tuple(p1_fixed),
            tuple(p2_fixed),
            p3_target,
            p4_target,
            p5_target,
            p6_target,
            (p4_target[0] + (p1_fixed[0] - p2_fixed[0]), p4_target[1] + (p1_fixed[1] - p2_fixed[1])),
            (p3_target[0] + (p6_target[0] - p5_target[0]), p3_target[1] + (p6_target[1] - p5_target[1])),
        ]
        
        src_pts = np.array([
            src_points[0],
            src_points[1],
            src_points[4],
            src_points[5],
        ], dtype=np.float32)
        
        dst_pts = np.array([
            dst_points[0],
            dst_points[1],
            dst_points[4],
            dst_points[5],
        ], dtype=np.float32)
        
        matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
        
        all_dst_x = [p[0] for p in dst_points]
        all_dst_y = [p[1] for p in dst_points]
        min_x = max(0, int(min(all_dst_x)))
        min_y = max(0, int(min(all_dst_y)))
        max_x = int(max(all_dst_x))
        max_y = int(max(all_dst_y))
        
        new_width = max(max_x - min_x, self.width)
        new_height = max(max_y - min_y, self.height)
        
        translate_matrix = np.array([
            [1, 0, -min_x],
            [0, 1, -min_y],
            [0, 0, 1]
        ], dtype=np.float32)
        
        combined_matrix = np.matmul(translate_matrix, matrix)
        
        if self.has_alpha:
            channels = cv2.split(self.img_np)
            corrected_channels = []
            for channel in channels:
                corrected = cv2.warpPerspective(channel, combined_matrix, (new_width, new_height))
                corrected_channels.append(corrected)
            corrected_img = cv2.merge(corrected_channels)
        else:
            if len(self.img_np.shape) == 3:
                corrected_img = cv2.warpPerspective(self.img_np, combined_matrix, (new_width, new_height))
            else:
                corrected_img = cv2.warpPerspective(self.img_np, combined_matrix, (new_width, new_height))
                corrected_img = cv2.cvtColor(corrected_img, cv2.COLOR_GRAY2RGB)
        
        if len(corrected_img.shape) == 3 and corrected_img.shape[2] == 4:
            corrected_img = cv2.cvtColor(corrected_img, cv2.COLOR_BGRA2RGBA)
            result = Image.fromarray(corrected_img, 'RGBA')
        else:
            result = Image.fromarray(corrected_img)
        
        return result
    
    def save(self, image: Image.Image, output_path: str):
        """
        保存图片
        
        Args:
            image: PIL Image 对象
            output_path: 输出路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.suffix.lower() in ['.png']:
            image.save(str(output_path), 'PNG', optimize=True, compress_level=9)
        elif output_path.suffix.lower() in ['.jpg', '.jpeg']:
            if image.mode in ['RGBA', 'LA', 'PA']:
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            image.save(str(output_path), 'JPEG', quality=95)
        else:
            image.save(str(output_path))

    def correct(self, target_angle: float = 30.0, method: str = 'affine'):
        if method == 'perspective':
            return self.correct_with_perspective_transform(target_angle)
        return self.correct_with_affine_transform(target_angle)
