import os
import sys
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
from config.kiwoomType import *
import logging
import time
# from datetime import datetime
# now = datetime.now()
# print(now.year)
# print(now.month+now.day)
# print(now.day)


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self.realType = RealType()

        print('kiwoom 클래스 입니다.')
        ## 변수 ##
        self.screen_start_stop_real = '1000'
        self.screen_my_info = '2000'
        self.screen_price_info = '3000'
        self.screen_pivot_info = '5000'
        self.account_select = 1
        self.use_money_percent = 0.1

        self.startline = 5            # 시작 기준 퍼센트
        self.endline = 0             # 손절 기준 퍼센트
        self.line1, self.line2, self.line3 = 20,30,50             # 라인 퍼센트
        self.panm1, self.panm2, self.panm3 = 50,50,100            # 매도 퍼센트
       
        self.no1 = 0                   # 조건식 선택
        self.no2 = 1                   # 조건식 선택
        self.no3 = 2                   # 조건식 선택
        self.no4 = 3                   # 조건식 선택

        self.ms = 10                   # 매수 수량
        
        self.dict=[]
        self.line_dict = {}
        self.not_account_stock_dict={}
        self.jango_dict = {}
        self.index = []
        self.name = []
        self.today_symbol = []

        ##시작##
        self.get_ocx_instance()
        self.event_slots()
        self.real_event_slots()

        self.signal_login_commConnect()
        
        self.GetConditionLoad()
        self.get_account_info()

        self.detail_account_info()
        self.having_check_info()
        self.dynamicCall('SetRealReg(QString, QString, QString, QString)', self.screen_start_stop_real, '', self.realType.REALTYPE['장시작시간']['장운영구분'], '0')

        self.GetConditionNameList()
        self.send_condition()
        for code in self.dict:
            screen_num = 4000
            fids = self.realType.REALTYPE['주식호가잔량']['호가시간']
            self.dynamicCall('SetRealReg(QString, QString, QString, QString)', screen_num, code, fids, '1')
            print('실시간 등록 코드: %s, 스크린번호: %s, fid번호: %s' % (code,screen_num,20))
    
    def get_ocx_instance(self):
        self.setControl('KHOPENAPI.KHOpenAPICtrl.1') 

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnEventConnect.connect(self._handler_login)
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def real_event_slots(self):
        self.OnReceiveConditionVer.connect(self._handler_condition_load)
        self.OnReceiveRealCondition.connect(self._handler_real_condition)
        self.OnReceiveRealData.connect(self.realdata_slot)
        self.OnReceiveChejanData.connect(self.chejan_slot)

    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def msg_slot(self, sScrNo, sRQName, sTrCode, sMsg):
        print(sScrNo, sRQName, sTrCode, sMsg)

    def login_slot(self, errCode):
        print(errors(errCode))
        self.login_event_loop.exit()

    def CommConnect(self):
        self.dynamicCall("CommConnect()")

    def _handler_login(self, err_code):
        print("handler login", err_code)

    def _handler_condition_load(self, ret, msg):
        print("handler condition load", ret, msg)

    def _handler_real_condition(self, code, type, cond_name, cond_index):
        # self.o(code)
        # e_price = abs(self.e_price)
        # if code not in self.dict: #type == 'D' and
        if code not in self.today_symbol:  
            self.dict.append(code)
            # print(self.ms,e_price)
            gr = self.dynamicCall('SendOrder(QString, QString, QString, QString, QString, int, QString, QString, int)',['조건식매수', self.screen_price_info, self.account_num,1, code, int(self.ms), 0, '03', ""])
            if gr == 0:
                ko = "성공"
                self.today_symbol.append(code)
            else:
                ko = "실패"
            print(cond_name, code, ko)
        else:
            print(code,"중복")

    def GetCommRealData(self):
        self.dynamicCall("GetCommRealData()")

    def GetConditionLoad(self):
        d =self.dynamicCall("GetConditionLoad()")
        print(d)

    def GetConditionNameList(self):
        data = self.dynamicCall("GetConditionNameList()")
        conditions = data.split(";")[:-1]
        for condition in conditions:
            index, name = condition.split('^')
            self.index.append(index)
            self.name.append(name)
        print(self.name)

    def SendCondition(self, screen, cond_name, cond_index, search):
        ret = self.dynamicCall("SendCondition(QString, QString, int, int)", screen, cond_name, cond_index, search)
    def SendConditionStop(self, screen, cond_name, cond_index):
        ret = self.dynamicCall("SendConditionStop(QString, QString, int)", screen, cond_name, cond_index)

    def send_condition(self):
        print("사용조건식", self.name[self.no1])
        k = self.SendCondition("100", self.name[self.no1], self.index[self.no1], 1)
        # print("사용조건식", self.name[self.no2])
        # k = self.SendCondition("100", self.name[self.no2], self.index[self.no2], 1)
        print("사용조건식", self.name[self.no3])
        k = self.SendCondition("100", self.name[self.no3], self.index[self.no3], 1)
        print("사용조건식", self.name[self.no4])
        k = self.SendCondition("100", self.name[self.no4], self.index[self.no4], 1)

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
                         # 스크린번호, 설정이름, 요청id, 사용안함, 다음페이지
        if sRQName == '예수금상세현황요청':
            deposit = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0, '주문가능금액')
            print('예수금 : %s' % int(deposit))
            self.use_money = int(deposit) * self.use_money_percent
            # self.use_money = self.use_money / 4
            ok_deposit = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0, '출금가능금액')
            print('출금가능금액 : %s' % int(ok_deposit))

            self.detail_account_info_event_loop.exit()

        if sRQName == '계좌평가현황요청':
            h = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0, '출력건수')
            for i in range(int(h)):
                h_code = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '종목코드').strip()[1:]
                h_name = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '평균단가')
                stock_quan = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '보유수량')
                self.dict.append(str(h_code))
                self.line_dict[str(h_code)]={"평균단가":int(h_name),"현재가":0,"최대":0,"1차":0,"2차":0,"3차":0,"손절":0,"상태":0}
                self.jango_dict[str(h_code)]={'보유수량':int(stock_quan)}
                self.today_symbol.append(str(h_code))
            self.real_price_check_event_loop.exit()
        
        if sRQName == '체결정보요청':
            self.e_price = self.dynamicCall('GetCommData(String, String, int, String)', 'OPT10003', '체결정보요청', 0, '현재가')
            self.e_price = self.e_price.replace(" ","")
            print(self.e_price)
            print(abs(int(self.e_price)))

    def get_account_info(self):
        account_list = self.dynamicCall('GetLogininfo(String)','ACCNO')
        self.account_num = account_list.split(';')[self.account_select]
        print('전체 계좌번호 %s' %account_list)
        print('나의 보유 계좌번호 %s' %self.account_num)

    def detail_account_info(self):
        print('예수금 요청')
        self.dynamicCall('SetInputValue(String, String)','계좌번호', self.account_num)
        self.dynamicCall('SetInputValue(String, String)','비밀번호', '0000')
        self.dynamicCall('SetInputValue(String, String)','비밀번호입력매체구분', '00')
        # self.dynamicCall('SetInputValue(String, String)','조회구분', '2')    
        self.dynamicCall('CommRqData(String, String, int, String)', '예수금상세현황요청', 'opw00001', '0', self.screen_my_info)
        self.detail_account_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop.exec_()

    def having_check_info(self):
        print('보유종목')
        self.dynamicCall('SetInputValue(String, String)','계좌번호', self.account_num)
        self.dynamicCall('SetInputValue(String, String)','비밀번호', '0000')
        self.dynamicCall('SetInputValue(String, String)','상장폐지조회구분', '0')
        self.dynamicCall('SetInputValue(String, String)','비밀번호입력매체구분', '00')
        self.dynamicCall('CommRqData(String, String, int, String)','계좌평가현황요청',"opw00004","0",self.screen_price_info)
        self.real_price_check_event_loop = QEventLoop()
        self.real_price_check_event_loop.exec_()

    # def o(self,code):
    #     time.sleep(0.5)
    #     print('=')
    #     self.dynamicCall('SetInputValue(String, String)','종목코드', code)
    #     k=self.dynamicCall('CommRqData(String, String, int, String)','체결정보요청',"OPT10003","0",self.screen_pivot_info)
    #     print(code, k)

    def realdata_slot(self, sCode, sRealType, sRealData):
        if sRealType == '장시작시간':
            fid = self.realType.REALTYPE[sRealType]['장운영구분']
            value = self.dynamicCall('GetCommRealData(QString, int)', str(sCode), fid)

            if value == '0':
                print('장 시작 전')
            elif value == '3':
                print('장 시작')
            elif value == '2':
                print('장 종료, 동시호가로 넘어감')
            elif value == '4':
                print('3시30분 장 종료')

        elif sRealType == '주식체결':
            print('check')
            try:
                C_count = int(self.jango_dict[str(sCode)]['보유수량'])
                CODE = self.line_dict[sCode]
                self.now_price = abs(int(self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['현재가'])))
                self.low_price = abs(int(self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['저가'])))
                CODE["현재가"] = self.now_price
                CODE["손절"] = CODE["평균단가"]*(1-0.01*self.endline)
                if CODE["최대"] < CODE["현재가"]:
                    CODE["최대"] = CODE["현재가"]
                    CODE["상태"] = 0
                if CODE['현재가'] < CODE["손절"]:
                    gr = self.dynamicCall('SendOrder(QString, QString, QString, QString, QString, int, int, QString, QString)',['손절매도', '0101', self.account_num, 2, sCode, C_count, 0, '03', ""])

                if CODE['현재가'] > CODE["평균단가"]*(1+0.01*self.startline) and CODE["상태"] == 0:
                    CODE["1차"] = CODE["평균단가"]+(CODE["최대"]-CODE["평균단가"])*(1-self.line1*0.01)
                    CODE["2차"] = CODE["평균단가"]+(CODE["최대"]-CODE["평균단가"])*(1-self.line2*0.01)
                    CODE["3차"] = CODE["평균단가"]+(CODE["최대"]-CODE["평균단가"])*(1-self.line3*0.01)
                    CODE["상태"] = 1

                if CODE["1차"] != 0:
                    if CODE["1차"] > CODE['현재가'] and CODE['상태'] == 1:
                        gr = self.dynamicCall('SendOrder(QString, QString, QString, QString, QString, int, int, QString, QString)',['1차매도', '0101', self.account_num, 2, sCode, int(C_count*0.01*self.panm1), 0, '03', ""])
                        CODE["상태"] = 2
                        print("1차매도", int(C_count*0.01*self.panm1), CODE)
                    elif CODE["2차"] > CODE['현재가'] and CODE['상태'] == 2:
                        gr = self.dynamicCall('SendOrder(QString, QString, QString, QString, QString, int, int, QString, QString)',['2차매도', '0101', self.account_num, 2, sCode, int(C_count*0.01*self.panm2), 0, '03', ""])
                        CODE["상태"] = 3
                        print("2차매도", int(C_count*0.01*self.panm2), CODE)
                    elif CODE["3차"] > CODE['현재가'] and CODE['상태'] == 3:
                        gr = self.dynamicCall('SendOrder(QString, QString, QString, QString, QString, int, int, QString, QString)',['3차매도', '0101', self.account_num, 2, sCode, int(C_count*0.01*self.panm3), 0, '03', ""])
                        CODE["상태"] = 4
                        print("3차매도", int(C_count*0.01*self.panm3), CODE)

            except:
                print(f'{sCode}오류')

    def chejan_slot(self,sGubun,nItemCnt,sFIdList):
        if int(sGubun) == 0:
            sCode = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['종목코드'])[1:]
            order_number = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문번호'])
            order_status = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문상태'])
            order_quan = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문수량'])
            order_quan = int(order_quan)
            not_chegual_quan = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['미체결수량'])
            not_chegual_quan = int(not_chegual_quan)
            chegual_quantity = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['체결량'])
            if chegual_quantity == '':
                chegual_quantity = 0
            else:
                chegual_quantity = int(chegual_quantity)

            if sCode not in self.not_account_stock_dict.keys():
                self.not_account_stock_dict.update({sCode:{}})
            self.not_account_stock_dict[sCode].update({'주문번호':order_number})
            self.not_account_stock_dict[sCode].update({'주문상태':order_status})
            self.not_account_stock_dict[sCode].update({'주문수량':order_quan})
            self.not_account_stock_dict[sCode].update({'미체결수량':not_chegual_quan})
            if order_quan == chegual_quantity:
                del self.not_account_stock_dict[sCode]

        elif int(sGubun) == 1:
            account_num = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['계좌번호'])
            sCode = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['종목코드'])[1:]
            stock_name = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['종목명'])
            stock_name = stock_name.strip()
            current_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['현재가'])
            current_price = float(current_price)
            stock_quan = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['보유수량'])
            stock_quan = int(stock_quan)
            like_quan = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['주문가능수량'])
            like_quan = int(like_quan)
            buy_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['손익율'])
            buy_price = float(buy_price)
            total_buy_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['총매입가'])
            total_buy_price = float(total_buy_price)
            buy_p_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['매입단가'])
            buy_p_price = float(buy_p_price)

            if sCode not in self.jango_dict.keys():
                self.jango_dict.update({sCode:{}})
            self.jango_dict[sCode].update({'현재가':current_price})
            self.jango_dict[sCode].update({'종목코드':sCode})
            self.jango_dict[sCode].update({'종목명':stock_name})
            self.jango_dict[sCode].update({'보유수량':stock_quan})
            self.jango_dict[sCode].update({'주문가능수량':like_quan})
            self.jango_dict[sCode].update({'손익율':buy_price})
            self.jango_dict[sCode].update({'총매입가':total_buy_price})
            self.jango_dict[sCode].update({'매입단가':buy_p_price})
            # print(self.not_account_stock_dict)
            # print(self.jango_dict)

            if sCode not in self.dict:
                self.dict.append(str(sCode))
                self.line_dict.update({sCode:{}})            
                self.line_dict[sCode]={"평균단가":buy_p_price,"현재가":0,"최대":0,"1차":0,"2차":0,"3차":0,"손절":0,"상태":0}
                screen_num = 4000
                fids = self.realType.REALTYPE['주식호가잔량']['호가시간']
                self.dynamicCall('SetRealReg(QString, QString, QString, QString)', screen_num, sCode, fids, '1')
                print('실시간 등록 코드: %s, 스크린번호: %s, fid번호: %s' % (sCode,screen_num,20))
            if stock_quan == 0:
                self.dynamicCall('SetRealRemove(QString,QString)',4000,sCode)
                del self.jango_dict[sCode]
                del self.line_dict[sCode]
                self.dict.remove(sCode)