# -*- encoding: utf-8 -*-
import os
import time
import websockets, ssl
import asyncio
# import threading
import argparse
import json
import traceback
from multiprocessing import Process
# from funasr.fileio.datadir_writer import DatadirWriter

import logging

# 配置日志记录，设置日志级别为ERROR，表示只记录错误及更严重的日志
logging.basicConfig(level=logging.ERROR)

# 创建一个ArgumentParser对象，用于解析命令行参数
parser = argparse.ArgumentParser()

# 解析主机地址（默认localhost）
parser.add_argument("--host",
                    type=str,  # 参数类型为字符串
                    default="localhost",  # 默认值为localhost
                    required=False,  # 该参数不是必需的
                    help="主机IP地址，localhost或0.0.0.0")  # 参数的中文说明

# 解析端口号（默认10095）
parser.add_argument("--port",
                    type=int,  # 参数类型为整数
                    default=10095,  # 默认端口为10095
                    required=False,  # 该参数不是必需的
                    help="grpc服务器端口")  # 参数的中文说明

# 解析chunk的大小（默认为 "5, 10, 5"）
parser.add_argument("--chunk_size",
                    type=str,  # 参数类型为字符串
                    default="5, 10, 5",  # 默认值
                    help="数据块的大小")  # 参数的中文说明

# 解析chunk的间隔时间（默认为10）
parser.add_argument("--chunk_interval",
                    type=int,  # 参数类型为整数
                    default=10,  # 默认值为10
                    help="数据块之间的间隔时间")  # 参数的中文说明

# 解析热词文件路径
parser.add_argument("--hotword",
                    type=str,  # 参数类型为字符串
                    default="",  # 默认值为空字符串
                    help="热词文件路径，每行一个热词 (例如：阿里巴巴 20)")  # 参数的中文说明

# 解析输入音频文件路径
parser.add_argument("--audio_in",
                    type=str,  # 参数类型为字符串
                    default=None,  # 默认值为None
                    help="输入音频文件路径")  # 参数的中文说明

# 解析音频采样率（默认16000）
parser.add_argument("--audio_fs",
                    type=int,  # 参数类型为整数
                    default=16000,  # 默认值为16000
                    help="音频的采样率")  # 参数的中文说明

# 设置是否在没有延迟的情况下发送音频数据（默认True）
parser.add_argument("--send_without_sleep",
                    action="store_true",  # 如果在命令行中提供此参数，则设置为True
                    default=True,  # 默认值为True
                    help="如果设置了audio_in，是否在没有延迟的情况下发送音频数据")  # 参数的中文说明

# 设置使用的线程数（默认1）
parser.add_argument("--thread_num",
                    type=int,  # 参数类型为整数
                    default=1,  # 默认值为1
                    help="使用的线程数量")  # 参数的中文说明

# 设置最大打印单词数（默认10000）
parser.add_argument("--words_max_print",
                    type=int,  # 参数类型为整数
                    default=10000,  # 默认值为10000
                    help="最大打印的单词数量")  # 参数的中文说明

# 设置输出目录路径
parser.add_argument("--output_dir",
                    type=str,  # 参数类型为字符串
                    default=None,  # 默认值为None
                    help="输出目录路径")  # 参数的中文说明

# 设置是否使用SSL连接（1为使用SSL，0为不使用）
parser.add_argument("--ssl",
                    type=int,  # 参数类型为整数
                    default=1,  # 默认值为1
                    help="1表示使用SSL连接，0表示不使用SSL连接")  # 参数的中文说明

# 设置是否使用ITN（1为使用，0为不使用）
parser.add_argument("--use_itn",
                    type=int,  # 参数类型为整数
                    default=1,  # 默认值为1
                    help="1表示使用ITN，0表示不使用ITN")  # 参数的中文说明

# 设置运行模式（默认为"2pass"，可选值：offline, online, 2pass）
parser.add_argument("--mode",
                    type=str,  # 参数类型为字符串
                    default="offline",  # 默认值为"2pass"
                    help="运行模式：offline（离线）、online（在线）、2pass（两次传递模式）")  # 参数的中文说明


args = parser.parse_args()
args.chunk_size = [int(x) for x in args.chunk_size.split(",")]
# print(args)
# voices = asyncio.Queue()
from queue import Queue
xzx = {}
voices = Queue()
offline_msg_done = False

if args.output_dir is not None:
    # if os.path.exists(args.output_dir):
    #     os.remove(args.output_dir)

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)





