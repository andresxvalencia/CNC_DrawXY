from urllib import request
from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtWidgets import ( 
    QApplication, QWidget, 
    QPushButton, QGridLayout,
    QLineEdit
)
from PyQt5.QtNetwork import QAbstractSocket

import requests
import sys

# url = "http://grblesp.local/command?commandText="
url = "http://192.168.0.1/command?commandText="


class Client(QWidget):
    def __init__(self):
        super().__init__()

        self.websocket = QWebSocket()
        self.websocket.connected.connect(self.onConnected)
        self.websocket.textMessageReceived.connect(self.onTextMsgRx)
        self.websocket.binaryMessageReceived.connect(self.onBinMsgRx)

        self.sendButton = QPushButton('Send Command')
        self.inputText = QLineEdit()
        self.grid = QGridLayout()        
        self.grid.addWidget(self.inputText, 1, 1)
        self.grid.addWidget(self.sendButton, 2, 1)
        self.setLayout(self.grid)

        self.sendButton.clicked.connect(self.sendCommand)

        self.url_ws = QUrl("ws://192.168.0.1")
        self.url_ws.setPort(81)
        self.websocket.open(self.url_ws)

        self.show()

    def __del__(self):
        self.websocket.close()

    def sendCommand(self):
        # if websocket is connected
        if self.websocket.state() == QAbstractSocket.SocketState.ConnectedState:
            cmd = self.inputText.text()
            try:
                # Send command. Wait for 5 seconds 
                requests.get(url + cmd, timeout=5)
            except requests.ConnectTimeout:
                print('Connected timeout')
        else:
            print('WebSocket is not connected')
            self.websocket.open(self.url_ws)

    def onConnected(self):
        print("WebSocket connected")

    def onTextMsgRx(self, msg):
        print(msg)

    def onBinMsgRx(self, msg):
        print(msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = Client()
    app.exec_()
