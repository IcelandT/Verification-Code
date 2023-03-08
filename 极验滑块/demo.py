# -*- coding: utf-8 -*-
import requests
import execjs
from time import time, sleep
import random
import json
import re
from PIL import Image
import cv2


headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}


def challenge_and_gt(url="https://www.geetest.com/demo/gt/register-slide-official"):
    """ 获取初始 challenge， gt 值 """
    params = {
        "t": int(time() * 1000)
    }

    response = requests.get(url=url, headers=headers, params=params).text
    json_res = json.loads(response)
    print(f"[*] challenge ==> {json_res['challenge']}")
    print(f"[*] gt ==> {json_res['gt']}")

    return json_res["gt"], json_res["challenge"]


def step_testing(gt, challenge, url="https://api.geevisit.com/ajax.php"):
    """ 这是获取验证码前必须请求的步骤 """
    params = {
        "gt": gt,
        "challenge": challenge,
        "lang": "zh-cn",
        "pt": 0,
        "client_type": "web",
        "callback": "geetest_" + str(int(time() * 1000))
    }
    response = requests.get(url=url, headers=headers, params=params).text
    sleep(random.uniform(0.5, 0.7))

    print(f"[*] step_testing ==> {response}")


def captcha_and_related_parameters(gt, challenge, url="https://api.geevisit.com/get.php"):
    """ 获取 captcha 图片，以及相关参数 """
    params = {
        "is_next": "true",
        "type": "slide3",
        "gt": gt,
        "challenge": challenge,
        "lang": "zh-cn",
        "https": "true",
        "protocol": "https://",
        "offline": "false",
        "product": "embed",
        "api_server": "api.geevisit.com",
        "isPC": "true",
        "autoReset": "true",
        "width": "100%",
        "callback": "geetest_" + str(int(time() * 1000))
    }

    response = requests.get(url=url, headers=headers, params=params).text
    sleep(random.uniform(0.5, 0.7))
    json_res = json.loads(re.findall("\((.*?)\)", response)[0])

    challenge = json_res["challenge"]
    bg = json_res["bg"]
    slice = json_res["slice"]
    c = json_res["c"]
    s = json_res["s"]
    print(f"[*] challenge ==> {challenge}")
    print(f"[*] bg ==> {bg}")
    print(f"[*] slice ==> {slice}")
    print(f"[*] c ==> {c}")
    print(f"[*] s ==> {s}")
    return challenge, bg, slice, c, s


def download_captcha(text, url="https://static.geetest.com/"):
    """ save captcha """
    captcha_url = url + text
    captcha_content = requests.get(url=captcha_url, headers=headers).content

    captcha_name = "bg.png" if "bg" in text else "slice.png"
    with open(f"./captcha/{captcha_name}", mode="wb") as f:
        f.write(captcha_content)
        print(f"[*] success save {captcha_name}")


def w(fake_track, gap_area, c, s, challenge, gt_val):
    """ get w encrypt """
    js_file = open("w_test_trajectory.js", encoding="utf-8")
    js_code = execjs.compile(js_file.read())
    w = js_code.call("encrypt", fake_track, gap_area, c, s, challenge, gt_val)
    js_file.close()

    print(f"[*] w ==> {w}")
    return w


def request(fake_track, gap_area, c, s, challenge, gt_val, url="https://api.geevisit.com/ajax.php"):
    """ request """
    params = {
        "gt": gt_val,
        "challenge": challenge,
        "lang": "zh-cn",
        "$_BCw": 0,
        "client_type": "web",
        "w": w(fake_track, gap_area, c, s, challenge, gt_val),
        "callback": "geetest_" + str(int(time() * 1000))
    }
    sleep(random.uniform(1, 2))
    response = requests.get(url=url, headers=headers, params=params).text
    print(response)


