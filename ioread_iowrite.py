#DAQ3000 Board

#asynchronous (single) read and write from Digital Port A, B, and C

#Port A = [A7 .. A0], etc ...


#Note: input and putput of port A, B, C are determined by
#	daqSetOption(handle, portnr ,daqh.DcofChannel,daqh.DcotP2Local8Mode, DIRECTION )
#
# portnr = 0,1,2  for port A,B,C 
#
# DIRECTION = daqh.DcovDigitalInput   for  INPUT
#           = daqh.DcovDigitalOutput  for OUTPUT
#
#
# daqSetOption with DIRECTION = daqh.DcovDigitalInput   sets all port bits to HIGH
# daqSetOption with DIRECTION = daqh.DcovDigitalOutput  sets all port bits to LOW

import daqx as daq
import daqxh as daqh


#Configure Port A for input
daq.SetOption(handle,0,daqh.DcofChannel,daqh.DcotP2Local8Mode,daqh.DcovDigitalInput)

#Configure Port B for input
daq.SetOption(handle,1,daqh.DcofChannel,daqh.DcotP2Local8Mode,daqh.DcovDigitalInput)

#Configure Port C for input
daq.SetOption(handle,2,daqh.DcofChannel,daqh.DcotP2Local8Mode,daqh.DcovDigitalInput)

#Read byte from Port A
valA = daq.IORead(handle, daqh.DiodtP2Local8, daqh.DiodpP2Local8, 0, daqh.DioepP2)

#Read byte from Port B
valB = daq.IORead(handle, daqh.DiodtP2Local8, daqh.DiodpP2Local8, 1, daqh.DioepP2)

#Read byte from Port C
valC = daq.IORead(handle, daqh.DiodtP2Local8, daqh.DiodpP2Local8, 2, daqh.DioepP2)


#asynchronous (single) write to Digital Port A, B, and C

#Configure Port A for output
daq.SetOption(handle,0,daqh.DcofChannel,daqh.DcotP2Local8Mode,daqh.DcovDigitalInput)

#Configure Port B for output
daq.SetOption(handle,1,daqh.DcofChannel,daqh.DcotP2Local8Mode,daqh.DcovDigitalOutput)

#Configure Port C for output
daq.SetOption(handle,2,daqh.DcofChannel,daqh.DcotP2Local8Mode,daqh.DcovDigitalOutput)

#Write 1 to Port A
daq.IOWrite(handle, daqh.DiodtP2Local8, daqh.DiodpP2Local8, 0, daqh.DioepP2, 1)

#Write 2 to Port B
daq.IOWrite(handle, daqh.DiodtP2Local8, daqh.DiodpP2Local8, 1, daqh.DioepP2, 2)

#Write 4 to Port C
daq.IOWrite(handle, daqh.DiodtP2Local8, daqh.DiodpP2Local8, 2, daqh.DioepP2, 4)




# now read and write from 16bit port AB = [B7 ... A0] with A0 = LSB and B7 = MSB
#

#Writing
WORD_P3		= 0xf0f0
#Configure port as output
daq.IOWrite(handle, daqh.DiodtP3LocalDig16, daqh.DiodpP3LocalDigIR, 0, daqh.DioepP3, 1)
#Write 0xf0f0 to port AB
daq.IOWrite(handle, daqh.DiodtP3LocalDig16, daqh.DiodpP3LocalDig16, 0, daqh.DioepP3, WORD_P3)


#Reading
#configure port as input
daq.IOWrite(handle, daqh.DiodtP3LocalDig16, daqh.DiodpP3LocalDigIR, 0, daqh.DioepP3, 0);
#Read Port AB 
retvalue = daq.IORead(handle, daqh.DiodtP3LocalDig16, daqh.DiodpP3LocalDig16, 0, daqh.DioepP3)

#NOTE: the same method for controlling DIRECTION of 16bit AB port does not work for 8bit ports
# daq.IOWrite(handle, daqh.DiodtP2Local8, daqh.DiodpP2LocalIR, portnr, daqh.DioepP2, 1) does not configure port portnr as output
# daq.IOWrite(handle, daqh.DiodtP2Local8, daqh.DiodpP2LocalIR, portnr, daqh.DioepP2, 0) does not configure port portnr as input
# use daqSetOption instead, as shown earlier

#NOTE: daq.SetOption() can be used instead of daqIOWrite(... , daqh.DiodpP3LocalDigIR, ...) to control direction of port:
# daq.SetOption(handle,0,daqh.DcofChannel,daqh.DcotP3Local16Mode,daqh.DcovDigitalOutput) configures port AB as Output with all bits set LOW
# daq.SetOption(handle,0,daqh.DcofChannel,daqh.DcotP3Local16Mode,daqh.DcovDigitalInput)  configures port AB as Input with all bits set HIGH



