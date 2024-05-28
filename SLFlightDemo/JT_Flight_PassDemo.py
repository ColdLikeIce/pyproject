import argparse
import decimal
import re
import time
import itertools
import json
from datetime import datetime, timedelta

from DrissionPage import ChromiumPage
from DrissionPage._configs.chromium_options import ChromiumOptions


def main():
    parser = argparse.ArgumentParser(description="Process some parameters.")
    parser.add_argument('--filter', type=str, help='A filter to greet.')
    args = parser.parse_args()
    url = 'https://www.lionair.co.id'

    filter=args.filter
    filter='Delhi|Banda Aceh|2024-05-17|2|1|1'
    co = ChromiumOptions()
    # co.no_imgs(True).mute(True)
    co.set_argument('--start-maximized')
    # co.incognito()  # 匿名模式
    p = ChromiumPage(co)
    try:
        p.get(url)
        p.wait.load_start()
        DoClick(p,filter)

    except Exception as e:
        print('出现异常', e)
    finally:
        p.close()
def DoRobot(p:ChromiumPage):
    title = p.title
    if "请稍候…" in title or 'Just a moment' in title:
        time.sleep(5)
        # 直接根据frame 获取元素
        frame = p.get_frame(1)
        btn = frame.ele('#challenge-stage')
        btn.click()

def DoClick(p:ChromiumPage,ft:str):
    origin = ft.split('|')[0]
    desc = ft.split('|')[1]
    fromtime = ft.split('|')[2]
    fromtime = datetime.strptime(fromtime, '%Y-%m-%d')
    adtSourceNum = ft.split('|')[3]
    childNum = ft.split('|')[4]

    title = p.title
    if 'Access' in title:
        raise ValueError("域名被禁止")
    p.ele('#departCity').click()

    sel = p.eles('css:#departureCityList > div.list-container > div > ul > li')
    for se in sel:
        if origin in se.text:
            se.click()
            break
    sel = p.eles('css:#arrivalCityList > div.list-container > div > ul > li')
    for se in sel:
        if desc in se.text:
            se.click()
            break
    p.ele('#date_0').click()
    hasday = False
    while hasday is False:
        date = p.ele('css:#ui-datepicker-div > div.ui-datepicker-header.ui-widget-header.ui-helper-clearfix.ui-corner-all > div').text
        date_format = "%B %Y"
        sdatetime = datetime.strptime(date, date_format)
        if sdatetime.month == fromtime.month:
            sdate = p.eles('css:.ui-state-default')
            for a in sdate:
                if int(a.text) == fromtime.day:
                    a.click()
                    hasday = True
                    break
        else:
            p.ele('css:#ui-datepicker-div > div.ui-datepicker-header.ui-widget-header.ui-helper-clearfix.ui-corner-all > a.ui-datepicker-next.ui-corner-all').click()
    p.ele('css:#passengersCounter').click()
    p.ele(f'css:#persons_0 > option[value="{adtSourceNum}"]').click()
    if int(childNum) > 0 :
        p.ele('css:#persons_1').click()
        chsel = p.ele(f'css:#persons_1 > option[value="{childNum}"]')
        chsel.click()
    p.ele('css:#trip-kind > div:nth-child(1) > label').click()
    p.ele('#btnSubmit').click()
    DoRobot(p)
    p.wait.eles_loaded('#ctl00_mainContent_lbContinue')
    builddata(p,ft)
    # 处理数据

