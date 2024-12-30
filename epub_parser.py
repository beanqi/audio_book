import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import argparse
import logging
from typing import List, Dict, Tuple
import re

class EpubParser:
    def __init__(self, epub_path: str):
        self.epub_path = epub_path
        self.book = None
        self.toc = None
        self.chapter_counter = 0  # 添加章节计数器
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_epub(self) -> bool:
        try:
            self.book = epub.read_epub(self.epub_path)
            self.toc = self.book.toc
            return True
        except Exception as e:
            self.logger.error(f"加载epub文件失败: {str(e)}")
            return False

    def get_chapter_content(self, chapter) -> str:
        try:
            if isinstance(chapter, tuple):
                chapter = chapter[0]
            if not isinstance(chapter, epub.Link):
                return ""

            documents = self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
            content = ""
            for doc in documents:
                if doc.get_name() == chapter.href:
                    soup = BeautifulSoup(doc.get_content(), 'html.parser')
                    for script in soup(["script", "style"]):
                        script.decompose()
                    content = soup.get_text().strip()
                    content = '\n'.join(line.strip() for line in content.splitlines() if line.strip())
                    break
            return content
        except Exception as e:
            self.logger.error(f"获取章节内容失败: {str(e)}")
            return ""

    def sanitize_filename(self, filename: str) -> str:
        filename = re.sub(r'[\\/*?:"<>|]', '', filename)
        filename = filename.strip()
        return filename if filename else 'chapter'

    def collect_chapter_content(self, section, level=1) -> str:
        """递归收集章节及其所有子章节的内容"""
        content = ""

        if isinstance(section, tuple):
            chapter, children = section[0], section[1]
            content += self.get_chapter_content(chapter) + "\n\n"
            if children:
                for child in children:
                    content += self.collect_chapter_content(child, level + 1)
        else:
            content += self.get_chapter_content(section) + "\n\n"

        return content

    def parse_and_save(self, output_dir: str, split_level: int):
        """
        按指定层级解析并保存内容

        Args:
            output_dir: 输出目录
            split_level: 文件切分层级
        """
        os.makedirs(output_dir, exist_ok=True)
        self.chapter_counter = 0  # 重置计数器

        def process_section(sections, current_level=1, parent_titles=None):
            if parent_titles is None:
                parent_titles = []

            for section in sections:
                if isinstance(section, tuple):
                    chapter, children = section[0], section[1]
                    current_titles = parent_titles + [chapter.title]

                    # 当前层级等于指定切分层级时，保存文件
                    if current_level == split_level:
                        self.chapter_counter += 1  # 增加计数器
                        content = self.collect_chapter_content(section)
                        full_title = "_".join(current_titles)
                        self.save_chapter(output_dir, full_title, content, current_titles)
                    elif current_level < split_level and children:
                        process_section(children, current_level + 1, current_titles)
                else:
                    # 处理单独的章节（没有子章节的情况）
                    if current_level == split_level:
                        self.chapter_counter += 1  # 增加计数器
                        current_titles = parent_titles + [section.title]
                        content = self.get_chapter_content(section)
                        full_title = "_".join(current_titles)
                        self.save_chapter(output_dir, full_title, content, current_titles)

        process_section(self.toc)

    def save_chapter(self, output_dir: str, filename: str, content: str, chapter_titles: List[str]):
        try:
            # 清理文件名并添加序号
            filename = self.sanitize_filename(filename)
            filename = f"{self.chapter_counter:03d}_{filename}"  # 添加3位数的序号前缀
            filepath = os.path.join(output_dir, f"{filename}.txt")

            # 处理重名文件
            base_filepath = filepath
            counter = 1
            while os.path.exists(filepath):
                name, ext = os.path.splitext(base_filepath)
                filepath = f"{name}_{counter}{ext}"
                counter += 1

            with open(filepath, 'w', encoding='utf-8') as f:
                # 写入完整的章节路径作为标题
                f.write(" > ".join(chapter_titles) + "\n\n")
                f.write(content)

            self.logger.info(f"保存章节: {' > '.join(chapter_titles)} -> {filepath}")

        except Exception as e:
            self.logger.error(f"保存章节 {filename} 失败: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Epub文件章节分割工具')
    parser.add_argument('input_file', help='输入的epub文件路径')
    parser.add_argument('output_dir', help='输出的文件夹路径')
    parser.add_argument('--level', type=int, help='文件切分层级（默认为1）', default=1)

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"错误：输入文件 {args.input_file} 不存在")
        return

    epub_parser = EpubParser(args.input_file)
    if not epub_parser.load_epub():
        return

    epub_parser.parse_and_save(args.output_dir, args.level)

if __name__ == "__main__":
    main()

# Created/Modified files during execution:
# 将在指定的输出目录下生成多个txt文件，文件名包含完整的章节路径
