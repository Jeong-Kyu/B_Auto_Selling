import os
import sys
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
from config.kiwoomType import *
import logging

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()

        print('kiwoom 클래스 입니다.')
        self.logging = logging
        self.realType = RealType()
        ### Event Loop 모듈 ###
        self.login_event_loop = None
        self.detail_account_info_event_loop = QEventLoop()
        ### 스크린번호 모음 ###
        self.screen_my_info = '2000'
        self.screen_real_stock = '5000' # 종목별 할당 스크린
        self.screen_meme_stock = '6000' # 종목별 주문용 스크린
        self.screen_start_stop_real = '1000'
        ### 변수 모음 ###
        self.account_num = None
        
        self.use_money = 0
        self.use_money_percent = 0.5

        self.account_stock_dict = {}
        self.not_account_stock_dict = {}
        self.portfolio_stock_dict = {}
        self.jango_dict = {}

        self.get_ocx_instance()
        self.event_slots()
        self.real_event_slots()

        self.signal_login_commConnect()
        self.get_account_info()
        self.detail_account_info() # 예수금
        self.detail_account_mystock() # 계좌평가 잔고 내역
        self.not_concluded_account() # 미체결 요청
        self.read_code() # 저장파일 불러오기
        self.screen_number_setting() # 스크린번호 할당
        self.dynamicCall('SetRealReg(QString, QString, QString, QString)', self.screen_start_stop_real, '', self.realType.REALTYPE['장시작시간']['장운영구분'], '0')
        
        for code in self.portfolio_stock_dict.keys():
            screen_num = self.portfolio_stock_dict[code]['스크린번호']
            fids = self.realType.REALTYPE['주식체결']['체결시간']
            self.dynamicCall('SetRealReg(QString, QString, QString, QString)', screen_num, code, fids, '1')
            print('실시간 등록 코드: %s, 스크린번호: %s, fid번호: %s' % (code,screen_num,fids))
    def get_ocx_instance(self):
        self.setControl('KHOPENAPI.KHOpenAPICtrl.1')

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def real_event_slots(self):
        self.OnReceiveRealData.connect(self.realdata_slot)
        self.OnReceiveChejanData.connect(self.chejan_slot)

    def signal_login_commConnect(self):
        self.dynamicCall('CommConnect()')
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def login_slot(self, errCode):
        print(errors(errCode))
        self.login_event_loop.exit()

    def get_account_info(self):
        account_list = self.dynamicCall('GetLogininfo(String)','ACCNO')
        self.account_num = account_list.split(';')[1]
        print('나의 보유 계좌번호 %s' %self.account_num)

    def detail_account_info(self):
        print('예수금 요청')
        self.dynamicCall('SetInputValue(String, String)','계좌번호', self.account_num)
        self.dynamicCall('SetInputValue(String, String)','비밀번호', '0000')
        self.dynamicCall('SetInputValue(String, String)','비밀번호입력매체구분', '00')
        self.dynamicCall('SetInputValue(String, String)','조회구분', '2')    
        self.dynamicCall('CommRqData(String, String, int, String)', '예수금상세현황요청', 'opw00001', '0', self.screen_my_info)

        self.detail_account_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop.exec_()

    def detail_account_mystock(self, sPrevNext='0'):
        print('계좌평가잔고내역 요청')
        self.dynamicCall('SetInputValue(String, String)','계좌번호', self.account_num)
        self.dynamicCall('SetInputValue(String, String)','비밀번호', '0000')
        self.dynamicCall('SetInputValue(String, String)','비밀번호입력매체구분', '00')
        self.dynamicCall('SetInputValue(String, String)','조회구분', '2')    
        self.dynamicCall('CommRqData(String, String, int, String)', '계좌평가잔고내역요청', 'opw00018', sPrevNext, self.screen_my_info)
        self.detail_account_info_event_loop.exec_()

    def not_concluded_account(self, sPrevNext='0'):
        print('미체결 요청')
        self.dynamicCall('SetInputValue(String, String)','계좌번호', self.account_num)
        self.dynamicCall('SetInputValue(String, String)','체결구분', '1')
        self.dynamicCall('SetInputValue(String, String)','매매구분', '0') 
        self.dynamicCall('CommRqData(String, String, int, String)', '실시간미체결요청', 'opw10075', sPrevNext, self.screen_my_info)
        # self.detail_account_info_event_loop.exec_()

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        # 스크린번호, 설정이름, 요청id, 사용안함, 다음페이지
        if sRQName == '예수금상세현황요청':
            deposit = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0, '예수금')
            print('예수금 : %s' % int(deposit))

            self.use_money = int(deposit) * self.use_money_percent
            self.use_money = self.use_money / 4

            ok_deposit = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0, '출금가능금액')
            # print('출금가능금액 %s' % ok_deposit)
            print('출금가능금액 : %s' % int(ok_deposit))

            self.detail_account_info_event_loop.exit()

        if sRQName == '계좌평가잔고내역요청':
            total_buy_money = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0, '총매입금액')
            total_buy_money_result = int(total_buy_money)
            print('총매입금액 : %s' % total_buy_money_result)
            total_loss_rate = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0, '총수익률(%)')
            total_loss_rate_result = float(total_loss_rate)
            print('총수익률(%%) : %s' % total_loss_rate_result)

            rows = self.dynamicCall('GetRepeatCnt(QString, QString)', sTrCode, sRQName)
            cnt = 0
            for i in range(rows):
                code = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '종목번호')
                code = code.strip()[1:]

                code_nm = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '종목명')
                stock_quantity = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '보유수량')
                buy_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '매입가')
                learn_rate = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '수익률(%)')
                current_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '현재가')
                total_chegual_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '매입금액')
                possible_quantity = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '매매가능수량')

                if code in self.account_stock_dict:
                    pass
                else:
                    self.account_stock_dict.update({code:{}})
                code_nm = code_nm.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())
                current_price = int(current_price.strip())
                total_chegual_price = int(total_chegual_price.strip())
                possible_quantity = int(possible_quantity.strip())


                self.account_stock_dict[code].update({'종목명':code_nm})
                self.account_stock_dict[code].update({'보유수량':stock_quantity})
                self.account_stock_dict[code].update({'매입가':buy_price})
                self.account_stock_dict[code].update({'수익률(%)':learn_rate})
                self.account_stock_dict[code].update({'현재가':current_price})
                self.account_stock_dict[code].update({'매입금액':total_chegual_price})
                self.account_stock_dict[code].update({'매매가능수량':possible_quantity})

                cnt += 1
            print('보유종목 %s' % self.account_stock_dict)

            if sPrevNext == '2':
                self.detail_account_mystock(sPrevNext='2')
            else:
                self.detail_account_info_event_loop.exit()

        if sRQName == '실시간미체결요청':
            rows = self.dynamicCall('GetRepeatCnt(QString, QString)', sTrCode, sRQName)
            for i in range(rows):
                code = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '종목코드')
                code_nm = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '종목명')
                order_no = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '주문번호')
                order_status = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '주문상태') # 접수,확인,체결
                order_quantity = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '주문수량')
                order_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '주문가격')
                order_gubun = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '주문구분') # -매도,+매수
                not_quantity = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '미체결수량')
                ok_quantity = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '체결량')

                code = code.strip()
                code_nm = code_nm.strip()
                order_no = int(order_no.strip())
                order_status = int(order_status.strip())
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                order_gubun = order_gubun.strip().lstrip('+').lstrip('-')
                not_quantity = int(not_quantity.strip())
                ok_quantity = int(ok_quantity.strip())

                if order_no in self.not_account_stock_dict:
                    pass
                else:
                    self.not_account_stock_dict[order_no] = {}
                nasd = self.not_account_stock_dict[order_no]
                nasd.update({'종목번호':code})
                nasd.update({'종목명':code_nm})
                nasd.update({'주문번호':order_no})
                nasd.update({'주문상태':order_status}) # 접수,확인,체결
                nasd.update({'주문수량':order_quantity})
                nasd.update({'주문가격':order_price})
                nasd.update({'주문구분':order_gubun}) # -매도,+매수
                nasd.update({'미체결수량':not_quantity})
                nasd.update({'체결량':ok_quantity})
                print('미체결 종목 : %s' % nasd)

            self.detail_account_info_event_loop.exit()

    def read_code(self):
        # kiwoom = Kiwoom()
        # self.dynamicCall('GetConditionLoad()')
        # # kiwoom.GetConditionLoad()
        # # 전체 조건식 리스트 얻기
        # # conditions = kiwoom.GetConditionNameList()
        # conditions = self.dynamicCall('GetConditionNameList()')

        # print('hhh',conditions)
        # # 0번 조건식에 해당하는 종목 리스트 출력
        # condition_index = conditions[0][0]
        # condition_name = conditions[0][1]
        # codes = self.dynamicCall('SendCondition(QString, QString, QString, int)', "0101", condition_name, condition_index, 0)
        # # codes = kiwoom.SendCondition("0101", condition_name, condition_index, 0)
        # self.portfolio_stock_dict.update({codes})
        # print(self.portfolio_stock_dict)
        if os.path.exists('condition_stock.txt'):
            f = open('condition_stock.txt','r',encoding='utf8')
            lines = f.readlines()
            for line in lines:
                if line != '':
                    ls = line.split('\t')
                    stock_code = ls[0]
                    # stock_name = ls[1]
                    # stock_price = int(ls[2].split('\n')[0])
                    # stock_price = abs(stock_price)
                    # print(stock_code)
                    # self.portfolio_stock_dict.update({stock_code})#:{'종목명':stock_name}})#, '현재가':stock_price}})
                    # print(stock_code)
            f.close()
        else:
            print(self.portfolio_stock_dict)

    def screen_number_setting(self):
        screen_overwrite = []
        # 계좌평가잔고내역 종목
        for code in self.account_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)
        # 미체결 종목
        for order_number in self.not_account_stock_dict.keys():
            code = self.not_account_stock_dict[order_number]['종목코드']
            if code not in screen_overwrite:
                screen_overwrite.append(code)
        # 포트폴리오 종목
        for code in self.portfolio_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        # 스크린 번호 할당
        cnt = 0
        for code in screen_overwrite:
            temp_screen = int(self.screen_real_stock)
            meme_screen = int(self.screen_meme_stock)

            if (cnt % 50) == 0:
                temp_screen += 1
                self.screen_real_stock = str(temp_screen)
            if (cnt % 50) == 0:
                meme_screen += 1
                self.screen_meme_stock = str(meme_screen)
            
            if code in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict[code].update({'스크린번호':str(self.screen_real_stock)})
                self.portfolio_stock_dict[code].update({'주문용스크린번호':str(self.screen_meme_stock)})
            elif code not in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict.update({code:{'스크린번호':str(self.screen_real_stock), '주문용스크린번호':str(self.screen_meme_stock)}})
            cnt += 1
        print(self.portfolio_stock_dict)

    def namelist_slot(self):
        self.dynamicCall('GetConditionLoad()')
        conditions = self.dynamicCall('GetConditionNameList()')
        print('hhh',conditions)
        # 0번 조건식에 해당하는 종목 리스트 출력
        condition_index = conditions[0][0]
        condition_name = conditions[0][1]
        codes = self.dynamicCall('SendCondition(QString, QString, QString, int)', "0101", condition_name, condition_index, 0)
        self.portfolio_stock_dict.update({codes})
        print(self.portfolio_stock_dict)

    def realdata_slot(self, sCode, sRealType, sRealData):
        if sRealType == '장시작시간':
            fid = self.realType.REALTYPE[sRealType]['장운영구분']
            value = self.dynamicCall('GetCommRealData(QString, int)', sCode, fid)

            if value == '0':
                print('장 시작 전')
            elif value == '3':
                print('장 시작')
            elif value == '2':
                print('장 종료, 동시호가로 넘어감')
            elif value == '4':
                print('3시30분 장 종료')
                for code in self.portfolio_stock_dict.keys():
                    self.dynamicCall('SetRealRemove(QString,QString)',self.portfolio_stock_dict[code]['스크린번호'],code)
                
                self.file_delete()
                sys.exit()
        elif sRealType == '주식체결':
            a = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['체결시간'])#HHMMSS
            b = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['현재가'])#+,-
            b = abs(int(b))
            c = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['전일대비'])#+,-
            c = abs(int(c))
            d = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['등락율'])#+,-
            d = float(d)
            e = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['(최우선)매도호가'])#+,-
            e = abs(int(e))
            f = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['(최우선)매수호가'])#+,-
            f = abs(int(f))
            g = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['거래량'])#+,-
            g = abs(int(g))
            h = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['누적거래량'])#+,-
            h = abs(int(h))
            i = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['고가'])#+,-
            i = abs(int(i))
            j = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['시가'])#+,-
            j = abs(int(j))
            k = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['저가'])#+,-
            k = abs(int(k))

            if sCode not in self.portfolio_stock_dict:
                self.portfolio_stock_dict.update({sCode:{}})
            self.portfolio_stock_dict[sCode].update({"체결시간":a})
            self.portfolio_stock_dict[sCode].update({"현재가":b})
            self.portfolio_stock_dict[sCode].update({"전일대비":c})
            self.portfolio_stock_dict[sCode].update({"등락율":d})
            self.portfolio_stock_dict[sCode].update({"(최우선)매도호가":e})
            self.portfolio_stock_dict[sCode].update({"(최우선)매수호가":f})
            self.portfolio_stock_dict[sCode].update({"거래량":g})
            self.portfolio_stock_dict[sCode].update({"누적거래량":h})
            self.portfolio_stock_dict[sCode].update({"고가":i})
            self.portfolio_stock_dict[sCode].update({"시가":j})
            self.portfolio_stock_dict[sCode].update({"저가":k})

            print(self.portfolio_stock_dict[sCode])

            upper=7
            lower=-2
            # 계좌잔고평가내역에 있고 오늘 산 잔고에 없을 경우
            if sCode in self.account_stock_dict.keys() and sCode not in self.jango_dict.keys():
                asd = self.account_stock_dict[sCode]
                meme_rate = (b - asd['매입가'])/asd['매입가']*100
                if asd['매매가능수량'] > 0 and (meme_rate > upper or meme_rate < lower):
                    order_success = self.dynamicCall('SendOrder(QString, QString, QString, int, QString, int, int, QString, QString',
                ['신규매도', self.portfolio_stock_dict[sCode]['주문용스크린번호'], self.account_num, 2,
                sCode, asd['매매가능수량'], 0, self.realType.SENDTYPE['거래구분']['시장가'],''])

                    if order_success == 0:
                        print('매도주문 전달 성공')
                        del self.account_stock_dict[sCode]
                    else:
                        print('매도주문 전달 실패')


            # 오늘 산 잔고에 있을 경우
            elif sCode in self.jango_dict.keys():
                jd = self.jango_dict[sCode]
                meme_rate = (b - jd['매입단가']) / jd['매입단가'] * 100
                if jd['주문가능수량'] > 0 and (meme_rate > upper or meme_rate < lower):
                    order_success = self.dynamicCall('SendOrder(QString,QString,QString,int,QString,int,int,QString,QString)',
                    ['신규매도', self.portfolio_stock_dict[sCode]['주문용스크린번호'],self.account_num,2,sCode,jd['주문가능수량'],
                    0, self.realType.SENDTYPE['거래구분']['시장가'],''])
                    if order_success == 0:
                        self.logging.debug('매도주문 전달 성공')
                    else:
                        self.logging.debug('매도주문 전달 실패')

            # 등락율이 2% 이상이고 오늘 산 잔고에 없을 경우
            elif d > upper and sCode not in self.jango_dict:
                result = (self.use_money * 0.1) / e
                quantity = int(result)
                order_success = self.dynamicCall('SendOrder(QString,QString,QString,int,QString,int,int,QString,QString',
                ['신규매수', self.portfolio_stock_dict[sCode]['주문용스크린번호'],self.account_num,1,sCode,quantity,e,
                self.realType.SENDTYPE['거래구분']['지정가'],'']
                )
                if order_success == 0:
                    self.logging.debug('매도주문 전달 성공')
                else:
                    self.logging.debug('매도주문 전달 실패')

            not_meme_list = list(self.not_account_stock_dict)
            for order_num in not_meme_list:
                code = self.not_account_stock_dict[order_num]['종목코드']
                meme_price = self.not_account_stock_dict[order_num]['주문가격']
                not_quantity = self.not_account_stock_dict[order_num]['미체결수량']
                order_gubun = self.not_account_stock_dict[order_num]['주문구분']

                if order_gubun == '매수' and not_quantity > 0 and e > meme_price:
                    order_success = self.dynamicCall('SendOrder(QString,QString,QString,int,QString,int,int,QString,QString)',
                    ['매수취소',self.portfolio_stock_dict[sCode]['주문용스크린번호'],self.account_num,3,code,0,0,
                    self.realType.SENDTYPE['거래구분']['지정가'],order_num])
                    if order_success == 0:
                      self.logging.debug('매수취소 전달 성공')
                    else:
                      self.logging.debug('매수취소 전달 실패')
                elif not_quantity == 0:
                    del self.not_account_stock_dict[order_num]

    def chejan_slot(self,sGubun,nItemCnt,sFIdList):
        if int(sGubun) == 0:
            account_num = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['계좌번호'])
            sCode = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['종목코드'])[1:]
            stock_name = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['종목명'])
            stock_name = stock_name.strip()
            origin_order_number = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['원주문번호'])
            order_number = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문번호'])
            order_status = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문상태'])
            order_quan = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문수량'])
            order_quan = int(order_quan)
            order_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문가격'])
            order_price = int(order_price)
            not_chegual_quan = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['미체결수량'])
            not_chegual_quan = int(not_chegual_quan)
            order_gubun = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문구분'])
            order_gubun = order_gubun.strip().lstrip('+').lstrip('-') 
            chegual_time_str = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문/체결시간'])
            chegual_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['체결가'])
            if chegual_price == '':
                chegual_price = 0
            else:
                chegual_price = int(chegual_price)
            chegual_quantity = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['체결량'])
            if chegual_quantity == '':
                chegual_quantity = 0
            else:
                chegual_quantity = int(chegual_quantity)
            current_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['현재가'])
            current_price = abs(int(current_price))
            first_sell_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['(최우선)매도호가'])
            first_sell_price = abs(int(first_sell_price))
            first_buy_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['(최우선)매수호가'])
            first_buy_price = abs(int(first_buy_price))

            if order_number not in self.not_account_stock_dict.keys():
                self.not_account_stock_dict.update({order_number:{}})
            self.not_account_stock_dict[order_number].update({'종목코드':sCode})
            self.not_account_stock_dict[order_number].update({'주문번호':order_number})
            self.not_account_stock_dict[order_number].update({'종목명':stock_name})
            self.not_account_stock_dict[order_number].update({'주문상태':order_status})
            self.not_account_stock_dict[order_number].update({'주문수량':order_quan})
            self.not_account_stock_dict[order_number].update({'주문가격':order_price})
            self.not_account_stock_dict[order_number].update({'미체결수량':not_chegual_quan})
            self.not_account_stock_dict[order_number].update({'원주문번호':origin_order_number})
            self.not_account_stock_dict[order_number].update({'주문구분':order_gubun})
            self.not_account_stock_dict[order_number].update({'주문/체결시간':chegual_time_str})
            self.not_account_stock_dict[order_number].update({'체결가':chegual_price})
            self.not_account_stock_dict[order_number].update({'체결량':chegual_quantity})
            self.not_account_stock_dict[order_number].update({'현재가':current_price})
            self.not_account_stock_dict[order_number].update({'(최우선)매도호가':first_sell_price})
            self.not_account_stock_dict[order_number].update({'(최우선)매수호가':first_buy_price})

            print(self.not_account_stock_dict)

        elif int(sGubun) == 1:
            account_num = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['계좌번호'])
            sCode = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['종목코드'])[1:]
            stock_name = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['종목명'])
            stock_name = stock_name.strip()
            current_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['현재가'])
            current_price = abs(int(current_price))
            stock_quan = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['보유수량'])
            stock_quan = int(stock_quan)
            like_quan = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['주문가능수량'])
            like_quan = int(like_quan)
            buy_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['매입단가'])
            buy_price = abs(int(buy_price))
            total_buy_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['총매입가'])
            total_buy_price = abs(int(total_buy_price))
            meme_gubun = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['매도매수구분'])
            meme_gubun = self.realType.REALTYPE['매도수구분'][meme_gubun]
            first_sell_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['(최우선)매도호가'])
            first_sell_price = abs(int(first_sell_price))
            first_buy_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['(최우선)매수호가'])
            first_buy_price = abs(int(first_buy_price))

            if sCode not in self.jango_dict.keys():
                self.jango_dict.update({sCode:{}})
            self.jango_dict[sCode].update({'현재가':current_price})
            self.jango_dict[sCode].update({'종목코드':sCode})
            self.jango_dict[sCode].update({'종목명':stock_name})
            self.jango_dict[sCode].update({'보유수량':stock_quan})
            self.jango_dict[sCode].update({'주문가능수량':like_quan})
            self.jango_dict[sCode].update({'매입단가':buy_price})
            self.jango_dict[sCode].update({'총매입가':total_buy_price})
            self.jango_dict[sCode].update({'매도매수구분':meme_gubun})
            self.jango_dict[sCode].update({'(최우선)매도호가':first_sell_price})
            self.jango_dict[sCode].update({'(최우선)매수호가':first_buy_price})
            
            if stock_quan == 0:
                del self.jango_dict[sCode]
                self.dynamicCall('SetRealRemove(QString, QString)', self.portfolio_stock_dict[sCode]['스크린번호'],sCode)
    
    # 송수신 메세지 get
    def msg_slot(self, sScrNo, sRQName, sTrCode, msg):
        print('스크린: %s, 요청이름: %s, tr코드: %s --- %s' %(sScrNo, sRQName, sTrCode, msg))

    # 파일 삭제
    def file_delete(self):
        if os.path.isfile('files/condtion_stock.txt'):
            os.remove('files/condtion_stock.txt')