"""
图片压缩核心模块
"""

from PIL import Image
from pathlib import Path


class ImageCompressor:
    """图片压缩工具类"""
    
    def __init__(self, input_path: str):
        """
        初始化压缩工具
        
        Args:
            input_path: 输入图片路径
        """
        self.input_path = Path(input_path)
        
        if not self.input_path.exists():
            raise FileNotFoundError(f"文件不存在：{input_path}")
        
        self.image = Image.open(input_path)
        self.original_size = self.input_path.stat().st_size
    
    def compress_png(self, output_path: str = None, compress_level: int = 9):
        """
        压缩 PNG 图片
        
        Args:
            output_path: 输出路径
            compress_level: 压缩级别（0-9），9 为最高压缩
            
        Returns:
            压缩后的文件大小
        """
        if output_path is None:
            output_path = self.input_path.parent / f"{self.input_path.stem}_compressed.png"
        else:
            output_path = Path(output_path)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.image.mode == 'P':
            self.image.save(str(output_path), 'PNG', optimize=True, compress_level=compress_level)
        elif self.image.mode == 'RGBA':
            self.image.save(str(output_path), 'PNG', optimize=True, compress_level=compress_level)
        else:
            self.image = self.image.convert('P', palette=Image.ADAPTIVE, colors=256)
            self.image.save(str(output_path), 'PNG', optimize=True, compress_level=compress_level)
        
        compressed_size = output_path.stat().st_size
        return compressed_size
    
    def get_compression_info(self):
        """
        获取压缩信息
        
        Returns:
            压缩信息字典
        """
        mode = self.image.mode
        has_alpha = mode in ['RGBA', 'LA', 'PA']
        
        info = {
            'original_size': self.original_size,
            'mode': mode,
            'has_alpha': has_alpha,
            'width': self.image.width,
            'height': self.image.height,
        }
        
        return info
    
    @staticmethod
    def compress_directory(input_dir: str, output_dir: str = None, compress_level: int = 9):
        """
        批量压缩目录中的图片
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            compress_level: 压缩级别
            
        Returns:
            压缩结果列表
        """
        input_p = Path(input_dir)
        
        if output_dir is None:
            output_p = input_p.parent / f"{input_p.name}_compressed"
        else:
            output_p = Path(output_dir)
        
        output_p.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        for img_path in input_p.glob('*.png'):
            try:
                compressor = ImageCompressor(str(img_path))
                output_path = output_p / img_path.name
                compressed_size = compressor.compress_png(str(output_path), compress_level)
                
                results.append({
                    'file': img_path.name,
                    'original_size': compressor.original_size,
                    'compressed_size': compressed_size,
                    'saved': compressor.original_size - compressed_size,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'file': img_path.name,
                    'error': str(e),
                    'success': False
                })
        
        return results
