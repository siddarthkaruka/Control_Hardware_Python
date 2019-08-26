# DAQTMREX01.CPP																
#																			
# This example demonstrates using the timer output on P3 DaqBoard3000
# to generate signals. Timer 0 will be a 1kHz Pulse Train, timer 
# 1 will be 50kHz	

# from IO import *

import time
import msvcrt
import daqx as daq
import daqxh as daqh

FREQ_DIV0	= 999   # for 1KHz		
FREQ_DIV1	= 19    # for 50 KHz

handle = daq.Open('DaqBoard3K0')
#settings for timer 0
daq.SetOption(handle, 0, daqh.DcofChannel, daqh.DcotTimerDivisor, FREQ_DIV0)
#settings for timer 1
daq.SetOption(handle, 1, daqh.DcofChannel, daqh.DcotTimerDivisor, FREQ_DIV1)

#turn on both timers simultaneously
daq.SetOption(handle, 0, daqh.DcofModule, daqh.DmotTimerControl, daqh.DcovTimerOn)

print "Signals currently being output...\nPress <Enter> to quit"

#while not msvcrt.kbhit():
#    time.sleep(10)

time.sleep(10)

daq.SetOption(handle, 0, daqh.DcofModule, daqh.DmotTimerControl, daqh.DcovTimerOff)
daq.Close(handle)
