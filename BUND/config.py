# -*- coding: utf-8 -*-

import os
import configparser 

# 当前文件路径
proDir = os.path.split(os.path.realpath(__file__))[0]

# 在当前文件路径下查找.ini文件
configPath = os.path.join(proDir, "Config.ini")
print(configPath)

conf = configparser.ConfigParser()

# 读取.ini文件
conf.read(configPath)

# print(conf.sections())  #['section1', 'section2', 'section3', 'section_test_1']
# print(conf.options('section1'))  # ['name', 'sex', 'option_plus']                  keys
# print(conf.items('section1')) # [('name', '2号'), ('sex', 'female'), ('option_plus', 'value')]


# get()函数读取section里的参数值
def read_item_value(section,key):
    return conf.get(section,key)
    
def write_item_value(section,key,value):    
    conf.set(section,key,value)
    conf.write(open(configPath,'w+'))

# COM
Port = read_item_value('COM','Port')
BaudRate = int(read_item_value('COM','BaudRate'))

# X-axis
X_lower = int(read_item_value('X_axis','X_lower'))
X_upper = int(read_item_value('X_axis','X_upper'))    # Max bufferd data 30min
X_grid_interval = int(read_item_value('X_axis','X_grid_interval'))

# Y-axis
Y_lower = float(read_item_value('Y_axis','Y_lower'))
Y_upper = float(read_item_value('Y_axis','Y_upper'))
Y_grid_interval = float(read_item_value('Y_axis','Y_grid_interval'))

# Slope Rate caculate points number, 40 points  = 10s(40 *250ms)
Slope_lenth = int(read_item_value('Slope','Slope_lenth'))

# pre-Configure Command
pre_cmd = []
for key in conf.options('pre_cmd'):
    pre_cmd.append(read_item_value('pre_cmd',key))

# Get readings            
GetReadingCmd = read_item_value('Reading','GetReadingCmd')
rsp_regular = read_item_value('Reading','rsp_regular')

# Get readings sample rate
interval  = int(read_item_value('timer','interval'))

if __name__ == '__main__':
    print(Port,BaudRate)
    print(X_lower,X_upper,X_grid_interval)
    print(Y_lower,Y_upper,Y_grid_interval)
    print(Slope_lenth)
    print(pre_cmd)
    
    print(GetReadingCmd,rsp_regular)
    print(interval)
    
    write_item_value('COM','Port','COM37')
    write_item_value('COM','BaudRate','115200')
    

    
    


