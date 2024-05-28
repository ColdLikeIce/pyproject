import argparse
import decimal
import time
import json
import re
from DrissionPage import ChromiumPage
from DrissionPage._configs.chromium_options import ChromiumOptions
from datetime import datetime, timedelta


def main():
    # start = time.time()
    parser = argparse.ArgumentParser(description="Process some parameters.")
    parser.add_argument('--url', type=str, help='A url to greet.')
    parser.add_argument('--ratecode', type=str, help='A ratecode to greet.')
    args = parser.parse_args()
    url = args.url
    ratecode = args.ratecode
    # url = 'https://search.lionairthai.com/default.aspx?aid=207&depCity=PER&arrCity=PNK&Jtype=2&depDate=17/06/2024&arrDate=18/06/2024&adult1=1&child1=0&infant1=0&promotioncode=&df=UK&afid=0&b2b=0&St=fa&DFlight=false&roomcount=1&culture=en-GB&ur=lionairthai.com'
    # ratecode = 'SL_PER_PNK_2024-06-17_(OD9119_JT712_202406170150-202406170850_4)|PNK_PER_2024-06-18_(JT685_OD9120_202406181345-202406190020_1)_1_0'
    # url ='https://search.lionairthai.com/default.aspx?aid=207&depCity=DMK&arrCity=BLR&Jtype=1&depDate=22/07/2024&adult1=1&child1=0&infant1=0&promotioncode=&df=UK&afid=0&b2b=0&St=fa&DFlight=false&roomcount=1&culture=en-GB&ur=lionairthai.com"'
    # ratecode = 'SL_DMK_BLR_2024-07-22_(SL216_202407222100-202407222310_4)_1_0'
    adt_price = 0
    child_price = 0
    co = ChromiumOptions().auto_port()
    # co.no_imgs(False).mute(True)
    # co.set_argument("--headless")
    co.set_argument('--start-maximized')
    # co.incognito()  # 匿名模式
    p = ChromiumPage(co)
    try:
        p.listen.start('GetFlightSearch')  # 开始监听，指定获取包含该文本的数据包
        p.get(url)
        title = p.title
        if "请稍候…" in title or 'Just a moment' in title:
            waitforFrame(p)
        packet = p.listen.wait(timeout=30)
        body = packet.response.body
        output = json.dumps(packet.response.body)
        priceobj = ""
        is_match = False
        if ratecode is not None and "SL" in ratecode:
            child_num = int(ratecode.split('_')[-1])
            adt_num = int(ratecode.split('_')[-2])
            peonum = adt_num + child_num
            regList = ratecode.strip().split('|')
            for reg in regList:
                index = regList.index(reg)
                result = re.search(r'\((.*?)\)', reg)
                flyalltext = result.group(1)
                flyinfo = flyalltext.split('_')
                level = flyinfo[-1]
                flyMat = ''
                for fly in flyinfo:
                    if '-' in fly:
                        break
                    flyMat += fly
                da = body["d"]
                outindex = 0
                for item in da:
                    if(item["AFDirection"] == "OutBound"):
                        outindex +=1
                        if index != 0:
                            continue
                    code = ''
                    if level == '4':
                        segObject = item["PromoFlight"]
                    else:
                        segObject = item["EconomyFlight"]
                    flights = segObject["outBoundFlights"]
                    for fly in flights:
                        segInfos = fly["Segments"]
                        for segItem in segInfos:
                            code += segItem["MarAirLine"]+segItem["FlightNo"].lstrip('0')
                            segPoints = segItem["SegmentIntermediatePoints"]
                            if segPoints:
                                for point in segPoints:
                                    code += segItem["MarAirLine"] + segItem["FlightNo"].lstrip('0')
                    if flyMat == code:
                        is_match = True
                        afindex = int(item["AFIndex"]) +1

                        if index == 0:
                            div = p.ele(f'css:#divOBFlightResults > div:nth-child({afindex})')
                        else:
                            afindex = afindex - outindex
                            div = p.ele(f'css:#divIBFlightResults > div:nth-child({afindex})')
                        if level == '4':
                            div.ele('css:.pro').click()
                            click_text = div.ele('css:.pro').text
                        else:
                            click_text = div.ele('css:.eco').text
                            div.ele('css:.eco').click()
                        if 'Sold Out' in click_text:  # 卖完
                            is_match = False
                            continue
                        break
            if is_match:
                parentdiv = p.ele('css:#ucTripSummary_divSummary')
                summary = parentdiv.ele('text:Pricing Summary')
                adt_sum = summary.next()
                p_span = adt_sum.ele("css:span:nth-child(1)")
                lab = adt_sum.ele("css:span:nth-child(1)").text
                if 'Adult' in lab:
                    price_span = adt_sum.ele("css:span:nth-child(2)")
                    em = price_span.ele('css:em').text
                    priceinfo = price_span.text
                    adt_info = priceinfo.split('x')
                    adt_num = int(adt_info[0])
                    adt_price = decimal.Decimal(adt_info[1].replace(em, '').replace(',','')) * adt_num
                if child_num > 0:
                    child_sum = summary.next(2)
                    lab = child_sum.ele("css:span:nth-child(1)").text
                    if 'Children' in lab:
                        child_info = child_sum.ele("css:span:nth-child(2)").text.split('x')
                        c_num = int(child_info[0])
                        child_price = decimal.Decimal(child_info[1].replace(em, '').replace(',','')) * c_num
                total_price = child_price + adt_price

                # 下一步
                p.ele('css:#btnContinue').click()
                p.wait.load_start()  # 等待页面进入加载状态
                print(p.url)
                if 'Passenger' not in p.url:
                    p.ele('css:#taxPopupModal > div > div > div.modal-footer > a.btn.btn-default.red').click()
                    p.wait.load_start()  # 等待页面进入加载状态
                    print(p.url)
                baseFare = p.ele('css:#ucPackageSummary_lblBaseFarePrice').text
                em = p.ele('css:#ucPackageSummary_lblBaseFarePrice > em').text
                baseFare = decimal.Decimal(baseFare.replace(em, '').replace(',', ''))
                taxes = p.ele('css:ucPackageSummary_lblTaxAmount').text
                taxes = decimal.Decimal(taxes.replace(em, '').replace(',', ''))
                adtTax = (taxes / total_price * adt_price).quantize(decimal.Decimal('1.00'), decimal.ROUND_CEILING)
                childTax = taxes - adtTax  # 小孩税
                adtPrice = (baseFare / total_price * adt_price).quantize(decimal.Decimal('1.00'), decimal.ROUND_CEILING)
                childPrice = baseFare - adtPrice
                adtSumPrice = adtTax + adtPrice
                childSumPrice = childTax + childPrice
                priceobj = {"adtSumPrice": str(adtSumPrice), "childSumPrice": str(childSumPrice), "adtTax": str(adtTax),
                            "childTax": str(childTax)}

        priceobj = {"match":is_match,"priceList":output,"detail":priceobj}
        output = json.dumps(priceobj)
        print('jsonstart', output, 'jsonend')

        # end = time.time()
        # print('Time:', end - start)

    except Exception as e:
        print('出现异常', e)
    finally:
        p.close()
# 获取飞机航班信息
def MidMatchStr(source:str):
    pattern = r"Flight:  (.*?) ,"
    result = re.match(pattern, source)
    return result.group(1)
# 等待人机验证计时器
def waitforFrame(p: ChromiumPage,timeout=20):
    start = time.time()
    while True:
        try:
            end = time.time()
            if end - start > timeout:
                print('人机处理超时')
                break
            title = p.title
            if "请稍候…"  not in title and  'Just a moment' not in title:
                break
            frame = p.get_frame(1)
            btn = frame.ele('#challenge-stage',timeout = 0.1)
            if btn is not None:
                btn.click()

        except Exception as e:
            continue

if __name__ == "__main__":
    main()


