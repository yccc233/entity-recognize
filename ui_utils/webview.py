from PySide2 import QtWebEngineWidgets, QtCore
import PySide2.QtWidgets as QtWidgets
import sys

class WebView(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, parent):
        QtWebEngineWidgets.QWebEngineView.__init__(self, parent)
        self.load(QtCore.QUrl('http://localhost:7474/browser/'))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mainWin = QtWidgets.QMainWindow()
    mainWin.show()
    wv = WebView(mainWin)
    mainWin.setFixedSize(800,700)
    wv.setFixedSize(mainWin.size())
    sys.exit(app.exec_())
