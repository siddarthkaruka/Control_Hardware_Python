# DAQDACEX02.CPP                                                                 
#                                                                          
# This example demonstrates the use of predefined AC waveform output from		
# a Daqboard device									 					
#																			
# Functions used:																
#	daqOpen(handle);																	
#	daqDacSetOutputMode(handle, devicType, chan, OutputMode)				
#  daqDacWaveSetTrig(handle, devicType, chan, triggerSource, rising);		
#	daqDacWaveSetClockSource(handle, devicType, chan, clockSource);			
#	daqDacWaveSetFreq(handle, devicType, chan, freq);						
#	daqDacWaveSetMode(handle, devicType, chan, waveformMode, updateCount);	
#	daqDacWaveSetPredefWave(handle, devicType, chan, signalType, amp,		
#							offset, dutycycle, phaseshift);					
#	daqDacWaveSetBuffer(handle, devicType, chan, buffer, count, mask);		
#	daqDacWaveArm(handle, deviceType)										
#	daqDacWaveDisarm(handle, deviceType)									
#	daqClose(handle);

import numpy as np
import daqx as daq
import daqxh as daqh

COUNT		= 1000
FREQ		= 100
SIGNAL0     = daqh.DdwtSquare
SIGNAL1	    = daqh.DdwtSine
AMP0		= 4.0			        #amplitude Vpp
AMP1		= 3.0
OFF0		= 0 				    #Offset from 0
OFF1		= 0
DUTY0		= 50				    #Duty cycle in % of total signal
DUTY1		= 75
PHASE0		= 0				        #phase shift in % of cycle
PHASE1		= 0

deviceTypes = [daqh.DddtLocal, daqh.DddtLocal]
chans = [0, 1]
#Both the amplitude and the offset accept values ranging from 0 to 65535 
#corresponding to 0 to twice maxVolt for amplitude PP and minVolt to maxVolt 
#for the offset.  
maxVolt = 10.0
minVolt = -10.0

buf0    = np.zeros((COUNT,), dtype=np.uint16)
buf1    = np.zeros((COUNT,), dtype=np.uint16)

devName = daq.GetDeviceList()[0]
print "Connecting to %s\n\n" % devName  
handle = daq.Open(devName)
if handle == -1:
    print "Cannot conncet to device\n"
    print "Exit"
    sys.exit(handle)

#both channels must have the following same settings
chan = chans[0]
daq.DacSetOutputMode(handle, daqh.DddtLocal, chan, daqh.DdomStaticWave)
daq.DacWaveSetTrig(handle, daqh.DddtLocal, chan, daqh.DdtsImmediate, 1)
daq.DacWaveSetClockSource(handle, daqh.DddtLocal, chan, daqh.DdcsDacClock)
daq.DacWaveSetFreq(handle, daqh.DddtLocal, chan, FREQ*COUNT)  #output freq = clock freq/buffersize
daq.DacWaveSetMode(handle, daqh.DddtLocal, chan, daqh.DdwmInfinite, 0)
chan = chans[1]
daq.DacSetOutputMode(handle, daqh.DddtLocal, chan, daqh.DdomStaticWave)
daq.DacWaveSetTrig(handle, daqh.DddtLocal, chan, daqh.DdtsImmediate, 1)
daq.DacWaveSetClockSource(handle, daqh.DddtLocal, chan, daqh.DdcsDacClock)
daq.DacWaveSetFreq(handle, daqh.DddtLocal, chan, FREQ*COUNT)  #output freq = clock freq/buffersize
daq.DacWaveSetMode(handle, daqh.DddtLocal, chan, daqh.DdwmInfinite, 0)


#waveform settings
AMP0_DWORD = int(round(65535 * AMP0/(maxVolt-minVolt) ))
AMP1_DWORD = int(round(65535 * AMP1/(maxVolt-minVolt) ))
OFF0_DWORD = int(round(65535 * (OFF0-minVolt)/(maxVolt-minVolt) ))
OFF1_DWORD = int(round(65535 * (OFF1-minVolt)/(maxVolt-minVolt) ))

daq.DacWaveSetPredefWave(handle, daqh.DddtLocal, chans[0], SIGNAL0, AMP0_DWORD, OFF0_DWORD, DUTY0, PHASE0)
daq.DacWaveSetPredefWave(handle, daqh.DddtLocal, chans[1], SIGNAL1, AMP1_DWORD, OFF1_DWORD, 50, PHASE1)

#buffer settings
daq.DacWaveSetBuffer(handle, daqh.DddtLocal ,chans[0], buf0, COUNT, daqh.DdtmCycleOn)
daq.DacWaveSetBuffer(handle, daqh.DddtLocal ,chans[1], buf1, COUNT, daqh.DdtmCycleOn)


#begin output
daq.DacWaveArm(handle, daqh.DddtLocal);

print "\nOutputting signals on channels 0 and 1\n"
print "Press <Enter> to halt signal and quit"
raw_input("Press Enter to continue...")

daq.DacWaveDisarm(handle, daqh.DddtLocal)

#Close device connection
daq.Close(handle)

