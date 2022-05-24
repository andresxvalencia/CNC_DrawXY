from PyQt5 import QtSvg, uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QSizePolicy
import sys


class Ui(QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        self.ui = uic.loadUi('viewsvg.ui', self)
        
        svgWidget = QtSvg.QSvgWidget('logo-ingelect.svg')
        svgWidget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ui.viewLayout.addWidget(svgWidget)


if __name__ == "__main__": 
    app = QApplication(sys.argv)
    window = Ui()
    window.show()
    app.exec_()
