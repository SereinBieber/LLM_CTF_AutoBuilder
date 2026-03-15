"""
文件处理器 - 处理文件的读写和复制
"""
from pathlib import Path
from typing import List, Optional
import shutil


class FileHandler:
    """文件处理器"""

    def __init__(self):
        self.text_extensions = {
            '.py', '.php', '.c', '.cpp', '.h', '.js', '.java', '.sql',
            '.txt', '.md', '.rst', '.json', '.yml', '.yaml', '.conf',
            '.ini', '.cfg', '.html', '.css', '.xml'
        }

    def read_file(self, path: Path) -> Optional[str]:
        """读取文本文件"""
        # 检查是否是文本文件
        if path.suffix.lower() not in self.text_extensions and path.suffix != '':
            # 可能是二进制文件，返回None
            return None

        # 尝试多种编码读取
        encodings = ['utf-8', 'gbk', 'latin-1', 'ascii']

        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"  ⚠️ 读取失败 {path.name}: {e}")
                return None

        return None

    def write_file(self, path: Path, content: str) -> bool:
        """写入文本文件"""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"  ⚠️ 写入失败 {path.name}: {e}")
            return False

    def copy_binary(self, src: Path, dst: Path) -> bool:
        """复制二进制文件"""
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            print(f"  ⚠️ 复制失败 {src.name}: {e}")
            return False

    def collect_files(self, directory: Path) -> List[Path]:
        """收集所有文件"""
        if not directory.exists():
            return []

        files = []
        for item in directory.rglob('*'):
            if item.is_file():
                files.append(item)

        return files

    def is_text_file(self, path: Path) -> bool:
        """判断是否为文本文件"""
        # 按扩展名判断
        if path.suffix.lower() in self.text_extensions:
            return True

        # 特殊文件名
        if path.name.upper() in ['README', 'DOCKERFILE', 'MAKEFILE', 'CHANGELOG']:
            return True

        # 尝试读取少量内容判断
        try:
            with open(path, 'r', encoding='utf-8') as f:
                f.read(1024)
            return True
        except:
            return False