import sys
from qtpy import QtGui, QtWidgets
#from qtpyTerminal import qtpyTerminal
from termqt import Terminal
from termqt import Terminal

# Create the Qt application and console.
app = QtWidgets.QApplication([])
mainwin = QtWidgets.QMainWindow()
mainwin.setWindowTitle("qtpyTerminal example")
container = QtWidgets.QWidget(mainwin)
container.setLayout(QtWidgets.QVBoxLayout())
mainwin.setCentralWidget(container)

label = QtWidgets.QLabel("This is a qtpyTerminal widget:")
container.layout().addWidget(label)
terminal = Terminal(height=200, width=400)
terminal.setFont(QtGui.QFont("Courier", 10))
terminal.write("mediamtx")
terminal.Ter,om

container.layout().addWidget(terminal)


# Show widget and launch Qt's event loop.
mainwin.show()
sys.exit(app.exec_())
