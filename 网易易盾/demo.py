# -*- coding: utf-8 -*-
import requests
import subprocess
import cv2
import os
import json
import re
import random


class MySubprocessPopen(subprocess.Popen):
    def __init__(self, *args, **kwargs):
        # 在调用父类（即 subprocess.Popen）的构造方法时，将 encoding 参数直接置为 UTF-8 编码格式
        super().__init__(encoding='UTF-8', *args, **kwargs)


subprocess.Popen = MySubprocessPopen

import execjs


captcha_path = "./captcha/"


def fp_val():
    """ get fp """
    js_file = open("fp.js", encoding="utf-8")
    js_code = execjs.compile(js_file.read())
    fp = js_code.call("fp_encrypt")
    js_file.close()
    print(f"[*] fp ==> {fp}")
    return fp


def cb_val():
    """ get cb """
    js_file = open("cb.js", encoding="utf-8")
    js_code = execjs.compile(js_file.read())
    cb = js_code.call("cb")
    js_file.close()
    print(f"[*] cb ==> {cb}")
    return cb


def data_val(token, track):
    """ get data val """
    js_file = open("data.js", encoding="utf-8")
    js_code = execjs.compile(js_file.read())
    data = js_code.call("get_data", token, track)
    js_file.close()
    print(f"[*] data ==> {data}")
    return data


def callback_val():
    js_file = open("callback.js", encoding="utf-8")
    js_code = execjs.compile(js_file.read())
    callback = js_code.call("callback")
    js_file.close()
    print(f"[*] callback ==> {callback}")
    return callback


def save_img(image_url):
    """ 保存图片 """
    for i in image_url.keys():
        name = "bg.jpg" if i == "bg" else "front.png"
        response = requests.get(url=image_url[f"{i}"]).content
        with open(file=os.path.join(captcha_path, name), mode="wb") as f:
            f.write(response)


