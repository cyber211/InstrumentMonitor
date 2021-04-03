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
import socket

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
        self.Dev_COM = None
        self.uut_dev = None
     	print(args)
        if args: 
            self.Dev_COM  = args[0]            
        if self.Dev_COM:
            # Initialize Decice COM, 
            self.uut_dev = device.SerialDevice(False, False, port = self.Dev_COM, baudrate = 9600)
        else:
            # Initial LAN device
            #UUT PORT(NOTE: PC need to config the same ip section)
            self.uut_Client_ip = '169.254.1.3'
            self.uut_lan_port = 3490    #
            self.uut_buf_size = 1024

            try:
                self.uut_dev = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                Addr = (self.uut_Client_ip,self.uut_lan_port)
                self.uut_dev.connect(Addr)
                print('Connectin created!')                
                    
            except Exception as e:    # 
                raise Exception(e)
        #print(self.sendcmd('SYST:REM\r\n'))
        print(self.sendcmd('*CLS\r\n'))
        
        
        fileTIME = datetime.datetime.now()
        File_timestamp = "%04d-%02d-%02d_%02d%02d%02d" % (fileTIME.year,fileTIME.month,fileTIME.day,fileTIME.hour, fileTIME.minute, fileTIME.second)

        self.fileNamme = r'./data/data_%s.txt'%(File_timestamp)
        print(self.fileNamme)
        
        # Initialize 坐标轴
        self.setCanvasBackground(Qt.white)
        self.alignScales()
        grid = QwtPlotGrid()
        grid.attach(self)
        grid.setMajorPen(QPen(Qt.black, 0, Qt.DotLine))
		
        self.setAxisScale(QwtPlot.xBottom, 0.0,300.1,10.0)
        self.setAxisAutoScale(QwtPlot.yLeft,True)
        #self.setAxisScale(QwtPlot.yLeft,99.99,100.0,0.0005)
		
        self.x = np.arange(0.0, 300, 0.5)#0.5 for ONE POINT, THIS SHOULD BE Align to the reading rate:250ms
        print(self.x)
        #self.z = np.zeros(len(self.x), np.float)
        list = []
        for i in range(len(self.x)):
            list.append(0)
          
        self.z = np.array(list)          

        self.setTitle("UUT Reading Monitor -  (mA)")
        self.insertLegend(QwtLegend(), QwtPlot.RightLegend);

        
        self.curveL = QwtPlotCurve("UUT Reading")
        self.curveL.attach(self)

        self.curveL.setPen(QPen(Qt.red))

        self.setAxisTitle(QwtPlot.xBottom, "Time (seconds)")
        self.setAxisTitle(QwtPlot.yLeft, "UUT - Reading(mA)")
        self.replot()
 
        self.startTimer(500)# ms # FOR GET READING
		
        self.starttime = time.clock();#unit: s
        self.idx = 0
        self.readfmt = "%f" 
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
        if self.Dev_COM:  # SerialDevice
            # tfdata = self.uut_get_val(self.uut_dev, "VAL?\r")   #Wolf
            #tfdata = self.uut_get_val(self.uut_dev, "READ:VOLT:DC?\r")   # GW VOLT
            #ifdata = self.uut_get_val(self.uut_dev, "READ:CURR:DC?\r")   # GW CURRENT
            #tfdata = self.uut_get_val(self.uut_dev, "x?\r\n")   # 8508 
            #print('Getting Serial data.........')
            tfdata = self.uut_get_val(self.uut_dev, "UPPER_VAL?\r\n")   # pass/pac
            #tfdata = 1000*self.uut_get_val(self.uut_dev, "CONF:CURR:DC +1.000000E-01,+1.000000E-07;:MEAS:CURR:DC?\r\n")   # 8846
        else:    # LanDevice
            print('Getting Serial data.........')
            tfdata = 1000.0*float(self.Get_Lan_Response("CONF:CURR:DC +1.000000E-01,+1.000000E-07;:MEAS:CURR:DC?\r\n"))   # 8846 
	
    
        print(tfdata)  #, "\t"	, ifdata

        self.z = np.concatenate((self.z[1:], self.z[:1]), 0)
        self.z[-1] = tfdata 
        
        self.curveL.setData(self.x, self.z)
        self.replot()
		
        self.idx = self.idx + 1
		#Write file to txt log
        self.SaveData(tfdata)
		
        now = time.clock();		
        if((now - self.starttime) > 250):  # 250 point (seconds)
		    self.starttime = time.clock(); # reset start time
		   
		    pngTIME = datetime.datetime.now()
		    FILE_timestamp = "%04d-%02d-%02d_%02d%02d%02d" % (pngTIME.year,pngTIME.month,pngTIME.day,pngTIME.hour, pngTIME.minute, pngTIME.second)
		    PNGFile = ('%s_%s' % (FILE_timestamp,'.png'))
		    self.exportTo('.\pic\%s'%PNGFile, size=(1920, 1080), resolution=200)
		    print PNGFile, "The snaped curve picture has been created."


    def sendcmd(self,cmd):
        cmd_encode = cmd.encode()
        if self.Dev_COM:
            self.uut_dev.write(cmd)
        else:
            self.uut_dev.send(cmd_encode)
        return cmd_encode
    # LAN Device   reaponse
    def Get_Lan_Response(self,cmd):
        self.sendcmd(cmd)
        Rsp = ''
        rtn = ''
        while(1):
            recv_data = self.uut_dev.recv(self.uut_buf_size)
            Rsp += recv_data.decode()
            #print(Rsp)
            
            if ('\n' or '\r') in Rsp:
                Rsp.strip()
                break
        return  Rsp  
	
    # Serial devie response	
    def uut_get_val(self,uut_dev_in, type = "x?\r\n"):      #[0-9]\d*\.\d+$    #r'[ -+]\d+\.\d+[Ee][-+][0-9]{2}'
        cmd_encode = type.encode()        
        print(cmd_encode)
        uut_dev_in.flush()
        m = uut_dev_in.trx(type,  r'[0-9]\d*\.\d+$')
        print m.group(0);
        return float(m.group(0))
		
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
    -p, --targetCOM:     parameter for target UUT COM
    
    """ % (sys.argv[0], ))
   
def make(argv):
    DeviceCOM =None
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
            
    if DeviceCOM:	
        demo = DataPlot(DeviceCOM)
    else:
        demo = DataPlot()
    demo.resize(1080, 768)
    demo.show()

    return demo


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demoapp = make(sys.argv[1:]) 
    demoapp.Saveinfo(" Ending\n")  
    sys.exit(app.exec_())
