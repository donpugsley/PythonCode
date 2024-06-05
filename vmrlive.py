# Read and plot live data from 3 VMRs and a Sync4, 200 Hz data rate
# 
# Initial Twinleaf gearUSB connection provides serial data; using tio-proxy
# toggles the data stream into binary mode, be aware if you are switching 
# back and forth

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
import serial
from ReadLine import *
from scipy import signal

# This is the serial port created when the VMR is plugged in - may need chmod 666 before use
portName = "/dev/ttyACM0"                      
baudrate = 230400
ser = serial.Serial(portName,baudrate)
reader = ReadLine(ser) # Initialize an efficient line reader

app = pg.mkQApp("Serial Data Plot") # Quicktime app
w = pg.GraphicsLayoutWidget(show=True) # Main window
plt = w.addPlot() # Empty plot taking up the whole window
plt.showGrid(True,True)
plt.setLogMode(True,False)
cx = plt.plot(pen="r") # Empty curves on the plot; set the curve data later
cy = plt.plot(pen="g") 
cz = plt.plot(pen="b") 

windowWidth = 1000 # width of the main window, also the size of the data buffer in samples
w.resize(windowWidth,round(0.6*windowWidth)) 
Dx = np.linspace(0,0,windowWidth) # Create the data array that will be plotted
Dy = np.linspace(0,0,windowWidth)
Dz = np.linspace(0,0,windowWidth)

# Function to extract values from one line of VMR data
def parseVMRserialline(line): 
    id,ct,mx,my,mz,ax,ay,az,gx,gy,gz,bar,temp = [-1]*13 # Initialize to an error flag value
    if line[0:2] == ':/': # We have VMR Data on a Sync4 port
        A = line.split()
        if len(A)==13:
            id = int(A[0][2]) # Sync4 port ID
            ct,mx,my,mz,ax,ay,az,gx,gy,gz,bar,temp = [float(s) for s in A[1:]] # Extract values
    return id,ct,mx,my,mz,ax,ay,az,gx,gy,gz,bar,temp

# Callback function - read data and update the plot when called
def update():
    global cx,cy,cz, Dx,Dy,Dz, windowWidth # provide subfunction access to these

    while ser.inWaiting() > 0: # While data is available
        b1 = (reader.readline()) # Read a complete line using the efficient line reader
        if len(b1) > 10:
            line = b1.decode('utf-8','ignore') # convert raw bytes to string
            # print(line)
            id,ct,mx,my,mz,ax,ay,az,gx,gy,gz,bar,temp = parseVMRserialline(line)

            if id == 0: # Choose one of the three VMRs to plot
                Dx = np.append(Dx, mx)              
                Dy = np.append(Dy, my)              
                Dz = np.append(Dz, mz)  
                
                if len(Dx) > windowWidth: # If we have filled the data buffer, keep only the end
                    Dx = Dx[-windowWidth:]
                    Dy = Dy[-windowWidth:]
                    Dz = Dz[-windowWidth:]

    # Time series plot
    # cx.setData(Dx) # Update the plot by setting the curve data
    # cy.setData(Dy)             
    # cz.setData(Dz)    

    # Spectrum
    fx, Px = signal.periodogram(Dx-np.mean(Dx), 200)
    cx.setData(fx,Px)
   
    fy, Py = signal.periodogram(Dy-np.mean(Dy), 200)
    cy.setData(fy,Py)
    
    fz, Pz = signal.periodogram(Dz-np.mean(Dz), 200)
    cz.setData(fz,Pz)
       

# Set an update and process Qt events until the window is closed.
timer = QtCore.QTimer() # Create a timer
timer.timeout.connect(update) # Call the update routine when the timer ticks
timer.start(50) # Timer event set for 50 times a second
pg.exec() # Fall into event loop... exits when main window is closed
