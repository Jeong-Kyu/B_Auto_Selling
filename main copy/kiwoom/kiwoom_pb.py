import os
import sys
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
from config.kiwoomType import *
import logging
import time
import operator

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
        self.screen_cpprice_info = '6000'
        self.account_select = 0
        self.use_money_percent = 0.1

        self.dict=[]
        self.pivot_dict = {}
        self.not_account_stock_dict={}
        self.jango_dict = {}

        self.code_count = 2  # 종목 최대 개수
        self.c_code = ['0' for i in range(self.code_count)]
        self.p_code = ['Z' for i in range(self.code_count)]

        self.level=-1
        self.status=0
        self.start=0

        self.start_time = 84501 # 시작 시간
        self.end_time = 151800  # 끝 시간

        self.msml = 1000000 # 종목당 매매 금액
        self.tic1 = 1 # 초기 방향성 매매 tic
        self.tic2 = 1 # 부분매도/반대매수 tic
        self.tic3 = 2 # 전량매도 tic 



        ##시작##
        self.get_ocx_instance()
        self.event_slots()
        self.real_event_slots()

        self.signal_login_commConnect()
        self.get_account_info()

        self.detail_account_info()
        self.having_check_info()

        self.having_price_info(yyyymm=202406)
        self.having_pivot_info(code='101V6000')
        
        self.dynamicCall('SetRealReg(QString, QString, QString, QString)', self.screen_start_stop_real, '', self.realType.REALTYPE['장시작시간']['장운영구분'], '0')
        screen_num = 4000
        fids = self.realType.REALTYPE['옵션호가잔량']['호가시간']
        self.dynamicCall('SetRealReg(QString, QString, QString, QString)', screen_num, '101V6000', fids, '1')
        print('실시간 등록 코드: %s, 스크린번호: %s, fid번호: %s' % ('101V6000',screen_num,fids))
    
        # for code in self.dict:
        #     screen_num = 4000
        #     fids = self.realType.REALTYPE['옵션호가잔량']['호가시간']
        #     self.dynamicCall('SetRealReg(QString, QString, QString, QString)', screen_num, code, fids, '1')
        #     print('실시간 등록 코드: %s, 스크린번호: %s, fid번호: %s' % (code,screen_num,fids))
    
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
        if sRQName == '선옵예탁금및증거금조회요청':
            deposit = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0, '주문가능총액')
            print('예탁금 : %s' % int(deposit))
            self.use_money = int(deposit) * self.use_money_percent
            # self.use_money = self.use_money / 4
            ok_deposit = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0, '인출가능총액')
            print('출금가능금액 : %s' % int(ok_deposit))

            self.detail_account_info_event_loop.exit()

        if sRQName == '계좌평가현황요청':
            h = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0, '출력건수')
            for i in range(int(h)):
                h_code = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '종목코드')
                h_name = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '종목명')
                h_count = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '보유수량')
                self.dict.append(h_code.strip()[1:])
                self.line_dict.update({h_code.strip()[1:]:{}})
            print(self.dict)
            self.real_price_check_event_loop.exit()

        if sRQName == '선옵일자별체결요청':
            self.sub = []
            h_price = abs(float(self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 1, '고가')))
            l_price = abs(float(self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 1, '저가')))
            e_price = abs(float(self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 1, '현재가n')))
            pivot = (h_price+l_price+e_price)/3
            one_d = (pivot*2)-l_price
            two_d = pivot+(h_price-l_price)
            one_a = (pivot*2)-h_price
            two_a = pivot-(h_price-l_price)
            self.pivot_dict.update({"2차저항":two_d,"1차저항":one_d,"기준선":pivot,"1차지지":one_a,"2차지지":two_a,"현재가":0,"중심":0})
            self.Pivot_event_loop.exit()

        if sRQName == '복수종목결제월별시세요청':
            self.c_code_count = [2 for i in range(self.code_count)]
            self.p_code_count = [2 for i in range(self.code_count)]
            for i in range(100):
                ch = abs(float(self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '현재가')))
                ph = abs(float(self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '풋_현재가')))
                if ch-0.5>0 and self.c_code_count[0]>ch:
                    self.c_code_count[0] = ch
                    self.c_code_count.sort(reverse=True)    
                    self.c_code[0] = str(self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '종목코드')).strip()
                    self.c_code.sort()  
                if ph-0.5>0 and self.p_code_count[0]>ph:
                    self.p_code_count[0] = ph
                    self.p_code_count.sort(reverse=True)
                    self.p_code[0] = str(self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, i, '풋_종목코드')).strip()    
                    self.p_code.sort(reverse=True) 
            while 2 in self.c_code_count:
                self.c_code_count.remove(2)
            while 2 in self.p_code_count:
                self.p_code_count.remove(2)
            while '0' in self.c_code:
                self.c_code.remove('0')
            while 'Z' in self.p_code:
                self.p_code.remove('Z')     
            print(self.c_code_count,self.p_code_count)                
            print(self.c_code,self.p_code)
            self.cpprive_event_loop.exit()

    def get_account_info(self):
        account_list = self.dynamicCall('GetLogininfo(String)','ACCNO')
        self.account_num = account_list.split(';')[self.account_select]
        print('전체 계좌번호 %s' %account_list)
        print('나의 보유 계좌번호 %s' %self.account_num)

    def detail_account_info(self):
        print('선옵예탁금및증거금조회요청 요청')
        self.dynamicCall('SetInputValue(String, String)','계좌번호', self.account_num)
        self.dynamicCall('SetInputValue(String, String)','비밀번호', '0000')
        self.dynamicCall('SetInputValue(String, String)','비밀번호입력매체구분', '00')
        # self.dynamicCall('SetInputValue(String, String)','조회구분', '2')    
        self.dynamicCall('CommRqData(String, String, int, String)', '선옵예탁금및증거금조회요청', 'opw20010', '0', self.screen_my_info)
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

    def having_pivot_info(self, code):
        print('Pivot작업')
        self.dynamicCall('SetInputValue(String, String)','종목코드', code)
        self.dynamicCall('CommRqData(String, String, int, String)','선옵일자별체결요청',"opt50002","0",self.screen_pivot_info)
        self.Pivot_event_loop = QEventLoop()
        self.Pivot_event_loop.exec_()

    def having_price_info(self, yyyymm):
        print('콜풋가격작업')
        self.dynamicCall('SetInputValue(String, String)','만기년월', yyyymm)
        a=self.dynamicCall('CommRqData(String, String, int, String)','복수종목결제월별시세요청',"opt50020","0",self.screen_cpprice_info)
        self.cpprive_event_loop = QEventLoop()
        self.cpprive_event_loop.exec_()

    def realdata_slot(self, sCode, sRealType, sRealData):
        # if sRealType == '장시작시간':
        #     fid = self.realType.REALTYPE[sRealType]['장운영구분']
        #     value = self.dynamicCall('GetCommRealData(QString, int)', sCode, fid)

        #     if value == '0':
        #         print('장 시작 전')
        #     elif value == '3':
        #         print('장 시작')
        #     elif value == '2':
        #         print('장 종료, 동시호가로 넘어감')
        #     elif value == '4':
        #         print('3시30분 장 종료')

        if sRealType == '선물시세':
            t = abs(float(self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['체결시간'])))
            startp = abs(float(self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['시가'])))
            realp = abs(float(self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['현재가'])))
            highp = abs(float(self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['고가'])))
            lowp = abs(float(self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['저가'])))
            self.pivot_dict.update({"현재가":realp}) #,"중심":(highp+lowp)/2"고점":highp,"저점":lowp          
            if self.status != 0 and self.status != 1:
                self.pivot_dict.update({"중심":(highp+lowp)/2})   
            pivot_dict_copy=self.pivot_dict.copy()
            d1 = sorted(pivot_dict_copy.items(), key=operator.itemgetter(1))
            now_level=d1.index(('현재가',realp))

            if self.status==0:
                if t>self.start_time:
                    self.start = realp
                    self.status = 1
                    print(self.start)
            elif self.status == 1:
                if self.start-0.05*self.tic1 > realp:
                    i=0
                    for p_code in self.p_code:
                        if self.not_account_stock_dict.get(p_code)==None:
                            if self.jango_dict.get(p_code)==None or self.jango_dict[p_code]['매수매도'] == 1:
                                gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['풋매수', '0101', self.account_num, p_code, 1, 2, '3', int(self.msml/250000/self.p_code_count[i]), 0, ""])
                                if gr ==0:
                                    print("풋매수 성공")
                                    if p_code not in self.not_account_stock_dict.keys():
                                        self.not_account_stock_dict.update({p_code:{"매수매도":2}})
                                    self.th = "p"
                                else:
                                    print(gr)
                                    print("풋매수 실패")
                        else:
                            if self.not_account_stock_dict[p_code]['매수매도'] == 1:
                                gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['풋매수', '0101', self.account_num, p_code, 1, 2, '3', int(self.msml/250000/self.p_code_count[i]), 0, ""])
                                if gr ==0:
                                    print("풋매수 성공")
                                    if p_code not in self.not_account_stock_dict.keys():
                                        self.not_account_stock_dict.update({p_code:{"매수매도":2}})
                                    self.th = "p"
                                else:
                                    print(gr)
                                    print("풋매수 실패")

                    for c_code in self.c_code:
                        if self.jango_dict.get(c_code)!=None and self.jango_dict[c_code]['주문가능수량'] != 0:
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['콜매도', '0101', self.account_num, c_code, 1, 1, '3', self.jango_dict[c_code]['주문가능수량'], 0, ""])
                            if gr ==0:
                                print("콜매도 성공")
                            else:
                                print(gr)
                                print("콜매도 실패")
                        i+=1
                elif self.start+0.05*self.tic1 < realp:
                    i=0
                    for c_code in self.c_code:
                        if self.not_account_stock_dict.get(c_code)==None:
                            if self.jango_dict.get(c_code)==None or self.jango_dict[c_code]['매수매도'] == 1:
                                gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['콜매수', '0101', self.account_num, c_code, 1, 2, '3', int(self.msml/250000/self.c_code_count[i]), 0, ""])
                                if gr ==0:
                                    print("콜매수 성공")
                                    if c_code not in self.not_account_stock_dict.keys():
                                        self.not_account_stock_dict.update({c_code:{"매수매도":2}})
                                    self.th = "c"
                                else:
                                    print(gr)
                                    print("콜매수 실패")
                        else:
                            if self.not_account_stock_dict[c_code]['매수매도'] == 1:
                                gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['콜매수', '0101', self.account_num, c_code, 1, 2, '3', int(self.msml/250000/self.c_code_count[i]), 0, ""])
                                if gr ==0:
                                    print("콜매수 성공")
                                    if c_code not in self.not_account_stock_dict.keys():
                                        self.not_account_stock_dict.update({c_code:{"매수매도":2}})
                                    self.th = "c"
                                else:
                                    print(gr)
                                    print("콜매수 실패")

                    for p_code in self.p_code:
                        if self.jango_dict.get(p_code)!=None and self.jango_dict[p_code]['주문가능수량'] != 0:
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['풋매도', '0101', self.account_num, p_code, 1, 1, '3', self.jango_dict[p_code]['주문가능수량'], 0, ""])
                            if gr ==0:
                                print("풋매도 성공")
                            else:
                                print(gr)
                                print("풋매도 실패")
                        i+=1
                if self.jango_dict != {}:
                    if self.level == -1:
                        self.level = now_level
                    elif self.level != now_level:
                        self.pivot_dict.update({"중심":(highp+lowp)/2})   
                        pivot_dict_copy=self.pivot_dict.copy()
                        d1 = sorted(pivot_dict_copy.items(), key=operator.itemgetter(1))
                        now_level=d1.index(('현재가',realp))

                        self.level = now_level
                        if self.level == len(d1)-1:
                            self.up=None
                        else:
                            self.up=d1[self.level+1][1]
                        if self.level == 0:
                            self.down=None
                        else:
                            self.down=d1[self.level-1][1]
                        self.status = 2

                        print(self.level)
                        print(self.up, self.down)        

            elif self.status == 2:
                if self.th == "c":
                    if self.down-0.05*self.tic2 > realp:
                        # print('분할매도')
                        self.status = 3
                        print(self.jango_dict)
                        for c_code in self.c_code:
                            if self.jango_dict.get(c_code)!=None:
                                gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['분할매도', '0101', self.account_num, c_code, 1, 1, '3', int(self.jango_dict[c_code]['주문가능수량']/2), 0, ""])
                                if gr ==0:
                                    print("분할매도 성공")
                                else:
                                    print(gr)
                                    print("분할매도 실패")
                        i=0
                        for p_code in self.p_code:
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['반대매수', '0101', self.account_num, p_code, 1, 2, '3', int(self.msml/250000/self.p_code_count[i]), 0, ""])
                            if gr ==0:
                                print("반대매수 성공")
                                self.k=1
                            else:
                                print(gr)
                                print("반대매수 실패")
                            i+=1
                    elif self.up == None:
                        pass
                    elif self.up < realp:
                        self.level = now_level
                        if self.level == len(d1)-1:
                            self.up=None
                        else:
                            self.up=d1[self.level+1][1]
                        if self.level == 0:
                            self.down=None
                        else:
                            self.down=d1[self.level-1][1]
                        print(self.up, self.down) 
                elif self.th == "p":
                    if self.up+0.05*self.tic2 < realp:
                        # print('분할매도')
                        self.status = 3
                        print(self.jango_dict)
                        for p_code in self.p_code:
                            if self.jango_dict.get(p_code)!=None:
                                gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['분할매도', '0101', self.account_num, p_code, 1, 1, '3', int(self.jango_dict[p_code]['주문가능수량']/2), 0, ""])
                                if gr ==0:
                                    print("분할매도 성공")
                                else:
                                    print(gr)
                                    print("분할매도 실패")
                        i=0
                        for c_code in self.c_code:
                            gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['반대매수', '0101', self.account_num, c_code, 1, 2, '3', int(self.msml/250000/self.c_code_count[i]), 0, ""])
                            if gr ==0:
                                print("반대매수 성공")
                                self.k=1
                            else:
                                print(gr)
                                print("반대매수 실패")
                            i+=1
                    elif self.down == None:
                        pass
                    elif self.down > realp:
                        self.level = now_level
                        if self.level == len(d1)-1:
                            self.up=None
                        else:
                            self.up=d1[self.level+1][1]
                        if self.level == 0:
                            self.down=None
                        else:
                            self.down=d1[self.level-1][1]
                        print(self.up, self.down)      

            elif self.status == 3:
                if self.th == "c":
                    if self.down-0.05*self.tic3 > realp:
                        # print('전량매도')
                        print(self.jango_dict)
                        for c_code in self.c_code:
                            if self.jango_dict.get(c_code)!=None and self.jango_dict[c_code]['주문가능수량'] != 0:
                                gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['전량매도', '0101', self.account_num, c_code, 1, 1, '3', int(self.jango_dict[c_code]['주문가능수량']), 0, ""])
                                if gr ==0:
                                    print("전량매도 성공")
                                else:
                                    print(gr)
                                    print("전량매도 실패")
                        self.level = now_level
                        if self.level == len(d1)-1:
                            self.up=None
                        else:
                            self.up=d1[self.level+1][1]
                        if self.level == 0:
                            self.down=None
                        else:
                            self.down=d1[self.level-1][1]
                        print(self.up, self.down)    
                        self.th == "p"
                        self.status = 2
                    elif self.down < realp:
                        for p_code in self.p_code:
                            if self.k == 1:
                                if self.jango_dict.get(p_code)!=None and self.jango_dict[p_code]['주문가능수량'] != 0:
                                    gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['반대전량매도', '0101', self.account_num, p_code, 1, 1, '3', int(self.jango_dict[p_code]['주문가능수량']), 0, ""])
                                    if gr ==0:
                                        print("반대전량매도 성공")
                                    else:
                                        print(gr)
                                        print("반대전량매도 실패")
                                elif self.not_account_stock_dict.get(p_code)!=None and self.not_account_stock_dict[p_code]['매수매도'] == 2:
                                    gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['반대전량매도', '0101', self.account_num, p_code, 1, 1, '3', int(self.jango_dict[p_code]['주문가능수량']), 0, ""])
                                    if gr ==0:
                                        self.k=0
                                        print("반대전량매도 성공")
                                    else:
                                        print(gr)
                                        print("반대전량매도 실패")
                        self.k=0

                elif self.th == "p":
                    if self.up+0.05*self.tic3 < realp:
                        # print('전량매도')
                        print(self.jango_dict)
                        for p_code in self.p_code:
                            if self.jango_dict.get(p_code)!=None and self.jango_dict[p_code]['주문가능수량'] != 0:
                                gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['전량매도', '0101', self.account_num, p_code, 1, 1, '3', int(self.jango_dict[p_code]['주문가능수량']), 0, ""])
                                if gr ==0:
                                    print("전량매도 성공")
                                else:
                                    print(gr)
                                    print("전량매도 실패")
                        self.level = now_level
                        if self.level == len(d1)-1:
                            self.up=None
                        else:
                            self.up=d1[self.level+1][1]
                        if self.level == 0:
                            self.down=None
                        else:
                            self.down=d1[self.level-1][1]
                        print(self.up, self.down)    
                        self.th == "c"
                        self.status = 2
                    elif self.up > realp:
                        for c_code in self.c_code:
                            if self.k == 1:
                                if self.jango_dict.get(c_code)!=None and self.jango_dict[c_code]['주문가능수량'] != 0:
                                    gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['반대전량매도', '0101', self.account_num, c_code, 1, 1, '3', int(self.jango_dict[c_code]['주문가능수량']), 0, ""])
                                    if gr ==0:
                                        self.k=0
                                        print("반대전량매도 성공")
                                    else:
                                        print(gr)
                                        print("반대전량매도 실패")
                                elif self.not_account_stock_dict.get(c_code)!=None and self.not_account_stock_dict[c_code]['매수매도'] == 2:
                                    gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['반대전량매도', '0101', self.account_num, c_code, 1, 1, '3', int(self.jango_dict[c_code]['주문가능수량']), 0, ""])
                                    if gr ==0:
                                        self.k=0
                                        print("반대전량매도 성공")
                                    else:
                                        print(gr)
                                        print("반대전량매도 실패")
                        self.k=0
            if t>self.end_time:
                codes = list(self.jango_dict.keys())
                for code in codes:
                    gr = self.dynamicCall('SendOrderFO(QString, QString, QString, QString, int, int, QString, int, int, QString)',['최종매도', '0101', self.account_num, code, 1, 1, '3', int(self.jango_dict[code]['주문가능수량']), 0, ""])
                    if gr ==0:
                        print("최종매도 성공")
                    else:
                        print(gr)
                        print("최종매도 실패")
                sys.exit()
    def chejan_slot(self,sGubun,nItemCnt,sFIdList):
        if int(sGubun) == 0:
            sCode = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['종목코드'])[:]
            order_number = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문번호'])
            order_status = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문상태'])
            msmd = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['매도수구분'])
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
            self.not_account_stock_dict[sCode].update({'매수매도':msmd})
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
            msmd = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['매도매수구분'])
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
            self.jango_dict[sCode].update({'매수매도':msmd})
            self.jango_dict[sCode].update({'보유수량':stock_quan})
            self.jango_dict[sCode].update({'주문가능수량':like_quan})
            self.jango_dict[sCode].update({'손익율':buy_price})
            self.jango_dict[sCode].update({'총매입가':total_buy_price})
            self.jango_dict[sCode].update({'매입단가':buy_p_price})
            print(self.not_account_stock_dict)
            print(self.jango_dict)

            if like_quan == 0:
                del self.jango_dict[sCode]