async def record_from_scp(chunk_begin, chunk_size):
    global voices
    is_finished = False

    # 如果输入是一个scp文件
    if args.audio_in.endswith(".scp"):
        f_scp = open(args.audio_in)  # 打开scp文件
        wavs = f_scp.readlines()  # 读取所有音频文件路径
    else:
        wavs = [args.audio_in]  # 如果是单一音频文件，直接将其放入列表中

    # 热词处理
    fst_dict = {}  # 存储热词字典
    hotword_msg = ""  # 初始化热词消息为空字符串
    if args.hotword.strip() != "":  # 如果指定了热词文件
        f_scp = open(args.hotword)  # 打开热词文件
        hot_lines = f_scp.readlines()  # 读取文件中的所有行
        for line in hot_lines:  # 遍历每一行
            words = line.strip().split(" ")  # 分割每一行，空格分隔
            if len(words) < 2:  # 如果格式不符合要求，跳过
                print("Please checkout format of hotwords")
                continue
            try:
                fst_dict[" ".join(words[:-1])] = int(words[-1])  # 将热词和对应的数字存入字典
            except ValueError:  # 如果转换数字失败，打印错误提示
                print("Please checkout format of hotwords")
        hotword_msg = json.dumps(fst_dict)  # 将热词字典转换为JSON格式
        # print(hotword_msg)  # 输出热词消息

    sample_rate = args.audio_fs  # 设置音频采样率
    wav_format = "pcm"  # 设置音频格式为pcm
    use_itn = True  # 是否使用ITN（自然语言处理中的反转数字标记等处理）

    if args.use_itn == 0:  # 如果未启用ITN（反转数字标记等处理）
        use_itn = False  # 将use_itn设置为False

    # 如果有指定音频块大小（chunk_size大于0）
    if chunk_size > 0:
        wavs = wavs[chunk_begin:chunk_begin + chunk_size]  # 切割音频列表，仅保留当前块的数据

    # 遍历每一个音频文件路径（wavs列表中的每个元素）
    for wav in wavs:
        wav_splits = wav.strip().split()  # 分割每行路径，以空格为分隔符

        # 获取音频文件名，如果只有一个路径信息，则将文件名设置为"demo"
        wav_name = wav_splits[0] if len(wav_splits) > 1 else "demo"
        # 获取音频文件路径，如果只有一个路径信息，则路径为文件名
        wav_path = wav_splits[1] if len(wav_splits) > 1 else wav_splits[0]

        # 如果路径为空，跳过当前循环
        if not len(wav_path.strip()) > 0:
            continue

        # 根据文件后缀判断音频格式并读取文件
        if wav_path.endswith(".pcm"):  # 如果是pcm格式
            with open(wav_path, "rb") as f:  # 以二进制读取模式打开文件
                audio_bytes = f.read()  # 读取音频内容
        elif wav_path.endswith(".wav"):  # 如果是wav格式
            import wave
            with wave.open(wav_path, "rb") as wav_file:  # 打开wav文件
                params = wav_file.getparams()  # 获取文件的参数（如通道数、采样率等）
                sample_rate = wav_file.getframerate()  # 获取音频采样率
                frames = wav_file.readframes(wav_file.getnframes())  # 读取音频数据帧
                audio_bytes = bytes(frames)  # 将读取到的帧数据转换为字节
        else:  # 如果是其他格式
            wav_format = "others"
            with open(wav_path, "rb") as f:
                audio_bytes = f.read()  # 读取音频文件内容

        # 计算每个音频块的跨度（每个块的字节数）
        stride = int(60 * args.chunk_size[1] / args.chunk_interval / 1000 * sample_rate * 2)

        # 计算音频文件的总块数
        chunk_num = (len(audio_bytes) - 1) // stride + 1

        # 构建消息体，准备发送
        message = json.dumps({
            "mode": args.mode,  # 模式，离线、在线、两次传递模式
            "chunk_size": args.chunk_size,  # 每个块的大小
            "chunk_interval": args.chunk_interval,  # 块之间的时间间隔
            "audio_fs": sample_rate,  # 音频采样率
            "wav_name": wav_name,  # 音频文件名
            "wav_format": wav_format,  # 音频格式
            "is_speaking": True,  # 是否正在说话
            "hotwords": hotword_msg,  # 热词信息
            "itn": use_itn  # 是否启用ITN
        })

        # voices.put(message)
        # 发送音频数据的第一部分（通常是开始说话时的音频）
        await websocket.send(message)
        is_speaking = True  # 设置正在说话标志为True

        # 遍历所有音频块，按顺序发送音频数据
        for i in range(chunk_num):
            beg = i * stride  # 当前块的起始位置
            data = audio_bytes[beg:beg + stride]  # 获取当前块的音频数据
            message = data  # 设置当前音频块为消息内容
            # voices.put(message)  # 可选：可以将消息放入队列（注释掉的代码）

            # 发送当前块的音频数据
            await websocket.send(message)

            # 如果是最后一个音频块，更新说话状态为结束
            if i == chunk_num - 1:
                is_speaking = False  # 设置说话结束标志
                message = json.dumps({"is_speaking": is_speaking})  # 构建说话结束的消息
                # voices.put(message)  # 可选：将结束消息放入队列（注释掉的代码）

                # 发送说话结束的消息
                await websocket.send(message)

            # 设置发送下一个音频块之前的休眠时间（根据模式不同，间隔时间不同）
            sleep_duration = 0.001 if args.mode == "offline" else 60 * args.chunk_size[1] / args.chunk_interval / 1000

            # 按照计算的时间间隔进行休眠
            await asyncio.sleep(sleep_duration)

        # # 如果是离线模式，延时2秒再关闭WebSocket连接
        # if not args.mode == "offline":
        #     await asyncio.sleep(2)

        # 如果是离线模式，等待消息接收完成
        if args.mode == "offline":
            global offline_msg_done
            while not offline_msg_done:  # 等待离线消息处理完成
                await asyncio.sleep(0.5)

        # 关闭WebSocket连接
        await websocket.close()


