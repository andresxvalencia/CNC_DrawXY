from PyQt5 import QtCore
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import *
from PyQt5.Qsci import *
from PyQt5.QtWidgets import QFileDialog
import serial
import serial.tools.list_ports as list_ports
import time
import view3d
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces
from PyQt5 import QtSvg, uic
from PyQt5.QtWidgets import QSizePolicy
import sys


class ReadPort(QtCore.QObject):
    update = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.serial = serial

    def run(self):
        while True:
            if self.serial.is_open:
                try:
                    if self.serial.in_waiting > 0:
                        data = self.serial.read()
                        data = data.replace(b'\r', b'')
                        text = data.decode('iso-8859-1')
                        self.update.emit(text)
                except:
                    pass


class UI(QtWidgets.QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        self.filename = None
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
            # self.serial.open()
            self.ui.connectButton.setEnabled(True)

            # self.timer = QtCore.QTimer()
            # if self.serial.is_open:
            #    self.timer.start(10)
            #    self.timer.timeout.connect(self.read)

            self.thread = QtCore.QThread()

            self.readPort = ReadPort()

            self.readPort.moveToThread(self.thread)
            self.thread.started.connect(self.readPort.run)

        self.ui.sendButton.clicked.connect(self.send)
        self.ui.upButton.clicked.connect(self.up_movement)
        self.ui.downButton.clicked.connect(self.down_movement)
        self.ui.rightButton.clicked.connect(self.right_movement)
        self.ui.leftButton.clicked.connect(self.left_movement)
        self.ui.pencilButton.clicked.connect(self.pencil_movement)
        self.ui.leftDownButton.clicked.connect(self.leftdown_movement)
        self.ui.rightUpButton.clicked.connect(self.rightup_movement)
        self.ui.leftUpButton.clicked.connect(self.leftup_movement)
        self.ui.rightDownButton.clicked.connect(self.rightdown_movement)
        self.ui.playButton.clicked.connect(self.play)
        self.ui.resetZeroButton.clicked.connect(self.resetZero)
        self.ui.returnZeroButton.clicked.connect(self.returnZero)
        self.ui.connectButton.clicked.connect(self.connect)

        self.view_3D = view3d.View3D()
        self.ui.viewLayout.addWidget(self.view_3D)

        # self.timer = QtCore.QTimer()
        # if self.serial.is_open:
        #    self.timer.start(10)
        #    self.timer.timeout.connect(self.read)

        self.thread = QtCore.QThread()

        self.readPort = ReadPort()

        self.readPort.moveToThread(self.thread)
        self.thread.started.connect(self.readPort.run)

        self.ui.openButton.clicked.connect(self.openFile)

    def clear(self):
        self.ui.textEdit.clear()

    def send(self):
        data = self.ui.inputEdit.text() + '\n'
        self.serial.write(data.encode('utf-8'))
        self.ui.inputEdit.setText('')

    def connect(self):
        if not self.serial.is_open:
            self.serial.open()
            # self.readTimer.start(10)
            self.thread.start()
            self.ui.sendButton.setEnabled(True)
            # self.ui.connectButton.setText('Disconnect')
            # self.ui.inputEdit.setEnabled(True)
        else:
            self.thread.quit()
            self.serial.close()
            # self.readTimer.stop()
            self.ui.sendButton.setEnabled(False)
            # self.ui.connectButton.setText('Connect')
            # self.ui.inputEdit.setEnabled(False)

    def up_movement(self):
        self.send_message('G21G91G1Y1F3000')
        self.send_message('G90G21')

    def down_movement(self):
        self.send_message('G21G91G1Y-1F3000')
        self.send_message('G90G21')

    def left_movement(self):
        self.send_message('G21G91G1X-1F3000')
        self.send_message('G90G21')

    def right_movement(self):
        self.send_message('G21G91G1X1F3000')
        self.send_message('G90G21')

    def rightup_movement(self):
        self.send_message('G21G91G1X1Y1F3000')
        self.send_message('G90G21')

    def rightdown_movement(self):
        self.send_message('G21G91G1X1Y-1F3000')
        self.send_message('G90G21')

    def leftup_movement(self):
        self.send_message('G21G91G1X-1Y1F3000')
        self.send_message('G90G21')

    def leftdown_movement(self):
        self.send_message('G21G91G1X-1Y-1F3000')
        self.send_message('G90G21')

    def pencil_movement(self):
        if self.pencilLabel.text() == 'OFF':
            self.pencilLabel.setText('ON')
            self.send_message('M03 S050')
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

    def execute_code(self):

        f = open(self.filename, 'r')
        time.sleep(2)

        for line in f:
            lecture = line.strip()
            if not lecture.startswith('(') and not lecture.startswith('%'):
                self.__editor.append(lecture + '\n')
        f.close()
        self.ui.playButton.clicked.connect(self.play)

    def openFile(self):
        path = '/home/andresxvalencia/Documentos/GitHub/CNC_DrawXY/Imagenes GCODE'
        self.filename = QFileDialog.getOpenFileName(self, "Open file", path,
                                                    "*.gcode *.ngc *.svg")[0]

        if self.filename != "":
            if self.filename.endswith('.svg'):
                self.drawFiguresvg()
                gcode_compiler = Compiler(interfaces.Gcode, movement_speed=1000, cutting_speed=300, pass_depth=5)

                curves = parse_file(self.filename)  # Parse an svg file into geometric curves

                gcode_compiler.append_curves(curves)
                gcode_compiler.compile_to_file("drawing.gcode", passes=2)
                print('File Converted to gcode')
                self.filename = "drawing.gcode"
            self.drawFigure()
            self.execute_code()

    def drawFigure(self):
        gcode = open(self.filename).read()
        self.view_3D.compute_data(gcode)
        self.view_3D.draw()

    def drawFiguresvg(self):
        svgWidget = QtSvg.QSvgWidget(self.filename)
        svgWidget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ui.svgLayout.addWidget(svgWidget)

    def play(self):
        f = open(self.filename, 'r')
        self.send_message("\n\n")
        for line in f:
            lecture = line.strip()
            if not lecture.startswith('(') and not lecture.startswith('%'):
                self.send_message(lecture)
                grbl_out = self.serial.readline().decode('utf-8')

        f.close()

    def resetZero(self):
        self.send_message('G10 P0 L20 X0 Y0 Z0')

    def returnZero(self):
        self.send_message('G21G90 G0Z5')
        self.send_message('G90 G0 X0 Y0')
        self.send_message('G90 G0 Z0')

    def __del__(self):
        if self.serial.is_open:
            self.serial.close()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = UI()
    ui.show()
    app.exec_()
