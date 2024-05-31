import threading
import math
import json
import re
from DrissionPage import ChromiumPage
from DrissionPage._configs.chromium_options import ChromiumOptions
from datetime import datetime, timedelta

class StockClass:
    def __init__(self, url,name, origin,stock):
        self.url = url
        self.name = name
        self.origin = origin
        self.stock = stock

# 定义一个函数，作为线程的执行体
def thread_function(stockobj:StockClass):
    url = stockobj.url
    name = stockobj.name
    origin = stockobj.origin
    stock = stockobj.stock
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
                print(f"{now.strftime('%H:%M')}: 【{name}】 : {price} : 【{sum}】")
            else:
                print("未找到匹配的内容")

    except Exception as e:
        print('出现异常', e)
    finally:
        p.close()

def main():
    # 创建对象数组
    people = [
        StockClass("https://quote.eastmoney.com/sz001979.html",'zs-sk', 9.81,1000),
        StockClass("https://quote.eastmoney.com/SZ002329.html", 'h-s',  3.73, 2500),
        StockClass("https://quote.eastmoney.com/sz002277.html",'you-a', 2.5,4000),
        StockClass("https://quote.eastmoney.com/sz001227.html", 'lz-yh', 2.74, 11200),
        StockClass("https://quote.eastmoney.com/sh601375.html", 'zy-zq', 4, 2400),
    ]
    # 创建线程对象
    threads = []
    for item in people:
        thread = threading.Thread(target=thread_function, args=(item,))
        threads.append(thread)

    # 启动线程
    for thread in threads:
        thread.start()

    # 等待所有线程执行完毕
    # for thread in threads:
    #     thread.join()

if __name__ == "__main__":
    main()
