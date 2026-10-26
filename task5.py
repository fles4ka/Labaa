import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor


class UFOWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Задание №5: Управление НЛО")
        self.resize(700, 500)
        self.ufo_x = 320
        self.ufo_y = 220
        self.step = 20
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.ufo_x -= self.step
        elif event.key() == Qt.Key_Right:
            self.ufo_x += self.step
        elif event.key() == Qt.Key_Up:
            self.ufo_y -= self.step
        elif event.key() == Qt.Key_Down:
            self.ufo_y += self.step

        if self.ufo_x < -40:
            self.ufo_x = self.width()
        elif self.ufo_x > self.width():
            self.ufo_x = -40

        if self.ufo_y < -40:
            self.ufo_y = self.height()
        elif self.ufo_y > self.height():
            self.ufo_y = -40

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QColor(100, 200, 255))
        painter.drawEllipse(self.ufo_x + 15, self.ufo_y, 30, 20)
        painter.setBrush(QColor(150, 150, 150))
        painter.drawEllipse(self.ufo_x, self.ufo_y + 10, 60, 20)
        painter.setBrush(QColor(255, 255, 0))
        painter.drawEllipse(self.ufo_x + 25, self.ufo_y + 15, 10, 10)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = UFOWindow()
    window.show()
    sys.exit(app.exec_())