import sys
from PySide6.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PySide6.QtGui import QPalette, QColor
from layout_colorwidget import Color

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")
        self.setMinimumSize(700, 500)

        layout = QGridLayout()

        #add a button to the widget
        button = QPushButton("Click me")
        layout.addWidget(button, 0, 0)

        layout.addWidget(Color("yellow"), 0, 3)
        layout.addWidget(Color("cyan"), 1, 0)
        layout.addWidget(Color("magenta"), 1, 1)
        layout.addWidget(Color("gray"), 1, 2)
        layout.addWidget(Color("black"), 1, 3)


        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()