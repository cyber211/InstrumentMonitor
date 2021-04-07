#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Open Source Declaration
--------------------------------------------------------------------------------------------------------------                
    Licensed under the terms of the PyQwt License
    Copyright (C) 2003-2009 Gerard Vermeulen, for the original PyQwt example
    Copyright (c) 2015 Pierre Raybaut, for the PyQt5/PySide port and further 
    developments (e.g. ported to PythonQwt API)
    (see LICENSE file for more details)

    Enviroments:
     - Python version: compatiblity with both 2 and  3
     - PyQt GPL v4.9.1 for python v2.7/ PyQt 5 for python v3
     - PythonQwt-0.5.5 for python v2.7/ PythonQwt 0.8.3 for python v3
     - pyserial
     - numpy
--------------------------------------------------------------------------------------------------------------                

Function Description
########################################################################
# 串口数据读取
# #1. 从UI界面给定的串口读取数据 
# #2. 读取数据的命令及格式，需要对应的修改，返回数据的格式采用正则表达式
# #3. 将数据实时的绘制成曲线图，每三分钟截图一次并作保存，或任意时刻通过菜单保存截图
# #4. 记录读到的数据到data.txt文件中保存
#
# TODO List：
#  #1. 可以在UI界面上设置命令及返回数据的格式正则表达式；
#  #2. 读取多个值，同时绘制多个曲线
#
# Usage: 
    Terminal :"python pySerialMonitor_Ploter_xxx.py" 
#########################################################################

