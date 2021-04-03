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

from qwt.qt.QtGui import QApplication, QPen, QBrush, QFrame
from qwt.qt.QtCore import QSize
from qwt.qt.QtCore import Qt
from qwt import (QwtPlot, QwtPlotMarker, QwtSymbol, QwtLegend, QwtPlotCurve,QwtPlotGrid,QwtPlotCanvas,
                 QwtAbstractScaleDraw)


class DataPlot(QwtPlot):

    def __init__(self, *args):
        QwtPlot.__init__(self, *args)

     	# Initialize Decice COM, 
        self.uut_dev = device.SerialDevice(False, False, port = args[0], baudrate = 115200)
        
        # Initialize 坐标轴
        self.setCanvasBackground(Qt.white)
        self.alignScales()
        grid = QwtPlotGrid()
        grid.attach(self)
        grid.setMajorPen(QPen(Qt.black, 0, Qt.DotLine))
		
        self.setAxisScale(QwtPlot.xBottom, 0.0,300.1,10.0)
        self.setAxisAutoScale(QwtPlot.yLeft,True)
        #self.setAxisScale(QwtPlot.yLeft,4.0,20.0,2.0)
		
        self.x = np.arange(0.0, 300.1, 0.5)#0.25 for ONE POINT, THIS SHOULD BE Align to the reading rate:250ms

        self.z = np.zeros(len(self.x), np.float)

        self.setTitle("UUT Reading Monitor")
        self.insertLegend(QwtLegend(), QwtPlot.RightLegend);

        
        self.curveL = QwtPlotCurve("UUT Reading")
        self.curveL.attach(self)

        self.curveL.setPen(QPen(Qt.red))

        self.setAxisTitle(QwtPlot.xBottom, "Time (seconds)")
        self.setAxisTitle(QwtPlot.yLeft, "UUT - Reading")
        self.replot()
 
        self.startTimer(500)#ms# FOR GET READING
		
        self.starttime = time.clock();#unit: s
        self.idx = 0
        self.readfmt = "%.5f" 
        self.Saveinfo("Starting...")



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
		tfdata = self.uut_get_val(self.uut_dev, "READ:VOLT:DC?\r")   # GW VOLT
		ifdata = self.uut_get_val(self.uut_dev, "READ:CURR:DC?\r")   # GW CURRENT

	
		print tfdata, "\t"	, ifdata

		self.z = np.concatenate((self.z[1:], self.z[:1]), 1)
		self.z[-1] = tfdata

		self.curveL.setData(self.x, self.z)
		self.replot()
		
		self.idx = self.idx + 1
		#Write file to txt log
		self.SaveData(tfdata,ifdata)
		
		now = time.clock();		
		if((now - self.starttime) > 250):  # 250 point (seconds)
		    self.starttime = time.clock(); # reset start time
		   
		    pngTIME = datetime.datetime.now()
		    FILE_timestamp = "%04d-%02d-%02d_%02d%02d%02d" % (pngTIME.year,pngTIME.month,pngTIME.day,pngTIME.hour, pngTIME.minute, pngTIME.second)
		    PNGFile = ('%s_%s' % (FILE_timestamp,'.png'))
		    self.exportTo('.\data0820\%s'%PNGFile, size=(1920, 1080), resolution=200)
		    print PNGFile, "The snaped curve picture has been created."


		
		
		
    def uut_get_val(self,uut_dev_in, type = "READ:VOLT:DC?\r\n"):      #[0-9]\d*\.\d+$
        m = uut_dev_in.trx(type,  r'[-+]\d+\.\d+[Ee][-+][0-9]{2}')
        print m.group(0);
        return float(m.group(0))
		
    def SaveData(self,tfdata,ifdata):
        fh = open(".\data0820\data.txt", "a")        
        now = datetime.datetime.now()
        timestamp = "%02d:%02d:%02d.%03d" % (now.hour, now.minute, now.second, now.microsecond /1000)

        str = "%s, %s, %s, %s\n" % (self.idx,timestamp, tfdata,ifdata)
        fh.write(str)
        fh.flush()

    def Saveinfo(self,info):
        fh = open("data.txt", "a")        
        now = datetime.datetime.now()
        timestamp = "%04d-%02d-%02d_%02d%02d%02d" % (now.year,now.month,now.day,now.hour, now.minute, now.second)
        title = "%s,   %s\n" % (timestamp,info)
        fh.write(title)

        fh.write("\nSN,TIME,VOLTAGE,CURRENT\n")

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
    -p, --targetCOM:     parameter for target UUT COM
    
    """ % (sys.argv[0], ))
   
def make(argv):
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
    #demo.Saveinfo(" Ending\n")  
    sys.exit(app.exec_())
