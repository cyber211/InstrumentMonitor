#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under the terms of the PyQwt License
# Copyright (C) 2003-2009 Gerard Vermeulen, for the original PyQwt example
# Copyright (c) 2015 Pierre Raybaut, for the PyQt5/PySide port and further 
# developments (e.g. ported to PythonQwt API)
# (see LICENSE file for more details)
#
# Created: Wed Dec 05 10:07:24 2012   by: Bob Cao
# Copyright (c) 2013 - Bob <yongbo.cao@fluke.com>

"""Python version:2.7.2"""
"""PyQt GPL v4.9.1 for python v2.7(x32)
   QT Designer version:4.8.0
""" 
######################################################################################################
# 串口数据读取
# #1. 直接从给定的串口读取数据， 需要修改对应的串口命令已经对应的解析正则表达式
# #2. 解析读到的数据，直接画图，每三分钟截图一次并作保存
# #3. 记录读到的数据到data.txt文件中保存
# #4. 读取两个值，绘制两个曲线
#
# Used module:
#       # PythonQwt-0.5.5
#       # numpy
#       # 
# Usage:    cmd window :"python pySerialMonitor_Ploter_General.py -p COMX" 
#       # 
#       # 
######################################################################################################

import sys, getopt
import serial
import device
import time
import datetime

import numpy as np
import random

from qwt.qt.QtGui import (QApplication, QPen, QBrush, QFrame,QFont,
                          QMainWindow,QLabel,QHBoxLayout,QVBoxLayout,
                          QWidget)
from qwt.qt.QtCore import QSize
from qwt.qt.QtCore import Qt
from qwt import (QwtPlot, QwtPlotMarker, QwtSymbol, QwtLegend, QwtPlotCurve,QwtPlotGrid,QwtPlotCanvas,
                 QwtAbstractScaleDraw,QwtText)


