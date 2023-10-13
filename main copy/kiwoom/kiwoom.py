import os
import sys
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
from config.kiwoomType import *
import logging
import copy

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self.realType = RealType()

        print('kiwoom 클래스 입니다.')
        ## 변수 ##
        self.screen_start_stop_real = '1000'
        self.screen_my_info = '2000'
        self.screen_price_info = '3000'
        self.screen_check = 1
        self.account_select = 0
        self.use_money_percent = 1
        self.cnt = 0

        ###############################################################
        self.target_call_price = 330       # 콜행사가
        self.target_call_price_p = 0.75   # 콜가격
        self.target_put_price = 302        # 풋행사가
        self.target_put_price_p = 1.02  # 풋가격
        self.sjmd = -0.2                   # 손절
        self.ijmd = 0.2                    # 익절
        self.one_line = 0.6                # 1차라인
        ###############################################################

        self.target_price = {f'201T3{self.target_call_price}':self.target_call_price_p,f'301T3{self.target_put_price}':self.target_put_price_p}
        self.dict = [f'201T3{self.target_call_price}',f'301T3{self.target_put_price}']
        print('목표가:%s, call:%s, put:%s' % (self.target_price,self.target_call_price,self.target_put_price))
        print(self.dict)
        self.target_count = 0
        ##딕셔너리##
        self.cp_present_price={}
        self.portfolio_stock_dict ={f'201T3{self.target_call_price}':{"현재가":0},f'301T3{self.target_put_price}':{"현재가":0}}#005930 201T1302 301T1302 10100000
        self.foline = {f'201T3{self.target_call_price}':{'1':0,'2':0,'s':0}, f'301T3{self.target_put_price}':{'1':0,'2':0,'s':0}}
        
        self.not_account_stock_dict = {}
        self.jango_dict = {}
        self.now_cp = {'call':0, 'put':0}
        self.lr=0

        self.get_ocx_instance()
        self.event_slots()
        self.real_event_slots()

        self.signal_login_commConnect()
        self.get_account_info()
        self.detail_account_info()

        self.dynamicCall('SetRealReg(QString, QString, QString, QString)', self.screen_start_stop_real, '', self.realType.REALTYPE['장시작시간']['장운영구분'], '0')
        
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

    def real_event_slots(self):
        self.OnReceiveRealData.connect(self.realdata_slot)
        self.OnReceiveChejanData.connect(self.chejan_slot)

    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

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

    def realdata_slot(self, sCode, sRealType, sRealData):
        
        if sRealType == '장시작시간':
            fid = self.realType.REALTYPE[sRealType]['장운영구분']
            value = self.dynamicCall('GetCommRealData(QString, int)', sCode, fid)

            if value == '0':
                print('장 시작 전')
            elif value == '3':
                print('장 시작')
                if sCode == f'201T3{self.target_call_price}':
                    self.target_call_price_p = abs(float(self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['현재가'])))
                elif sCode == f'301T3{self.target_put_price}':
                    self.target_put_price_p = abs(float(self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['현재가'])))
                print(self.target_call_price_p, self.target_put_price_p)
            elif value == '2':
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

        elif sRealType == '옵션시세':
            if sCode == f'201T3{self.target_call_price}':
                self.cnt += 1
                price_info = int(self.screen_price_info)
                if (self.cnt % 50) == 0:
                    price_info += 1 
                    self.screen_price_info  = str(price_info)
                self.hjg = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['현재가'])#+,-
                self.hjg = abs(float(self.hjg))
                l = self.portfolio_stock_dict[sCode]['현재가']
                self.portfolio_stock_dict[sCode].update({"현재가":self.hjg})
                self.portfolio_stock_dict[sCode].update({"이전 현재가":l})
                # print(self.portfolio_stock_dict)
                if l == 0:
                    pass
                elif l <= self.target_price[sCode] and self.hjg > self.target_price[sCode]:
                    if int(self.now_cp['call']) == int(self.now_cp['put']) or int(self.now_cp['call']+1) == (int(self.now_cp['put'])):
                        gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['콜매수', self.screen_price_info, self.account_num, f'201T3{int(self.target_call_price)}', 1, 2, '4', 10, 0, ""])
                        self.now_cp.update({'call':(int(self.now_cp['call'])+1)})
                        print(self.now_cp)

                elif l >= self.target_price[sCode] and self.hjg < self.target_price[sCode]:
                    if f'201T3{int(self.target_call_price)}' in self.jango_dict.keys():
                        bs = self.jango_dict[f'201T3{int(self.target_call_price)}']['주문가능수량']
                        gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['콜매도', self.screen_price_info, self.account_num, f'201T3{int(self.target_call_price)}', 1, 1, '3', bs, 0, ""])
                    else:
                        pass
                

            if sCode == f'301T3{self.target_put_price}':
                self.cnt += 1
                price_info = int(self.screen_price_info)
                if (self.cnt % 50) == 0:
                    price_info += 1 
                    self.screen_price_info  = str(price_info)
                self.hjg2 = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['현재가'])#+,-
                self.hjg2 = abs(float(self.hjg2))
                l = self.portfolio_stock_dict[sCode]['현재가']
                self.portfolio_stock_dict[sCode].update({"현재가":self.hjg2})
                self.portfolio_stock_dict[sCode].update({"이전 현재가":l})
                if l == 0:
                    pass
                elif l <= self.target_price[sCode] and self.hjg2 > self.target_price[sCode]:
                    if int(self.now_cp['call']) == int(self.now_cp['put']) or int(self.now_cp['call']) == (int(self.now_cp['put'])+1):
                        gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['풋매수', self.screen_price_info, self.account_num, f'301T3{int(self.target_put_price)}', 1, 2, '4', 10, 0, ""])
                        self.now_cp.update({'put':(int(self.now_cp['put'])+1)})
                        print(self.now_cp)
                elif l >= self.target_price[sCode] and self.hjg2 < self.target_price[sCode]:                        
                    if f'301T3{int(self.target_put_price)}' in self.jango_dict.keys():
                        bs = self.jango_dict[f'301T3{int(self.target_put_price)}']['주문가능수량']
                        gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['풋매도', self.screen_price_info, self.account_num, f'301T3{int(self.target_put_price)}', 1, 1, '3', bs, 0, ""])
                    else:
                        pass

            if sCode in self.jango_dict.keys():
                self.cnt += 1
                price_info = int(self.screen_price_info)
                if (self.cnt % 50) == 0:
                    price_info += 1 
                    self.screen_price_info  = str(price_info)

                realp = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['현재가'])#+,-
                realp = abs(float(realp))
                if self.lr < realp:
                    self.lr = realp

                if realp/self.jango_dict[sCode]['매입단가']-1 < self.sjmd:
                    bs = self.jango_dict[sCode]['주문가능수량']
                    gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['손절매도', self.screen_price_info, self.account_num, sCode, 1, 1, '3', bs, 0, ""])
                    print('손절매도',self.portfolio_stock_dict)     
                    self.jango_dict[sCode]['주문가능수량'] = 0
                    self.foline[sCode].update({})

                elif realp/self.jango_dict[sCode]['매입단가']-1 > self.ijmd:
                    self.foline[sCode].update({'1':((self.lr/self.jango_dict[sCode]['매입단가']-1)*self.one_line+1)*self.jango_dict[sCode]['매입단가']})

                    if self.foline[sCode]['1'] != 0:
                        if self.foline[sCode]['1'] > realp:
                            bs = self.jango_dict[sCode]['주문가능수량']
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['익절매도', self.screen_price_info, self.account_num, sCode, 1, 1, '3', bs, 0, ""])
                            print('1차 익절매도',self.portfolio_stock_dict,self.foline)     
                            self.jango_dict[sCode]['주문가능수량'] = 0
                            self.target_price = self.hjg
                            print(f'기준가 변경 : {self.hjg}')
                            self.foline[sCode].update({'1':0})

    def chejan_slot(self,sGubun,nItemCnt,sFIdList):

        if int(sGubun) == 4:
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
            print(self.jango_dict)
            
            if like_quan == 0:
                del self.jango_dict[sCode]