class Geetest:
    def __init__(self):
        self.gt = None
        self.challenge = None
        self.captcha_path = "./captcha/"
        self.gap_area = None

    def reset_captcha(self):
        """ 还原验证码底图 """
        segmentation_height = 10
        segmentation_width = 80
        end_height = 160
        end_width = 260
        ut = [39, 38, 48, 49, 41, 40, 46, 47, 35, 34, 50, 51, 33, 32, 28, 29, 27, 26, 36, 37, 31, 30, 44, 45, 43, 42,
              12, 13, 23, 22, 14, 15, 21, 20, 8, 9, 25, 24, 6, 7, 3, 2, 0, 1, 11, 10, 4, 5, 19, 18, 16, 17]

        with Image.open(self.captcha_path + "bg.png") as image:
            # 创建底图
            dst = Image.new("RGB", (end_width, end_height))
            for i in range(len(ut)):
                x = ut[i] % 26 * 12 + 1
                y = segmentation_width if 25 < ut[i] else 0
                cut = image.crop((x, y, x + segmentation_height, y + segmentation_width))

                new_x = i % 26 * 10
                new_y = segmentation_width if i > 25 else 0
                dst.paste(cut, (new_x, new_y))

            dst.save(self.captcha_path + "reset.png")
            print("[*] reset captcha success!")

    def determine_gap_area(self):
        """ OpenCV确定缺口位置 """
        bg = cv2.imread(self.captcha_path + "reset.png")
        slice = cv2.imread(self.captcha_path + "slice.png")

        th, tw = slice.shape[:2]

        # 灰度转换
        captcha_image = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
        slice_image = cv2.cvtColor(slice, cv2.COLOR_BGR2GRAY)

        # 高斯模糊
        captcha_image = cv2.GaussianBlur(captcha_image, (5, 5), 0, 0)
        slice_image = cv2.GaussianBlur(slice_image, (5, 5), 0, 0)

        # Canny 边缘检测
        captcha_image = cv2.Canny(captcha_image, 255, 255)
        slice_image = cv2.Canny(slice_image, 255, 255)

        # 模板匹配
        captcha_rv = cv2.matchTemplate(captcha_image, slice_image, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(captcha_rv)

        # 识别区域
        identify_areas = (max_loc[0] + tw, max_loc[1] + th)
        cv2.rectangle(bg, max_loc, identify_areas, (0, 0, 255), 2)

        print(f"[*] determine gap area ==> {max_loc[0]} !")
        self.gap_area = max_loc[0]

    def fake_track(self):
        """ 模拟轨迹 """
        slide_track = [
            [random.randint(-50, -20), random.randint(-50, -20), 0],
            [0, 0, 0],
        ]

        if self.gap_area < 100:
            move_section = 1  # 如果移动距离小于100 那么move次数为x加上 7到20之间的数
        else:
            move_section = 2  # 如果移动距离小于100 那么move次数为x加上 2乘 7到20之间的数

        up_down = random.randint(0, 1)  # 确定一个方向 x大于0或x小于0
        y = 0  # 数组的y值
        time = random.randint(100, 180)  # 初始时间 即为第二个数组的时间  后续时间累加操作就可以了
        count = 0
        flag = 0
        repetition = int(self.gap_area / 4)  # 重复x出现的个数
        frist_count = random.randint(6, 10)  # 前面y为0的数组个数
        for i in range(self.gap_area * random.randint(move_section * 7, move_section * 21)):  # move_section 在这里起作用
            if i + 1 > self.gap_area:  # 如果i+1要等于x 或者小于x 但这里基本上都是等于x
                break
            if up_down == 0:  # up_down如果大于0 那么这个轨迹就是y增轨迹
                if i > frist_count:
                    if count == 0:
                        y += random.randint(0, 1)
                        count += 1
                    if flag > random.randint(8, 10):
                        count = 0
                        flag = 0
                    if i + 1 > int(self.gap_area / 5) * 4:
                        time += random.randint(20, 70)
                    elif i + 1 > self.gap_area - 3:
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
                    if i + 1 > int(self.gap_area / 5) * 4:
                        time += random.randint(7, 40)
                    elif i + 1 > self.gap_area - 3:
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

        print(f"[*] fake track ==> {slide_track}")
        return slide_track

    def run(self):
        """ run project """
        self.gt, self.challenge = challenge_and_gt()
        step_testing(self.gt, self.challenge)

        # 获取验证码及相关参数, 对验证码进行保存
        self.challenge, bg, slice, c, s = captcha_and_related_parameters(self.gt, self.challenge)
        download_captcha(bg)
        download_captcha(slice)

        # 还原底图
        self.reset_captcha()
        # 确定缺口位置
        self.determine_gap_area()
        # 模拟轨迹
        fake_track = self.fake_track()

        # fake request
        request(fake_track, self.gap_area, c, s, self.challenge, self.gt)


if __name__ == '__main__':
    geetest = Geetest()
    geetest.run()