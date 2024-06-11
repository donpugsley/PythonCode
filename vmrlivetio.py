# Read and plot live data from one VMR using the tio tcp proxy interface
# and pyqtgraph, with a Qt Designer GUI

# How fast will this go?
SR = 200 # VMR Sampling rate
WINDOWSEC = 20 # Seconds of data in plot window
BUFFERSIZE = SR*WINDOWSEC
DATASIZE = 25 # Points of data to get at a time

import sys
import argparse
import numpy as np
from PyQt6.QtWidgets import QApplication
import pyqtgraph as pg
from scipy import signal
import tldevice

def getTimebase(dev):
  timebase_id = dev._tio.protocol.streamInfo['stream_timebase_id']
  return dev._tio.protocol.timebases[timebase_id]['timebase_Fs']

def vmrdevice(url,sr):
  dev = tldevice.Device(url)
  assert(dev.dev.name()=='VMR')
  timebasehz = getTimebase(dev)
  decimation = int(timebasehz/sr)
  dev.vector.data.decimation(decimation)
  return dev

parser = argparse.ArgumentParser(prog='vectorMonitor', description='Vector Field Graphing Monitor')
parser.add_argument("url", nargs='?', default='tcp://localhost', help='URL: tcp://localhost')
args = parser.parse_args()
dev = vmrdevice(args.url,SR)

# Load the QT Designer .ui file 
uiclass, baseclass = pg.Qt.loadUiType("VMR.ui")
class MainWindow(uiclass, baseclass):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

# Create the main window and set up the UI
app = QApplication(sys.argv)
window = MainWindow() 
w = window.mywidget # This is the promoted GraphicsLayoutWidget 
tplot = w.addPlot(row=0,col=0) 
tplot.showGrid(True,True)

cx = tplot.plot(pen="r") # Add empty curves to the plot; set the curve data later
cy = tplot.plot(pen="g") 
cz = tplot.plot(pen="b") 
ctf = tplot.plot(pen="y")

splot = w.addPlot(row=1,col=0) 
splot.showGrid(True,True)
splot.setLogMode(True,False)
sx = splot.plot(pen="r") # Add empty curves to the plot; set the curve data later
sy = splot.plot(pen="g") 
sz = splot.plot(pen="b") 
stf = splot.plot(pen="y")

# TODO - FTMG version
# p = [w.addPlot(row=0, col=0), w.addPlot(row=0, col=1), w.addPlot(row=0, col=2),
#      w.addPlot(row=1, col=0), w.addPlot(row=1, col=1), w.addPlot(row=1, col=2),
#      w.addPlot(row=2, col=0), w.addPlot(row=2, col=1), w.addPlot(row=2, col=2)]
# c = [p[i].plot() for i in range(len(p))]

Dx = np.linspace(0,0,BUFFERSIZE) # Create the data array that will be plotted
Dy = np.linspace(0,0,BUFFERSIZE)
Dz = np.linspace(0,0,BUFFERSIZE)
Dtf = np.linspace(0,0,BUFFERSIZE)

# Get some VMR data points
def getVMRdata(dev,DATASIZE): 
    # Get new data from the sensor
    d = dev.data(DATASIZE+1)
    return np.array(d) # np.transpose(d) - this was a tio version change?  Working as of 6/11/2024

# Callback function - read data and update the plot when called
def update():
    global dev,cx,cy,cz, sx,sy,sz,stf, Dx,Dy,Dz,Dtf, BUFFERSIZE, DATASIZE # provide subfunction access to these

# Get some VMR data 
    mx,my,mz,ax,ay,az,gx,gy,gz,bar,temp = getVMRdata(dev,DATASIZE)

    tf = np.sqrt(mx*mx+my*my+mz*mz)
    Dx = np.append(Dx, mx)              
    Dy = np.append(Dy, my)              
    Dz = np.append(Dz, mz)  
    Dtf = np.append(Dtf, tf)
    
    if len(Dx) > BUFFERSIZE: # If we have filled the data buffer, keep only the end
        Dx = Dx[-BUFFERSIZE:]
        Dy = Dy[-BUFFERSIZE:]
        Dz = Dz[-BUFFERSIZE:]
        Dtf = Dtf[-BUFFERSIZE:]

    # Time series plot
    cx.setData(Dx-np.mean(Dx)) # Update the plot by setting the curve data
    cy.setData(Dy-np.mean(Dy))             
    cz.setData(Dz-np.mean(Dz))    
    ctf.setData(Dtf-np.mean(Dtf))    

    # Spectrum
    fx, Px = signal.periodogram(Dx-np.mean(Dx), SR)
    sx.setData(fx,Px)
   
    fy, Py = signal.periodogram(Dy-np.mean(Dy), SR)
    sy.setData(fy,Py)
    
    fz, Pz = signal.periodogram(Dz-np.mean(Dz), SR)
    sz.setData(fz,Pz)
       
    ftf, Ptf = signal.periodogram(Dtf-np.mean(Dtf), SR)
    stf.setData(ftf,Ptf)

# Set an update and process Qt events until the window is closed.
timer = pg.QtCore.QTimer() # Create a timer
timer.timeout.connect(update) # Call the update routine when the timer ticks
timer.start(round(SR/DATASIZE)) # Timer event set for 50 times a second
window.show()
app.exec() # Fall into event loop... exits when main window is closed
