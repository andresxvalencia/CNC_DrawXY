from PyQt5 import QtCore
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import *
from PyQt5.Qsci import *
from PyQt5.QtWidgets import QFileDialog
import serial
import serial.tools.list_ports as list_ports
import sys
import time
import view3d


class UI(QtWidgets.QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        self.ui = uic.loadUi('GUIFuncional/GUIDrawXY.ui', self)
        self.serial = serial.Serial()

        self.__editor = QsciScintilla()
        self.ui.codeLayout.addWidget(self.__editor)

        font = QFont()
        font.setFamily('Arial Black')
        font.setFixedPitch(True)
        font.setPointSize(9)

        lexer = QsciLexerPython()
        lexer.setDefaultFont(font)
        lexer.setDefaultPaper(QColor("#000000"))
        lexer.setDefaultColor(QColor("#186A0D"))
        self.__editor.setLexer(lexer)
        self.__editor.setUtf8(True)  # Set encoding to UTF-8
        self.__editor.setFont(font)
        self.__editor.setMarginsFont(font)
        self.__editor.setSelectionBackgroundColor(QColor("#186A0D"))

        self.__editor.setCaretForegroundColor(QColor("#20de07"))  # Configuración del signo de intercalación

        fontmetrics = QFontMetrics(font)  # Características del Margen
        self.__editor.setMarginsFont(font)
        self.__editor.setMarginsForegroundColor(QColor("#20de07"))
        self.__editor.setMarginsBackgroundColor(QColor("#20de07"))
        self.__editor.setMarginWidth(0, fontmetrics.width("0000") + 1)
        self.__editor.setMarginLineNumbers(0, True)
        self.__editor.setMarginsBackgroundColor(QColor("#193817"))

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
        self.ui.leftDownButton.clicked.connect(self.leftdown_movement)
        self.ui.rightUpButton.clicked.connect(self.rightup_movement)
        self.ui.leftUpButton.clicked.connect(self.leftup_movement)
        self.ui.rightUpButton.clicked.connect(self.rightup_movement)

        self.view_3D = view3d.View3D()
        self.ui.viewLayout.addWidget(self.view_3D)

        self.timer = QtCore.QTimer()
        if self.serial.is_open:
            self.timer.start(10)
            self.timer.timeout.connect(self.read)

        self.ui.openButton.clicked.connect(self.openFile)

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

    def rightup_movement(self):
        self.send_message('G21G91X1Y1F10')
        self.send_message('G90G21')

    def rightdown_movement(self):
        self.send_message('G21G91X1Y-1F10')
        self.send_message('G90G21')

    def leftup_movement(self):
        self.send_message('G21G91X-1Y1F10')
        self.send_message('G90G21')

    def leftdown_movement(self):
        self.send_message('G21G91X-1Y-1F10')
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

    def execute_code(self, filename):
        # s = serial.Serial(self.ui.portOptions.currentText(), 115200)

        f = open(filename, 'r')

        # s.write("\n\n".encode('utf-8'))
        time.sleep(2)
        # s.flushInput()

        for line in f:
            lecture = line.strip()
            if not lecture.startswith('(') and not lecture.startswith('%'):
                self.__editor.append(lecture + '\n')
                # print('Sending: ' + lecture)
                self.send_message(lecture)
                # grbl_out = s.readline().decode('utf-8')
                # print(': ' + grbl_out.strip())

        # input("  Press <Enter> to exit and disable grbl.")

        f.close()
        # s.close()

    def openFile(self):
        path = r"C:\Users\cocuy\Dropbox\My PC (LAPTOP-7D3H6IAV)\Documents\Universidad\2022-1\Sistemas " \
               r"Embebidos\GitHub\CNC_DrawXY\Imagenes GCODE\ "
        filename = QFileDialog.getOpenFileName(self, "Open file", path,
                                               "*.gcode, *.ngc")[0]
        self.execute_code(filename)
        self.drawFigure(filename)

    def drawFigure(self, filename):
        gcode = open(filename).read()
        self.view_3D.compute_data(gcode)
        self.view_3D.draw()

    def __del__(self):
        if self.serial.is_open:
            self.serial.close()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = UI()
    ui.show()
    app.exec_()
