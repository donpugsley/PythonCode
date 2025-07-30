# Read and plot live data from one PPM using the tio tcp proxy interface
# and pyqtgraph, with a Qt Designer GUI

# How fast will this go?  200 Hzseems to work OK
# TODO - try streaming, the simple scheme loses some data points

SR = 480 # PPM Sampling rate - set this from the command line
TIMERTICKSPERSECOND = 20
DATASIZE = round(SR/TIMERTICKSPERSECOND) # Amount of data to grab at each tick
WINDOWSEC = 5    # Seconds of data in plot window
BUFFERSIZE = int(SR*WINDOWSEC)
WELCHFACTOR = 6 # Number of segments for Welch PSD

import sys
import argparse
import numpy as np
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont
import pyqtgraph as pg
from scipy import signal
import tldevice

def getTimebase(dev): # Get VMR timebase clock rate
  timebase_id = dev._tio.protocol.streamInfo['stream_timebase_id']
  return dev._tio.protocol.timebases[timebase_id]['timebase_Fs']

def ppmdevice(url): # Open VMR port and set requested sampling rate
  dev = tldevice.Device(url)
  if dev.dev.name()=='PPM':
      return dev
  else:      
      dev = tldevice.Device(url+'/0')
      return dev

parser = argparse.ArgumentParser(prog='PPM-Monitor', description='Scalar Field Graphing Monitor')
parser.add_argument("url", nargs='?', default='tcp://localhost', help='URL: tcp://localhost')
args = parser.parse_args()
dev = ppmdevice(args.url)

# GUI control variables
removeMean, clearPlotFlag = [False]*2
# showX, showY, showZ = [True]*3
showTF = True

# Load the QT Designer .ui file 
uiclass, baseclass = pg.Qt.loadUiType("PPM.ui")
class MainWindow(uiclass, baseclass):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.checkBoxDC.stateChanged.connect(self.DC_state_changed)
        # self.checkBoxTF.stateChanged.connect(self.TF_state_changed)
        # self.checkBoxX.stateChanged.connect(self.X_state_changed)
        # self.checkBoxY.stateChanged.connect(self.Y_state_changed)
        # self.checkBoxZ.stateChanged.connect(self.Z_state_changed)
     
    def DC_state_changed(self, int):
        global removeMean
        removeMean = not self.checkBoxDC.isChecked()
    # def TF_state_changed(self, int):
    #     global showTF, clearPlotFlag
    #     showTF = self.checkBoxTF.isChecked()
    #     clearPlotFlag = True
    # def X_state_changed(self, int):
    #     global showX, clearPlotFlag
    #     showX = self.checkBoxX.isChecked()
    #     clearPlotFlag = True
    # def Y_state_changed(self, int):
    #     global showY, clearPlotFlag
    #     showY = self.checkBoxY.isChecked()
    #     clearPlotFlag = True
    # def Z_state_changed(self, int):
    #     global showZ, clearPlotFlag
    #     showZ = self.checkBoxZ.isChecked()
    #     clearPlotFlag = True

 # Create the main window and set up the UI
app = QApplication(sys.argv)
window = MainWindow() 
w = window.mywidget # This is the promoted GraphicsLayoutWidget used for fast plottting

# Create a modeless dialog box for text data display
dialog = QDialog(None)
dialog.setWindowTitle("Twinleaf PPM Data (latest, mean, peak to peak)")
MinValue = QLabel()
MaxValue = QLabel()
MeanValue = QLabel()
layout = QVBoxLayout(dialog)
layout.addWidget(MinValue)
MinValue.setFont(QFont('Arial', 26))
layout.addWidget(MaxValue)
MaxValue.setFont(QFont('Arial', 26))
layout.addWidget(MeanValue)
MeanValue.setFont(QFont('Arial', 26))
dialog.setLayout(layout)

tplot = w.addPlot(row=0,col=0) 
tplot.showGrid(True,True)

# cx = tplot.plot(pen="r") # Add empty curves to the plot; set the curve data later
# cy = tplot.plot(pen="g") 
# cz = tplot.plot(pen="b") 
ctf = tplot.plot(pen="y")

splot = w.addPlot(row=1,col=0) 
splot.showGrid(True,True)
splot.setLogMode(True,False)
# sx = splot.plot(pen="r") # Add empty curves to the plot; set the curve data later
# sy = splot.plot(pen="g") 
# sz = splot.plot(pen="b") 
stf = splot.plot(pen="y")

# TODO - FTMG version
# p = [w.addPlot(row=0, col=0), w.addPlot(row=0, col=1), w.addPlot(row=0, col=2),
#      w.addPlot(row=1, col=0), w.addPlot(row=1, col=1), w.addPlot(row=1, col=2),
#      w.addPlot(row=2, col=0), w.addPlot(row=2, col=1), w.addPlot(row=2, col=2)]
# c = [p[i].plot() for i in range(len(p))]

