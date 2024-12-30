from flask import Flask, request, send_file
from werkzeug.utils import secure_filename
from epub_parser import EpubParser
import os
from datetime import datetime
import shutil
import logging

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_temp_dir(epub_filename):
    # 创建临时目录名称
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = os.path.splitext(epub_filename)[0]
    output_dir = f"{base_name}_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def create_zip_file(output_dir):
    # 创建zip文件
    zip_filename = f"{output_dir}.zip"
    shutil.make_archive(output_dir, 'zip', output_dir)
    return zip_filename

def cleanup_files(output_dir, zip_filename):
    # 清理临时文件
    try:
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        if os.path.exists(zip_filename):
            os.remove(zip_filename)
    except Exception as e:
        logger.error(f"清理文件失败: {str(e)}")

@app.route('/parse_epub', methods=['POST'])
def parse_epub():
    try:
        if 'file' not in request.files:
            return {'error': '没有文件上传'}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {'error': '未选择文件'}, 400
            
        if not file.filename.endswith('.epub'):
            return {'error': '仅支持epub文件'}, 400

        # 获取切分层级参数
        level = request.form.get('level', 1, type=int)
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        file.save(filename)

        # 创建输出目录
        output_dir = create_temp_dir(filename)

        # 解析epub文件
        parser = EpubParser(filename)
        if not parser.load_epub():
            return {'error': '解析epub文件失败'}, 500

        # 解析并保存章节
        parser.parse_and_save(output_dir, level)

        # 创建zip文件
        zip_filename = create_zip_file(output_dir)

        # 发送zip文件
        response = send_file(
            zip_filename,
            as_attachment=True,
            download_name=os.path.basename(zip_filename)
        )

        # 注册清理函数
        @response.call_on_close
        def cleanup():
            os.remove(filename)  # 删除原始epub文件
            cleanup_files(output_dir, zip_filename)

        return response

    except Exception as e:
        logger.error(f"处理失败: {str(e)}")
        return {'error': f'处理失败: {str(e)}'}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
