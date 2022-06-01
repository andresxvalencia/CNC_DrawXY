from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtWidgets import QApplication

import sys

url = "ws://192.168.0.1/command?commandText="


class Client(QObject):
    def __init__(self, parent):
        super().__init__(parent)

        self.websocket = QWebSocket()
        self.websocket.connected.connect(self.onConnected)
        self.websocket.textMessageReceived.connect(self.onTextMsgRx)
        self.websocket.binaryMessageReceived.connect(self.onBinMsgRx)

        cmd = QUrl(url + "$$")
        cmd.setPort(81)
        self.websocket.open(cmd)

        self.websocket.



    def onConnected(self):
        print("Connected")

    def onTextMsgRx(self, msg):
        print(msg)

    def onBinMsgRx(self, msg):
        print(msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = Client(app)
    app.exec_()
