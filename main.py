from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import *
from PyQt5.Qsci import *
from PyQt5.QtWidgets import QFileDialog
import serial
import serial.tools.list_ports as list_ports
import sys
import time
import view3d
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces
from PyQt5.QtWidgets import QSizePolicy
from PyQt5 import QtSvg, uic
import cairosvg
import pygame.camera
from PIL import Image, ImageQt, ImageFilter
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer
import os
import requests
from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtNetwork import QAbstractSocket
import GUIFuncional.recursos


class ReadPort(QtCore.QObject):
    update = QtCore.pyqtSignal(str)

    def __init__(self, s):
        super().__init__()
        self.serial = s
        self.isrunning = True

    def stop(self):
        self.isrunning = False

    def run(self):
        print('Empieza Thread ReadPort')
        while self.isrunning:
            if self.serial.is_open:
                try:
                    if self.serial.in_waiting > 0:
                        print('Serial está disponible')
                        data = self.serial.readline()
                        data = data.replace(b'\r', b'')
                        text = data.decode('iso-8859-1')
                        self.update.emit(text)
                except:
                    pass


class PlayThread(QtCore.QObject):
    update = QtCore.pyqtSignal(str)

    def __init__(self, s):
        super().__init__()
        self.serial = s

    def setFileName(self, f):
        self.f = f

    def run(self):
        if self.serial.is_open:
            for line in self.f:
                lecture = line.strip()
                if not lecture.startswith('(') and not lecture.startswith('%'):
                    if lecture.startswith('M3 S90.0'):
                        lecture = 'G21G91G1Z-10F3000'
                    if lecture.startswith('M5'):
                        lecture = 'G21G91G1Z+10F3000'
                    lecture = lecture + '\n'
                    data = lecture.encode('utf-8')
                    self.serial.write(data)
                    self.update.emit(lecture)
                    data = self.serial.readline()
                    data = data.replace(b'\r', b'')
                    text = data.decode('iso-8859-1')
                    self.update.emit(text)


class Readgcode(QtCore.QObject):
    update = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.isrunning = True

    def setFileName(self, f):
        self.f = f

    def stop(self):
        self.isrunning = False
        # self.f.close()

    def start(self):
        if not self.isrunning:
            self.isrunning = True
            self.run()

    def run(self):
        while self.isrunning:
            time.sleep(2)
            for line in self.f:
                lecture = line.strip()
                if not lecture.startswith('(') and not lecture.startswith('%'):
                    lecture = lecture + '\n'
                    self.update.emit(lecture)
            self.stop()


