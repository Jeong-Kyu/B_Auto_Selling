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
        self.target_price = 300
        self.ij = 0.10
        self.ij2 = 0.05
        self.sj = 0.10
        self.oneline = 0.7
        self.twoline = 0.6
        self.threeline = 0.5
        self.msml = 1
        ##########################################
        self.call_limit = 1000
        self.put_limit = 0
        ##########################################
        # self.target_adj_price = int(round((self.target_price/2.5))*2.5)

        self.target_call_price = 325#int((round((self.target_price/2.5))+1)*2.5)
        self.target_put_price = 295#int((round((self.target_price/2.5))-1)*2.5)
        
        self.z_c = 10
        self.z_p = 10
        self.target_count = 0

        ##딕셔너리##
        self.prices = []
        self.c_present_price={}
        self.p_present_price={}
        self.portfolio_stock_dict ={"현재가":0}
        
        self.not_account_stock_dict = {}
        self.jango_dict = {}
        self.now_cp = {'call':0, 'put':0}
        self.lr=0

        ##딕셔너리##
        self.cp_present_price={}
        self.portfolio_stock_dict ={"현재가":0}
        
        self.not_account_stock_dict = {}
        self.jango_dict = {}
        self.now_cp = {'call':0, 'put':0}
        self.lr=0

        self.get_ocx_instance()
        self.event_slots()
        self.real_event_slots()

        self.signal_login_commConnect()
        self.get_account_info()
    
        self.call_price_check()
        for ic in self.c_present_price.keys():
            self.ic = ic
            self.real_price_check()
            time.sleep(0.3)
        # print(self.c_present_price)

        self.put_price_check()
        for ic in self.p_present_price.keys():
            self.ic = ic
            self.real_price_check()
            time.sleep(0.3)
        # print(self.p_present_price)

        self.detail_account_info()
        self.dynamicCall('SetRealReg(QString, QString, QString, QString)', self.screen_start_stop_real, '', self.realType.REALTYPE['장시작시간']['장운영구분'], '0')

        self.dict = ['101T6000',f'201T4{self.target_call_price}',f'301T4{self.target_put_price}']
        print(self.dict)
        self.foline = {f'201T4{self.target_call_price}':{'1':0,'2':0,'3':0,'s':0}, f'301T4{self.target_put_price}':{'1':0,'2':0,'3':0,'s':0}}

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
            for i in range (45, 75):
                callatm = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, 'ATM구분')
                atm_index.append(callatm.strip())
            atm_one = atm_index.index('1')
            s_one = atm_one + 45 - 15
            e_one = atm_one + 45 + 15
            for i in range (s_one, e_one):
                callcode = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '종목코드')
                callprice = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '행사가')
                self.c_present_price.update({callcode.split()[0] : {'행사가' : callprice.split()[0]}})
            self.call_price_check_event_loop.exit()

        if sRQName == '풋행사가':
            atm_index=[]
            for i in range (45, 75):
                putatm = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, 'ATM구분')
                atm_index.append(putatm.strip())
            atm_one = atm_index.index('1')
            s_one = atm_one + 45 - 15
            e_one = atm_one + 45 + 15
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
                    self.target_call_price = int(float(self.c_present_price[self.ic]['행사가']))
                    print(self.c_present_price[self.ic])

            elif self.ic in self.p_present_price:
                self.p_present_price[self.ic].update({'현재가':abs(float(price.strip()))})  
                if self.z_p > abs(1-abs(float(price.strip()))):
                    self.z_p = abs(1-abs(float(price.strip())))
                    self.target_put_price = int(float(self.p_present_price[self.ic]['행사가']))
                    print(self.p_present_price[self.ic])
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
        self.dynamicCall('SetInputValue(String, String)','만기년월', '202304') 
        self.dynamicCall('CommRqData(String, String, int, String)','콜행사가',"opt50004","0", self.screen_my_info)
        self.call_price_check_event_loop = QEventLoop()
        self.call_price_check_event_loop.exec_()

    def put_price_check(self):
        print('풋행사가 조사')
        self.dynamicCall('SetInputValue(String, String)','만기년월', '202304') 
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
                print('장 종료, 동시호가로 넘어감')
                shjg = self.dynamicCall("GetCommRealData(QString, int)", '101T6000', self.realType.REALTYPE['선물시세']['현재가'])#+,-
                print(shjg)
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

            self.hjg = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['현재가'])#+,-
            self.hjg = abs(float(self.hjg))

            l = self.portfolio_stock_dict['현재가']
            # self.portfolio_stock_dict.update({"체결시간":a})
            self.portfolio_stock_dict.update({"현재가":self.hjg})
            self.portfolio_stock_dict.update({"이전 현재가":l})
            # self.portfolio_stock_dict.update({"거래량":g})
            # print(self.portfolio_stock_dict)
            if l == 0:
                if self.target_price == 0 :
                    self.target_price=self.hjg
                    print('기준선',self.target_price)
                    pass
                else:
                    pass
            elif l <= self.target_price and self.hjg > self.target_price:
                # print(l,self.target_price,hjg)
                if int(self.now_cp['call']) == 0:
                    self.now_cp['call'] = 1
                    for t in range(self.msml):
                        gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['콜매수', '0101', self.account_num, f'201T4{int(self.target_call_price)}', 1, 2, '3', 1, 0, ""])
                        if gr == 0:
                            print(f'콜매수{t}')
                    # self.now_cp.update({'call':(int(self.now_cp['call'])+1)})
                    # print(self.now_cp)
            elif l <= self.target_price+0.1 and self.hjg > self.target_price+0.1:
                if f'301T4{int(self.target_put_price)}' in self.not_account_stock_dict.keys():
                    bs = self.not_account_stock_dict[f'301T4{int(self.target_put_price)}']['미체결수량']
                    jb = self.not_account_stock_dict[f'301T4{int(self.target_put_price)}']['주문번호']
                    gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['풋취소', '0101', self.account_num, f'301T4{int(self.target_put_price)}', 3, 1, '3', bs, 0, jb])
                    if gr==0:
                        print('풋취소')
                if f'301T4{int(self.target_put_price)}' in self.jango_dict.keys():
                    self.now_cp['put'] = 0
                    bs = self.jango_dict[f'301T4{int(self.target_put_price)}']['주문가능수량']
                    gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['풋매도', '0101', self.account_num, f'301T4{int(self.target_put_price)}', 1, 1, '3', bs, 0, ""])
                    print('풋매도')#,self.portfolio_stock_dict)
                else:
                    pass

            elif l >= self.target_price and self.hjg < self.target_price:
                # print(l,self.target_price,hjg)
                if int(self.now_cp['put']) == 0:
                    self.now_cp['put'] = 1
                    for t in range(self.msml):
                        gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['풋매수', '0101', self.account_num, f'301T4{int(self.target_put_price)}', 1, 2, '3', 1, 0, ""])
                        if gr == 0:
                            print(f'풋매수{t}')
                        # self.now_cp.update({'put':(int(self.now_cp['put'])+1)})
                        # print(self.now_cp)
                       
            elif l >= self.target_price-0.1 and self.hjg < self.target_price-0.1:
                if f'201T4{int(self.target_put_price)}' in self.not_account_stock_dict.keys():
                    bs = self.not_account_stock_dict[f'201T4{int(self.target_put_price)}']['미체결수량']
                    jb = self.not_account_stock_dict[f'201T4{int(self.target_put_price)}']['주문번호']
                    gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['콜취소', '0101', self.account_num, f'201T4{int(self.target_put_price)}', 3, 1, '3', bs, 0, jb])
                    if gr==0:
                        print('콜취소')# print(gr)
                if f'201T4{int(self.target_call_price)}' in self.jango_dict.keys():
                    self.now_cp['call'] = 0
                    bs = self.jango_dict[f'201T4{int(self.target_call_price)}']['주문가능수량']
                    gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['콜매도', '0101', self.account_num, f'201T4{int(self.target_call_price)}', 1, 1, '3', bs, 0, ""])
                    print('콜매도')#,self.portfolio_stock_dict)
                else:
                    pass
            elif self.hjg > self.call_limit:
                if f'201T4{int(self.target_call_price)}' in self.jango_dict.keys():
                    self.now_cp['call'] = 0
                    bs = self.jango_dict[f'201T4{int(self.target_call_price)}']['주문가능수량']
                    gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['콜매도', '0101', self.account_num, f'201T4{int(self.target_call_price)}', 1, 1, '3', bs, 0, ""])
                    print('콜매도')#,self.portfolio_stock_dict)
            elif self.hjg < self.put_limit:
                if f'301T4{int(self.target_put_price)}' in self.jango_dict.keys():
                    self.now_cp['put'] = 0
                    bs = self.jango_dict[f'301T4{int(self.target_put_price)}']['주문가능수량']
                    gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['풋매도', '0101', self.account_num, f'301T4{int(self.target_put_price)}', 1, 1, '3', bs, 0, ""])
                    print('풋매도')#,self.portfolio_stock_dict)
            else:
                pass

        elif sRealType == '옵션시세':
            if sCode in self.jango_dict.keys():
                realp = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['현재가'])#+,-
                realp = abs(float(realp))
                if self.lr < realp:
                    self.lr = realp

                if realp/self.jango_dict[sCode]['매입단가']-1 < -self.sj:
                    bs = self.jango_dict[sCode]['주문가능수량']
                    gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['손절매도', '0101', self.account_num, sCode, 1, 1, '3', bs, 0, ""])
                    print('손절매도',self.portfolio_stock_dict)     
                    self.jango_dict[sCode]['주문가능수량'] = 0
                    self.foline[sCode].update({})
                    self.lr=0

                elif realp/self.jango_dict[sCode]['매입단가']-1 > self.ij:
                    self.foline[sCode].update({'1':((self.lr/self.jango_dict[sCode]['매입단가']-1)*self.oneline+1)*self.jango_dict[sCode]['매입단가']})
                    self.foline[sCode].update({'2':((self.lr/self.jango_dict[sCode]['매입단가']-1)*self.twoline+1)*self.jango_dict[sCode]['매입단가']})
                    self.foline[sCode].update({'3':((self.lr/self.jango_dict[sCode]['매입단가']-1)*self.threeline+1)*self.jango_dict[sCode]['매입단가']})
                    
                elif realp/self.jango_dict[sCode]['매입단가']-1 > self.ij2 and realp/self.jango_dict[sCode]['매입단가']-1 < self.ij:
                    self.foline[sCode].update({'3':((self.lr/self.jango_dict[sCode]['매입단가']-1)*self.threeline+1)*self.jango_dict[sCode]['매입단가']})
                    self.foline[sCode].update({'s':4})

                if self.foline[sCode]['1'] != 0:
                    if self.foline[sCode]['s'] == 0 and self.foline[sCode]['1'] > realp:
                    # if self.foline[sCode]['1'] > realp:
                        bs = self.jango_dict[sCode]['주문가능수량']
                        gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['익절매도', '0101', self.account_num, sCode, 1, 1, '3', int(bs/2), 0, ""])
                        print('1차 익절매도',self.portfolio_stock_dict,self.foline)     
                        self.jango_dict[sCode]['주문가능수량'] = bs - int(bs/2)
                        # self.foline[sCode].update({'1':0})
                        self.foline[sCode].update({'s':1})
                        # print(self.foline[sCode])

                    elif self.foline[sCode]['s'] == 1 and self.foline[sCode]['2'] > realp:
                        bs = self.jango_dict[sCode]['주문가능수량']
                        gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['익절매도', '0101', self.account_num, sCode, 1, 1, '3', int(bs/2), 0, ""])
                        print('2차 익절매도',self.portfolio_stock_dict,self.foline)     
                        self.jango_dict[sCode]['주문가능수량'] = bs - int(bs/2)
                        # self.foline[sCode].update({'2':0})
                        self.foline[sCode].update({'s':2})
                        # print(self.foline[sCode])

                    elif self.foline[sCode]['s'] == 2 and self.foline[sCode]['3'] > realp:
                        bs = self.jango_dict[sCode]['주문가능수량']
                        gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['익절매도', '0101', self.account_num, sCode, 1, 1, '3', bs, 0, ""])
                        print('3차 익절매도',self.portfolio_stock_dict,self.foline)     
                        self.jango_dict[sCode]['주문가능수량'] = 0
                        # self.foline[sCode].update({'3':0})
                        self.foline[sCode].update({'1':0,'2':0,'3':0,'s':0})
                        print(self.foline[sCode])
                        self.now_cp['call'] = 0
                        self.now_cp['put'] = 0
                        self.lr=0

                elif self.foline[sCode]['s'] == 4 and self.foline[sCode]['3'] > realp:
                    bs = self.jango_dict[sCode]['주문가능수량']
                    gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['익절매도', '0101', self.account_num, sCode, 1, 1, '3', bs, 0, ""])
                    print('선행 익절매도',self.portfolio_stock_dict,self.foline)     
                    self.jango_dict[sCode]['주문가능수량'] = 0
                    # self.foline[sCode].update({'3':0})
                    self.foline[sCode].update({'1':0,'2':0,'3':0,'s':0})
                    print(self.foline[sCode])
                    self.now_cp['call'] = 0
                    self.now_cp['put'] = 0
                    self.lr=0

    def chejan_slot(self,sGubun,nItemCnt,sFIdList):
        if int(sGubun) == 0:
            # account_num = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['계좌번호'])
            sCode = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['종목코드'])
            # stock_name = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['종목명'])
            # stock_name = stock_name.strip()
            # origin_order_number = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['원주문번호'])
            order_number = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문번호'])
            order_status = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문상태'])
            # print(order_status)
            order_quan = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문수량'])
            order_quan = int(order_quan)
            # order_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문가격'])
            # order_price = float(order_price)
            not_chegual_quan = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['미체결수량'])
            not_chegual_quan = int(not_chegual_quan)
            # order_gubun = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문구분'])
            # order_gubun = order_gubun.strip().lstrip('+').lstrip('-') 
            # chegual_time_str = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문/체결시간'])
            # chegual_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['체결가'])
            # if chegual_price == '':
            #     chegual_price = 0
            # else:
            #     chegual_price = float(chegual_price)
            chegual_quantity = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['체결량'])
            if chegual_quantity == '':
                chegual_quantity = 0
            else:
                chegual_quantity = int(chegual_quantity)
            # current_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['현재가'])
            # current_price = abs(float(current_price))
            # first_sell_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['(최우선)매도호가'])
            # first_sell_price = abs(float(first_sell_price))
            # first_buy_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['(최우선)매수호가'])
            # first_buy_price = abs(float(first_buy_price))

            if sCode not in self.not_account_stock_dict.keys():
                self.not_account_stock_dict.update({sCode:{}})
            # self.not_account_stock_dict[order_number].update({'종목코드':sCode})
            self.not_account_stock_dict[sCode].update({'주문번호':order_number})
            # self.not_account_stock_dict[order_number].update({'종목명':stock_name})
            self.not_account_stock_dict[sCode].update({'주문상태':order_status})
            self.not_account_stock_dict[sCode].update({'주문수량':order_quan})
            # self.not_account_stock_dict[order_number].update({'주문가격':order_price})
            self.not_account_stock_dict[sCode].update({'미체결수량':not_chegual_quan})
            # self.not_account_stock_dict[order_number].update({'원주문번호':origin_order_number})
            # self.not_account_stock_dict[order_number].update({'주문구분':order_gubun})
            # self.not_account_stock_dict[order_number].update({'주문/체결시간':chegual_time_str})
            # self.not_account_stock_dict[order_number].update({'체결가':chegual_price})
            # self.not_account_stock_dict[sCode].update({'체결량':chegual_quantity})
            # self.not_account_stock_dict[order_number].update({'현재가':current_price})
            # self.not_account_stock_dict[order_number].update({'(최우선)매도호가':first_sell_price})
            # self.not_account_stock_dict[order_number].update({'(최우선)매수호가':first_buy_price})
            if order_quan == chegual_quantity:
                del self.not_account_stock_dict[sCode]
            # print(self.not_account_stock_dict)

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
                self.dict.append(sCode)
                self.foline[sCode] = {'1':0,'2':0,'3':0,'s':0}
                screen_num = 4000
                fids = self.realType.REALTYPE['옵션호가잔량']['호가시간']
                self.dynamicCall('SetRealReg(QString, QString, QString, QString)', screen_num, sCode, fids, '1')
                print('실시간 등록 코드: %s, 스크린번호: %s, fid번호: %s' % (sCode,screen_num,20))
            if like_quan == 0:
                del self.jango_dict[sCode]
                # self.dynamicCall('SetRealRemove(QString, QString)', self.portfolio_stock_dict[sCode]['스크린번호'],sCode)