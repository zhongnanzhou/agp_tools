"""
AGP UI 模块
"""

from .main_window import MainWindow
from .angle_detect import AngleDetectPanel
from .angle_correct import AngleCorrectPanel
from .image_crop import ImageCropPanel
from .image_compress import ImageCompressPanel

__all__ = [
    'MainWindow',
    'AngleDetectPanel',
    'AngleCorrectPanel', 
    'ImageCropPanel',
    'ImageCompressPanel',
]

