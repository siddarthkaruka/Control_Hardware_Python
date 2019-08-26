# DAQDIGIOEX02.CPP																	
#																			
# This example demonstrates the Digital I/O on P3.
# DaqBook/3000 Series devices only.							
#																			
# Functions used:																
#	daqOpen(handle);																	
# daqIOWrite(handle, deviceType, devicePort, whichDevice, WhichExpPort, data)		
# daqIORead(handle, deviceType, devicePort, whichDevice, WhichExpPort, &data)		
#	daqClose(handle);

# from IO import *

import time
import msvcrt


WORD_P3		= 0xf0f0	

handle = daqOpen('DaqBoard3K0')
#configure port as output
daqIOWrite(handle, daqh.DiodtP3LocalDig16, daqh.DiodpP3LocalDigIR, 0, daqh.DioepP3, 1)
#send word from daq*
daqIOWrite(handle, daqh.DiodtP3LocalDig16, daqh.DiodpP3LocalDig16, 0, daqh.DioepP3, WORD_P3)
				
#configure port as input
daqIOWrite(handle, daqh.DiodtP3LocalDig16, daqh.DiodpP3LocalDigIR, 0, daqh.DioepP3, 0)
#read word on daq*
retvalue = daqIORead(handle, daqh.DiodtP3LocalDig16, daqh.DiodpP3LocalDig16, 0, daqh.DioepP3)

print "Digital input/output complete\n\n"
daqClose(handle)



    