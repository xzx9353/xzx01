import ast
import os
import re
import subprocess
import requests
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from werkzeug.utils import secure_filename
import concurrent.futures
import json
from threading import Lock
import time
import shutil
app = Flask(__name__)

rz=""
delete_lock = Lock()

# 设置文件保存路径
UPLOAD_FOLDER = r"data\file"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # 确保保存目录存在

# 用于并行执行任务的线程池
executor = ThreadPoolExecutor(max_workers=26)  # 调整为 50 以适应你的需求
MAX_FILE_SIZE_MB = 100  # 限制单个文件最大为 100MB
MAX_FILE_COUNT = 100    # 限制文件夹最多保存 100 个文件
start_time=0
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'aac', 'ogg'}  # 允许的音频文件类型

def allowed_file(filename):
    # 判断文件扩展名是否在允许的扩展名列表中
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# 定义执行命令的函数
def run_command(command, audio_file_path, url_count, current_count):
    global start_time,rz
    try:
        print(f"执行命令: {command}")  # 打印命令
        process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True)
        duration_value=0
        if process.stdout:
            # print(f"命令{command}执行成功，输出:\n{process.stdout}")
            duration_seconds = re.search(r'durationSeconds：(\d+)', process.stdout)
            if duration_seconds:
                duration_value = int(duration_seconds.group(1))  # 转换为整数
                # duration_value = duration_seconds.group(1)
                # 删除 durationSeconds 部分
                process.stdout = re.sub(r'durationSeconds：\d+', '', process.stdout)

            # print("durationSeconds 的值:", duration_value)
            # print("删除后的字符串:", process.stdout)
            lines = process.stdout.split('\n')
            # data = [ast.literal_eval(line) for line in lines]
            data = []
            for line in lines:
                line = line.strip()  # 去掉行首尾空格
                if line:  # 如果该行不是空行
                    # 替换单引号为双引号
                    line = line.replace("'", '"')
                    # print(f"正在解析的行：{line}")
                    try:
                        # 尝试将每一行转换为字典
                        parsed_data = ast.literal_eval(line)
                        data.append(parsed_data)
                        message="File uploaded successfully"
                        status= "SUCCESS"
                        # 检查 data 中的每个字典的 'Text' 字段
                        for item in data:
                            if isinstance(item, dict):
                                text_value = item.get('Text', '').strip()  # 获取 Text 字段并去除空格
                                text_value = text_value.replace('。', '')  # 去掉全角句号
                                if text_value == "SUCCESS_WITH_NO_VALID_FRAGMENT":
                                    # data = []  # 清空 data
                                    item['Text'] = ""  # 清空 Text 字段
                                    # status="FAILURE"
                                    message = "SUCCESS_WITH_NO_VALID_FRAGMENT"
                                    break  # 一旦匹配成功，就跳出循环
                        # print(f"解析成功: {parsed_data}")
                    except (SyntaxError, ValueError) as e:
                        rz= f"解析失败: {e}，行内容：{line}"
                        print(f"解析失败: {e}，行内容：{line}")
            json_data = {
                "message": message,
                "status": status,
                "result": data,  # 将原来的 result 替换成 data
                "durationSeconds": duration_value
            }
            rz=json_data
            print(json.dumps(json_data, ensure_ascii=False, indent=4))


        if process.stderr:
            rz=f"命令错误输出:\n{process.stderr}"
            print(f"命令错误输出:\n{process.stderr}")

        # 执行删除操作只有在所有命令都执行完成后
        with delete_lock:
            # 如果当前输出数量等于URL数量，执行删除操作
            if current_count == url_count:
                # 删除音频文件
                print(audio_file_path)
                if os.path.exists(audio_file_path):
                    os.remove(audio_file_path)
                    print(f"已删除文件: {audio_file_path}")
                else:
                    print(f"文件不存在，无法删除: {audio_file_path}")

                # 删除目录中的文件
                directory = 'data/ypfl'
                if os.path.exists(directory) and os.path.isdir(directory):
                    for filename in os.listdir(directory):
                        file_path = os.path.join(directory, filename)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            print(f"已删除文件: {file_path}")
                else:
                    print(f"目录 {directory} 不存在或不是有效的目录")


                # directory = 'data/file'
                # if os.path.exists(directory) and os.path.isdir(directory):
                #     # 遍历并删除目录中的所有文件和子目录
                #     for filename in os.listdir(directory):
                #         file_path = os.path.join(directory, filename)
                #         # 如果是文件，则删除文件
                #         if os.path.isfile(file_path):
                #             os.remove(file_path)
                #             print(f"已删除文件: {file_path}")
                #         # 如果是子目录，则删除子目录及其内容
                #         elif os.path.isdir(file_path):
                #             shutil.rmtree(file_path)
                #             print(f"已删除子目录及其内容: {file_path}")
                # else:
                #     # 若目录不存在则不执行任何操作
                #     pass
                # 打印总运行时间
                end_time = time.time()
                total_time = end_time - start_time
                print(f"所有 URL 处理完成，总共运行时间: {total_time:.2f} 秒")

    except subprocess.CalledProcessError as e:
        rz=f"命令执行失败: {e}"
        print(f"命令执行失败: {e}")
        if e.stderr:
            rz = f"错误输出:\n{e.stderr}"
            print(f"错误输出:\n{e.stderr}")
    except Exception as e:
        rz = f"发生错误: {e}"
        print(f"发生错误: {e}")


