# -*- coding: utf-8 -*-

import argparse
import base64
import datetime
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
    # pic = '.\img\\rootbot.png'
    co = ChromiumOptions()
    co.no_imgs(True).mute(True)

    # 如果你的代理需要认证，可能需要使用以下格式：

    co.set_argument('--no-sandbox')
    co.set_argument('--start-maximized')
    co.incognito()  # 匿名模式
    p = ChromiumPage(co)
    sleeptime = 0
    try:
        targets = ['/assets/js/bundle','api/availability/search']
        p.listen.start(targets=targets)  # 开始监听，指定获取包含该文本的数据包
        p.get(url)
        # p.wait.load_start()
        isrobot = DoRobot(p, pic, url,0)
        if not isrobot:
           sleeptime = DoClick(p, False)
        if sleeptime >0:
            raise ValueError("遇到人机了")

    except Exception as e:
        print(e)
        if not isrobot:
            DoRobot(p, pic, url,sleeptime)
    finally:
        p.close()
    end_time = time.time()
    print("耗时: {:.2f}秒".format(end_time - start_time))


def DoClick(p: ChromiumPage, sec: bool):
    title = p.title
    print(f'title:{title}')
    if 'Access' in title:
        return
    if sec:
        time.sleep(3)
    cookies = p.ele('#onetrust-accept-btn-handler', timeout=2)
    if cookies:
        cookies.click()
    cookies = p.ele('.close', timeout=2)
    if cookies:
        cookies.click()
    p.ele('.:toStation').click()
    desc = p.ele('css:.stationPickerDestDropdown > div > div > div.d-flex.flex-column.flex-wrap.ng-star-inserted > div:nth-child(1) > div > p',timeout=3)
    desc.click()
    p.ele('.:btn-block').click()
    # 这个就随意了。主要是为了验证点击之后是不是能通过而已
    sleeptime = 0
    index =0

    while True:
        packet = p.listen.wait(timeout=10)
        if not packet:
            if index == 0:
               raise ValueError("vpn出现问题,站点不让访问")
            else:
                break
        print(f'url: 【{packet.url}】')
        index += 1
        if 'assets/js/bundle' in packet.url:
            if sec:
                packet = p.listen.wait(timeout=6)
                if not packet:
                     print('人机第二次失败')
                     break
            else:
                if sleeptime <= 0:
                    passtimestr = packet.response.body
                    sleeptime = getsleeptime(passtimestr['ob'])
                    print('得到结果【', sleeptime)
                    # 清空请求
                    p.listen.pause(True)
                    p.listen.resume()
                    if sleeptime > 0:
                        break
                    else:
                        packet = p.listen.wait(timeout=6)
        if 'api/availability/search' in packet.url:
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
            return 0
    return sleeptime

def DoRobot(page: ChromiumPage, pic: str, url: str,sleep_time:int):
    try:
        rot = page.ele('#px-captcha-modal', timeout=1)
        rot2 = page.ele('#px-captcha', timeout=1)
        sleeptime = sleep_time
        isrobot = False
        if rot or rot2 or 'Access' in page.title:
            print(f'进入到机器人处理界面{sleeptime}')
            isrobot = True
            while sleeptime <= 0:
                re = page.listen.wait(timeout=6)  # 等待并获取一个数据包
                if not re:
                    raise ValueError("vpn出现问题,站点不让访问")
                if 'assets/js/bundle' in re.url:
                    passtimestr = re.response.body
                    sleeptime = getsleeptime(passtimestr['ob'])
                    print('得到结果【', sleeptime)
                    page.listen.pause(True)
                    page.listen.resume()
            # 前面的休眠时间是为了这时候的截取屏幕，不然容易截了个加载中的页面
            # 截取当前屏幕
            print('开始截图')
            sleeptime = math.ceil(sleeptime / 1000)
            if rot2:
                page.actions.move_to('#px-captcha',offset_x=265,duration=1)
                print(f'点击元素[px-captcha] 休眠[{sleeptime}]')
                page.actions.hold()
                time.sleep(sleeptime)
                page.actions.release()
                time.sleep(5)
                page.get(url)
                DoClick(page, True)
                return isrobot

            # 截图匹配

            # screenshot = pyautogui.screenshot()
            # now = datetime.datetime.now().strftime('%H%M')
            # screenshot.save(f'{now}.png')
            # screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            # # 写死
            # x = 925
            # y = 643
            # # 模板图片列表 有多的就继续加也可以替换
            # templates = [pic]
            # print(f'开始匹配 模板{len(templates)}')
            # # 遍历所有模板，寻找匹配
            # for template_name in templates:
            #     template = cv2.imread(template_name)
            #     height, width, channels = template.shape
            #
            #     # 模板匹配
            #     res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            #     # 设置匹配阈值 高于阀值才算匹配
            #     threshold = 0.8
            #     loc = np.where(res >= threshold)
            #
            #     # 检查是否找到匹配项
            #     if np.any(res >= threshold):
            #         # 取匹配区域的第一个点作为点击位置
            #         for pt in zip(*loc[::-1]):
            #             # 这里的x轴的值最好控制在中间，成功率高一点 35是我本机的值，大家根据自己的自己弄，或者就截图那个复选框的图片
            #             # 测试过程中发现vpn也很重要，4月7号的vpn还行 4月8号换了vpn之后发现会有时间点击校验失败
            #             center_point = (pt[0] + width // 2 - 35, pt[1] + height // 2)
            #             break
            #         print(center_point[0], center_point[1])
            #         # 如果找到匹配，就点击并退出循环
            #         x = int(center_point[0])
            #         y = int(center_point[1])
            #         break
            # pyautogui.moveTo(x, y)
            # pyautogui.mouseDown(button='left')
            #
            # # pyautogui.click(x, y, interval=sleeptime)
            # print(f'点击休眠{sleeptime}【{x} {y}】')
            # time.sleep(sleeptime)
            # pyautogui.mouseUp(button='left')
            # time.sleep(5)
            # page.get(url)
            # DoClick(page, True)
            # return isrobot
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
