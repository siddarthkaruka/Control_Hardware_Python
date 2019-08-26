# Control_Hardware_Python 
## Developed in 2014, uses Python 2

Python program to develop a GUI that can:
1. Interact with the data acquisition board that can provide both output voltages and take input signals
2. Use the output voltages to drive a galvo mirror hardware to perform laser scanning, with custom waveforms designed within the program
3. Use the output voltages to control the piezo stage that holds the sample on the microscope
4. Use the input ports to collect data for further analysis.

MainProgram.py is the actual program to exceute and all others are supporting files. This program contains the following classes:
1. Board : Manages connections to the IOtech daq board 
2. Form : Initialize waveform settings and provide options to update them
3. Zscan : Manages the piezo movements, uses a traingle waveform for continuous z-scans
4. Galvo : Manages connections to the galvo scanner, and provides various options for the scanning patterns
5. MainGUI : Provide a GUI option, with buttons that can control all the above mentioned functionality
