from openai import OpenAI
from typing import Dict, List
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class BookChapterPodcastGenerator:
    def __init__(self, api_key: str = "xxxaaa"):
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepinfra.com/v1/openai")  # 新的初始化方式

    def generate_podcast_script(self, 
                              chapter_text: str, 
                              book_title: str = "", 
                              chapter_title: str = "",
                              output_file: str = None) -> Dict:
        prompt = f"""
        请基于以下来自《{book_title}》{chapter_title}章节的原文内容，撰写一份用于播客的完整稿件，且必须能直接用于朗读。要求如下：
        1. 精准呈现作者的主要观点和论点。
        2. 包含作者提供的支持论点、证据和示例。
        3. 提炼并纳入关键引用与数据，保持准确性。
        4. 使用简洁、流畅的语言，保证可读性与可听性。
        5. 不得生成与原文无关的内容或任何解释性文段。
        6. 输出仅包含播客稿件正文，无需额外说明或提示。
        7. 以中文撰写稿件，字数不少于3000字。

        原文内容：
        {chapter_text}
        
        示例格式：
        第X章：XXX
        一两句话概括本章内容。
        正文内容……
        """

        try:
            # 使用流式输出
            stream = self.client.chat.completions.create(
                model="Qwen/Qwen2.5-72B-Instruct",
                messages=[
                    {"role": "system", "content": "你是一个专业的读书助手，善于将书籍内容转化为生动的播客。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=30000,
                timeout=2000,
                stream=True  # 启用流式输出
            )
            
            # 收集流式响应
            podcast_script = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    podcast_script += chunk.choices[0].delta.content
                    # 可选：实时打印输出
                    print(chunk.choices[0].delta.content, end='', flush=True)

            result = {
                "book_title": book_title,
                "chapter_title": chapter_title,
                "podcast_script": podcast_script,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(podcast_script)
                print(f"\n播客脚本已保存到: {output_file}")
            return result

        except Exception as e:
            print(f"生成播客脚本时发生错误: {str(e)}")
            return None

    def batch_process_chapters(self, 
                             chapters: List[Dict], 
                             output_dir: str = "podcast_scripts",
                             max_workers: int = 30) -> List[Dict]:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        results = []

        def process_chapter(chapter):
            output_file = os.path.join(
                output_dir, 
                f"{chapter['book_title']}_{chapter['chapter_title']}.txt"
            ).replace(" ", "_")
            return self.generate_podcast_script(
                chapter_text=chapter['text'],
                book_title=chapter['book_title'],
                chapter_title=chapter['chapter_title'],
                output_file=output_file
            )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chapter = {executor.submit(process_chapter, chapter): chapter for chapter in chapters}
            for future in as_completed(future_to_chapter):
                chapter = future_to_chapter[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"处理章节 {chapter['chapter_title']} 时发生错误: {str(e)}")

        return results

def main():
    api_key = "5YX3tAaOILHUWM0pSMOMWJ23L5xIC9DPHY"
    generator = BookChapterPodcastGenerator(api_key)
    chapters = []
    input_dir = "inflation_or_deflation"
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            chapter_title = os.path.splitext(filename)[0]
            with open(os.path.join(input_dir, filename), 'r', encoding='utf-8') as file:
                chapter_text = file.read()
                chapters.append({
                    "text": chapter_text,
                    "book_title": "通胀，还是通缩：全球经济迷思",
                    "chapter_title": chapter_title
                })
    results = generator.batch_process_chapters(chapters, max_workers=15)

if __name__ == "__main__":
    main()
