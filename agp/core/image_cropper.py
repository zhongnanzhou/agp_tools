"""
图片切分与合并核心模块
"""

from PIL import Image
from pathlib import Path
from typing import Union


class ImageCropper:
    """图片切分工具类"""
    
    SUPPORTED_SPLITS = {
        4: (2, 2),
        6: (2, 3),
        8: (2, 4),
        9: (3, 3),
    }
    SUPPORTED_EXTS = ("png", "jpg", "jpeg")
    
    def __init__(self, input_source: Union[str, Path, Image.Image], output_format: str = 'png'):
        """
        初始化切分工具
        
        Args:
            input_source: 输入图片路径或 PIL Image 对象
            output_format: 输出格式（png 或 jpg）
        """
        self.input_path = None
        if isinstance(input_source, Image.Image):
            self.image = input_source.copy()
        else:
            self.input_path = Path(input_source)
            if not self.input_path.exists():
                raise FileNotFoundError(f"文件不存在：{input_source}")
            self.image = Image.open(self.input_path)
        self.width, self.height = self.image.size
        self.output_format = output_format.lower()
        self.output_dir = self.input_path.parent / self.input_path.stem if self.input_path else None

    def _resolve_output_dir(self, output_dir: Union[str, Path, None] = None):
        if output_dir:
            return Path(output_dir)
        if self.output_dir:
            return self.output_dir
        raise ValueError("内存图片切分需要显式指定输出目录")

    def _save_piece(self, piece: Image.Image, output_path: Path):
        save_image = piece
        if self.output_format in ("jpg", "jpeg") and save_image.mode in ['RGBA', 'LA', 'PA']:
            save_image = save_image.convert("RGB")
        if self.output_format == "png":
            save_image.save(str(output_path), optimize=True, compress_level=9)
        elif self.output_format in ("jpg", "jpeg"):
            save_image.save(str(output_path), quality=95)
        else:
            save_image.save(str(output_path))
    
    def split_image(
        self,
        rows: int,
        cols: int,
        output_dir: Union[str, Path, None] = None,
        save_to_disk: Union[bool, None] = None,
        naming_style: str = "grid"
    ):
        """
        将图片切成 rows x cols 份
        
        Args:
            rows: 行数
            cols: 列数
            
        Returns:
            切分后的图片列表或输出文件路径列表
        """
        if save_to_disk is None:
            save_to_disk = self.input_path is not None
        target_output_dir = None
        if save_to_disk:
            target_output_dir = self._resolve_output_dir(output_dir)
            target_output_dir.mkdir(parents=True, exist_ok=True)
        
        images = []
        output_files = []
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
                if target_output_dir:
                    stem = self.input_path.stem if self.input_path else "crop"
                    if naming_style == "index":
                        output_name = f"{len(images)}.{self.output_format}"
                    else:
                        output_name = f"{stem}_{row}_{col}.{self.output_format}"
                    output_path = target_output_dir / output_name
                    self._save_piece(crop, output_path)
                    output_files.append(str(output_path))
        
        return output_files if target_output_dir else images
    
    def split_by_count(self, count: int, output_dir: Union[str, Path, None] = None, naming_style: str = "grid"):
        """
        按指定数量切分图片
        
        Args:
            count: 切分数量（4、6、8、9）
            
        Returns:
            切分后的图片列表或输出文件路径列表
        """
        if count not in self.SUPPORTED_SPLITS:
            raise ValueError(f"不支持的切分数量：{count}，支持的有：{list(self.SUPPORTED_SPLITS.keys())}")
        
        rows, cols = self.SUPPORTED_SPLITS[count]
        return self.split_image(
            rows,
            cols,
            output_dir=output_dir,
            save_to_disk=(output_dir is not None or self.input_path is not None),
            naming_style=naming_style
        )

    def crop(self, rows: int = 2, cols: int = 2):
        images = self.split_image(rows, cols, save_to_disk=False)
        if not images:
            return None
        cell_width, cell_height = images[0].size
        mode = images[0].mode
        if mode in ['RGBA', 'LA', 'PA']:
            background = (0, 0, 0, 0)
        else:
            background = (255, 255, 255)
        result = Image.new(mode, (cell_width * cols, cell_height * rows), background)
        for idx, piece in enumerate(images):
            row = idx // cols
            col = idx % cols
            result.paste(piece, (col * cell_width, row * cell_height))
        return result
    
    @staticmethod
    def merge_images(image_paths: list, rows: int, cols: int, output_path: str = None):
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
        
        merged = Image.new(first_img.mode, (total_width, total_height), (0, 0, 0, 0) if first_img.mode in ['RGBA', 'LA', 'PA'] else (255, 255, 255))
        
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
            ext = output_p.suffix.lower()
            if ext == ".png":
                merged.save(str(output_p), optimize=True, compress_level=9)
            elif ext in [".jpg", ".jpeg"]:
                save_img = merged.convert("RGB") if merged.mode in ['RGBA', 'LA', 'PA'] else merged
                save_img.save(str(output_p), quality=95)
            else:
                merged.save(str(output_p))
        
        return merged

    @classmethod
    def detect_split_layout(cls, input_dir: Union[str, Path]):
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"目录不存在：{input_dir}")
        for count, (rows, cols) in sorted(cls.SUPPORTED_SPLITS.items(), key=lambda x: x[0], reverse=True):
            ok_ext = None
            for ext in cls.SUPPORTED_EXTS:
                if all((input_path / f"{idx}.{ext}").exists() for idx in range(1, count + 1)):
                    ok_ext = ext
                    break
            if ok_ext:
                return count, rows, cols, ok_ext
        raise ValueError(f"目录格式不正确，未找到有效切分图片：{input_dir}")

    @classmethod
    def merge_from_directory(cls, input_dir: Union[str, Path], output_path: Union[str, Path, None] = None):
        count, rows, cols, ext = cls.detect_split_layout(input_dir)
        input_path = Path(input_dir)
        image_paths = [str(input_path / f"{idx}.{ext}") for idx in range(1, count + 1)]
        merged = cls.merge_images(image_paths, rows, cols, str(output_path) if output_path else None)
        if output_path:
            return str(output_path)
        default_output = input_path.parent / f"{input_path.name}_merged.{ext}"
        if ext == "png":
            merged.save(str(default_output), optimize=True, compress_level=9)
        elif ext in ("jpg", "jpeg"):
            save_img = merged.convert("RGB") if merged.mode in ['RGBA', 'LA', 'PA'] else merged
            save_img.save(str(default_output), quality=95)
        else:
            merged.save(str(default_output))
        return str(default_output)
