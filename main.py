from PyQt5 import QtWidgets, uic
from PyQt5 import QtCore
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *
import serial
import serial.tools.list_ports as list_ports
import sys
import view3d

class UI(QtWidgets.QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        self.ui = uic.loadUi('GUI/GUIDrawXY.ui', self)
        self.serial = serial.Serial()

        self.__editor = QsciScintilla()
        self.ui.codeLayout.addWidget(self.__editor)

        font = QFont()
        font.setFamily('Courier')
        # Courier
        font.setFixedPitch(True)
        font.setPointSize(12)

        lexer = QsciLexerPython()
        lexer.setDefaultFont(font)
        self.__editor.setLexer(lexer)
        self.__editor.setUtf8(True)  # Set encoding to UTF-8
        self.__editor.setFont(font)
        self.__editor.setMarginsFont(font)

        fontmetrics = QFontMetrics(font)
        self.__editor.setMarginsFont(font)
        self.__editor.setMarginWidth(0, fontmetrics.width("0000") + 6)
        self.__editor.setMarginLineNumbers(0, True)
        self.__editor.setMarginsBackgroundColor(QColor("#cccccc"))

        ports = list_ports.comports()

        for baud in self.serial.BAUDRATES:
            self.ui.baudOptions.addItem(str(baud))

        self.ui.baudOptions.setCurrentIndex(self.serial.BAUDRATES.index(115200))

        if ports:
            for port in ports:
                self.ui.portOptions.addItem(port.device)
            self.serial.baudrate = 115200
            self.serial.port = self.ui.portOptions.currentText()
            self.serial.open()
        self.ui.sendButton.clicked.connect(self.send)
        self.ui.upButton.clicked.connect(self.up_movement)
        self.ui.downButton.clicked.connect(self.down_movement)
        self.ui.rightButton.clicked.connect(self.right_movement)
        self.ui.leftButton.clicked.connect(self.left_movement)
        self.ui.pencilButton.clicked.connect(self.pencil_movement)

        self.timer = QtCore.QTimer()
        if self.serial.is_open:
            self.timer.start(10)
            self.timer.timeout.connect(self.read)

    def send(self):
        data = self.ui.inputEdit.text() + '\n'
        self.serial.write(data.encode('utf-8'))
        self.ui.inputEdit.setText('')

    def read(self):
        if self.serial.is_open:
            if self.serial.in_waiting > 0:
                data = self.serial.read()
                text = self.ui.textEdit.toPlainText()
                text += data.decode('utf-8')
                self.ui.textEdit.setText(text)

    def up_movement(self):
        self.send_message('G21G91G1Y1F10')
        self.send_message('G90G21')

    def down_movement(self):
        self.send_message('G21G91G1Y-1F10')
        self.send_message('G90G21')

    def left_movement(self):
        self.send_message('G21G91X-1F10')
        self.send_message('G90G21')

    def right_movement(self):
        self.send_message('G21G91X1F10')
        self.send_message('G90G21')

    def pencil_movement(self):
        if self.pencilLabel.text() == 'OFF':
            self.pencilLabel.setText('ON')
            self.send_message('M03 S090')
            # self.send_message('G90G21')

        elif self.pencilLabel.text() == 'ON':
            self.pencilLabel.setText('OFF')
            self.send_message('M05')
            # self.send_message('G90G21')

    def send_message(self, message):
        text = self.ui.textEdit.toPlainText()
        text += message + '\n'
        self.ui.textEdit.setText(text)
        data = message + '\n'
        self.serial.write(data.encode('utf-8'))
        # lectura = self.serial.readline().decode('utf-8')

    def __del__(self):
        if self.serial.is_open:
            self.serial.close()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = UI()
    ui.show()
    app.exec_()
