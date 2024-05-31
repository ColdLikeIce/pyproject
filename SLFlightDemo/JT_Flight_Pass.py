import argparse
import copy
import decimal
import re
import time
import itertools
import json
from asyncio import exceptions
import datetime

from DrissionPage import ChromiumPage
from DrissionPage._configs.chromium_options import ChromiumOptions


def main():

    start_time = time.time()
    parser = argparse.ArgumentParser(description="Process some parameters.")
    parser.add_argument('--filter', type=str, help='A filter to greet.')
    args = parser.parse_args()
    url = 'https://secure2.lionair.co.id/LionAirIBE2/OnlineBooking.aspx'


    filter=args.filter
    # filter = 'PER|PNK|20240617-20240618|1|0|1'
    # filter = 'PER|PNK|20240617|1|0|1'
    co = ChromiumOptions().auto_port()
    # co.no_imgs(True).mute(True)
    # co.set_argument("--headless")
    co.set_argument('--start-maximized')
    # co.incognito()  # 匿名模式
    p = ChromiumPage(co)
    try:
        p.get(url)
        title = p.title
        if "请稍候…" in title or 'Just a moment' in title:
            #直接根据frame 获取元素
            waitforFrame(p)
            p.wait.ele_displayed('css:#ctl00_mainContent_UcFlightSelection_lbSearch',timeout=10)

        s = DoClick(p,filter)
        s = str(s).replace('None','null').replace('\'','"').replace('False','false').replace('True','true')
        print('jsonstart',s,'jsonend')
    except Exception as e:
        print('出现异常', e)
    finally:
        p.close()
    end_time = time.time()
    print("耗时: {:.2f}秒".format(end_time - start_time))

# 等待人机验证计时器
def waitforFrame(p: ChromiumPage,timeout=10):
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

# 点击按钮输入框
def DoClick(p:ChromiumPage,ft:str):
    origin = ft.split('|')[0]
    desc = ft.split('|')[1]
    duringtime = ft.split('|')[2].split('-')
    fromtime = datetime.datetime.strptime(duringtime[0], '%Y%m%d')
    hasreturn = False
    if len(duringtime)>1:
        hasreturn = True
        totime = datetime.datetime.strptime(duringtime[-1], '%Y%m%d')
    adtSourceNum = ft.split('|')[3]
    childNum = ft.split('|')[4]

    title = p.title
    if 'Access' in title:
        raise ValueError("域名被禁止")
    orgin_div = p.ele('#ctl00_mainContent_UcFlightSelection_ddlOri-selectized')
    orgin_div.click()
    orgin_div = orgin_div.parent().next()
    orgin_div = orgin_div.ele(f'@data-value={origin}')
    if orgin_div is not None:
        orgin_div.click()
    else:
        raise ValueError("起始地参数错误")

    desc_div = p.ele('#ctl00_mainContent_UcFlightSelection_ddlDes-selectized')
    desc_div.click()
    desc_div = desc_div.parent().next()
    desc_div = desc_div.ele(f'@data-value={desc}')
    if desc_div is not None:
        desc_div.click()
    else:
        raise ValueError("目的地参数错误")
    #  起始日期点击
    p.ele('#departureDateField').click()
    hasday = False
    while hasday is False:
        date = p.ele('css:#ui-datepicker-div > div.ui-datepicker-group.ui-datepicker-group-first > div > div').text
        date_format = "%B %Y"
        sdatetime = datetime.datetime.strptime(date, date_format)
        if sdatetime.month == fromtime.month:
            sdate = p.eles('css:#ui-datepicker-div > div.ui-datepicker-group.ui-datepicker-group-first > table > tbody > tr > td > a')
            for a in sdate:
                if int(a.text) == fromtime.day:
                    a.click()
                    hasday = True
                    break
        else:
            p.ele('css:#ui-datepicker-div > div.ui-datepicker-group.ui-datepicker-group-last > div > a > span').click()
    p.ele('#returnDateField').click()
    if hasreturn:
        hasday = False
        while hasday is False:
            date = p.ele('css:#ui-datepicker-div > div.ui-datepicker-group.ui-datepicker-group-first > div > div').text
            date_format = "%B %Y"
            sdatetime = datetime.datetime.strptime(date, date_format)
            if sdatetime.month == totime.month:
                sdate = p.eles('css:#ui-datepicker-div > div.ui-datepicker-group.ui-datepicker-group-first > table > tbody > tr > td > a')
                for a in sdate:
                    if int(a.text) == totime.day:
                        a.click()
                        hasday = True
                        break
            else:
                p.ele('css:#ui-datepicker-div > div.ui-datepicker-group.ui-datepicker-group-last > div > a > span').click()

    # 人数点击
    css_selector = f'css:#ctl00_mainContent_UcFlightSelection_ddlADTCount > option[value="{adtSourceNum}"]'
    adtsel = p.ele(css_selector)
    adtsel.click()
    if int(childNum) > 0 :
        p.ele('css:ctl00_mainContent_UcFlightSelection_ddlCNNCount').click()
        chsel = p.ele(f'css:#ctl00_mainContent_UcFlightSelection_ddlCNNCount > option[value="{childNum}"]')
        chsel.click()
    p.ele('css:#selCountry > option[value="en-US"]').click()
    # 是否单程
    if hasreturn != True:
        p.ele('css:#main-content > div.form-horizontal.step1-search > div.row > div.col-sm-6.step1TripType > label:nth-child(2)').click()
    p.ele('#ctl00_mainContent_UcFlightSelection_lbSearch').click()
    p.wait.eles_loaded('#ctl00_mainContent_lbContinue')
    # 处理数据
    return builddata(p,ft)