class sendSocket(QtCore.QObject):
    update = QtCore.pyqtSignal(str)

    def __init__(self, s):
        super().__init__()
        self.url = "http://192.168.0.1/command?commandText="
        self.websocket = s
        self.url_ws = QUrl("ws://192.168.0.1")
        self.websocket.textMessageReceived.connect(self.onTextMsgRx)
        self.websocket.binaryMessageReceived.connect(self.onBinMsgRx)
        self.state = True

    def setFileName(self, f):
        self.f = f

    def run(self):
        print('Ejecutando Run...')
        if self.websocket.state() == QAbstractSocket.SocketState.ConnectedState:
            print('Transmitiendo...')
            for line in self.f:
                cmd = line.strip()
                if not cmd.startswith('(') and not cmd.startswith('%') and not cmd == '':
                    requests.get(self.url + cmd, timeout=5)
                    print(cmd)
                    self.update.emit(cmd)
                    self.state = False
                    while not self.state:
                        pass
        else:
            print('WebSocket is not connected')
            self.websocket.open(self.url_ws)

    def onTextMsgRx(self, msg):
        # print('Mensaje recibido:' + msg)
        pass

    def onBinMsgRx(self, msg):
        print('Bits recibidos')
        msg = msg.replace(b'\r', b'')
        text = str(msg, 'iso-8859-1')
        self.state = True
        self.update.emit(text)


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

        self.label = self.ui.photo

        pygame.camera.init()
        cameras = pygame.camera.list_cameras()
        self.cam = pygame.camera.Camera(cameras[0], (50, 50))

        self.timer = QTimer()
        self.timer.timeout.connect(self.showCamera)

        self.cam.start()

        self.timer.start()

        self.show()

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

            self.readPort = ReadPort(self.serial)

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

        self.websocket = QWebSocket()
        self.websocket.connected.connect(self.onConnected)
        # self.websocket.textMessageReceived.connect(self.onTextMsgRx)
        # self.websocket.binaryMessageReceived.connect(self.onBinMsgRx)
        self.url = "http://192.168.0.1/command?commandText="
        self.url_ws = QUrl("ws://192.168.0.1")
        self.url_ws.setPort(81)
        self.websocket.open(self.url_ws)

        self.thread = QtCore.QThread()
        self.thread2 = QtCore.QThread()
        self.thread3 = QtCore.QThread()
        self.thread4 = QtCore.QThread()

        self.readPort = ReadPort(self.serial)
        self.readPort.moveToThread(self.thread)
        self.thread.started.connect(self.readPort.run)

        self.playThread = PlayThread(self.serial)
        self.playThread.moveToThread(self.thread2)
        self.thread2.started.connect(self.playThread.run)

        self.displayThread = Readgcode()
        self.displayThread.moveToThread(self.thread3)
        self.thread3.started.connect(self.displayThread.run)

        self.socketThread = sendSocket(self.websocket)
        self.socketThread.moveToThread(self.thread4)
        self.thread4.started.connect(self.socketThread.run)

        self.showImage = True
        self.threshold = 100

        self.ui.openButton.clicked.connect(self.openFile)
        self.ui.thresholdButton.clicked.connect(self.setThreshold)

        self.ui.uploadPhotoButton.clicked.connect(self.uploadPhoto)
        self.ui.cancelButton.clicked.connect(self.cancelPhoto)
        self.ui.takePhotoButton.clicked.connect(self.savePhoto)

        self.ui.TxButton.clicked.connect(self.changeName)

        self.currentText = self.ui.inputTx.text()


    def onConnected(self):
        print("WebSocket connected")

    def onTextMsgRx(self, msg):
        print(msg)

    def onBinMsgRx(self, msg):
        print(msg)

    def showCamera(self):

        image = self.cam.get_image()

        raw_str = pygame.image.tostring(image, 'RGB')
        pil_image = Image.frombytes('RGB', image.get_size(), raw_str)

        self.pil_image = pil_image.convert('L')

        img_new = self.pil_image.point(lambda x: 255 if x > self.threshold else 0)
        self.img_newFiltered = img_new.filter(ImageFilter.CONTOUR)
        self.im = ImageQt.ImageQt(self.img_newFiltered)
        pixmap = QPixmap.fromImage(self.im)
        if self.showImage:
            self.label.setPixmap(pixmap)

    def savePhoto(self):
        picture = self.img_newFiltered
        picture.save('Capture.bmp')
        pixmap = QPixmap('Capture.bmp')
        self.label.setPixmap(pixmap)
        self.showImage = False

    def uploadPhoto(self):
        input_file = "Capture.bmp"
        output_file = "Capture.svg"

        os.system("potrace {} --svg -o {}".format(input_file, output_file))

        self.filename = "Capture.svg"

        self.runFile()

    def cancelPhoto(self):
        self.showImage = True
        self.showCamera()

    def setThreshold(self):
        text = int(self.ui.inputThreshold.text())
        self.threshold = text

    def clear(self):
        self.ui.textEdit.clear()

    def send(self):
        data = self.ui.inputEdit.text() + '\n'
        self.serial.write(data.encode('utf-8'))
        self.ui.inputEdit.setText('')
        self.readPort.update.connect(self.readline)

    def readline(self, message):
        self.ui.textEdit.append(message)

    def connect(self):
        if not self.serial.is_open:
            self.serial.open()
            # self.readTimer.start(10)
            self.thread.start()
            self.ui.sendButton.setEnabled(True)
            print('Se estableció la conexión serial')
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
        self.send_message('G21G91G1Y1F10')
        self.send_message('G90G21')

    def down_movement(self):
        self.send_message('G21G91G1Y-1F10')
        self.send_message('G90G21')

    def left_movement(self):
        self.send_message('G21G91G1X-1F10')
        self.send_message('G90G21')

    def right_movement(self):
        self.send_message('G21G91G1X1F10')
        self.send_message('G90G21')

    def rightup_movement(self):
        self.send_message('G21G91G1X1Y1F10')
        self.send_message('G90G21')

    def rightdown_movement(self):
        self.send_message('G21G91G1X1Y-1F10')
        self.send_message('G90G21')

    def leftup_movement(self):
        self.send_message('G21G91G1X-1Y1F10')
        self.send_message('G90G21')

    def leftdown_movement(self):
        self.send_message('G21G91G1X-1Y-1F10')
        self.send_message('G90G21')

    def pencil_movement(self):
        if self.pencilLabel.text() == 'OFF':
            self.pencilLabel.setText('ON')
            self.send_message('G21G91G1Z+5F3000')
            self.send_message('G90G21')

        elif self.pencilLabel.text() == 'ON':
            self.pencilLabel.setText('OFF')
            self.send_message('G21G91G1Z-5F3000')
            self.send_message('G90G21')

    def send_message(self, message):
        self.currentText = self.ui.inputTx.text()

        if self.currentText == 'SERIAL':
            print('Ejecutando Serial')
            text = self.ui.textEdit.toPlainText()
            text += message + '\n'
            self.ui.textEdit.setText(text)
            data = message + '\n'
            self.serial.write(data.encode('utf-8'))
        else:
            print('Ejecutando Wifi')
            text = self.ui.textEdit.toPlainText()
            text += message + '\n'
            self.ui.textEdit.setText(text)
            if self.websocket.state() == QAbstractSocket.SocketState.ConnectedState:
                try:
                    # Send command. Wait for 5 seconds
                    requests.get(self.url + message, timeout=5)
                except requests.ConnectTimeout:
                    print('Connected timeout')
            else:
                print('WebSocket is not connected')
                self.websocket.open(self.url_ws)

    def execute_code(self):

        f = open(self.filename, 'r')

        self.displayThread.setFileName(f)
        self.thread3.start()
        self.displayThread.start()


        self.displayThread.update.connect(self.appendGcode)
        """
        for line in f:
            lecture = line.strip()
            if not lecture.startswith('(') and not lecture.startswith('%'):
                self.__editor.append(lecture + '\n')
                
        """
        # f.close()
        # self.displayThread.stop()

        self.ui.playButton.clicked.connect(self.play)

    def appendGcode(self, lecture):
        self.__editor.append(lecture)

    def openFile(self):
        path = r"/home/juanes/Documentos/GitHub/CNC_DrawXY/Imagenes GCODE/"
        self.filename = QFileDialog.getOpenFileName(self, "Open file", path,
                                                    "*.gcode *.ngc *.svg")[0]
        self.runFile()

    def runFile(self):

        if self.filename != "":
            if self.filename.endswith('.svg'):
                svg = cairosvg.svg2svg(
                    url=self.filename,
                    write_to='svg-converted.svg',
                    scale=0.1
                )

                self.filename = 'svg-converted.svg'

                # print('New File Name: ' + self.filename)

                self.drawFiguresvg()
                gcode_compiler = Compiler(interfaces.Gcode, movement_speed=1000, cutting_speed=300, pass_depth=1)

                curves = parse_file(self.filename)  # Parse an svg file into geometric curves

                gcode_compiler.append_curves(curves)
                gcode_compiler.compile_to_file("drawing.gcode", passes=1)
                # print('File Converted to gcode')
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

    def changeName(self):

        self.currentText = self.ui.inputTx.text()

        if self.currentText == 'SERIAL':
            self.ui.inputTx.setText('WI-FI')
            self.ui.TxButton.setIcon(QtGui.QIcon('GUIFuncional/imagenes/wifi.svg'))
        else:
            self.ui.inputTx.setText('SERIAL')
            self.ui.TxButton.setIcon(QtGui.QIcon('GUIFuncional/imagenes/serial.svg'))


    def play(self):
        self.readPort.stop()
        f = open(self.filename, 'r')

        self.currentText = self.ui.inputTx.text()

        if self.currentText == 'SERIAL':
            self.playThread.setFileName(f)
            self.thread2.start()
            self.playThread.update.connect(self.appendMessage)
        else:
            self.socketThread.setFileName(f)
            self.thread4.start()
            self.socketThread.update.connect(self.appendMessage)

    def appendMessage(self, message):
        self.ui.textEdit.append(message)

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
