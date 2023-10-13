from pykiwoom.kiwoom import *

kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)

kospi = kiwoom.GetCodeListByMarket('0')
kosdaq = kiwoom.GetCodeListByMarket('10')
etf = kiwoom.GetCodeListByMarket('8')

print(len(kospi), kospi)
print(len(kosdaq), kosdaq)
print(len(etf), etf)

# 파라미터	 시장
# "0"	    코스피
# "3"	    ELW
# "4"	    뮤추얼펀드
# "5"	    신주인수권
# "6"	    리츠
# "8"	    ETF
# "9"	    하이얼펀드
# "10"	    코스닥
# "30"	    K-OTC
# "50"	    코넥스