def builddata(p:ChromiumPage,ft:str):
    adtSourceNum = ft.split('|')[3]
    childNum = ft.split('|')[4]
    p.ele('css:#selCountry  > option[value="en-US"]').click()
    priceList = buildtable(p,ft)
    return priceList
def buildtable_old(p:ChromiumPage,ft:str,isreturn:bool):
    cabinClass = ft.split('|')[5]
    index = 0
    priceList = []
    tableid = 'ctl00_mainContent_tblOutFlightBlocks'
    trid = 'ctl00_mainContent_fs_FR00_C'
    if isreturn:
        tableid = 'ctl00_mainContent_tblInFlightBlocks'
        trid = 'ctl00_mainContent_fs_FR01_C'
    table = p.eles(f'css:#{tableid} > tbody > tr')
    for tr in table:
        tdid = tr.attr('id')
        if tdid is None:
            continue
        if tdid != "" and '_1' in tdid:
            index = index + 1
            isCheap = True
            sale = tr.ele('css:td:nth-child(2)')
            lotoIndex = 0
            if '售完' in sale.text or 'Sold Out' in sale.text or 'N/A' in sale.text:
                isCheap = False
                lotoIndex = 1
                sale = tr.ele('css:td:nth-child(3)')
            if cabinClass == '4':  # 超级经济舱
                lotoIndex = 0
                sale = tr.ele('css:td:nth-child(2)')
                isCheap = True
            if cabinClass == '2':  # 商务舱
                lotoIndex = 2
                sale = tr.ele('css:td:nth-child(4)')
                isCheap = False
            if '售完' in sale.text or 'Sold Out' in sale.text or 'N/A' in sale.text:
                continue
            else:
                p.ele(f'css:#{trid}{index - 1}_SLOT{lotoIndex} > label > span').click()
                if isreturn:
                    p.wait.eles_loaded('#ctl00_mainContent_ucSidebar1_divSidebarReturnContent')
                else:
                    p.wait.eles_loaded('#ctl00_mainContent_ucSidebar1_divSidebarDepartureContent')

                # p.wait.ele_displayed('#ctl00_mainContent_ucSidebar1_divSidebarDepartureContent')
                model = SearchAirticket_PriceDetail()
                model.Currency = p.ele('css:#ctl00_mainContent_ucSidebar1_divSidebarTotalPrice > span.total-currency').text
                adtNum = int(p.ele('#adultGuest').text)  # 成人数量
                adtPrice = decimal.Decimal(p.ele('#adultGuestFare').text.replace(',', '')) * adtNum  # 成人价格
                childNum = int(p.ele('#childGuest').text)  # 儿童数量
                childPrice = 0 if childNum == '' else decimal.Decimal(
                    p.ele('#childGuestFare').text.replace(',', '')) * childNum  # 儿童价格
                baseFare = decimal.Decimal(p.ele('#baseFare').text.replace(',', ''))  # 发布价格
                taxes = decimal.Decimal(p.ele('#taxesAndFees').text.replace(',', ''))  # 总税
                adtTax = (taxes * (adtPrice / baseFare)).quantize(decimal.Decimal('1.00'),
                                                                  decimal.ROUND_CEILING)  # 成人税
                childTax = taxes - adtTax  # 小孩税
                adtSumPrice = adtTax + adtPrice
                childSumPrice = childTax + childPrice
                model.AdultPrice = str(adtSumPrice)
                model.AdultTax = str(adtTax)
                model.ChildPrice = str(childSumPrice)
                model.ChildTax = str(childTax)
                model.NationalityType = 0
                model.TicketInvoiceType = 0  # 没有默认0
                model.SuitAge = "0~99"
                model.MinFittableNum = 1
                model.MaxFittableNum = 7
                model.DeliveryPolicy = "SpecialOffer" if isCheap else "Standardproduct"
                ticketAirline = ''  # 出票航司等于第一个
                if isreturn:
                    desc_seglist = buildSegList(p, True,ft)
                    model.RetSegments = desc_seglist['segmentsList']
                    rateCode = f'{desc_seglist["rateCode"]}'
                else:
                    from_seglist = buildSegList(p, False,ft)
                    model.FromSegments = from_seglist['segmentsList']
                    rateCode = f'{from_seglist["rateCode"]}'

                model.RateCode = f"{rateCode}"
                model.TicketAirline = ticketAirline
                print(model.RateCode)
                priceList.append(model)
    return  priceList