# 定义文件下载的函数
def get_file_from_url(url, save_dir):
    """从给定 URL 下载文件并保存到指定目录"""
    try:
        # 请求文件并检查大小
        response = requests.head(url)  # 使用 HEAD 请求来获取文件头信息
        content_length = response.headers.get('Content-Length')
        if content_length:
            file_size_mb = int(content_length) / (1024 * 1024)  # 转换为 MB
            if file_size_mb > MAX_FILE_SIZE_MB:
                return None, f"文件大小超过限制：{file_size_mb:.2f} MB"

        # 下载文件
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # 使用 URL 提取文件名
        filename = os.path.basename(url)
        save_path = os.path.join(save_dir, filename)

        # 保存文件
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        return save_path, None  # 返回文件路径和错误信息
    except requests.exceptions.RequestException as e:
        print(f"下载文件失败: {e}")
        return None, f"下载文件失败: {e}"

# 检查文件夹中文件数量
def check_file_count(save_dir):
    """检查文件夹中的文件数量"""
    file_count = len([f for f in os.listdir(save_dir) if os.path.isfile(os.path.join(save_dir, f))])
    return file_count < MAX_FILE_COUNT  # 如果文件数量小于限制返回 True

# 上传处理函数
@app.route('/upload', methods=['POST'])
def ASR_func():
    global start_time,rz
    # 记录开始时间
    start_time = time.time()
    data = request.form
    # print(data)

    # 检查是否上传了文件
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({'error': 'Unsupported file types'}), 400

        # 保存上传的文件
        if file:
            filename = secure_filename(file.filename)  # 安全的文件名
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)

            # 创建并执行命令
            command = ["python", "cs3.py", "--audio_in", path]
            executor.submit(run_command, command, path, 1, 1)  # 当前url数量为1，已处理的数量为1
            while True:
                if not rz=="":
                    return jsonify(rz), 200


    data = request.json  # 获取 JSON 数据
    print(data)
    # 检查是否提供了 URL
    if 'url' in data:
        urls = data['url']  # 获取 URL 列表
        if not urls:
            return jsonify({"error": "Not provided URL"}), 400

        # 检查文件夹中的文件数量
        if not check_file_count(UPLOAD_FOLDER):
            return jsonify({'error': f"You can only save at most in a folder {MAX_FILE_COUNT} files"}), 400

        # 使用线程池并行下载每个 URL 对应的文件
        futures = []
        url_count = len(urls)
        for idx, url in enumerate(urls):
            result, error = get_file_from_url(url, UPLOAD_FOLDER)

            if error:
                return jsonify({"error": error}), 400

            # 获取文件的原始文件名
            file_name = os.path.basename(result)

            # 生成唯一的文件名，如果已存在同名文件
            unique_file_path = generate_unique_filename(os.path.join(UPLOAD_FOLDER, file_name))

            # 重命名文件
            os.rename(result, unique_file_path)

            # 每个URL下载完后执行命令
            command = ["python", "cs3.py", "--audio_in", unique_file_path]
            executor.submit(run_command, command, unique_file_path, url_count, idx + 1)

        return jsonify({"message": "所有任务已启动"}), 200

    else:
        return jsonify({"error": "No documents were provided or URL"}), 400
def generate_unique_filename(file_path):
    # 如果文件路径已存在，逐步生成唯一文件名
    base, extension = os.path.splitext(file_path)
    counter = 1
    while os.path.exists(file_path):
        file_path = f"{base}{counter}{extension}"
        counter += 1
    return file_path
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10096)
