import sys

import pygame.camera
from PIL import Image, ImageQt, ImageFilter

from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QGridLayout,
    QWidget
)

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer


class ViewImage(QWidget):

    def __init__(self):
        super().__init__()

        self.label = QLabel()

        pygame.camera.init()
        cameras = pygame.camera.list_cameras()
        self.cam = pygame.camera.Camera(cameras[0])

        self.timer = QTimer()
        self.timer.timeout.connect(self.showCamera)

        self.cam.start()

        self.timer.start()

        self.show()

    def showCamera(self):
        image = self.cam.get_image()

        raw_str = pygame.image.tostring(image, 'RGB')
        pil_image = Image.frombytes('RGB', image.get_size(), raw_str)

        self.pil_image = pil_image.convert('L')

        threshold = 120
        img_new = self.pil_image.point(lambda x: 255 if x > threshold else 0)
        img_newFiltered = img_new.filter(ImageFilter.CONTOUR)

        self.im = ImageQt.ImageQt(img_newFiltered)
        pixmap = QPixmap.fromImage(self.im)
        self.label.setPixmap(pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = ViewImage()
    sys.exit(app.exec_())