def buildtable(p:ChromiumPage,ft:str):
    cabinClass = ft.split('|')[5]
    markId = ''
    index = 0
    fromtime = ft.split('|')[2]
    hasreturn = True if '-' in fromtime else False
    priceList = []
    table = p.eles(f'css:#ctl00_mainContent_tblOutFlightBlocks > tbody > tr')
    if hasreturn:
       desc_table = p.eles(f'css:#ctl00_mainContent_tblInFlightBlocks > tbody > tr')
    for tr in table:
        tdid = tr.attr('id')
        if tdid is None:
            continue
        if tdid != "" and '_1' in tdid:
            index = index + 1
            isCheap = True
            sale = tr.ele('css:td:nth-child(2)')
            lotoIndex = 0
            if '售完' in sale.text or 'Sold Out' in sale.text or 'N/A' in sale.text:
                isCheap = False
                lotoIndex = 1
                sale = tr.ele('css:td:nth-child(3)')
            if cabinClass == '4':  # 超级经济舱
                lotoIndex = 0
                sale = tr.ele('css:td:nth-child(2)')
                isCheap = True
            if cabinClass == '2':  # 商务舱
                lotoIndex = 2
                sale = tr.ele('css:td:nth-child(4)')
                isCheap = False
            if '售完' in sale.text or 'Sold Out' in sale.text or 'N/A' in sale.text:
                continue
            else:
                p.ele(f'css:#ctl00_mainContent_fs_FR00_C{index - 1}_SLOT{lotoIndex} > label > span').click()
                p.wait.eles_loaded('#ctl00_mainContent_ucSidebar1_divSidebarDepartureContent')
                markId = tdid.replace('_1', '')
                if hasreturn:
                    desc_index = 0
                    for desc_tr in desc_table:
                        desc_tdid = desc_tr.attr('id')
                        if desc_tdid is None:
                            continue
                        if desc_tdid != "" and '_1' in desc_tdid:
                            desc_index = desc_index + 1
                            isCheap = True
                            sale = desc_tr.ele('css:td:nth-child(2)')
                            lotoIndex = 0
                            if '售完' in sale.text or 'Sold Out' in sale.text or 'N/A' in sale.text:
                                isCheap = False
                                lotoIndex = 1
                                sale = desc_tr.ele('css:td:nth-child(3)')
                            if cabinClass == '4':  # 超级经济舱
                                lotoIndex = 0
                                sale = desc_tr.ele('css:td:nth-child(2)')
                                isCheap = True
                            if cabinClass == '2':  # 商务舱
                                lotoIndex = 2
                                sale = desc_tr.ele('css:td:nth-child(4)')
                                isCheap = False
                            if '售完' in sale.text or 'Sold Out' in sale.text or 'N/A' in sale.text:
                                continue
                            else:
                                p.ele(f'css:#ctl00_mainContent_fs_FR01_C{desc_index - 1}_SLOT{lotoIndex} > label > span').click()
                                p.wait.eles_loaded('#ctl00_mainContent_ucSidebar1_divSidebarReturnContent')
                                model = createpricedetail(p,ft,True)
                                print(model.RateCode)
                                priceList.append(model.__dict__)
                else:
                    model = createpricedetail(p,ft,False)
                    print(model.RateCode)
                    priceList.append(model.__dict__)

    return  priceList