# 获取背景图和slide
def get_bg_slide(url="https://c.dun.163.com/api/v3/get"):
    params = {
        "referer": "https://dun.163.com/trial/jigsaw",
        "zoneId": "CN31",
        "acToken": "",
        "id": "07e2387ab53a4d6f930b8d9a9be71bdf",
        "fp": fp_val(),
        "https": "true",
        "type": "2",
        "version": "2.21.3",
        "dpr": "1.21875",
        "dev": "1",
        "cb": cb_val(),
        "ipv6": "false",
        "runEnv": "10",
        "group": "",
        "scene": "",
        "lang": "zh-CN",
        "sdkVersion": "undefined",
        "width": "320",
        "audio": "false",
        "sizeType": "10",
        "smsVersion": "v2",
        "token": "",
        "callback": "__JSONP_6tve4an_1"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    response = requests.get(url=url, headers=headers, params=params).text
    json_res = json.loads(re.findall("\((.*?)\)", response)[0])

    bg = json_res["data"]["bg"][0]
    front = json_res["data"]["front"][0]
    token = json_res["data"]["token"]
    image_url_dict = dict(zip(["bg", "front"], [bg, front]))
    print(f"[*] image_url_dict ==> {image_url_dict}")

    save_img(image_url_dict)
    return token


def identify_gap_location():
    """ 使用 opencv 识别验证码的缺口位置 """
    bg_image = cv2.imread(os.path.join(captcha_path, "bg.jpg"))
    front_image = cv2.imread(os.path.join(captcha_path, "front.png"))
    bg_image_copy = bg_image

    th, tw = front_image.shape[:2]

    # 灰度图转换
    bg_image = cv2.cvtColor(bg_image, cv2.COLOR_BGR2GRAY)
    front_image = cv2.cvtColor(front_image, cv2.COLOR_BGR2RGB)

    # 高斯模糊
    bg_image = cv2.GaussianBlur(bg_image, (5, 5), 0, 0)
    front_image = cv2.GaussianBlur(front_image, (5, 5), 0, 0)

    # canny 边缘检测
    bg_image = cv2.Canny(bg_image, 255, 255)
    front_image = cv2.Canny(front_image, 255, 255)

    # 模板匹配
    captcha_rv = cv2.matchTemplate(bg_image, front_image, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(captcha_rv)

    # 识别区域
    identify_areas = (max_loc[0] + tw, max_loc[1] + th)
    cv2.rectangle(bg_image_copy, max_loc, identify_areas, (0, 0, 255), 2)

    print(f"[*] location ==> {max_loc[0]}")
    return max_loc[0]


def create_track(location):
    """ 模拟生成轨迹 """
    slide_track = []

    if location < 100:
        move_section = 4  # 如果移动距离小于100 那么move次数为x加上 7到20之间的数
    else:
        move_section = 4  # 如果移动距离小于100 那么move次数为x加上 2乘 7到20之间的数

    up_down = random.randint(0, 1)  # 确定一个方向 x大于0或x小于0
    y = 0  # 数组的y值
    time = random.randint(160, 230)  # 初始时间 即为第二个数组的时间  后续时间累加操作就可以了
    count = 0
    flag = 0
    repetition = int(location / 4)  # 重复x出现的个数
    frist_count = random.randint(6, 10)  # 前面y为0的数组个数
    for i in range(location * random.randint(move_section * 7, move_section * 21)):  # move_section 在这里起作用
        if i + 1 > location:  # 如果i+1要等于x 或者小于x 但这里基本上都是等于x
            break
        if up_down == 0:  # up_down如果大于0 那么这个轨迹就是y增轨迹
            if i > frist_count:
                if count == 0:
                    y += random.randint(0, 1)
                    count += 1
                if flag > random.randint(8, 10):
                    count = 0
                    flag = 0
                if i + 1 > int(location / 5) * 4:
                    time += random.randint(20, 70)
                elif i + 1 > location - 3:
                    time += random.randint(80, 180)
                else:
                    time += random.randint(0, 5)
                slide_track.append([i + 1, y, time])
                flag += 1
                if random.randint(0, 1):
                    if repetition:
                        slide_track.append([i + 1, y, time + random.randint(0, 3)])
                        flag += 1
                        repetition -= 1
            else:  # 前面几个数组y都为0
                time += random.randint(0, 5)
                slide_track.append([i + 1, y, time])
                if random.randint(0, 1):
                    if repetition:
                        slide_track.append([i + 1, y, time + random.randint(0, 3)])
                        repetition -= 1

        if up_down == 1:  # up_down如果小于0 那么这个轨迹就是y减轨迹
            if i > frist_count:
                if count == 0:
                    y -= random.randint(0, 1)
                    count += 1
                if flag > random.randint(8, 10):
                    count = 0
                    flag = 0
                if i + 1 > int(location / 5) * 4:
                    time += random.randint(7, 40)
                elif i + 1 > location - 3:
                    time += random.randint(80, 180)
                else:
                    time += random.randint(0, 5)
                slide_track.append([i + 1, y, time])
                flag += 1
                if random.randint(0, 1):
                    if repetition:
                        slide_track.append([i + 1, y, time + random.randint(0, 3)])
                        flag += 1
                        repetition -= 1
            else:
                time += random.randint(0, 5)
                slide_track.append([i + 1, y, time])
                if random.randint(0, 1):
                    if repetition:
                        slide_track.append([i + 1, y, time + random.randint(0, 3)])
                        repetition -= 1

    print(f"[*] fake track ==> {slide_track[4:]}")
    return slide_track[4:]


def request(data, token, url="https://c.dun.163.com/api/v3/check"):
    """ 请求 """
    params = {
        "referer": "https://dun.163.com/trial/jigsaw",
        "zoneId": "CN31",
        "id": "07e2387ab53a4d6f930b8d9a9be71bdf",
        "token": token,
        "acToken": "undefined",
        "data": data,
        "width": "320",
        "type": "2",
        "version": "2.21.3",
        "cb": cb_val(),
        "extraData": "",
        "bf": "0",
        "runEnv": "10",
        "sdkVersion": "undefined",
        "callback": callback_val()
    }
    headers = {
        "Referer": "https://dun.163.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    response = requests.get(url=url, headers=headers, params=params).text
    print(response)


def run():
    """ 运行项目 """
    # 获取验证码
    token = get_bg_slide()

    # 识别验证码缺口位置
    location = identify_gap_location()
    # 模拟生成轨迹
    track = create_track(location)
    # data 加密结果
    data = data_val(token, track)

    request(data, token)


if __name__ == '__main__':
    run()