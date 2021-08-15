import sys, re, time
from PySide2 import QtGui,QtCore,QtWidgets
from ui_utils import webview, highlighter, loadui
from neo4j_utils import neo4j
import data_utils as util
import threading


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("信息挖掘")
        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setFixedSize(600, 400)
        # 建立一个窗口，居中MainWindow
        self.mainWidget = QtWidgets.QWidget()
        self.setCentralWidget(self.mainWidget)
        # 主要布局器，纵向布局
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)
        self.color = QtGui.QColor('#FFEBCD')  # 背景颜色
        self.setPalette(self.color)


        # 标签：存放提示、进度等
        self.label = QtWidgets.QLabel('程序构建完成...')
        # 按钮1：打开文件
        self.button1 = QtWidgets.QPushButton(text='打开文件')
        self.button1.clicked.connect(self.click1)
        self.mainLayout.addWidget(self.button1)
        # 按钮2：分析文本
        self.button2 = QtWidgets.QPushButton(text='开始分析')
        self.button2.clicked.connect(self.click2)
        # 按钮3：查看文本关系
        self.button3 = QtWidgets.QPushButton(text='保存信息')
        self.button3.clicked.connect(self.click3)
        # 按钮4：打开h5页面
        self.button4 = QtWidgets.QPushButton(text='图谱页面')
        self.button4.clicked.connect(self.click4)
        self.mainLayout.addWidget(self.button4)
        # 文本框：显示文本信息
        self.textEdit = QtWidgets.QTextEdit(self.mainWidget)
        self.textEdit.setPlaceholderText('//请导入文本')
        # 设置背景色
        pl = QtGui.QPalette()
        brush = QtGui.QBrush()
        brush.setColor(self.color)
        pl.setBrush(QtGui.QPalette.Base, brush)
        self.textEdit.setPalette(pl)

        # 布局
        # 横向布局，保存分析、三元组、图谱按钮
        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.addWidget(self.button2)
        self.hbox.addWidget(self.button3)
        self.hbox.addWidget(self.button4)
        self.mainLayout.addWidget(self.button1)
        self.mainLayout.addLayout(self.hbox)
        self.mainLayout.addWidget(self.label)
        self.mainLayout.addWidget(self.textEdit)
        # 其他的初始化
        # 定义高亮方法
        self.highLighter = highlighter.MyHighlighter(self.textEdit)
        # 保存实体类别和二元组
        self.covid = []
        self.gene = []
        self.phen = []
        self.protein = []
        self.doubles = []
        # 二元组关系标签，用时间形式表示当前文本的关系组，如(COVID)-[20210511113641]->(ACE)
        self.saveTime = ''

    # 打开文件
    def click1(self):
        # str = '新冠中ACE2和受体基因血管紧张素转化酶2有关，且会导致发热现象。'
        fileDialog = QtWidgets.QFileDialog()
        path = fileDialog.getOpenFileName(dir='/Users/yucheng', filter='(*.txt)')
        if not path[0]:
            return
        with open(path[0], 'r') as f:
            str = f.read()
        str.replace('-', '_')
        self.textEdit.setPlainText(str)
        self.label.setText('导入文件 {}'.format(path[0]))

    # 开始分析
    def click2(self):
        if not self.textEdit.toPlainText():
            self.label.setText('请导入文本！')
            return
        self.label.setText('开始分析...请稍等...')
        self.doubles = []
        text = self.textEdit.toPlainText()
        text = util.clean_text_character(text)
        paras = util.split_text_to_paragraph(text)
        entities = []
        for p in paras:  # 段落分割
            sentences = util.split_paragraph_to_sentences(p)
            sentences = util.clean_sentences(sentences)  # 清洗句子，防止句中有杂质
            isCovid = False  # 记录段落和covid的相关性，首先是false
            for sentence in sentences:  # 句子分割
                sentence = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]|（.*?）", "", sentence)
                predict = entity.predict(sentence)  # 获取实体并输出
                print(sentence)
                print('predict:{}'.format(predict))
                if 'COVID' in predict:  # 此句关联到新冠相关，本段落中往后的语句都与新冠相关
                    isCovid = True
                # 获取高亮相关实体
                self.covid, self.gene, self.phen, self.protein = util.classify_kind_to_list(predict)
                entities += util.handle_list_to_highlight(self.covid, self.gene, self.phen, self.protein)
                entities = util.clean_entities_from_predict(entities)  # 清洗实体数据
                # 获取二元组
                sentence_double = util.getDouble_by_sentence_and_isCovid(predict, isCovid)
                for sd in sentence_double:  # 去重
                    if sd not in self.doubles:
                        self.doubles.append(sd)
        print('highlight:{}'.format(entities))
        print('doules:{}'.format(self.doubles))
        self.highLighter.setHighLightData(entities)
        self.highLighter.highlightBlock(self.textEdit.toPlainText())
        self.textEdit.setText(self.textEdit.toPlainText())
        self.saveTime = time.strftime('%Y%m%d%H%M%S')  # 生成标记ID
        self.label.setText('分析完成！')

    # 保存信息
    def click3(self):
        if self.doubles == []:
            self.label.setText('没有可保存的信息！')
            return
        neo = neo4j.Neo4j()
        ok, errmsg = neo.insertNeo4j(self.doubles)
        if ok:
            self.label.setText('保存成功！')
        else:
            self.label.setText(errmsg)

    # 图谱h5
    def click4(self):
        webWin = QtWidgets.QMainWindow(self)
        webWin.setFixedSize(900, 600)
        wv = webview.WebView(webWin)
        wv.setFixedSize(webWin.size())
        webWin.show()


if __name__ == '__main__':
    # 加载动画
    app = QtWidgets.QApplication(sys.argv)
    pixmap = QtGui.QPixmap('./src/gif/load.gif')
    splash = QtWidgets.QSplashScreen(pixmap)
    splashlabel = QtWidgets.QLabel(splash)
    splashgif = QtGui.QMovie('./src/gif/load.gif')
    splashlabel.setMovie(splashgif)
    splashgif.start()
    splash.show()

    import ner.getEntities as entity

    mainWin = MainWindow()
    splash.finish(mainWin)
    mainWin.show()
    sys.exit(app.exec_())
