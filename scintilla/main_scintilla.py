import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        self.ui = uic.loadUi('GUI/GUIDrawXY.ui', self)
        
        self.__editor = QsciScintilla()
        self.ui.codeLayout.addWidget(self.__editor)
        
        font = QFont()
        font.setFamily('Courier')
        #Courier
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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    window.show()    
    app.exec_()
