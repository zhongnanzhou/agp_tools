"""
文件处理工具模块
"""

from pathlib import Path
import os
import shutil


class FileHelper:
    """文件处理工具类"""
    
    @staticmethod
    def get_files_by_extension(directory: str, extensions: list) -> list:
        """
        获取目录下指定扩展名的所有文件
        
        Args:
            directory: 目录路径
            extensions: 扩展名列表，如 ['.png', '.jpg']
            
        Returns:
            文件路径列表
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return []
        
        files = []
        for ext in extensions:
            files.extend(dir_path.glob(f'*{ext}'))
            files.extend(dir_path.glob(f'*{ext.upper()}'))
        
        return sorted(files)
    
    @staticmethod
    def ensure_dir(directory: str) -> Path:
        """
        确保目录存在，不存在则创建
        
        Args:
            directory: 目录路径
            
        Returns:
            Path 对象
        """
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    @staticmethod
    def get_output_path(input_path: str, output_dir: str = None, suffix: str = '_output') -> Path:
        """
        生成输出文件路径
        
        Args:
            input_path: 输入文件路径
            output_dir: 输出目录（默认与输入相同）
            suffix: 输出文件后缀
            
        Returns:
            输出文件 Path 对象
        """
        input_p = Path(input_path)
        
        if output_dir:
            output_p = Path(output_dir)
        else:
            output_p = input_p.parent
        
        output_p = output_p / f"{input_p.stem}{suffix}{input_p.suffix}"
        
        FileHelper.ensure_dir(str(output_p.parent))
        
        return output_p
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        格式化文件大小
        
        Args:
            size_bytes: 字节数
            
        Returns:
            格式化后的字符串，如 '1.23 MB'
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"
