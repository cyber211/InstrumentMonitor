#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import serial
import time
import re
import time
import os
import sys

class SerialDevice(serial.Serial):
    def __init__(self, tx_log = False, rx_log = False, *args, **kwargs):
        self.tx_log = tx_log
        self.rx_log = rx_log
        serial.Serial.__init__(self, *args, **kwargs)
        #self.setTimeout(0.1)
        #self.setWriteTimeout(1.0)
        
    def read(self, size = 1):
        data = serial.Serial.read(self, size)
        if self.rx_log:
          sys.stdout.write(data)          
        return data 

    def readline(self):
        data = serial.Serial.readline(self)
        if self.rx_log:
          sys.stdout.write(data)
        return data 
        
        
    def write(self, data):
        serial.Serial.write(self, data)
        if self.tx_log:
          sys.stdout.write(data)
        return

    def trx(self, omsg, imsg, delay = 0, trx_wait = 2):
        m = None        
        #imsg = r'[ -+]\d+\.\d+[Ee][-+][0-9]{2}'
        if omsg: self.write(omsg) 
        start = time.time()

        line = ''
        m = None
        while True:
            line = line + self.readline().decode()
            #print(line)
            #line = r'+5.0002334E-01'
            
            if ('\n' in line) or ('\r' in line):  #
                print(line.strip())
                break

            now = time.time()
            print(type(now - start),now - start,(now - start) > trx_wait)
            
            if (now - start) > trx_wait:
               #raise Exception("trx timeout")
               print("trx timeout")
               break
               
        time.sleep(delay)
        
        if ',' in line: 
            m = line.split(',')[0].strip()
            m2 = line.split(',')[1].strip()
        return m,m2