# 定义异步函数 message，处理 WebSocket 接收到的消息
async def message(id):
    global websocket, voices, offline_msg_done,xzx # 引入全局变量
    text_print = ""  # 用于存储当前要打印的文本

    # 如果指定了输出目录，则打开文件进行写入，否则不写入文件
    if args.output_dir is not None:
        ibest_writer = open(os.path.join(args.output_dir, "text.{}".format(id)), "a", encoding="gbk")
    else:
        ibest_writer = None  # 不写入文件

    try:
        while True:
            # 等待并接收来自 websocket 的消息
            meg = await websocket.recv()
            meg = json.loads(meg)  # 解析 JSON 格式的消息

            # print(meg)
            # 获取消息中的关键信息
            wav_name = meg.get("wav_name", "demo")  # 获取音频文件名，默认为 "demo"
            text = meg["text"]  # 获取识别出的文本
            if not text:  # 检查 text 是否为空或为 None
                print("{2139: ('SUCCESS_WITH_NO_VALID_FRAGMENT', '。')}")
            timestamp = ""  # 时间戳
            offline_msg_done = meg.get("is_final", False)  # 判断是否为最终结果
            if "timestamp" in meg:
                timestamp = meg["timestamp"]  # 如果有时间戳，则赋值
                # print(meg)

                # 确保 meg 包含 "stamp_sents" 字段，并且 "stamp_sents" 是一个包含字典的列表
                if "stamp_sents" in meg and isinstance(meg["stamp_sents"], list):
                    stamp_sents = meg["stamp_sents"]  # 获取 "stamp_sents" 列表
                    # 提取 "end" 和 "text_seg" 并存入 xzx1，格式为字典
                    xzx1 = {entry['start']: (entry['text_seg'], entry.get('punc', ''))
                            for entry in stamp_sents if 'end' in entry and 'text_seg' in entry}
                    # print("cscsc")
                    print(xzx1)
                    xzx = xzx1

            # 如果指定了输出目录，写入文本到文件
            if ibest_writer is not None:
                if timestamp != "":
                    text_write_line = "{}\t{}\t{}\n".format(wav_name, text, timestamp)
                else:
                    text_write_line = "{}\t{}\n".format(wav_name, text)
                ibest_writer.write(text_write_line)  # 写入文件

            # 如果消息中没有 "mode"，则跳过当前循环
            if 'mode' not in meg:
                continue

            # 根据 "mode" 字段判断处理方式
            if meg["mode"] == "offline":
                # 离线模式，打印时间戳或文本
                if timestamp != "":
                    text_print += "{} timestamp: {}".format(text, timestamp)
                    # print(text +  ": " + timestamp)
                else:
                    text_print += "{}".format(text)

                # 打印当前识别的文本
                # print("\rpid" + str(id) + ": " + wav_name + ": " + text_print)
                offline_msg_done = True  # 标记消息已处理完毕


                # 注释掉的部分，若需要可取消注释来实现控制
                # offline_msg_done=True
    except Exception as e:
        pass
        # print("Exception:", e)  # 捕获并打印异常信息
        # traceback.print_exc()  # 可选，打印详细异常信息
        # await websocket.close()  # 可选，关闭 WebSocket 连接



