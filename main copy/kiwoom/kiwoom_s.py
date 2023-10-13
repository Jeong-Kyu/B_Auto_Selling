import os
import sys
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
from config.kiwoomType import *
import logging
import time

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self.realType = RealType()

        print('kiwoom 클래스 입니다.')
        ## 변수 ##
        self.screen_start_stop_real = '1000'
        self.screen_my_info = '2000'
        self.screen_price_info = '3000'

        self.account_select = 1
        self.use_money_percent = 1
        ##########################################
        self.target_price = 0 # 자동 시작가격 시작시 0
        self.jm_count = 2
        ##########################################
        self.sjij = 0.20     # 이익% 도달 전
        self.sjline = 0.5     
        ##########################################
        self.ij = 0.60        # 이익% 도달 후
        self.sj = 0.05
        self.oneline = 0.9
        self.twoline = 0.85
        self.threeline = 0.8
        self.msml = 2
        self.ms = 0 #몇칸뒤에 살지
        self.md = 2 #몇칸뒤에 팔지
        ##########################################
        self.call_limit = 331.20 #1000
        self.put_limit = 312.07 #0
        ##########################################
        ##딕셔너리##
        self.target_call_price = [0]
        self.target_put_price = [0]

        self.c_present_price={}
        self.p_present_price={}

        self.portfolio_stock_dict ={"현재가":0}
        self.not_account_stock_dict = {}
        self.jango_dict = {}
        
        self.now_cp = {'call':0, 'put':0}
        ##설정##
        self.z_c = 5
        self.z_p = 5

        ##시작##
        self.get_ocx_instance()
        self.event_slots()
        self.real_event_slots()

        self.signal_login_commConnect()
        self.get_account_info()
    
        self.call_price_check()
        for ic in self.c_present_price.keys():
            self.ic = ic
            self.real_price_check()
            time.sleep(0.4)
        for u in range(1,self.jm_count+1):
            self.target_call_price.append(int(self.target_call_price[0]+2.5*u))
            self.target_call_price.append(int(self.target_call_price[0]-2.5*u))
        self.target_call_price[0] = int(self.target_call_price[0])

        self.put_price_check()
        for ic in self.p_present_price.keys():
            self.ic = ic
            self.real_price_check()
            time.sleep(0.4)
        for u in range(1,self.jm_count+1):
            self.target_put_price.append(int(self.target_put_price[0]+2.5*u))
            self.target_put_price.append(int(self.target_put_price[0]-2.5*u))
        self.target_put_price[0] = int(self.target_put_price[0])

        self.detail_account_info()
        self.dynamicCall('SetRealReg(QString, QString, QString, QString)', self.screen_start_stop_real, '', self.realType.REALTYPE['장시작시간']['장운영구분'], '0')

        self.dict = ['101T6000',f'201T5{self.target_call_price[0]}',f'301T5{self.target_put_price[0]}']
        print(self.dict)
        self.foline = {f'201T5{self.target_call_price[0]}':{'now':0,'high':0,'status':0,'1':0,'2':0,'3':0,'lowcut':0}, 
                       f'301T5{self.target_put_price[0]}':{'now':0,'high':0,'status':0,'1':0,'2':0,'3':0,'lowcut':0}}

        for code in self.dict:
            # print(code)
            screen_num = 4000
            fids = self.realType.REALTYPE['옵션호가잔량']['호가시간']
            self.dynamicCall('SetRealReg(QString, QString, QString, QString)', screen_num, code, fids, '1')
            print('실시간 등록 코드: %s, 스크린번호: %s, fid번호: %s' % (code,screen_num,20))
    
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
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def msg_slot(self, sScrNo, sRQName, sTrCode, sMsg):
        print(sScrNo, sRQName, sTrCode, sMsg)
    def login_slot(self, errCode):
        print(errors(errCode))
        self.login_event_loop.exit()

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
                         # 스크린번호, 설정이름, 요청id, 사용안함, 다음페이지
        if sRQName == '예수금상세현황요청':
            deposit = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0, '주문가능총액')
            print('예수금 : %s' % int(deposit))

            self.use_money = int(deposit) * self.use_money_percent
            # self.use_money = self.use_money / 4

            ok_deposit = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0, '인출가능총액')
            print('출금가능금액 : %s' % int(ok_deposit))

            self.detail_account_info_event_loop.exit()

        if sRQName == '콜행사가':
            atm_index=[]
            for i in range (40, 80):
                callatm = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, 'ATM구분')
                atm_index.append(callatm.strip())
            atm_one = atm_index.index('1')
            s_one = atm_one + 45 - 10
            e_one = atm_one + 45 + 10
            for i in range (s_one, e_one):
                callcode = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '종목코드')
                callprice = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '행사가')
                self.c_present_price.update({callcode.split()[0] : {'행사가' : callprice.split()[0]}})
            self.call_price_check_event_loop.exit()

        if sRQName == '풋행사가':
            atm_index=[]
            for i in range (40, 80):
                putatm = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, 'ATM구분')
                atm_index.append(putatm.strip())
            atm_one = atm_index.index('1')
            s_one = atm_one + 45 - 10
            e_one = atm_one + 45 + 10
            for i in range (s_one, e_one):
                putcode = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '종목코드')
                putprice = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '행사가')
                self.p_present_price.update({putcode.split()[0] : {'행사가' : putprice.split()[0]}})
            self.put_price_check_event_loop.exit()

        if sRQName == '종목가격':
            price = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0, '현재가')
            if self.ic in self.c_present_price:
                self.c_present_price[self.ic].update({'현재가':abs(float(price.strip()))})
                if self.z_c > abs(1-abs(float(price.strip()))):
                    self.z_c = abs(1-abs(float(price.strip())))
                    self.target_call_price[0] = float(self.c_present_price[self.ic]['행사가'])

            elif self.ic in self.p_present_price:
                self.p_present_price[self.ic].update({'현재가':abs(float(price.strip()))})  
                if self.z_p > abs(1-abs(float(price.strip()))):
                    self.z_p = abs(1-abs(float(price.strip())))
                    self.target_put_price[0] = float(self.p_present_price[self.ic]['행사가'])
            self.real_price_check_event_loop.exit()

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
        self.dynamicCall('CommRqData(String, String, int, String)', '예수금상세현황요청', 'opw20010', '0', self.screen_my_info)
        self.detail_account_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop.exec_()

    def call_price_check(self):
        print('콜행사가 조사')
        self.dynamicCall('SetInputValue(String, String)','만기년월', '202305') 
        self.dynamicCall('CommRqData(String, String, int, String)','콜행사가',"opt50004","0", self.screen_my_info)
        self.call_price_check_event_loop = QEventLoop()
        self.call_price_check_event_loop.exec_()

    def put_price_check(self):
        print('풋행사가 조사')
        self.dynamicCall('SetInputValue(String, String)','만기년월', '202305') 
        self.dynamicCall('CommRqData(String, String, int, String)','풋행사가',"opt50065","0", self.screen_my_info)
        self.put_price_check_event_loop = QEventLoop()
        self.put_price_check_event_loop.exec_()

    def real_price_check(self):
        # print('종목별 가격')
        self.dynamicCall('SetInputValue(String, String)','종목코드', self.ic) 
        k=self.dynamicCall('CommRqData(String, String, int, String)','종목가격',"opt50001","0",self.screen_price_info)
        self.real_price_check_event_loop = QEventLoop()
        self.real_price_check_event_loop.exec_()

    def realdata_slot(self, sCode, sRealType, sRealData):
        
        if sRealType == '장시작시간':
            fid = self.realType.REALTYPE[sRealType]['장운영구분']
            value = self.dynamicCall('GetCommRealData(QString, int)', sCode, fid)

            if value == '0':
                print('장 시작 전')
            elif value == '3':
                print('장 시작')
            elif value == '2':
                self.now_cp = {'call':1, 'put':1}
                print('장 종료, 동시호가로 넘어감')
                for sCode in self.jango_dict.keys():
                    bs = self.jango_dict[sCode]['주문가능수량']
                    gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['당일종료매도', '0101', self.account_num, sCode, 1, 1, '3', bs, 0, ""])
                    print('당일종료매도',self.portfolio_stock_dict)     
                    self.jango_dict[sCode]['주문가능수량'] = 0

            elif value == '4':
                print('3시30분 장 종료')
                # for code in self.portfolio_stock_dict.keys():
                #     self.dynamicCall('SetRealRemove(QString,QString)',self.portfolio_stock_dict[code]['스크린번호'],code)
                # sys.exit()

        elif sRealType == '선물시세':

            self.now_price = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['현재가'])
            self.now_price = abs(float(self.now_price))

            self.ago_price = self.portfolio_stock_dict['현재가']
            self.portfolio_stock_dict.update({"현재가":self.now_price})
            self.portfolio_stock_dict.update({"이전 현재가":self.ago_price})
            if self.ago_price == 0:
                if self.target_price == 0:
                    self.target_price = self.now_price
                    print('기준선',self.target_price)
                    pass
                else:
                    pass

            elif self.ago_price <= self.target_price+(0.05*self.ms) and self.now_price > self.target_price+(0.05*self.ms):
                if int(self.now_cp['call']) == 0:
                    self.now_cp['call'] = 1
                    for price in self.target_call_price:
                        for k in range(self.msml):
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['콜매수', '0101', self.account_num, f'201T5{int(price)}', 1, 2, '3', 1, 0, ""])
                            if gr == 0:
                                print(f'{price} 콜매수{k}')
                            if k+1%5 == 0:
                                time.sleep(1)
                        time.sleep(0.5)
                    
            elif self.ago_price >= self.target_price-(0.05*self.ms) and self.now_price < self.target_price-(0.05*self.ms): 
                if int(self.now_cp['put']) == 0:
                    self.now_cp['put'] = 1
                    for price in self.target_put_price:
                        for k in range(self.msml):
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['풋매수', '0101', self.account_num, f'301T5{int(price)}', 1, 2, '3', 1, 0, ""])
                            if gr == 0:
                                print(f'{price} 풋매수{k}')
                            if k+1%5 == 0:
                                time.sleep(1)
                        time.sleep(0.5)

            elif self.ago_price <= self.target_price+(0.05*self.md) and self.now_price > self.target_price+(0.05*self.md):
                if int(self.now_cp['put']) == 1:
                    self.now_cp['put'] = 0
                    for price in self.target_put_price:
                        if f'301T5{int(price)}' in self.not_account_stock_dict.keys():
                            bs = self.not_account_stock_dict[f'301T5{int(price)}']['미체결수량']
                            jb = self.not_account_stock_dict[f'301T5{int(price)}']['주문번호']
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['풋취소', '0101', self.account_num, f'301T5{int(price)}', 3, 1, '3', bs, 0, jb])
                            if gr==0:
                                print('풋취소')
                        if f'301T5{int(price)}' in self.jango_dict.keys():
                            self.now_cp['put'] = 0
                            bs = self.jango_dict[f'301T5{int(price)}']['주문가능수량']
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['풋매도', '0101', self.account_num, f'301T5{int(price)}', 1, 1, '3', bs, 0, ""])
                            print('풋매도')
                        else:
                            pass
                        
            elif self.ago_price >= self.target_price-(0.05*self.md) and self.now_price < self.target_price-(0.05*self.md):
                if int(self.now_cp['call']) == 1:
                    self.now_cp['call'] = 0
                    for price in self.target_call_price:
                        if f'201T5{int(price)}' in self.not_account_stock_dict.keys():
                            bs = self.not_account_stock_dict[f'201T5{int(price)}']['미체결수량']
                            jb = self.not_account_stock_dict[f'201T5{int(price)}']['주문번호']
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['콜취소', '0101', self.account_num, f'201T5{int(price)}', 3, 1, '3', bs, 0, jb])
                            if gr==0:
                                print('콜취소')
                        if f'201T5{int(price)}' in self.jango_dict.keys():
                            self.now_cp['call'] = 0
                            bs = self.jango_dict[f'201T5{int(price)}']['주문가능수량']
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['콜매도', '0101', self.account_num, f'201T5{int(price)}', 1, 1, '3', bs, 0, ""])
                            print('콜매도')
                        else:
                            pass

            elif self.now_price > self.call_limit:
                if int(self.now_cp['call']) == 1:
                    self.now_cp['call'] = 0    
                    for price in self.target_call_price:
                        if f'201T5{int(price)}' in self.jango_dict.keys():
                            self.now_cp['call'] = 0
                            bs = self.jango_dict[f'201T5{int(price)}']['주문가능수량']
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['콜매도', '0101', self.account_num, f'201T5{int(price)}', 1, 1, '3', bs, 0, ""])
                            print('limit 콜매도')

            elif self.now_price < self.put_limit:
                if int(self.now_cp['put']) == 1:
                    self.now_cp['put'] = 0    
                    for price in self.target_put_price:
                        if f'301T5{int(price)}' in self.jango_dict.keys():
                            self.now_cp['put'] = 0
                            bs = self.jango_dict[f'301T5{int(price)}']['주문가능수량']
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['풋매도', '0101', self.account_num, f'301T5{int(price)}', 1, 1, '3', bs, 0, ""])
                            print('limit 풋매도')
            else:
                pass

        elif sRealType == '옵션시세':
            if sCode in self.jango_dict.keys():
                self.key = []
                if sCode == f'201T5{self.target_call_price[0]}':
                    for k in self.target_call_price:
                        self.key.append(f'201T5{k}')
                elif sCode == f'301T5{self.target_put_price[0]}':
                    for k in self.target_put_price:
                        self.key.append(f'301T5{k}')
                else:
                    self.key = [sCode]

                realp = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['현재가'])#+,-
                realp = abs(float(realp))
                self.foline[sCode].update({'now':realp})
                if self.foline[sCode]['high'] < realp:
                    self.foline[sCode].update({'high':realp})

                n_percent = self.foline[sCode]['now']/self.jango_dict[sCode]['매입단가']-1
                h_percent = self.foline[sCode]['high']/self.jango_dict[sCode]['매입단가']-1
                
                if n_percent < -self.sj:
                    for key in self.key:
                        bs = self.jango_dict[key]['주문가능수량']
                        gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['손절매도', '0101', self.account_num, key, 1, 1, '3', bs, 0, ""])
                        self.jango_dict[key]['주문가능수량'] = 0
                    print('손절매도',self.foline[sCode])     
                    self.foline[sCode].update({'now':0,'high':0,'status':0,'1':0,'2':0,'3':0,'lowcut':0})
                    if sCode == f'201T5{int(self.target_call_price[0])}':
                        self.now_cp['call'] = 0
                    elif sCode == f'301T5{int(self.target_put_price[0])}':
                        self.now_cp['put'] = 0

                elif n_percent >= self.ij:
                    self.foline[sCode].update({'1':(h_percent*self.oneline+1)*self.jango_dict[sCode]['매입단가']})
                    self.foline[sCode].update({'2':(h_percent*self.twoline+1)*self.jango_dict[sCode]['매입단가']})
                    self.foline[sCode].update({'3':(h_percent*self.threeline+1)*self.jango_dict[sCode]['매입단가']})

                elif n_percent > self.sjij and n_percent < self.ij:
                    self.foline[sCode].update({'lowcut':(h_percent*self.sjline+1)*self.jango_dict[sCode]['매입단가']})

                if self.foline[sCode]['1'] != 0:

                    if self.foline[sCode]['status'] == 0 and self.foline[sCode]['1'] > self.foline[sCode]['now']:
                        for key in self.key:
                            bs = self.jango_dict[key]['주문가능수량']
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['익절매도', '0101', self.account_num, key, 1, 1, '3', round(bs/2), 0, ""])
                            self.jango_dict[key]['주문가능수량'] = bs - round(bs/2)
                        print('1차 익절매도',self.foline[sCode],round(bs/2))     
                        self.foline[sCode].update({'status':1})

                    elif self.foline[sCode]['status'] == 1 and self.foline[sCode]['2'] > self.foline[sCode]['now']:
                        for key in self.key:
                            bs = self.jango_dict[key]['주문가능수량']
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['익절매도', '0101', self.account_num, key, 1, 1, '3', round(bs/2), 0, ""])  
                            self.jango_dict[key]['주문가능수량'] = bs - round(bs/2)
                        print('2차 익절매도',self.foline[sCode],round(bs/2))                              
                        self.foline[sCode].update({'status':2})

                    elif self.foline[sCode]['status'] == 2 and self.foline[sCode]['3'] > self.foline[sCode]['now']:
                        for key in self.key:
                            bs = self.jango_dict[key]['주문가능수량']
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['익절매도', '0101', self.account_num, key, 1, 1, '3', bs, 0, ""])    
                            self.jango_dict[key]['주문가능수량'] = 0
                        print('3차 익절매도',self.foline[sCode],bs) 
                        self.foline[sCode].update({'now':0,'high':0,'status':0,'1':0,'2':0,'3':0,'lowcut':0})
                        if sCode == f'201T5{int(self.target_call_price[0])}' or f'301T5{int(self.target_put_price[0])}':
                            self.now_cp['call'] = 0
                            self.now_cp['put'] = 0
                            self.target_price = self.now_price
                            print(f'기준변경 : {self.target_price}')
                            time.sleep(0.5)
                        
                elif self.foline[sCode]['lowcut'] != 0 and self.foline[sCode]['lowcut']>self.foline[sCode]['now']:
                    for key in self.key:
                        bs = self.jango_dict[key]['주문가능수량']
                        gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['익절매도', '0101', self.account_num, key, 1, 1, '3', bs, 0, ""])   
                        self.jango_dict[key]['주문가능수량'] = 0
                    print('선행 익절매도',self.foline[sCode],bs)  
                    self.foline[sCode].update({'now':0,'high':0,'status':0,'1':0,'2':0,'3':0,'lowcut':0})
                    if sCode == f'201T5{int(self.target_call_price[0])}' or f'301T5{int(self.target_put_price[0])}':
                        self.now_cp['call'] = 0
                        self.now_cp['put'] = 0
                        self.target_price = self.now_price
                        print(f'기준변경 : {self.target_price}')
                        time.sleep(0.5)
                            
    def chejan_slot(self,sGubun,nItemCnt,sFIdList):
        if int(sGubun) == 0:
            sCode = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['종목코드'])
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

        elif int(sGubun) == 4:
            account_num = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['계좌번호'])
            sCode = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['종목코드'])[:]
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
            # print(self.jango_dict)
            if sCode not in self.dict:
                if sCode[-3:] not in self.target_call_price and sCode[-3:] not in self.target_put_price:
                    self.dict.append(sCode)
                    self.foline[sCode] = {'now':0,'high':0,'status':0,'1':0,'2':0,'3':0,'lowcut':0}
                    screen_num = 4000
                    fids = self.realType.REALTYPE['옵션호가잔량']['호가시간']
                    self.dynamicCall('SetRealReg(QString, QString, QString, QString)', screen_num, sCode, fids, '1')
                    print('실시간 등록 코드: %s, 스크린번호: %s, fid번호: %s' % (sCode,screen_num,20))
            if like_quan == 0:
                del self.jango_dict[sCode]