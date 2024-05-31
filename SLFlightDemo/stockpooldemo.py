import argparse
import decimal
import math
import time
import json
import re
from DrissionPage import ChromiumPage
from DrissionPage._configs.chromium_options import ChromiumOptions
from datetime import datetime, timedelta


def main():
    url = 'https://quote.eastmoney.com/sz000032.html'
    origin = 15.4
    stock = 700
    co = ChromiumOptions().auto_port()
    co.no_imgs(False).mute(True)
    co.set_argument("--headless")
    co.set_argument('--start-maximized')
    # co.incognito()  # 匿名模式
    p = ChromiumPage(co)
    try:
        p.listen.start('api/qt/stock/kline/get')  # 开始监听，指定获取包含该文本的数据包
        p.get(url)
        while True:
            packet = p.listen.wait(timeout=2)
            if not packet:
                continue
            text = packet.response.body
            output = json.dumps(packet.response.body)
            # 定义一个正则表达式模式
            # 获取当前日期和时间
            now = datetime.now()

            # 将日期转换为指定格式
            formatted_date = now.strftime("%Y-%m-%d")
            pattern = fr"{formatted_date}"

            # 在字符串中搜索第一个匹配的位置
            match = re.search(pattern, text)

            # 输出匹配的位置
            if match:
                start = match.start()
                end = match.end()
                text = text[start:end + 50]
                price = text.split(',')[2]
                sum = (float(price) - origin) * stock
                sum = math.ceil(sum)
                print(f"{now.strftime('%H:%M')} : {price} : 【{sum}】")
            else:
                print("未找到匹配的内容")
        # print('jsonstart', output, 'jsonend')

        # end = time.time()
        # print('Time:', end - start)

    except Exception as e:
        print('出现异常', e)
    finally:
        p.close()
# 获取飞机航班信息
def MidMatchStr(text:str):
    # 定义一个正则表达式模式
    # 获取当前日期和时间
    now = datetime.now()

    # 将日期转换为指定格式
    formatted_date = now.strftime("%Y-%m-%d")
    pattern = fr"{formatted_date}"

    # 在字符串中搜索第一个匹配的位置
    match = re.search(pattern, text)

    # 输出匹配的位置
    if match:
        start = match.start()
        end = match.end()
        text = text[start:end+50]
        price = text.split(',')[2]
        print(f"{now.strftime('%H:%M')}-{price}")
    else:
        print("未找到匹配的内容")

if __name__ == "__main__":
    main()