def createpricedetail(p:ChromiumPage,ft:str,hasreturn:bool):
    model = SearchAirticket_PriceDetail()
    model.Currency = p.ele('css:#ctl00_mainContent_ucSidebar1_divSidebarTotalPrice > span.total-currency').text
    adtNum = int(p.ele('#adultGuest').text)  # 成人数量
    adtPrice = decimal.Decimal(p.ele('#adultGuestFare').text.replace(',', '')) * adtNum  # 成人价格
    childNum = int(p.ele('#childGuest').text)  # 儿童数量
    childPrice = 0 if childNum == '' else decimal.Decimal(
        p.ele('#childGuestFare').text.replace(',', '')) * childNum  # 儿童价格
    baseFare = decimal.Decimal(p.ele('#baseFare').text.replace(',', ''))  # 发布价格
    taxes = decimal.Decimal(p.ele('#taxesAndFees').text.replace(',', ''))  # 总税
    adtTax = (taxes * (adtPrice / baseFare)).quantize(decimal.Decimal('1.00'), decimal.ROUND_CEILING)  # 成人税
    childTax = taxes - adtTax  # 小孩税
    adtSumPrice = adtTax + adtPrice
    childSumPrice = childTax + childPrice
    model.AdultPrice = str(adtSumPrice)
    model.AdultTax = str(adtTax)
    model.ChildPrice = str(childSumPrice)
    model.ChildTax = str(childTax)
    model.NationalityType = 0
    model.TicketInvoiceType = 0  # 没有默认0
    model.SuitAge = "0~99"
    model.MinFittableNum = 1
    model.MaxFittableNum = 7
    # model.DeliveryPolicy = "SpecialOffer" if isCheap else "Standardproduct"  todo

    ticketAirline = ''  # 出票航司等于第一个

    from_seglist = buildSegList(p, False, ft)
    if hasreturn:
        desc_seglist = buildSegList(p, True, ft)
        rateCode = f'JT_{from_seglist["rateCode"]}|{desc_seglist["rateCode"]}'
        model.RetSegments = desc_seglist['segmentsList']
    else:
        rateCode = f'JT_{from_seglist["rateCode"]}'
    model.FromSegments = from_seglist['segmentsList']

    model.RateCode = f"{rateCode}_{adtNum}_{childNum}"
    model.TicketAirline = ticketAirline
    return model