class DataPlot(QwtPlot):

    def __init__(self, *args):
        QwtPlot.__init__(self, *args)

         # Initialize Decice COM, 
        self.uut_dev = device.SerialDevice(False, False, port = args[0], baudrate = 9600)
        fileTIME = datetime.datetime.now()
        File_timestamp = "%04d-%02d-%02d_%02d%02d%02d" % (fileTIME.year,fileTIME.month,fileTIME.day,fileTIME.hour, fileTIME.minute, fileTIME.second)

        self.fileNamme = '.\data\data_%s.txt'%File_timestamp
        print(self.fileNamme)
        self.x_range = 600.1
        self.x_interval = 10.0
        self.y_range_Upper = 7010.0
        self.y_range_Lower = 0.0
        self.y_interval = 250.0
        self.unit = 'kPa'  # default value, will replaced by actual reading.
        self.lenth = 40
        
        print(self.sendcmd(self.uut_dev,"echo 0\r\n"))
        time.sleep(1)
        print(self.sendcmd(self.uut_dev,"prompt off\r\n"))
        
        # QwtPlot property
        # Initialize 坐标轴
        self.setCanvasBackground(Qt.white)  #Qt.white
        self.alignScales()
        grid = QwtPlotGrid()
        grid.attach(self)
        grid.setMajorPen(QPen(Qt.black, 0, Qt.DotLine))
        
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
        self.insertLegend(QwtLegend(), QwtPlot.RightLegend);

        
        self.curveL = QwtPlotCurve("UUT Reading")
        self.curveL.attach(self)
        pen = QPen(Qt.red)
        pen.setWidth(1.5)
        self.curveL.setPen(pen)
        
        # show peak line and point value
        fn = self.fontInfo().family()
        self.peakMarker = m = QwtPlotMarker()
        m.setLineStyle(QwtPlotMarker.HLine)
        m.setLabelAlignment(Qt.AlignLeft | Qt.AlignTop)
        m.setLinePen(QPen(Qt.blue, 1.5, Qt.DashDotLine))
        
        text = QwtText('dfdfdfdf')
        text.setColor(Qt.red)
        text.setBackgroundBrush(QBrush(self.canvasBackground()))
        text.setFont(QFont(fn, 12, QFont.Bold))         
        m.setLabel(text)
        # MarkPoint symbol
        m.setSymbol(QwtSymbol(QwtSymbol.Diamond,
                              QBrush(Qt.blue),
                              QPen(Qt.green),
                              QSize(7,7)))
        m.attach(self)
        
        # text marker
        self.txtMarker = m = QwtPlotMarker()
        m.setValue(self.x_range/2, self.y_range_Upper - self.y_interval/2)   # show position
        m.setLabelAlignment(Qt.AlignRight | Qt.AlignBottom)
        text = QwtText('initial')
        text.setFont(QFont(fn, 20, QFont.Bold))
        text.setColor(Qt.white)
        text.setBackgroundBrush(QBrush(Qt.black))
        text.setBorderPen(QPen(Qt.red, 2))

        m.setLabel(text)
        m.attach(self)
        

        self.setAxisTitle(QwtPlot.xBottom, "Time (seconds)")
        self.setAxisTitle(QwtPlot.yLeft, "UUT - Reading(%s)"%(self.unit))
        self.replot()
 
        self.startTimer(250)#ms# FOR GET READING
        
        self.starttime = time.clock();#unit: s
        self.idx = 0
        self.readfmt = "%f" 
        self.Saveinfo("Starting...")

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
        
        tfdata = self.uut_get_val(self.uut_dev, "UPPER_VAL?\r\n")   # pass/pac
    
        self.showPeak(int(self.x_range),tfdata)    
        #print(tfdata)  #, "\t"    , ifdata

        self.z = np.concatenate((self.z[1:], self.z[:1]), 0)
        self.z[-1] = tfdata

        # Rate
        self.RateList = np.concatenate((self.RateList[1:], self.RateList[:1]), 0)
        self.RateList[-1] = tfdata 
        self.showTxtLabel(0, self.y_range_Upper,str('Slope Rate:%f %s/min'%((self.RateList[-1]-self.RateList[0])/(self.lenth*250.0/1000.0/60.0) ,self.unit)))
          
        
        self.curveL.setData(self.x, self.z)
        self.setTitle("Max:%f, min:%f, Peak2Peak:%f "%(np.amax(self.z),np.amin(self.z),np.ptp(self.z)))
        self.setAxisTitle(QwtPlot.yLeft, "UUT - Reading(%s)"%(self.unit))
        self.replot()
        
        self.idx = self.idx + 1
        #Write file to txt log
        self.SaveData(tfdata)
        
        now = time.clock();        
        if((now - self.starttime) > int(self.x_range)):  #  points (seconds)
            self.starttime = time.clock(); # reset start time
           
            pngTIME = datetime.datetime.now()
            FILE_timestamp = "%04d-%02d-%02d_%02d%02d%02d" % (pngTIME.year,pngTIME.month,pngTIME.day,pngTIME.hour, pngTIME.minute, pngTIME.second)
            PNGFile = ('%s_%s' % (FILE_timestamp,'.png'))
            self.exportTo('.\pic\%s'%PNGFile, size=(1920, 1080), resolution = 200)
            print(PNGFile, "The snaped curve picture has been created.")
        
        
    def uut_get_val(self,uut_dev_in, type = "x?\r\n"):      #[0-9]\d*\.\d+$    #r'[ -+]\d+\.\d+[Ee][-+][0-9]{2}'
        cmd_encode = type.encode()
        
        m, self.unit = uut_dev_in.trx(type,  r'^[-]?([0-9]{1,}[.]?[0-9]*)')   # r'[-]?\d+\.\d+')
        #print m.group(0);
        if m:
            return float(m.group(0))
        else:
            return 10.0

    def sendcmd(self,uut_dev_in, cmd):    
        cmd_encode = cmd.encode()        
        uut_dev_in.write(cmd_encode)

        return cmd_encode
        
    def SaveData(self,tfdata):
        fh = open(self.fileNamme, "a")        
        now = datetime.datetime.now()
        timestamp = "%02d:%02d:%02d.%03d" % (now.hour, now.minute, now.second, now.microsecond /1000)

        str = "%s, %s, %s\n" % (self.idx,timestamp, tfdata)
        fh.write(str)
        fh.flush()

    def Saveinfo(self,info):
        fh = open(self.fileNamme, "a")       
        now = datetime.datetime.now()
        timestamp = "%04d-%02d-%02d_%02d%02d%02d" % (now.year,now.month,now.day,now.hour, now.minute, now.second)
        title = "%s,   %s\n" % (timestamp,info)
        fh.write(title)

        fh.write("\nSN,TIME,SenseNiose\n")

        fh.flush()
        
def make():
    demo = DataPlot()
    
    demo.resize(500, 300)
    demo.show()
    return demo

    # option usage 
def usage():
    sys.stderr.write("""USAGE: %s [options]
    options:
    -h, --help:             show this usage, example cmdline:" python thisfile.py -p COM24",
    -p, --targetCOM:        parameter for target UUT COM
    
    """ % (sys.argv[0], ))
   
def make(argv):   # 重构
    try:
        opts, args = getopt.getopt(argv,"hp:",["targetCOM="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
        
    for opt, arg in opts:
        if opt in ('-h','--help'):
            usage()
            sys.exit()
        elif opt in ("-p", "--targetSCOM"):
            DeviceCOM = arg
        else:
            usage()
            sys.exit(0)
            
    demo = DataPlot(DeviceCOM)
    demo.resize(1080, 768)
    
    demo.show()

    return demo


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    demo = make(sys.argv[1:]) 
    demo.setWindowTitle('Py Serial Monitor')
    demo.Saveinfo(" Ending\n")  
    sys.exit(app.exec_())