# Created: Wed Dec 05 10:07:24 2012   by: Bob Cao
# Copyright (c) 2013 - Bob <yongbo.cao#fluke.com>,<yongbo_cao#163.com>
"""

import sys, getopt
import serial

import time
import datetime
import config

import numpy as np
import random
kProgramDeveloperName = 'Bob Cao (yongbo_cao#163.com)'
kProgVersion = '1.5'
print(sys.version)

kPythonVersion = '{}.{}.{}'.format(sys.version_info.major,sys.version_info.minor,sys.version_info.micro)

#PYTHON 2
if(sys.version_info.major == 2):
    import device
    from qwt.qt.QtGui import (QApplication, QPen, QBrush, QFrame,QFont,QToolBar,QStatusBar,
                              QMainWindow,QLabel,QHBoxLayout,QVBoxLayout,QIcon, QPixmap,
                              QWidget,QToolButton, QPrinter, QPrintDialog,QLineEdit,QMessageBox)                          
    from qwt.qt.QtCore import QSize
    from qwt.qt.QtCore import Qt,pyqtSignal,QObject
    from qwt import (QwtPlot,QwtPlotMarker,QwtSymbol,QwtLegend,QwtPlotCurve,QwtPlotGrid,QwtPlotCanvas,
                     QwtAbstractScaleDraw,QwtText,QwtPlotRenderer,QwtScaleDraw)    #QwtDateScaleDraw

# PYTHON 3
if(sys.version_info.major == 3):
    import device_py3

    from qtpy.QtGui import (QPen, QFont, QIcon, QPixmap,QBrush)
    from qtpy.QtPrintSupport import QPrinter, QPrintDialog
    from qtpy.QtCore import Qt,QObject,QSize
    from qtpy.QtCore import Signal as pyqtSignal
    from qtpy.QtWidgets import (
        QFrame,
        QWidget,
        QMainWindow,
        QApplication,
        QToolButton,
        QToolBar,
        QHBoxLayout,
        QVBoxLayout,
        QLabel,
        QToolBar,
        QLineEdit,
        QStatusBar,
        QMessageBox
    )

    from qwt import (
        QwtPlot,
        QwtPlotMarker,
        QwtSymbol,
        QwtLegend,
        QwtPlotGrid,
        QwtPlotCurve,
        QwtPlotItem,
        #QwtLogScaleEngine,
        QwtText,
        QwtPlotRenderer,
        QwtPlotCanvas,
        QwtAbstractScaleDraw,
        QwtScaleDraw,
    )

class TimeScaleDraw(QwtScaleDraw):
    def __init__(self, baseTime, *args):
        QwtScaleDraw.__init__(self, *args)
        self.baseTime = baseTime
 
    def label(self, value):
        upTime = self.baseTime.addSecs(int(value))
        return QwtText(upTime.toString())

class VLine(QFrame):
    # a simple VLine, like the one you get from designer
    def __init__(self):
        super(VLine, self).__init__()
        self.setFrameShape(self.VLine)  # |self.Sunken

class DataPlot(QwtPlot):
    # signal define
    signal_showinfo = pyqtSignal(object)
    
    def __init__(self, *args):
        QwtPlot.__init__(self, *args)
        
        self.uut_dev = None
        self.timerId = None
        #self.interval = 250    # ms
        self.interval = config.interval    # ms
        
        fileTIME = datetime.datetime.now()
        File_timestamp = "%04d-%02d-%02d_%02d%02d%02d" % (fileTIME.year,fileTIME.month,fileTIME.day,fileTIME.hour, fileTIME.minute, fileTIME.second)

        self.fileNamme = '.\data\data_%s.txt'%File_timestamp
        print('Raw data record file name:%s'%self.fileNamme)
        # default parameters from config file
        self.x_ZERO = config.X_lower
        self.x_range = config.X_upper
        self.x_interval = config.X_grid_interval
        self.y_range_Upper = config.Y_upper
        self.y_range_Lower = config.Y_lower
        self.y_interval = config.Y_grid_interval
        self.unit = 'kPa'  # default value, will replaced by actual reading.
        #self.getReadingCommand = r"UPPER_VAL?\r\n"  # default pass and pac
        #self.getResp_rex = r'^[-]?([0-9]{1,}[.]?[0-9]*)'
                              
        self.lenth = config.Slope_lenth #  40 = 10s caculate the slowrate
                
        # QwtPlot property        
        # Initialize 坐标轴
        self.setCanvasBackground(Qt.white)  #Qt.white
        self.alignScales()
        grid = QwtPlotGrid()
        grid.attach(self)
        grid.setMajorPen(QPen(Qt.black, 0, Qt.DotLine))
        # x Axis property 
        #self.setAxisScaleDraw(QwtPlot.xBottom, TimeScaleDraw(self.cpuStat.upTime()))        
        #timeScale = QwtDateScaleDraw(Qt.LocalTime)
        #print(timeScale)
        #self.setAxisScaleDraw(QwtPlot.xBottom, timeScale) 
        
        self.setAxisScale(QwtPlot.xBottom, 0.0,self.x_range,self.x_interval)      
        
        
        
        #self.setAxisAutoScale(QwtPlot.yLeft,True)
        #self.setAxisScale(QwtPlot.yLeft,99.99,100.0,0.0005)
        self.setAxisScale(QwtPlot.yLeft,self.y_range_Lower,self.y_range_Upper,self.y_interval)
        self.setAxisLabelRotation(QwtPlot.xBottom,-45.0)
        
        self.x = np.arange(0.0, self.x_range + 1, 0.25)#0.25 for ONE POINT, THIS SHOULD BE Align to the reading rate:250ms

        #self.z = np.zeros(len(self.x), np.float)
        list = []
        for i in range(len(self.x)):
            list.append(0.0)
        self.z = np.array(list)  
       
        rlist = []
        
        for i in range(self.lenth):  # 10s
            rlist.append(0.0)       
        self.RateList = np.array(rlist)           

        self.setTitle("UUT Reading Monitor - OutPort(%s)\r\n"%(self.unit))
        #self.insertLegend(QwtLegend(), QwtPlot.RightLegend);
        
        self.curveL = QwtPlotCurve("UUT Reading")
        self.curveL.attach(self)
        pen = QPen(Qt.red)
        pen.setWidth(1.5)
        #pen.setWidth(1)
        self.curveL.setPen(pen)
        
        font = QFont()
        font.setFamily("Calibri")   #,Consolas
        font.setPointSize(16)
        
        # show the latest reading. line and point value
        self.peakMarker = m = QwtPlotMarker()
        m.setLineStyle(QwtPlotMarker.HLine)
        m.setLabelAlignment(Qt.AlignLeft | Qt.AlignTop)
        m.setLinePen(QPen(Qt.blue, 1.5, Qt.DashDotLine))
        
        text = QwtText('Reading: ----')
        text.setColor(Qt.red)       
        text.setBackgroundBrush(QBrush(self.canvasBackground()))        

        text.setFont(font)
        
        m.setLabel(text)
        # MarkPoint symbol
        m.setSymbol(QwtSymbol(QwtSymbol.Diamond,
                              QBrush(Qt.blue),
                              QPen(Qt.green),
                              QSize(7,7)))
        m.attach(self)
        
        # text marker  , display slope rate
        self.txtMarker = m = QwtPlotMarker()
        m.setValue(self.x_range/2, self.y_range_Upper - self.y_interval/2)   # show position
        m.setLabelAlignment(Qt.AlignRight | Qt.AlignBottom)
        text = QwtText('Slope Rate: ----')
        text.setFont(font)
        text.setColor(Qt.white)
        text.setBackgroundBrush(QBrush(Qt.black))
        text.setBorderPen(QPen(Qt.red, 2))

        m.setLabel(text)
        m.attach(self)        

        self.setAxisTitle(QwtPlot.xBottom, "Time (seconds)")
        self.setAxisTitle(QwtPlot.yLeft, "UUT - Reading(%s)"%(self.unit))
        
        self.replot()
        
 
        #self.startTimer(250)#ms# FOR GET READING        
        #self.starttime = time.clock();#unit: s    python2
        self.starttime = time.time()  # python3
        
        self.idx = 0
        self.readfmt = "%f" 
        self.Saveinfo("Starting...")
        
    def setPara(self,y_lower,y_upper,y_interval,x_interval,x_upper,x_lower): # y_lower,y_upper,y_interval,x_interval,X-Upper,x_lower
        self.y_range_Upper = y_upper
        self.y_range_Lower = y_lower
        self.x_interval = x_interval
        self.y_interval = y_interval
        self.x_range = x_upper
        self.x_ZERO = x_lower
        
        self.setAxisScale(QwtPlot.xBottom, self.x_ZERO,self.x_range,self.x_interval) # self.x_range
        #self.setAxisAutoScale(QwtPlot.yLeft,True)
        #self.setAxisScale(QwtPlot.yLeft,99.99,100.0,0.0005)
        self.setAxisScale(QwtPlot.yLeft,self.y_range_Lower,self.y_range_Upper,self.y_interval)        
        
        self.replot()
    
    def StartTimer(self):
        if not self.uut_dev:
            print("Please connect the device first!\r\n**********************************************")
            self.signal_showinfo.emit("Please connect the device first!")
            QMessageBox.warning(self, 'Warning','Please connect the device first!',QMessageBox.Yes,QMessageBox.Yes)
            
        else:
            if not self.timerId:
                print(self.interval)
                self.timerId = self.startTimer(self.interval)
                self.signal_showinfo.emit("Timer Started!")
    
    def StopTimer(self):
        if self.timerId:            
            if(QMessageBox.Yes == QMessageBox.warning(self, 'Warning','Are you want to stop the refresh of the curve?',QMessageBox.Yes | QMessageBox.No,QMessageBox.No)):
                self.killTimer(self.timerId)
                self.timerId = None
                self.signal_showinfo.emit("Timmer stoped!")
            
            
    
    def Connect(self,COMPort,baudrate):
        if self.uut_dev is None:
            try:
                self.uut_dev = device_py3.SerialDevice(False, False, port = COMPort , baudrate = baudrate) #'''args[0]'''            
                self.signal_showinfo.emit('Device opened success!')
                
                # Do Configuration settings:
                for cmd in config.pre_cmd:
                    print(self.sendcmd(self.uut_dev,cmd + "\r\n"))                
                    time.sleep(0.5)
                #print(self.sendcmd(self.uut_dev,"echo 0\r\n"))
                #print(self.sendcmd(self.uut_dev,"prompt off\r\n"))
                
            except Exception as e:
                print(e,'\r\nDevice opened failed!')
                self.signal_showinfo.emit('Device opened failed!\r\n**********************************************')
                QMessageBox.warning(self, 'Warning','Device opened failed! Please Check the COM port!!',QMessageBox.Yes,QMessageBox.Yes)
                
            

        else:
            print("Device already opened!")            
            self.signal_showinfo.emit("Device already opened!")
            QMessageBox.warning(self, 'Warning','Device has already opened!',QMessageBox.Yes,QMessageBox.Yes)
            
        
    def DisConnect(self):
        self.StopTimer()
        if self.uut_dev:
            self.uut_dev.close()  
            self.uut_dev = None
            print("Device disconnected! \r\n")
            self.signal_showinfo.emit("Device disconnected!")
            QMessageBox.warning(self, 'Warning','Device disconnected!',QMessageBox.Yes,QMessageBox.Yes)
        
    
    def showPeak(self, x,amplitude):
        self.peakMarker.setValue(x,amplitude)   # position
        label = self.peakMarker.label()
        label.setText('Reading: %f %s' %(amplitude,self.unit))
        self.peakMarker.setLabel(label)

    def showTxtLabel(self, x,y,txt):
        self.txtMarker.setValue(x,y)
        label = self.txtMarker.label()        
        label.setText(txt)
        self.txtMarker.setLabel(label)

    def alignScales(self):
        self.canvas().setFrameStyle(QFrame.Box | QFrame.Plain)
        self.canvas().setLineWidth(1)
        for i in range(QwtPlot.axisCnt):
            scaleWidget = self.axisWidget(i)
            if scaleWidget:
                scaleWidget.setMargin(0)
            scaleDraw = self.axisScaleDraw(i)
            if scaleDraw:
                scaleDraw.enableComponent(QwtAbstractScaleDraw.Backbone, False)
    
    def timerEvent(self, e):
        # send cmd and get readings, record times, X is second;
        # tfdata = self.uut_get_val(self.uut_dev, "VAL?\r")   #Wolf
        #tfdata = self.uut_get_val(self.uut_dev, "READ:VOLT:DC?\r")   # GW VOLT
        #ifdata = self.uut_get_val(self.uut_dev, "READ:CURR:DC?\r")   # GW CURRENT
        #tfdata = self.uut_get_val(self.uut_dev, "x?\r\n")   # 8508
        
        tfdata = self.uut_get_val(self.uut_dev, config.GetReadingCmd + "\r\n")  #"UPPER_VAL?\r\n")   # pass/pac
    
        self.showPeak(int(self.x_range),tfdata)	
        #print(tfdata)  #, "\t"	, ifdata

        self.z = np.concatenate((self.z[1:], self.z[:1]), 0)
        if(tfdata < 99999999.0):
            self.z[-1] = tfdata
        else:
            self.z[-1] = 99999999.0

        # Rate
        self.RateList = np.concatenate((self.RateList[1:], self.RateList[:1]), 0)
        self.RateList[-1] = tfdata 
        self.showTxtLabel(self.x_ZERO, self.y_range_Upper,str('Slope Rate:%f %s/min'%((self.RateList[-1]-self.RateList[0])/(self.lenth*250.0/1000.0/60.0) ,self.unit)))
          
        
        self.curveL.setData(self.x, self.z)
        self.setTitle("Max:%f, min:%f, Peak2Peak:%f "%(np.amax(self.z),np.amin(self.z),np.ptp(self.z)))
        self.setAxisTitle(QwtPlot.yLeft, "UUT - Reading(%s)"%(self.unit))
        self.replot()
        
        self.idx = self.idx + 1
        #Write file to txt log
        self.SaveData(tfdata)
        
        
        #now = time.clock(); 
        now = time.time();         
        if((now - self.starttime) > int(self.x_range)):  #  points (seconds)
            
            #self.starttime = time.clock(); # reset start time
            self.starttime = time.time(); # reset start time
           
            pngTIME = datetime.datetime.now()
            FILE_timestamp = "%04d-%02d-%02d_%02d%02d%02d" % (pngTIME.year,pngTIME.month,pngTIME.day,pngTIME.hour, pngTIME.minute, pngTIME.second)
            PNGFile = ('%s_%s' % (FILE_timestamp,'.png'))
            self.exportTo('.\pic\%s'%PNGFile, size=(1920, 1080), resolution=100)
            print(PNGFile, "The snaped curve picture has been created.")
        
        
    def uut_get_val(self,uut_dev_in, type = "x?\r\n"):      #[0-9]\d*\.\d+$    #r'[ -+]\d+\.\d+[Ee][-+][0-9]{2}'   #r'[-]?\d+\.\d+' 匹配正负小数
        cmd_encode = type.encode()
        
        m, self.unit = uut_dev_in.trx(cmd_encode,  config.rsp_regular)   #r'^[-]?([0-9]{1,}[.]?[0-9]*)')   # ^[-]?([0-9]{1,}[.]?[0-9]*)$   - 匹配正负小数和整数
        
        if m:
            return float(m.group(0))
        else:
            return 7200.0   ## 

    def sendcmd(self,uut_dev_in, cmd):    
        cmd_encode = cmd.encode()        
        uut_dev_in.write(cmd_encode)

        return cmd_encode
        
    def SaveData(self,tfdata):
        fh = open(self.fileNamme, "a")        
        now = datetime.datetime.now()
        timestamp = "%02d:%02d:%02d.%03d" % (now.hour, now.minute, now.second, now.microsecond /1000)

        rstr = "%s, %s, %s\n" % (self.idx,timestamp, tfdata)
        fh.write(rstr)
        fh.flush()

    def Saveinfo(self,info):
        fh = open(self.fileNamme, "a")       
        now = datetime.datetime.now()
        timestamp = "%04d-%02d-%02d_%02d%02d%02d" % (now.year,now.month,now.day,now.hour, now.minute, now.second)
        title = "%s,   %s\n" % (timestamp,info)
        fh.write(title)
        fh.write("\nSN,TIME,SenseNiose\n")
        fh.flush()

class CurveDemo(QMainWindow):
 
    def __init__(self, *args):
        QMainWindow.__init__(self, *args)
 
        self.plot = DataPlot(self)
        self.plot.setContentsMargins(5, 5, 5, 0)
        self.setCentralWidget(self.plot)
        
        # signal slot connect
        self.plot.signal_showinfo.connect(self.showInfo)
        
        font = QFont()
        font.setFamily("Calibri")   #,Consolas
        font.setPointSize(16)
        
        font2 = QFont()
        font2.setFamily("Calibri")
        font2.setPointSize(12)
        
        self.plot.setFont(font2)
       
        #  add toolbar
        toolBar = QToolBar(self)
        toolBar.setOrientation(Qt.Vertical)
        self.addToolBar(toolBar)
        # label COM
        lbl_COM = QLabel("COM:",toolBar)
        lbl_COM.setFont(font2)
        lbl_COM.setStyleSheet("")        
        toolBar.addWidget(lbl_COM)
        
        #lineEdit_COM
        self.lineEdit_COM =  QLineEdit(str(config.Port))
        self.lineEdit_COM.setFont(font2)    
        #self.lineEdit_COM.setMinimumWidth(100)
        toolBar.addWidget(self.lineEdit_COM)
        
        # label baudrate
        lbl_baud = QLabel("BAUD Rate:",toolBar)
        lbl_baud.setFont(font2)
        lbl_baud.setStyleSheet("") 
        toolBar.addWidget(lbl_baud)
        
        #lineEdit_baud 
        self.lineEdit_baud =  QLineEdit(str(config.BaudRate))
        #self.lineEdit_baud.setMinimumWidth(100)
        self.lineEdit_baud.setFont(font2)
        toolBar.addWidget(self.lineEdit_baud)
        
        # Connect device,              QIcon(const QString &filename);     // 从图像文件构造图标
        btnConnect = QToolButton(toolBar)
        btnConnect.setText("Connect")
        btnConnect.setFont(font2)
        btnConnect.setIcon(QIcon('./icon/Connect.png'))
        btnConnect.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolBar.addWidget(btnConnect)        
        btnConnect.clicked.connect(self.GetComSettings_Connect)

        # disConnect device
        btnDisConnect = QToolButton(toolBar)
        btnDisConnect.setText("DisConnect")
        btnDisConnect.setFont(font2)
        btnDisConnect.setIcon(QIcon('./icon/Disconnect.jfif'))
        btnDisConnect.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolBar.addWidget(btnDisConnect)        
        
        btnDisConnect.clicked.connect(self.plot.DisConnect)
        
        toolBar.addSeparator()        
        
        # Start timer
        btnStartTimer = QToolButton(toolBar)
        btnStartTimer.setText("Start Timer")
        btnStartTimer.setFont(font2)
        btnStartTimer.setIcon(QIcon('./icon/start.jfif'))
        btnStartTimer.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolBar.addWidget(btnStartTimer)
        btnStartTimer.clicked.connect(self.plot.StartTimer)
        
        # Stop timer
        btnStopTimer = QToolButton(toolBar)
        btnStopTimer.setText("Stop Timer")
        btnStopTimer.setFont(font2)
        btnStopTimer.setIcon(QIcon('./icon/stop.jfif'))
        btnStopTimer.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolBar.addWidget(btnStopTimer)
        btnStopTimer.clicked.connect(self.plot.StopTimer)
        
        toolBar.addSeparator()
        
        #X_LOWER   
        lbl_x_lower = QLabel("X-Lower:", toolBar)  
        lbl_x_lower.setFont(font2)    

        toolBar.addWidget(lbl_x_lower)
        
        self.LineEdit_x_lower= QLineEdit(str(0),toolBar)
        self.LineEdit_x_lower.setFont(font2)

        toolBar.addWidget(self.LineEdit_x_lower)
        
        #X_Upper   
        lbl_x_upper = QLabel("X-Upper:", toolBar)  
        lbl_x_upper.setFont(font2)    

        toolBar.addWidget(lbl_x_upper)
        
        
        self.LineEdit_x_upper= QLineEdit(str(config.X_upper),toolBar)
        self.LineEdit_x_upper.setFont(font2)

        toolBar.addWidget(self.LineEdit_x_upper)
        
        #X_interval   
        lbl_x_inteval = QLabel("X-Interval(s):", toolBar)  
        lbl_x_inteval.setFont(font2)    

        toolBar.addWidget(lbl_x_inteval)
        
        self.LineEdit_x_interval= QLineEdit(str(config.X_grid_interval),toolBar)
        self.LineEdit_x_interval.setFont(font2)

        toolBar.addWidget(self.LineEdit_x_interval)
        
        # Y_Lower 
        lbl_y_lower = QLabel("Y-Lower:", toolBar)
        lbl_y_lower.setFont(font2)

        toolBar.addWidget(lbl_y_lower)
        
        self.LineEdit_y_Lower = QLineEdit(str(config.Y_lower), toolBar)
        self.LineEdit_y_Lower.setFont(font2)

        toolBar.addWidget(self.LineEdit_y_Lower)
        
        # Y_Upper 
        lbl_y_uppwer = QLabel("Y-Upper:", toolBar)
        lbl_y_uppwer.setFont(font2)
 
        toolBar.addWidget(lbl_y_uppwer)
        
        self.LineEdit_Y_Upper = QLineEdit(str(config.Y_upper), toolBar)
        self.LineEdit_Y_Upper.setFont(font2)

        toolBar.addWidget(self.LineEdit_Y_Upper)
        # Y-Interval
        lbl_Y_Interval = QLabel("Y-Interval:", toolBar)
        lbl_Y_Interval.setFont(font2)

        toolBar.addWidget(lbl_Y_Interval)
        
        self.LineEdit_y_interval= QLineEdit(str(config.Y_grid_interval), toolBar)
        self.LineEdit_y_interval.setFont(font2)
   
        toolBar.addWidget(self.LineEdit_y_interval)      
        
        # Set axis para
        btnSet = QToolButton(toolBar)
        btnSet.setText("Set Paras")
        btnSet.setFont(font2)
        btnSet.setIcon(QIcon('./icon/Settings.jfif'))
        btnSet.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolBar.addWidget(btnSet)
        btnSet.clicked.connect(self.SetParas) 
                
        toolBar.addSeparator()
        
        # add print btn to toolbar
        btnPrint = QToolButton(toolBar)
        btnPrint.setText("Print")
        btnPrint.setFont(font2)
        btnPrint.setIcon(QIcon('./icon/print.jfif'))
        btnPrint.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolBar.addWidget(btnPrint)
        btnPrint.clicked.connect(self.print_)
        
        # add Export btn to toolbar
        btnExport = QToolButton(toolBar)
        btnExport.setText("Export")
        btnExport.setFont(font2)
        btnExport.setIcon(QIcon('./icon/snapshot.jfif'))
        btnExport.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolBar.addWidget(btnExport)
        btnExport.clicked.connect(self.exportDocument)
        
        toolBar.addSeparator()
        
        # add About btn to toolbar
        btnAbout = QToolButton(toolBar)
        btnAbout.setText("About")
        btnAbout.setFont(font2)
        btnAbout.setIcon(QIcon('./icon/about.png'))
        btnAbout.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolBar.addWidget(btnAbout)
        btnAbout.clicked.connect(self.About)
      
        #self.statusBar().setStyleSheet("QStatusBar::item{border: 5px}")
        self.statusBar().setStyleSheet("color:green")
        #self.statusBar().addPermanentWidget(VLine())
        self.statusBar().addPermanentWidget(QLabel("X = "))
        #self.statusBar().addPermanentWidget(VLine())
        self.statusBar().addPermanentWidget(QLabel("Y = "))
        
        #self.statusBar().addPermanentWidget(VLine())
        
        PermanentLabel = QLabel("Version:" + kProgVersion  + " Developed by " + kProgramDeveloperName + " Python. Running with " + kPythonVersion )
        font3 = QFont()
        font3.setFamily("Calibri")
        font3.setPointSize(12)
        PermanentLabel.setFont(font3)

        self.statusBar().setFont(font3)
        self.statusBar().addPermanentWidget(PermanentLabel)
        
        
        
        self.showInfo("Show info here ......")
        
        
        
    
    # get UI settings
    def SetParas(self):
        '''
        y_lower,y_upper,y_interval,x_interval,X-Upper,x_lower
        '''       
        self.plot.setPara(int(self.LineEdit_y_Lower.text()),
                          int(self.LineEdit_Y_Upper.text()),
                          int(self.LineEdit_y_interval.text()),
                          int(self.LineEdit_x_interval.text()),
                          int(self.LineEdit_x_upper.text()),
                          int(self.LineEdit_x_lower.text()))

    # get COM settings
    def GetComSettings_Connect(self):
        '''
            com, baud
        '''   
        self.showInfo('COM:%s, BaudRate: %d'%(self.lineEdit_COM.text(),int(self.lineEdit_baud.text())))        
        self.plot.Connect(self.lineEdit_COM.text(),int(self.lineEdit_baud.text()))
      
    def About(self):
        QMessageBox.about(self, "About", __doc__)
    
    
    def print_(self):
        printer = QPrinter(QPrinter.HighResolution)
 
        printer.setCreator('Bode example')
        printer.setOrientation(QPrinter.Landscape)
        printer.setColorMode(QPrinter.Color)
 
        docName = str(self.plot.title().text())
        if not docName:
            docName.replace('\n', ' -- ')
            printer.setDocName(docName)
 
        dialog = QPrintDialog(printer)
        if dialog.exec_():
            renderer = QwtPlotRenderer()
            if (QPrinter.GrayScale == printer.colorMode()):
                renderer.setDiscardFlag(QwtPlotRenderer.DiscardBackground)
                renderer.setDiscardFlag(QwtPlotRenderer.DiscardCanvasBackground)
                renderer.setDiscardFlag(QwtPlotRenderer.DiscardCanvasFrame)
                renderer.setLayoutFlag(QwtPlotRenderer.FrameWithScales)
            renderer.renderTo(self.plot, printer)
 
    def exportDocument(self):
        renderer = QwtPlotRenderer(self.plot)
        renderer.exportTo(self.plot, "./export/export_%s"%(str(datetime.datetime.now())))
     
    def showInfo(self, text=""):
        self.statusBar().showMessage(text)

                 
    def moved(self, point):
        info = "x =%g, y =%g" % (
            self.plot.invTransform(QwtPlot.xBottom, point.x()),
            self.plot.invTransform(QwtPlot.yLeft, point.y()),
            #self.plot.invTransform(QwtPlot.yRight, point.y())
            )
        self.showInfo(info)
 
    def selected(self, _):
        self.showInfo()
 
   
def make(argv):  
    demo = CurveDemo()      
    #demo.show()
    demo.showMaximized()
    return demo


if __name__ == "__main__":
    app = QApplication(sys.argv)    
    
    demo = make(sys.argv[1:]) 
    demo.setWindowTitle('Py Serial Monitor')
    demo.setWindowIcon(QIcon('./icon/Titleicon.jfif'))    
    
    sys.exit(app.exec_())