def buildSegList(p:ChromiumPage,isreturn:bool,ft:str):
    origin = ft.split('|')[0]
    desc = ft.split('|')[1]
    segmentsList = []
    startDate = p.ele('css:#departure-flight-details > div.flight-time-details').text

    summary = p.ele('css:#ctl00_mainContent_ucSidebar1_divSidebarDepartureFlightSummary')
    if isreturn:
        startDate = p.ele('css:#returning-flight-details > div.flight-time-details').text
        summary = p.ele('css:#ctl00_mainContent_ucSidebar1_divSidebarReturnFlightSummary')
    startDate = startDate.split(',')[-1]

    flight = summary.eles('css:div.flight-summary-details')
    portInfo = summary.eles('css:div.port-summary')
    timeInfo = summary.eles('css:div.time-summary')
    rateCode = ''
    for i in range(len(flight)):
        f = flight[i]
        flyInfo = MidMatchStr(f.text).strip()
        # 正则表达式模式
        pattern = r'\d+'
        # 提取所有数字作为航班号
        flyNo = re.search(pattern, f.text)
        flyNo = flyNo.group()
        arrInfo = flyInfo.replace(flyNo, '')
        if i == 0:
            ticketAirline = arrInfo
        flyNo = flyNo.lstrip('0')  # 去除0
        startTime = timeInfo[i].ele('css:div.dep-time').text
        eTime = timeInfo[i].ele('css:div.arr-time').text
        sTime = startDate.strip(' ') + ' ' + startTime
        eTime = startDate.strip(' ') + ' ' + eTime
        sTime = datetime.datetime.strptime(sTime, "%d %b %Y %H:%M")
        eTime = datetime.datetime.strptime(eTime, "%d %b %Y %H:%M")
        depPort = portInfo[i].ele('css:div.dep-port').text
        arrPort = portInfo[i].ele('css:div.arr-port').text
        if sTime > eTime:
            eTime = eTime + datetime.timedelta(days=1)
        s_deptdate = sTime.strftime('%Y-%m-%d')
        seg = SearchAirticket_Segment()
        seg.Carrier = arrInfo
        seg.CabinClass = 4 if 'Promo' in f.text  else 1 if 'Economy' in f.text  else 2
        seg.FlightNumber = flyNo
        seg.DepAirport = depPort
        seg.ArrAirport = arrPort
        seg.DepDate = sTime.strftime('%Y-%m-%d %H:%M')
        seg.ArrDate = eTime.strftime('%Y-%m-%d %H:%M')
        seg.StopCities = arrPort
        seg.CodeShare = True if arrInfo != 'JT' else False
        if seg.CodeShare == True:
            seg.ShareCarrier = arrInfo
            seg.ShareFlightNumber = flyNo
        if i == 0:
            if isreturn:
                rateCode = f'{desc}_{origin}_{s_deptdate}'
            else:
                rateCode = f'{origin}_{desc}_{s_deptdate}'
        start_time = sTime.strftime('%H%M')
        end_time = eTime.strftime('%H%M')
        rateCode += f'_{arrInfo}{flyNo}_{start_time}-{end_time}_{seg.CabinClass}'
        segmentsList.append(seg.__dict__)
    return {'rateCode':rateCode,'segmentsList':segmentsList}
def MidMatchStr(source:str):
    pattern = r"Flight: (.*?) ,"
    result = re.match(pattern, source)
    return result.group(1)


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
        self.RetSegments = None
    def toJSON(self):
        return json.dumps(
            self,
            default=lambda o: o.__dict__,
            sort_keys=True,
            indent=4)
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


