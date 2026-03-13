"""
图片切分与合并核心模块
"""

from PIL import Image
from pathlib import Path


class ImageCropper:
    """图片切分工具类"""
    
    SUPPORTED_SPLITS = {
        4: (2, 2),
        6: (2, 3),
        8: (2, 4),
        9: (3, 3),
    }
    
    def __init__(self, input_path: str, output_format: str = 'png'):
        """
        初始化切分工具
        
        Args:
            input_path: 输入图片路径
            output_format: 输出格式（png 或 jpg）
        """
        self.input_path = Path(input_path)
        
        if not self.input_path.exists():
            raise FileNotFoundError(f"文件不存在：{input_path}")
        
        self.image = Image.open(input_path)
        self.width, self.height = self.image.size
        self.output_format = output_format.lower()
        
        self.output_dir = self.input_path.parent / self.input_path.stem
    
    def split_image(self, rows: int, cols: int):
        """
        将图片切成 rows x cols 份
        
        Args:
            rows: 行数
            cols: 列数
            
        Returns:
            切分后的图片列表
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        images = []
        cell_width = self.width // cols
        cell_height = self.height // rows
        
        for row in range(rows):
            for col in range(cols):
                left = col * cell_width
                top = row * cell_height
                right = left + cell_width
                bottom = top + cell_height
                
                crop = self.image.crop((left, top, right, bottom))
                images.append(crop)
                
                output_name = f"{self.input_path.stem}_{row}_{col}.{self.output_format}"
                output_path = self.output_dir / output_name
                crop.save(str(output_path), quality=95)
        
        return images
    
    def split_by_count(self, count: int):
        """
        按指定数量切分图片
        
        Args:
            count: 切分数量（4、6、8、9）
            
        Returns:
            切分后的图片列表
        """
        if count not in self.SUPPORTED_SPLITS:
            raise ValueError(f"不支持的切分数量：{count}，支持的有：{list(self.SUPPORTED_SPLITS.keys())}")
        
        rows, cols = self.SUPPORTED_SPLITS[count]
        return self.split_image(rows, cols)
    
    def merge_images(self, image_paths: list, rows: int, cols: int, output_path: str = None):
        """
        合并图片
        
        Args:
            image_paths: 图片路径列表
            rows: 行数
            cols: 列数
            output_path: 输出路径
            
        Returns:
            合并后的图片
        """
        if not image_paths:
            raise ValueError("图片列表为空")
        
        first_img = Image.open(image_paths[0])
        cell_width = first_img.width
        cell_height = first_img.height
        
        total_width = cell_width * cols
        total_height = cell_height * rows
        
        merged = Image.new('RGB', (total_width, total_height), (255, 255, 255))
        
        for idx, img_path in enumerate(image_paths):
            if idx >= rows * cols:
                break
            
            img = Image.open(img_path)
            row = idx // cols
            col = idx % cols
            
            left = col * cell_width
            top = row * cell_height
            
            merged.paste(img, (left, top))
        
        if output_path:
            output_p = Path(output_path)
            output_p.parent.mkdir(parents=True, exist_ok=True)
            merged.save(str(output_p), quality=95)
        
        return merged
