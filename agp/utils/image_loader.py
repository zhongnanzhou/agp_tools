"""
图片加载工具模块
"""

import PIL
from PIL import Image
from pathlib import Path
import numpy as np


class ImageLoader:
    """图片加载工具类"""
    
    SUPPORTED_FORMATS = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp']
    
    @staticmethod
    def load_image(file_path: str):
        """
        加载图片
        
        Args:
            file_path: 图片路径
            
        Returns:
            PIL Image 对象
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")
        
        img = Image.open(file_path)
        return img
    
    @staticmethod
    def get_image_info(file_path: str):
        """
        获取图片信息
        
        Args:
            file_path: 图片路径
            
        Returns:
            字典，包含图片信息
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")
        
        img = Image.open(file_path)
        
        info = {
            'path': str(path),
            'name': path.name,
            'width': img.width,
            'height': img.height,
            'mode': img.mode,
            'format': img.format,
            'size_bytes': path.stat().st_size,
            'has_alpha': img.mode in ['RGBA', 'LA', 'PA'],
        }
        
        return info
    
    @staticmethod
    def is_supported(file_path: str) -> bool:
        """检查是否支持该格式"""
        return Path(file_path).suffix.lower() in ImageLoader.SUPPORTED_FORMATS
    
    @staticmethod
    def to_numpy(img: Image.Image) -> np.ndarray:
        """将 PIL Image 转换为 NumPy 数组"""
        return np.array(img)
    
    @staticmethod
    def from_numpy(arr: np.ndarray) -> PIL.Image:
        """将 NumPy 数组转换为 PIL Image"""
        return Image.fromarray(arr)
