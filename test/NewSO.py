import sys 
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
import pythoncom

# from pykiwoom.kiwoom import *

# kiwoom = Kiwoom()
# kiwoom.CommConnect(block=True)

# # 주식계좌
# accounts = kiwoom.GetLoginInfo("ACCNO")
# stock_account = accounts[0]
# print(stock_account)
# # 삼성전자, 10주, 시장가주문 매수
# a=kiwoom.SendOrderFO("시장가", "0101", stock_account, "301T1282", 1, 2, '3', 1, 0, "")
# print(a)


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        print('start')
        self.get_ocx_instance()
        self.event_slots()
        self.signal_login_commConnect()
       
        # self.OnEventConnect.connect(self.OnEventConnect)
        # self.OnReceiveTrData.connect(self.OnReceiveTrData)

    def get_ocx_instance(self):
        self.setControl('KHOPENAPI.KHOpenAPICtrl.1')

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
    
    def login_slot(self, errCode):
        print(errCode)

    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")

    def OnReceiveTrData(self, screen, rqname, trcode, record, next):
        print(screen, rqname, trcode, record, next)
        # per = self.GetCommData(trcode, rqname, 0, "콜옵션행사가")
        pd = []
        for i in range (50, 70):
            pbr = self.GetCommData(trcode, rqname, i, "행사가")
            pd.append(pbr)
        print(pd)

    def GetMasterCodeName(self, code):
        name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return name

    def OnEventConnect(self, err_code):
        self.login = True

    def SetInputValue(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def CommRqData(self, rqname, trcode, next, screen):
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen)

    def GetCommData(self, trcode, rqname, index, item):
        data = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, index, item)
        return data.strip()


# class MyWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()

#         self.kiwoom = Kiwoom()
#         self.kiwoom.CommConnect()

#         # tr request 
#         self.kiwoom.SetInputValue("종목코드", "10100000")
#         self.kiwoom.SetInputValue("만기년월", "202301")
#         self.kiwoom.CommRqData("call", "opt50004", 0, "0101")
#         self.kiwoom.CommRqData("put", "opt50064", 0, "0101")


if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = MyWindow()
#     window.show()
#     app.exec_()

    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    app.exec_()