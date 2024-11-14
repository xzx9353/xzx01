import json

import requests

# # 上传文件
# url = "http://localhost:10096/upload"
# file_path = r"C:\Users\Administrator\Downloads\failVideo1.mp3"
#
# with open(file_path, 'rb') as file:
#     files = {'file': file}
#     response = requests.post(url, files=files)
# # 确保正确解码响应内容
# response.encoding = 'utf-8'
# # 检查响应
# print("文件上传响应:")
# print(response.status_code)
# response_json = response.json()  # 直接使用 .json() 方法解析 JSON 响应
# print("解析后的响应内容:", json.dumps(response_json, ensure_ascii=False))

# 上传多个 URL
url = 'http://127.0.0.1:10096/upload'
data = {
    "url": [
        "https://puresoul.ningjingtech.com:10443/meta/test1.mp3",  # 替换为有效的 URL
        # "https://puresoul.ningjingtech.com:10443/meta/test2.mp3",  # 替换为有效的 URL
        # "https://puresoul.ningjingtech.com:10443/meta/test3.mp3",   # 替换为有效的 URL
        # "https://puresoul.ningjingtech.com:10443/meta/test4.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test5.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test6.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test7.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test8.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test9.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test10.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test11.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test12.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test13.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test14.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test15.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test16.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test17.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test18.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test19.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test20.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test21.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test22.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test23.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test24.mp3",
        # "https://puresoul.ningjingtech.com:10443/meta/test25.mp3",
        "https://puresoul.ningjingtech.com:10443/meta/test26.mp3"

    ]
}

response = requests.post(url, json=data)  # 发送 JSON 格式的数据

# 检查响应
print("URL 上传响应:")
print(response.status_code)
# print(response.text)

# 如果响应是 JSON 格式，解析它
try:
    print(response.json())
except ValueError:
    print("响应不是有效的 JSON 格式")