# Dx = np.linspace(0,0,BUFFERSIZE) # Create the data array that will be plotted
# Dy = np.linspace(0,0,BUFFERSIZE)
# Dz = np.linspace(0,0,BUFFERSIZE)
Dtf = np.linspace(0,0,BUFFERSIZE)

# Get some PPM data points
def getPPMdata(dev): 
    # Get new data from the sensor
    d = dev.data(DATASIZE,timeaxis=False, flush=False)
    return np.array(d) # np.transpose(d) - this was a tio version change?  Working as of 6/11/2024

# Callback function - read data and update the plot when called
def update():
    # global dev,cx,cy,cz, sx,sy,sz,stf, Dx,Dy,Dz,Dtf, BUFFERSIZE, DATASIZE, tplot,splot,clearPlotFlag,cx,cy,cz,ctf,sx,sy,sz,stf, XValue,YValue,ZValue,dialog
    global dev,Dtf, BUFFERSIZE, tplot,splot,clearPlotFlag,ctf,stf, MinValue,MaxValue,MeanValue,dialog

    D = getPPMdata(dev)

    tf = D[:][0] # D[:][1] is signal quality
    # Dx = np.append(Dx, mx)              
    # Dy = np.append(Dy, my)              
    # Dz = np.append(Dz, mz)  
    Dtf = np.append(Dtf, tf)
    
    if len(Dtf) > BUFFERSIZE: # If we have filled the data buffer, keep only the end
        # Dx = Dx[-BUFFERSIZE:]
        # Dy = Dy[-BUFFERSIZE:]
        # Dz = Dz[-BUFFERSIZE:]
        Dtf = Dtf[-BUFFERSIZE:]


    if clearPlotFlag:
        tplot.clear()
        splot.clear()        
        # cx = tplot.plot(pen="r") # Add empty curves to the plot; set the curve data later
        # cy = tplot.plot(pen="g") 
        # cz = tplot.plot(pen="b") 
        ctf = tplot.plot(pen="y")
        # sx = splot.plot(pen="r") # Add empty curves to the plot; set the curve data later
        # sy = splot.plot(pen="g") 
        # sz = splot.plot(pen="b") 
        stf = splot.plot(pen="y")
        clearPlotFlag = False

    # Time series plot
    if removeMean:
        # if showX:
        #     cx.setData(Dx-np.mean(Dx))
        # if showY:
        #     cy.setData(Dy-np.mean(Dy))             
        # if showZ:
        #     cz.setData(Dz-np.mean(Dz))    
        if showTF:
            ctf.setData(Dtf-np.mean(Dtf))    
    else:
        # if showX:
        #     cx.setData(Dx) 
        # if showY:
        #     cy.setData(Dy)             
        # if showZ:
        #     cz.setData(Dz)    
        if showTF:
            ctf.setData(Dtf)    
    

    # Spectrum
    # if showX:
    #     # fx, Px = signal.periodogram(Dx,SR,detrend='constant',scaling='density')
    #     fx, Px = signal.welch(Dx,SR,nperseg=np.floor(BUFFERSIZE/WELCHFACTOR),detrend='constant',scaling='density')
    #     sx.setData(fx,np.sqrt(Px))
    # if showY:
    #     # fy, Py = signal.periodogram(Dy,SR,detrend='constant',scaling='density')
    #     fy, Py = signal.welch(Dy,SR,nperseg=np.floor(BUFFERSIZE/WELCHFACTOR),detrend='constant',scaling='density')
    #     sy.setData(fy,np.sqrt(Py))
    # if showZ:    
    #     # fz, Pz = signal.periodogram(Dz,SR,detrend='constant',scaling='density')
    #     fz, Pz = signal.welch(Dz,SR,nperseg=np.floor(BUFFERSIZE/WELCHFACTOR),detrend='constant',scaling='density')
    #     sz.setData(fz,np.sqrt(Pz))
    if showTF:       
        # ftf, Ptf = signal.periodogram(Dtf,SR,detrend='constant',scaling='density')
        ftf, Ptf = signal.welch(Dtf,SR,nperseg=np.floor(BUFFERSIZE/WELCHFACTOR),detrend='constant',scaling='density')
        stf.setData(ftf,np.sqrt(Ptf))

    MinValue.setText(f'Min: {np.min(Dtf):.0f} nT\t Max: {np.max(Dtf):.0f} nT\t Mean: {np.mean(Dtf):.0f} nT')
    dialog.show()


# Set an update and process Qt events until the window is closed.
timer = pg.QtCore.QTimer() # Create a timer
timer.timeout.connect(update) # Call the update routine when the timer ticks
timer.start(TIMERTICKSPERSECOND) # Timer event ticks 20 times a second
window.show()
app.exec() # Fall into event loop... exits when main window is closed
dialog.close()