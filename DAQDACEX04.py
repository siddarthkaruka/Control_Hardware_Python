# DAQDACEX04.CPP                                                                 
#                                                                          
#                                                                          
# This example demonstrates the use of a dynamically updated user defined	
# AC waveform output from a DaqBoard2K.  Note that Dynamic waveforms are	
# only available to the DaqBoard2K.
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
#  daqDacTransferStart(handle, devicType, chan);							
#	daqDacWaveArm(handle, deviceType)										
#  daqDacTransferGetStat(DaqHandleT handle, DaqDacDeviceType deviceType,	
#                        DWORD chan, PDWORD active, PDWORD retCount)		
#	daqDacWaveDisarm(handle, deviceType)									
#	daqClose(handle);

import numpy as np
import time
import msvcrt
import daqx as daq
import daqxh as daqh

COUNT		= 2048
FREQ		= 2000

#You must set up both DAC channels with the same settings, or the output will be 
#incorrect. However, the buffer values may be different.

#set initial values for the buffers
#the buffer values must be interleaved, a 2D buffer is teh best way to do this
#The signals are dynamically updated square waves which will rise in Vmrs but 
#retain the same Vpp
buf0        = np.zeros((COUNT), dtype=np.uint16)
buf1        = np.zeros((COUNT), dtype=np.uint16) + 60000
buf         = (np.column_stack((buf0,buf1)))
buf_flatten = buf.flatten()

devName = daq.GetDeviceList()[0]
print "Connecting to %s\n\n" % devName  
handle = daq.Open(devName)
if handle == -1:
    print "Cannot conncet to device\n"
    print "Exit"
    sys.exit(handle)

#settings for channel 0
#Set for a static waveform
daq.DacSetOutputMode(handle, daqh.DddtLocal, 0, daqh.DdomDynamicWave);
#Immediate Trigger, (the final paramater is not yet used)
daq.DacWaveSetTrig(handle, daqh.DddtLocal, 0, daqh.DdtsImmediate, 0)
#Use the Local DAC clock
daq.DacWaveSetClockSource(handle, daqh.DddtLocal, 0, daqh.DdcsDacClock)
#Set the frequency
daq.DacWaveSetFreq(handle, daqh.DddtLocal, 0, FREQ)  
#Repeat infinatly, the final parameter (updateCount) is ignore with infinite loop
daq.DacWaveSetMode(handle, daqh.DddtLocal, 0, daqh.DdwmInfinite, 0)	
#for an infintite loop, the buffer must cycle
daq.DacWaveSetBuffer(handle, daqh.DddtLocal, 0, buf, COUNT, daqh.DdtmCycleOn + daqh.DdtmUpdateBlock)
#set channel 0 to be a user wave
daq.DacWaveSetUserWave(handle, daqh.DddtLocal, 0)	

#settings for channel1, see channel 0 settings for explanations
daq.DacSetOutputMode(handle, daqh.DddtLocal, 1, daqh.DdomDynamicWave)
daq.DacWaveSetTrig(handle, daqh.DddtLocal, 1, daqh.DdtsImmediate, 0)
daq.DacWaveSetClockSource(handle, daqh.DddtLocal, 1, daqh.DdcsDacClock)
daq.DacWaveSetFreq(handle, daqh.DddtLocal, 1, FREQ)
daq.DacWaveSetMode(handle, daqh.DddtLocal, 1, daqh.DdwmInfinite, 0)	
daq.DacWaveSetBuffer(handle, daqh.DddtLocal, 1, buf, COUNT, daqh.DdtmCycleOn + daqh.DdtmUpdateBlock)
daq.DacWaveSetUserWave(handle, daqh.DddtLocal, 1)

#load data from buffers
daq.DacTransferStart(handle, daqh.DddtLocal, 0);
daq.DacTransferStart(handle, daqh.DddtLocal, 1);
#begin output
daq.DacWaveArm(handle, daqh.DddtLocal);

print "\nOutputting signals on channels 0 and 1\n"
print "Press <Enter> to halt signal and quit"

retCount, active = (0,0)

while not msvcrt.kbhit():
    #transfer status and transfer count can be determined here
    active, retCount = daq.AdcTransferGetStat(handle)
    time.sleep(0.5)
    #The signals are dynamically updated square waves which will rise in Vrms but 
    #retain the same Vpp
    #see if you need to start over
    if buf[retCount%COUNT][0] == 60000:
        #update starting with the next count in buffer
        startindx = retCount%COUNT
        buf[startindx:,0] = 0
        buf[startindx:,1] = 60000
        buf[:startindx,0] = 0
        buf[:startindx,1] = 60000
    else:
        startindx = retCount%COUNT
        buf[startindx:,0] += 10000
        buf[startindx:,1] -= 10000
        buf[:startindx,0] += 10000
        buf[:startindx,1] -= 10000

#halt output
daq.DacWaveDisarm(handle, daqh.DddtLocal)

#Close device connection
daq.Close(handle)

