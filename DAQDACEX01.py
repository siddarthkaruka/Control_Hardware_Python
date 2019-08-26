# DAQDACEX01.CPP																	
#																			
# This example demonstrates the use of DC output from any Daq* device		
#																			
# Functions used:																
#	daqOpen(handle);																	
#	daqDacSetOutputMode(handle, devicType, chan, OutputMode)				
#  daqDacWtMany(handle, deviceTypes, chans, dataVals, counts)				
#	daqClose(handle);

import daqx as daq
import daqxh as daqh

CHANCOUNT  = 2
OUT_ONE    = 2.5
OUT_TWO    = 3.0
chans      = [0, 1]
flt_vlt = [OUT_ONE, OUT_TWO]

devName = daq.GetDeviceList()[0]
print "Attempting to Connect with %s\n\n" % devName  
handle = daq.Open(devName)
if handle == -1:
    print "Cannot conncet to device\n"
    print "Exit"
    sys.exit(handle)

#DAC takes range of values from 0 for the Daq's minumum output to
#65535 for the Daq's maximum output

#The following routine automatically determines the max and min voltage for 
#the device used

maxVolt = 10.0
minVolt = -10.0

#set output settings
cnt_vlt = [int(round( (vlt-minVolt)*65535/(maxVolt-minVolt) )) for vlt in flt_vlt]
#set output mode of channel 1 and 2
daq.DacSetOutputMode(handle, daqh.DddtLocal, chans[0], daqh.DdomVoltage)
daq.DacSetOutputMode(handle, daqh.DddtLocal, chans[1], daqh.DdomVoltage)

#start output
daq.DacWtMany(handle, [daqh.DddtLocal, daqh.DddtLocal], chans, cnt_vlt)

print "Outputting %2.2f on chan 0 and %2.2f on chan 1\n" % (OUT_ONE, OUT_TWO)
print "Press any key to turn off DC output"

raw_input("Press Enter to continue...")

cnt_vlt = [int(round( (vlt-minVolt)*65535/(maxVolt-minVolt) )) for vlt in [0,0]]
daq.DacWtMany(handle, [daqh.DddtLocal, daqh.DddtLocal], chans, cnt_vlt)

#Close device connection
daq.Close(handle)


