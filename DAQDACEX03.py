# DAQDACEX03.CPP                                                                 
#                                                                          
#                                                                          
# This example demonstrates the use of a static user defined AC waveform	
# output from a Daqboard device									 		
#																			
# Functions used:																
#	daqOpen(handle);																	
#	daqDacSetOutputMode(handle, devicType, chan, OutputMode)				
#  daqDacWaveSetTrig(handle, devicType, chan, triggerSource, rising);		
#	daqDacWaveSetClockSource(handle, devicType, chan, clockSource);			
#	daqDacWaveSetFreq(handle, devicType, chan, freq);						
#	daqDacWaveSetMode(handle, devicType, chan, waveformMode, updateCount);	
#	daqDacWaveSetUserWave(handle, devicType, chan);							
#	daqDacWaveSetBuffer(handle, devicType, chan, buffer, count, mask);		
#	daqDacWaveArm(handle, deviceType)										
#	daqDacWaveDisarm(handle, deviceType)									
#	daqClose(handle);

import numpy as np
import daqx as daq
import daqxh as daqh
import sys

COUNT		= 2048
FREQ		= 1000

buf0A    = np.zeros((COUNT/4), dtype=np.uint16)
buf1A    = np.zeros((COUNT/4), dtype=np.uint16) + 60000
buf0B    = np.zeros((COUNT/4), dtype=np.uint16) + 20000
buf1B    = np.zeros((COUNT/4), dtype=np.uint16) + 40000
buf0C    = np.zeros((COUNT/4), dtype=np.uint16) + 40000
buf1C    = np.zeros((COUNT/4), dtype=np.uint16) + 20000
buf0D    = np.zeros((COUNT/4), dtype=np.uint16) + 60000
buf1D    = np.zeros((COUNT/4), dtype=np.uint16)

buf0 = np.concatenate((buf0A,buf0B,buf0C,buf0D))
buf1 = np.concatenate((buf1A,buf1B,buf1C,buf1D))

buf = np.zeros((2,COUNT,), dtype=np.uint16)
buf[0] = buf0
buf[1] = buf1

devName = daq.GetDeviceList()[0]
print "Connecting to %s\n\n" % devName  
handle = daq.Open(devName)
if handle == -1:
    print "Cannot conncet to device\n"
    print "Exit"
    sys.exit(handle)

#settings for channel 0
#Set for a static waveform
daq.DacSetOutputMode(handle, daqh.DddtLocal, 0,  daqh.DdomStaticWave)
#Immediate Trigger, (the final paramater is not yet used)
daq.DacWaveSetTrig(handle,  daqh.DddtLocal, 0,  daqh.DdtsImmediate, 0)
#Use the Local DAC clock
daq.DacWaveSetClockSource(handle,  daqh.DddtLocal, 0,  daqh.DdcsDacClock)
#Set the frequency
daq.DacWaveSetFreq(handle,  daqh.DddtLocal, 0, FREQ)
#Repeat infinatly, the final parameter (updateCount) is ignore with infinite loop
daq.DacWaveSetMode(handle,  daqh.DddtLocal, 0,  daqh.DdwmInfinite, 0)	
#for an infintite loop, the buffer must cycle
daq.DacWaveSetBuffer(handle, daqh.DddtLocal, 0, buf0, COUNT, daqh.DdtmCycleOn + daqh.DdtmUpdateBlock)
#set channel 0 to be a user wave
daq.DacWaveSetUserWave(handle, daqh.DddtLocal, 0)	

#settings for channel1, see channel 0 settings for explanation
daq.DacSetOutputMode(handle, daqh.DddtLocal, 3,  daqh.DdomStaticWave)
daq.DacWaveSetTrig(handle,  daqh.DddtLocal, 3,  daqh.DdtsImmediate, 0)
daq.DacWaveSetClockSource(handle, daqh.DddtLocal, 3,  daqh.DdcsDacClock)
daq.DacWaveSetFreq(handle,  daqh.DddtLocal, 3, FREQ)
daq.DacWaveSetMode(handle,  daqh.DddtLocal, 3,  daqh.DdwmInfinite, 0)
daq.DacWaveSetBuffer(handle, daqh.DddtLocal, 3, buf1, COUNT, daqh.DdtmCycleOn + daqh.DdtmUpdateSingle)
daq.DacWaveSetUserWave(handle, daqh.DddtLocal, 3)

#begin output
daq.DacWaveArm(handle, daqh.DddtLocal);

print "\nOutputting signals on channels 0 and 1\n"
print "Press <Enter> to halt signal and quit"
raw_input("Press Enter to continue...")

daq.DacWaveDisarm(handle, daqh.DddtLocal)

#Close device connection
daq.Close(handle)

