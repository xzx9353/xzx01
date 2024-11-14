# -*- encoding: utf-8 -*-
import argparse
import os
import subprocess
import concurrent.futures
import ast
from pydub import AudioSegment


# 步骤 1: 音轨分离
def split_audio(input_audio_path, output_left_path, output_right_path):
    # 加载音频文件
    audio = AudioSegment.from_file(input_audio_path)
    # 获取音频文件时长（秒）
    audio_duration = round(audio.duration_seconds)  # 取整到秒
    print(f"durationSeconds：{audio_duration} ")

    # 检查音频是否为立体声
    if audio.channels == 2:
        # 分离立体声成左右声道
        channels = audio.split_to_mono()

        # 保存左右声道
        channels[0].export(output_left_path, format="wav")  # 左声道
        channels[1].export(output_right_path, format="wav")  # 右声道
        # print(f"音轨已分离并保存为 {output_left_path} 和 {output_right_path}")
    elif audio.channels == 1:
        print("音频文件单声道，无法分离声道。")
        # 如果是单声道，直接保存两个文件，内容相同
        audio.export(output_left_path, format="wav")
        audio.export(output_right_path, format="wav")
        print(f"音轨是单声道，已复制到 {output_left_path} 和 {output_right_path}")
    else:
        print("音频文件格式不支持，无法分离声道。")


# 步骤 2: 执行命令处理音频
def run_command(command, speaker_id):
    try:
        process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True)
        if process.stdout:
            # print(process.stdout)
            # if process.stdout.strip() == "SUCCESS_WITH_NO_VALID_FRAGMENT":
            #     process.stdout={'is_final': False, 'mode': 'offline', 'text': 'SUCCESS_WITH_NO_VALID_FRAGMENT', 'wav_name': 'demo'}
            #     process.stdout=0
            # 解析输出并提取信息
            parsed_result = ast.literal_eval(process.stdout)

            # 合并连续的句子
            merged_result = []
            current_text = ""
            current_speaker_id = speaker_id
            current_begin_time = None

            for begin_time, (text_seg, punc) in parsed_result.items():
                # 拼接 text_seg 和 punc
                text = text_seg+punc
                current_text = text
                current_speaker_id = speaker_id
                current_begin_time = begin_time


                # 判断句子是否结束（以句号或问号结尾）
                # if not (current_text.endswith('。') or current_text.endswith('？')):
                #     current_text +=  text
                #     continue  # 继续合并
                current_text = current_text.replace(" ", "")
                if current_text:
                    merged_result.append({
                        "Text": current_text,
                        "SpeakerId": current_speaker_id,
                        "BeginTime": current_begin_time
                    })

                # 开始新的句子
                current_text = text
                current_speaker_id = speaker_id
                current_begin_time = begin_time

            # 添加最后一个句子
            if current_text:
                merged_result.append({
                    "Text": current_text,
                    "SpeakerId": current_speaker_id,
                    "BeginTime": current_begin_time
                })

            # 返回处理后的合并结果
            return merged_result

    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
    return []


def run_command1(command, speaker_id):
    try:
        process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True)
        if process.stdout:
            # if process.stdout.strip() == "SUCCESS_WITH_NO_VALID_FRAGMENT":
            #     process.stdout={'is_final': False, 'mode': 'offline', 'text': 'SUCCESS_WITH_NO_VALID_FRAGMENT', 'wav_name': 'demo'}
            # 解析输出并提取信息
            parsed_result = ast.literal_eval(process.stdout)

            # 合并连续的句子
            merged_result = []
            current_text = ""
            current_speaker_id = speaker_id
            current_begin_time = None

            for begin_time, (text_seg, punc) in parsed_result.items():
                # 拼接 text_seg 和 punc
                text = text_seg+punc
                current_text = text
                current_speaker_id = speaker_id
                current_begin_time = begin_time


                # 判断句子是否结束（以句号或问号结尾）
                # if not (current_text.endswith('。') or current_text.endswith('？')):
                #     current_text +=  text
                #     continue  # 继续合并
                current_text = current_text.replace(" ", "")
                if current_text:
                    merged_result.append({
                        "Text": current_text,
                        "SpeakerId": current_speaker_id,
                        "BeginTime": current_begin_time
                    })

                # 开始新的句子
                current_text = text
                current_speaker_id = speaker_id
                current_begin_time = begin_time

            # 添加最后一个句子
            if current_text:
                merged_result.append({
                    "Text": current_text,
                    "SpeakerId": current_speaker_id,
                    "BeginTime": current_begin_time
                })

            # 返回处理后的合并结果
            return merged_result

    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
    return []

# 主函数
def main():
    parser = argparse.ArgumentParser(description="音频文件处理")
    parser.add_argument("--audio_in", type=str, required=True, help="输入音频文件路径")
    args = parser.parse_args()
    # 输入音频文件路径
    input_audio = args.audio_in
    # output_left = r"data\ypfl\left_channel.wav"
    # output_right = r"data\ypfl\right_channel.wav"
    # 从输入音频文件的路径中提取文件名（不含扩展名）
    filename_without_extension = os.path.splitext(os.path.basename(input_audio))[0]

    # 从文件名中提取数字部分（例如 'test3' 中的 '3'）
    file_number = ''.join(filter(str.isdigit, filename_without_extension))

    # 定义输出路径，使用提取的数字部分来命名输出文件
    output_left = os.path.join(r"data\ypfl", f"left_channel_{file_number}.wav")
    output_right = os.path.join(r"data\ypfl", f"right_channel_{file_number}.wav")

    # 步骤 1: 音轨分离
    split_audio(input_audio, output_left, output_right)

    # 定义命令和参数，分别为左声道和右声道
    command_left = [
        "python", "cs.py",
        "--host", "127.0.0.1",
        "--port", "10095",
        "--mode", "offline",
        "--audio_in", output_left
    ]

    command_right = [
        "python", "cs.py",
        "--host", "127.0.0.1",
        "--port", "10095",
        "--mode", "offline",
        "--audio_in", output_right
    ]

    # 使用 ThreadPoolExecutor 并行执行两个命令
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(run_command, command_left, 0),  # left_channel.wav 对应 SpeakerId: 0
            executor.submit(run_command1, command_right, 1)  # right_channel.wav 对应 SpeakerId: 1
        ]

        results = []  # 用于存储两个 SpeakerId 的结果


        # 等待每个线程完成并收集结果
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                results.extend(result)  # 将每个结果添加到 results 列表中
        # 按 BeginTime 排序所有结果
        results = sorted(results, key=lambda entry: entry['BeginTime'])

        # 打印排序后的结果
        for entry in results:
            print(entry)


# 运行主函数
if __name__ == "__main__":
    # output_left = r"..\audio\left_channel.wav"
    # output_right = r"..\audio\right_channel.wav"
    # # 删除文件
    # if os.path.exists(output_left):
    #     os.remove(output_left)
    #     print(f"已删除: {output_left}")
    # else:
    #     print(f"文件不存在: {output_left}")
    #
    # if os.path.exists(output_right):
    #     os.remove(output_right)
    #     print(f"已删除: {output_right}")
    # else:
    #     print(f"文件不存在: {output_right}")
    main()
