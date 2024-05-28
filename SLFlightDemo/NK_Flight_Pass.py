# -*- coding: utf-8 -*-

import argparse
import base64
import math
import time
import json
import cv2
import numpy as np
import pyautogui
from DrissionPage import ChromiumPage
from DrissionPage._configs.chromium_options import ChromiumOptions


def main():
    start_time = time.time()
    parser = argparse.ArgumentParser(description="Process some parameters.")
    # parser.add_argument('--url', type=str, help='A url to greet.')
    parser.add_argument('--path', type=str, help='A path to greet.')
    args = parser.parse_args()

    url = 'https://www.spirit.com/'
    pic = args.path
    co = ChromiumOptions()
    co.no_imgs(True).mute(True)
    # 设置代理
    proxy_info = {
        "http": "http://us01.mofacloud.com:25114"
    }
    # 如果你的代理需要认证，可能需要使用以下格式：
    # co.set_argument('--proxy-server=http://chacha20-ietf-poly1305:686e9afd-008d-4b2f-bdc7-5c6f995cfe91@us01.mofacloud.com:25114')

    co.set_argument('--no-sandbox')
    co.set_argument('--start-maximized')
    co.incognito()  # 匿名模式
    p = ChromiumPage(co)
    try:
        targets = ['/assets/js/bundle']
        p.listen.start(targets=targets)  # 开始监听，指定获取包含该文本的数据包
        p.get(url)
        # p.wait.load_start()
        isrobot = DoRobot(p, pic, url)
        if not isrobot:
            DoClick(p, False)

    except Exception as e:
        print(e)
        if not isrobot:
            DoRobot(p, pic, url)
    finally:
        p.close()
    end_time = time.time()
    print("耗时: {:.2f}秒".format(end_time - start_time))


def DoClick(p: ChromiumPage, sec: bool):
    title = p.title
    print(f'title:{title}')
    if 'Access' in title:
        return
    if (sec):
        time.sleep(3)
    cookies = p.ele('#onetrust-accept-btn-handler', timeout=2)
    if cookies:
        cookies.click()
    cookies = p.ele('.close', timeout=2)
    if cookies:
        cookies.click()
    p.ele('.:toStation').click()
    desc = p.ele(
        'css:.stationPickerDestDropdown > div > div > div.d-flex.flex-column.flex-wrap.ng-star-inserted > div:nth-child(1) > div > p')
    desc.click()
    targets = ['api/availability/search']
    p.listen.start(targets=targets)
    p.ele('.:btn-block').click()
    # 这个就随意了。主要是为了验证点击之后是不是能通过而已
    packet = p.listen.wait(timeout=10)
    if not packet:
        raise ValueError("监听接口失败")
    coo = packet.request.cookies
    header = packet.request.headers
    token = ''
    cookies = ''
    for cooitem in coo:
        name = cooitem['name']
        value = cooitem['value']
        cookies += f'{name}={value};'
        if cooitem['name'] == 'tokenData':
            token = cooitem['value']
    person_dict = {"header": dict(header), "token": token, "cookies": cookies}
    print('jsonstart' + json.dumps(person_dict) + 'jsonEnd')

def DoRobot(page: ChromiumPage, pic: str, url: str):
    try:
        rot = page.ele('#px-captcha-modal', timeout=1)
        rot2 = page.ele('#px-captcha', timeout=1)
        sleeptime = 0
        isrobot = False
        if rot or rot2 or 'Access' in page.title:
            print('进入到机器人处理界面')

            # 截取整个屏幕
            # screenshot = pyautogui.screenshot()
            # 保存截图为文件
            # screenshot.save('.\screenshot.png')
            isrobot = True
            while sleeptime <= 0:
                re = page.listen.wait(timeout=6)  # 等待并获取一个数据包
                if not re:
                    raise ValueError("vpn出现问题,站点不让访问")
                passtimestr = re.response.body
                sleeptime = getsleeptime(passtimestr['ob'])
                print('得到结果【', sleeptime)
            # 前面的休眠时间是为了这时候的截取屏幕，不然容易截了个加载中的页面
            # 截取当前屏幕
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # 模板图片列表 有多的就继续加也可以替换
            templates = [pic]

            # 遍历所有模板，寻找匹配
            for template_name in templates:
                template = cv2.imread(template_name)
                height, width, channels = template.shape

                # 模板匹配
                res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
                # 设置匹配阈值 高于阀值才算匹配
                threshold = 0.8
                loc = np.where(res >= threshold)

                # 检查是否找到匹配项
                if np.any(res >= threshold):
                    # 取匹配区域的第一个点作为点击位置
                    for pt in zip(*loc[::-1]):
                        # 这里的x轴的值最好控制在中间，成功率高一点 35是我本机的值，大家根据自己的自己弄，或者就截图那个复选框的图片
                        # 测试过程中发现vpn也很重要，4月7号的vpn还行 4月8号换了vpn之后发现会有时间点击校验失败
                        center_point = (pt[0] + width // 2 - 35, pt[1] + height // 2)
                        break
                    print(center_point[0], center_point[1])
                    # 如果找到匹配，就点击并退出循环
                    x = int(center_point[0])
                    y = int(center_point[1])

                    pyautogui.moveTo(x, y)
                    pyautogui.mouseDown(button='left')
                    sleeptime = math.ceil(sleeptime / 1000)

                    # pyautogui.click(x, y, interval=sleeptime)
                    print(sleeptime)
                    time.sleep(sleeptime)
                    pyautogui.mouseUp(button='left')
                    time.sleep(5)
                    break
            page.get(url)
            DoClick(page, True)
            return isrobot
    except Exception as e:
        print(e)
        return True


# 获取休眠时间
def getsleeptime(buffer: str):
    buffer = base64.b64decode(buffer)
    base64_string = buffer.decode('ascii')
    res = getpt(base64_string, 122)
    index = res.find('1oo11o')
    if index == -1:
        res = getpt(base64_string, 0)
        index = res.find('1oo11o')
    if (index == -1):
        return 0
    words = res.split('|')
    for word in words:
        index = word.find('1oo11o')
        if (index != -1):
            index = words.index(word)
            desc = words[index + 4].split('_')[-1]
            desc = getpt(desc, 10)
            return int(desc)
    return 0


def getpt(source: str, len: int):
    res = ''
    for se in source:
        f = ord(se)
        cc = len ^ f
        res += chr(cc)
    return res


if __name__ == "__main__":
    main()