# 定义异步函数 ws_client，用于 WebSocket 客户端通信
async def ws_client(id, chunk_begin, chunk_size):
    # 如果没有指定音频输入文件（audio_in），则默认从第 0 个开始，并且只处理一个 chunk
    if args.audio_in is None:
        chunk_begin = 0
        chunk_size = 1
    global websocket, voices, offline_msg_done  # 引入全局变量

    # 遍历需要处理的音频数据块范围（从 chunk_begin 到 chunk_begin + chunk_size）
    for i in range(chunk_begin, chunk_begin + chunk_size):
        offline_msg_done = False  # 重置离线消息标志
        voices = Queue()  # 初始化声音队列

        # 根据是否使用 SSL 连接选择 URI 和 SSL 上下文
        if args.ssl == 1:
            ssl_context = ssl.SSLContext()  # 创建 SSL 上下文
            ssl_context.check_hostname = False  # 禁止验证主机名
            ssl_context.verify_mode = ssl.CERT_NONE  # 不验证证书
            uri = "wss://{}:{}".format(args.host, args.port)  # WebSocket 安全连接（wss）
        else:
            uri = "ws://{}:{}".format(args.host, args.port)  # WebSocket 非安全连接（ws）
            ssl_context = None  # 不使用 SSL 上下文

        # print("connect to", uri)  # 打印连接信息

        # 通过 websockets 库连接到 WebSocket 服务器
        # 设置子协议为 "binary"，禁用 ping_interval（即不自动发送 ping），如果使用 SSL 则传递 ssl_context
        async with websockets.connect(uri, subprotocols=["binary"], ping_interval=None, ssl=ssl_context) as websocket:
            # 如果指定了音频输入文件，则创建一个异步任务进行音频文件的录制和发送
            if args.audio_in is not None:
                task = asyncio.create_task(record_from_scp(i, 1))  # 创建任务进行音频录制
            # 创建另一个异步任务处理来自 WebSocket 的消息
            task3 = asyncio.create_task(message(str(id) + "_" + str(i)))  # 处理指定 id 和文件 id 的消息
            # 等待两个任务同时完成
            await asyncio.gather(task, task3)

    exit(0)  # 完成后退出程序



# 定义函数 one_thread，执行 WebSocket 客户端连接并处理指定的音频数据块
def one_thread(id, chunk_begin, chunk_size):
    # 运行异步的 WebSocket 客户端函数 ws_client
    asyncio.get_event_loop().run_until_complete(ws_client(id, chunk_begin, chunk_size))
    # 保持事件循环一直运行
    asyncio.get_event_loop().run_forever()

# 主程序入口
if __name__ == '__main__':
    # 根据输入的音频文件列表计算每个进程应该处理的音频文件数量
    if args.audio_in.endswith(".scp"):  # 如果是 SCP 文件格式
        f_scp = open(args.audio_in)  # 打开 SCP 文件
        wavs = f_scp.readlines()  # 读取所有音频文件路径
    else:  # 如果是单个音频文件
        wavs = [args.audio_in]  # 直接将其放入列表中

    # 遍历音频文件列表，解析每个文件的名称和路径
    for wav in wavs:
        wav_splits = wav.strip().split()  # 按空格分隔音频文件信息
        wav_name = wav_splits[0] if len(wav_splits) > 1 else "demo"  # 文件名
        wav_path = wav_splits[1] if len(wav_splits) > 1 else wav_splits[0]  # 文件路径
        audio_type = os.path.splitext(wav_path)[-1].lower()  # 获取音频文件类型（扩展名）

    total_len = len(wavs)  # 获取总音频文件数量

    # 计算每个进程处理的音频文件数量
    if total_len >= args.thread_num:
        chunk_size = int(total_len / args.thread_num)  # 每个进程处理的音频文件数量
        remain_wavs = total_len - chunk_size * args.thread_num  # 余下的音频文件数
    else:
        chunk_size = 1  # 如果音频文件少于进程数，每个进程处理一个文件
        remain_wavs = 0  # 无剩余音频文件

    process_list = []  # 进程列表
    chunk_begin = 0  # 当前进程处理的起始音频文件索引

    # 创建并启动多个进程，每个进程处理一部分音频文件
    for i in range(args.thread_num):
        now_chunk_size = chunk_size  # 每个进程要处理的音频文件数量
        if remain_wavs > 0:  # 如果有剩余的音频文件
            now_chunk_size = chunk_size + 1  # 给当前进程分配一个额外的文件
            remain_wavs -= 1  # 余下音频文件减 1
        # 为当前进程分配音频文件的起始位置和大小
        p = Process(target=one_thread, args=(i, chunk_begin, now_chunk_size))
        chunk_begin += now_chunk_size  # 更新下一个进程的起始位置
        p.start()  # 启动进程
        process_list.append(p)  # 将进程添加到进程列表中


    # 等待所有子进程结束
    for i in process_list:
        p.join()

    # print('end')  # 所有进程结束后，打印结束信息

