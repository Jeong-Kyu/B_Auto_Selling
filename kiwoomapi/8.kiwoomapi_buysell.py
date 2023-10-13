from pykiwoom.kiwoom import *

kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)

# 주식계좌
accounts = kiwoom.GetLoginInfo("ACCNO")
stock_account = accounts[0]
print(stock_account)
stock0_account = accounts[1]
print(stock0_account)

# 삼성전자, 10주, 시장가주문 매수
a=kiwoom.SendOrder("시장가", "0101", stock_account, "309B5317", 1, 2, '3', 1, 0, "")
print(a)
# a=kiwoom.SendOrderFO("시장가", "0101", stock_account, "301T2315", 2, 2, '3', 4, 0, "")309B5317
# print(a)

# from pykiwoom.kiwoom import *

# kiwoom = Kiwoom()
# kiwoom.CommConnect(block=True)

# # 주식계좌
# accounts = kiwoom.GetLoginInfo("ACCNO")
# stock_account = accounts[0]

# # 삼성전자, 10주, 시장가주문 매도
# b = kiwoom.SendOrder("시장가매도", "0101", stock0_account, 2, "005930", 1, 0, "03", "")
# print(b)
#           SendOrderFO(
#           BSTR sRQName,     // 사용자 구분명
#           BSTR sScreenNo,   // 화면번호
#           BSTR sAccNo,      // 계좌번호 10자리 
#           BSTR sCode,       // 종목코드 
#           LONG lOrdKind,    // 주문종류 1:신규매매, 2:정정, 3:취소
#           BSTR sSlbyTp,     // 매매구분	1: 매도, 2:매수
#           BSTR sOrdTp,      // 거래구분(혹은 호가구분)은 아래 참고
#           LONG lQty,        // 주문수량 
#           BSTR sPrice,      // 주문가격 
#           BSTR sOrgOrdNo    // 원주문번호
#           )