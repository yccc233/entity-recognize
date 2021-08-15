from PySide2 import QtWidgets, QtGui, QtCore
import sys

class LoadUI:
    def __init__(self, path, message='', w=240, h=200):
        _desk = QtWidgets.QDesktopWidget()
        self.W, self.H, self.w, self.h = _desk.width(), _desk.height(), w, h
        self.x = (self.W-self.w)/2
        self.y = (self.H-self.h-100)/2

        self.widget = QtWidgets.QWidget()
        self.widget.setGeometry(self.x, self.y, self.w, self.h+50)
        # self.widget.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        # self.widget.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.widget.show()

        self.label = QtWidgets.QLabel(self.widget)
        self.label.setGeometry(0,0,self.w,self.h)
        self.movie = QtGui.QMovie(path)
        self.label.setMovie(self.movie)
        self.label.show()
        self.movie.setSpeed(100)
        self.movie.start()
        self.movie.stateChanged.connect(self._restart)

        self.label = QtWidgets.QLabel(self.widget)
        self.label.setText(message)
        self.label.setGeometry(10,self.h-30,self.w,30)
        self.label.show()

    def finish(self):
        self.widget.close()

    def _restart(self):
        self.movie.start()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    mainw = LoadUI('./src/gif/load.gif', '加载中，请稍等...')
    # for i in range(5):
    #     print(mainw.movie.loopCount())
    #     time.sleep(1)
    sys.exit(app.exec_())