def builddata(p:ChromiumPage,ft:str):
    p.ele('css:#selCountry  > option[value="en-US"]').click()
    cabinClass = ft.split('|')[5]
    table = p.eles('css:#ctl00_mainContent_tblOutFlightBlocks > tbody > tr')
    markId = ''
    index = 0
    origin = ft.split('|')[0]
    desc = ft.split('|')[1]
    fromtime = ft.split('|')[2]
    priceList = []
    for tr in table:
        tdid = tr.attr('id')
        if tdid is None:
            continue
        if markId not in tdid:
            s=2
        if tdid != ""  and '_1' in tdid:
            index=index+1
            isCheap = True
            sale = tr.ele('css:td:nth-child(2)')
            lotoIndex = 0
            if  '售完' in sale.text or 'Sold Out' in sale.text or 'N/A' in sale.text:
                isCheap = False
                lotoIndex = 1
                sale = tr.ele('css:td:nth-child(3)')
            if cabinClass == 4:  # 超级经济舱
                lotoIndex = 0
                sale = tr.ele('css:td:nth-child(2)')
            if cabinClass == 1:  # 经济舱
                lotoIndex = 1
                sale = tr.ele('css:td:nth-child(3)')
            if cabinClass == 2:  # 商务舱
                lotoIndex = 2
                sale = tr.ele('css:td:nth-child(4)')
            if '售完' in sale.text or 'Sold Out' in sale.text or 'N/A' in sale.text:
                continue
            else:
                p.ele(f'css:#ctl00_mainContent_fs_FR00_C{index - 1}_SLOT{lotoIndex} > label > span').click()
                p.wait.ele_displayed('#ctl00_mainContent_ucSidebar1_divSidebarDepartureContent')
                markId = tdid.replace('_1', '')
                model = SearchAirticket_PriceDetail()
                model.Currency = p.ele('css:#ctl00_mainContent_ucSidebar1_divSidebarTotalPrice > span.total-currency').text
                adtNum = int(p.ele('#adultGuest').text)  # 成人数量
                adtPrice = decimal.Decimal(p.ele('#adultGuestFare').text.replace(',','')) * adtNum # 成人价格
                childNum = int(p.ele('#childGuest').text)  # 儿童数量
                childPrice = 0 if childNum == '' else decimal.Decimal(p.ele('#childGuestFare').text.replace(',','')) * childNum # 儿童价格
                baseFare = decimal.Decimal(p.ele('#baseFare').text.replace(',',''))  # 发布价格
                taxes = decimal.Decimal(p.ele('#taxesAndFees').text.replace(',',''))  # 总税
                adtTax = (taxes * (adtPrice / baseFare)).quantize(decimal.Decimal('1.00'), decimal.ROUND_CEILING)  # 成人税
                childTax = taxes - adtTax  # 小孩税
                adtSumPrice = adtTax + adtPrice
                childSumPrice = childTax + childPrice
                model.AdultPrice = adtSumPrice
                model.AdultTax = adtTax
                model.ChildPrice = childSumPrice
                model.ChildTax = childTax
                model.NationalityType = 0
                model.TicketInvoiceType = 0  # 没有默认0
                model.SuitAge = "0~99"
                model.MinFittableNum = 1
                model.MaxFittableNum = 7
                model.DeliveryPolicy = "SpecialOffer" if isCheap  else "Standardproduct"

                startDate = p.ele('css:#departure-flight-details > div.flight-time-details').text
                startDate = startDate.split(',')[-1]
                summary = p.ele('css:#ctl00_mainContent_ucSidebar1_divSidebarDepartureFlightSummary')
                flight = summary.eles('css:div.flight-summary-details')
                portInfo = summary.eles('css:div.port-summary')
                timeInfo = summary.eles('css:div.time-summary')
                rateCode = f"JT_{origin}_{desc}_{fromtime}_{cabinClass}"
                ticketAirline = ''  # 出票航司等于第一个
                segmentsList = []
                for i in range(len(flight)):
                    f = flight[i]
                    flyInfo = MidMatchStr(f.text,'Flight:',end=',').strip()
                    # 正则表达式模式
                    pattern = r'\d+'
                    # 提取所有数字作为航班号
                    flyNo = re.search(pattern, f.text)
                    flyNo = flyNo.group()
                    arrInfo = flyInfo.replace(flyNo,'')
                    if i==0:
                        ticketAirline = arrInfo
                    flyNo = flyNo.strip('0')  # 去除0
                    startTime = timeInfo[i].ele('css:div.dep-time').text
                    eTime = timeInfo[i].ele('css:div.arr-time').text
                    sTime = startDate + ' ' + startTime
                    eTime = startDate + ' ' + eTime
                    sTime = datetime.strptime(sTime, "%d %B %Y %H:%M")
                    eTime = datetime.strptime(eTime, "%d %B %Y %H:%M")
                    depPort = portInfo[i].ele('css:div.dep-port').text
                    arrPort = portInfo[i].ele('css:div.arr-port').text
                    if sTime > eTime:
                        eTime = eTime + + timedelta(days=1)
                    rateCode += f'_{flyInfo}_{sTime.strftime("%Y%m%d%H%M")}'
                    seg = SearchAirticket_Segment()
                    seg.Carrier = arrInfo
                    seg.CabinClass = ''
                    seg.FlightNumber = flyNo
                    seg.DepAirport = depPort
                    seg.ArrAirport = arrPort
                    seg.DepDate = sTime.strftime('%Y-%m-%d %H:%M')
                    seg.ArrDate = eTime.strftime('%Y-%m-%d %H:%M')
                    seg.StopCities = arrPort,
                    seg.CodeShare = True if arrInfo == 'JT' else False
                    if seg.CodeShare == True:
                        seg.ShareCarrier = arrInfo
                        seg.ShareFlightNumber = flyNo
                    segmentsList.append(seg)
                model.FlightSegments = segmentsList
                model.TicketAirline= ticketAirline
                priceList.append(model)
    return priceList

def MidMatchStr(source:str,start:str,end:str):
    pattern = f'\\[{start}\\](.*?)\\[{end}\\]'
    matches = re.findall(pattern, source)
    if matches:
        for i, match in enumerate(matches):
            return match
    else:
        return ''

class SearchAirticket_PriceDetail:
    def __init__(self):
        self.RateCode = None
        self.Currency = None
        self.AdultPrice = None
        self.AdultTax = None
        self.ChildPrice = None
        self.ChildTax = None
        self.NationalityType = None
        self.Nationality = None
        self.SuitAge = None
        self.MinFittableNum = None
        self.MaxFittableNum = None
        self.DeliveryPolicy = None
        self.TicketInvoiceType = None
        self.TicketAirline = None
        self.Rule = None
        self.FromSegments = None
class SearchAirticket_Segment:
    def __init__(self):
        self.Carrier = None
        self.Cabin = None
        self.CabinClass = None
        self.FlightNumber = None
        self.DepAirport = None
        self.ArrAirport = None
        self.StopCities = None
        self.CodeShare = None
        self.ShareCarrier = None
        self.ShareFlightNumber = None
        self.AircraftCode = None
        self.Group = None
        self.FareBasis = None
        self.DepDate = None
        self.ArrDate = None
        self.GdsType = None
        self.PosArea = None
        self.BaggageRule = None
if __name__ == "__main__":
    main()


