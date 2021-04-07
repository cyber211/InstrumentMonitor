
# COM
Port = 'COM37'
BaudRate = 9600


# X-axis
X_lower = 0
X_upper = 1800    # Max bufferd data 30min
X_grid_interval = 30

# Y-axis
Y_lower = -10
Y_upper = 2100
Y_grid_interval = 50

# Slope Rate caculate points number, 40 points  = 10s(40 *250ms)
Slope_lenth = 40

# pre-Configure Command
pre_cmd = [
            'echo off',
            'prompt off'
            ]
            
GetReadingCmd = "UPPER_VAL?"
rsp_regular = r'^[-]?([0-9]{1,}[.]?[0-9]*)'

# Get readings sample rate
interval  = 250  # ms
