# from pykiwoom.kiwoom import *
# import pprint

# kiwoom = Kiwoom()
# kiwoom.CommConnect(block=True)

# group = kiwoom.GetThemeGroupList(1)
# pprint.pprint(group)

# from pykiwoom.kiwoom import *
# import pprint

# kiwoom = Kiwoom()
# kiwoom.CommConnect(block=True)

# tickers = kiwoom.GetThemeGroupCode('141')
# print(tickers)

from pykiwoom.kiwoom import *
import pprint

kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)

tickers = kiwoom.GetThemeGroupCode('330')
for ticker in tickers:
    name = kiwoom.GetMasterCodeName(ticker)
    print(ticker, name)