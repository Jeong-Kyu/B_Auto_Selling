# import schedule
# import time

# from pykiwoom.kiwoom import *
# import pprint


# def start():

#     # 로그인
#     kiwoom = Kiwoom()
#     kiwoom.CommConnect(block=True)
#     print('1')
#     # 조건식을 PC로 다운로드
#     kiwoom.GetConditionLoad()
#     print('2')

#     # 전체 조건식 리스트 얻기
#     conditions = kiwoom.GetConditionNameList()
#     print('3')

#     # 0번 조건식에 해당하는 종목 리스트 출력
#     condition_index = conditions[0][0]
#     condition_name = conditions[0][1]
#     codes = kiwoom.SendCondition("0101", condition_name, condition_index, 0)
#     print(conditions)
#     print(codes)

# #     # 주식계좌
# #     accounts = kiwoom.GetLoginInfo("ACCNO")
# #     stock_account = accounts[1]
# #     print(stock_account)
# #     # 삼성전자, 10주, 시장가주문 매수
# #     for i in codes:
# #         kiwoom.SendOrder("시장가매수", "0101", stock_account, 1, i, 10, 0, "03", "")
# #     print('.')

# schedule.every(1).seconds.do(start)

# while True:
#     schedule.run_pending()
#     time.sleep(1)



import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
import os

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle("Kiwoom 실시간 조건식 테스트")

        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveConditionVer.connect(self._handler_condition_load)
        self.ocx.OnReceiveRealCondition.connect(self._handler_real_condition)
        self.CommConnect()

        btn1 = QPushButton("condition down")
        btn2 = QPushButton("condition list")
        btn3 = QPushButton("condition send")

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(btn1)
        layout.addWidget(btn2)
        layout.addWidget(btn3)
        self.setCentralWidget(widget)

        # event
        btn1.clicked.connect(self.GetConditionLoad)
        btn2.clicked.connect(self.GetConditionNameList)
        btn3.clicked.connect(self.send_condition)

    def CommConnect(self):
        self.ocx.dynamicCall("CommConnect()")

    def _handler_login(self, err_code):
        print("handler login", err_code)

    def _handler_condition_load(self, ret, msg):
        print("handler condition load", ret, msg)

    def _handler_real_condition(self, code, type, cond_name, cond_index):
        current_price = self.ocx.dynamicCall('GetCommData(QString, QString, int, QString)', 10, '주식체결', 0, '현재가')
        f = open('condition_stock.txt','a')
        f.write(f"{code} {current_price}\n")
        f.close
        print(cond_name, code, type)

        
    def GetCommRealData(self):
        self.ocx.dynamicCall("GetCommRealData()")


    def GetConditionLoad(self):
        self.ocx.dynamicCall("GetConditionLoad()")

    def GetConditionNameList(self):
        data = self.ocx.dynamicCall("GetConditionNameList()")
        conditions = data.split(";")[:-1]
        for condition in conditions:
            index, name = condition.split('^')
            print(index, name)

    def SendCondition(self, screen, cond_name, cond_index, search):
        ret = self.ocx.dynamicCall("SendCondition(QString, QString, int, int)", screen, cond_name, cond_index, search)
        print(ret)
    def SendConditionStop(self, screen, cond_name, cond_index):
        ret = self.ocx.dynamicCall("SendConditionStop(QString, QString, int)", screen, cond_name, cond_index)

    def send_condition(self):
        k = self.SendCondition("100", "test", "001", 1)
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()