from pykiwoom.kiwoom import *

kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)

#상장주식수
stock_cnt = kiwoom.GetMasterListedStockCnt("005930")
print("삼성전자 상장주식수: ", stock_cnt)
#감리구분
감리구분 = kiwoom.GetMasterConstruction("005930")
print(감리구분)
#상장일
상장일 = kiwoom.GetMasterListedStockDate("005930")
print(상장일)
print(type(상장일))        # datetime.datetime 객체
#전일가
전일가 = kiwoom.GetMasterLastPrice("005930")
print(int(전일가))
print(type(전일가))
#종목상태
종목상태 = kiwoom.GetMasterStockState("005930")
print(종목상태)