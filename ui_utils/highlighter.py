from PySide2.QtCore import Qt
from PySide2 import QtGui
import re


class MyHighlighter(QtGui.QSyntaxHighlighter):
    # highlight数据是一个二维的列表，列表第一个一定需要是类别，所以不是三元组的格式
    def __init__(self, parent):
        QtGui.QSyntaxHighlighter.__init__(self, parent)
        self.parent = parent
        self.highlight_data = []
        self.covidColor = QtGui.QColor('#FF00FF')
        self.geneColor = Qt.green
        self.phenColor = Qt.red
        self.proteinColor = Qt.blue
        self.highlight_data = []

    # 对text文本区进行高亮，实际就是对整个textEdit高亮标记关键字
    def highlightBlock(self, text):
        for highlight in self.highlight_data:
            pos_s = [i.start() for i in re.finditer(highlight[1], text)]
            for pos in pos_s:
                self.setFormat(pos, len(highlight[1]), self.getColorByStr(highlight[0]))

    def setHighLightData(self, highlight_data):
        self.highlight_data = highlight_data

    def getColorByStr(self, str):
        if str == 'COVID':
            return self.covidColor
        elif str == 'GENE':
            return self.geneColor
        elif str == 'PHEN':
            return self.phenColor
        elif str == 'PROTEIN':
            return self.proteinColor
        else:
            return None
