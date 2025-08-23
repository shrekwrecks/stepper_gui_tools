# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'bluetooth.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QDial, QHBoxLayout, QLabel,
    QMainWindow, QMenu, QMenuBar, QSizePolicy,
    QSlider, QSpacerItem, QStatusBar, QWidget)

from pyqtgraph import PlotWidget

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1215, 818)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.linear_plot_widget = PlotWidget(self.centralwidget)
        self.linear_plot_widget.setObjectName(u"linear_plot_widget")
        self.linear_plot_widget.setGeometry(QRect(210, 360, 731, 300))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.linear_plot_widget.sizePolicy().hasHeightForWidth())
        self.linear_plot_widget.setSizePolicy(sizePolicy)
        self.linear_plot_widget.setMinimumSize(QSize(300, 300))
        self.linear_plot_widget.setSizeIncrement(QSize(1, 1))
        self.linear_plot_widget.setStyleSheet(u"background-color: rgb(255, 255, 255);")
        self.state_label = QLabel(self.centralwidget)
        self.state_label.setObjectName(u"state_label")
        self.state_label.setGeometry(QRect(10, 440, 81, 17))
        self.layoutWidget = QWidget(self.centralwidget)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(240, 20, 677, 302))
        self.horizontalLayout = QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.radial_left = PlotWidget(self.layoutWidget)
        self.radial_left.setObjectName(u"radial_left")
        sizePolicy.setHeightForWidth(self.radial_left.sizePolicy().hasHeightForWidth())
        self.radial_left.setSizePolicy(sizePolicy)
        self.radial_left.setMinimumSize(QSize(300, 300))
        self.radial_left.setSizeIncrement(QSize(1, 1))
        self.radial_left.setStyleSheet(u"background-color: rgb(255, 255, 255);")

        self.horizontalLayout.addWidget(self.radial_left)

        self.horizontalSpacer = QSpacerItem(63, 20, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.radial_right = PlotWidget(self.layoutWidget)
        self.radial_right.setObjectName(u"radial_right")
        sizePolicy.setHeightForWidth(self.radial_right.sizePolicy().hasHeightForWidth())
        self.radial_right.setSizePolicy(sizePolicy)
        self.radial_right.setMinimumSize(QSize(300, 300))
        self.radial_right.setSizeIncrement(QSize(1, 1))
        self.radial_right.setStyleSheet(u"background-color: rgb(255, 255, 255);")

        self.horizontalLayout.addWidget(self.radial_right)

        self.speed1_scale_slider = QSlider(self.centralwidget)
        self.speed1_scale_slider.setObjectName(u"speed1_scale_slider")
        self.speed1_scale_slider.setGeometry(QRect(210, 20, 16, 301))
        self.speed1_scale_slider.setMaximum(40000)
        self.speed1_scale_slider.setSingleStep(100)
        self.speed1_scale_slider.setOrientation(Qt.Orientation.Vertical)
        self.speed23_scale_slider = QSlider(self.centralwidget)
        self.speed23_scale_slider.setObjectName(u"speed23_scale_slider")
        self.speed23_scale_slider.setGeometry(QRect(930, 19, 20, 311))
        self.speed23_scale_slider.setMaximum(40000)
        self.speed23_scale_slider.setSingleStep(100)
        self.speed23_scale_slider.setOrientation(Qt.Orientation.Vertical)
        self.acceleration_slider = QSlider(self.centralwidget)
        self.acceleration_slider.setObjectName(u"acceleration_slider")
        self.acceleration_slider.setGeometry(QRect(180, 360, 20, 301))
        self.acceleration_slider.setMinimum(4000)
        self.acceleration_slider.setMaximum(200000)
        self.acceleration_slider.setSingleStep(500)
        self.acceleration_slider.setOrientation(Qt.Orientation.Vertical)
        self.speed1_label = QLabel(self.centralwidget)
        self.speed1_label.setObjectName(u"speed1_label")
        self.speed1_label.setGeometry(QRect(100, 300, 91, 17))
        self.speed23_label = QLabel(self.centralwidget)
        self.speed23_label.setObjectName(u"speed23_label")
        self.speed23_label.setGeometry(QRect(970, 320, 101, 17))
        self.acceleration_label = QLabel(self.centralwidget)
        self.acceleration_label.setObjectName(u"acceleration_label")
        self.acceleration_label.setGeometry(QRect(80, 640, 91, 17))
        self.speed0_scale_dial = QDial(self.centralwidget)
        self.speed0_scale_dial.setObjectName(u"speed0_scale_dial")
        self.speed0_scale_dial.setGeometry(QRect(40, 30, 121, 131))
        self.speed0_scale_dial.setMaximum(50000)
        self.speed0_scale_dial.setSingleStep(100)
        self.speed0_label = QLabel(self.centralwidget)
        self.speed0_label.setObjectName(u"speed0_label")
        self.speed0_label.setGeometry(QRect(50, 160, 91, 17))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1215, 22))
        self.menuHi = QMenu(self.menubar)
        self.menuHi.setObjectName(u"menuHi")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuHi.menuAction())

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Hello", None))
        self.state_label.setText(QCoreApplication.translate("MainWindow", u"state_label", None))
        self.speed1_label.setText(QCoreApplication.translate("MainWindow", u"Speed1", None))
        self.speed23_label.setText(QCoreApplication.translate("MainWindow", u"Speed23", None))
        self.acceleration_label.setText(QCoreApplication.translate("MainWindow", u"Accel:", None))
        self.speed0_label.setText(QCoreApplication.translate("MainWindow", u"Speed0", None))
        self.menuHi.setTitle(QCoreApplication.translate("MainWindow", u"Hi", None))
    # retranslateUi

