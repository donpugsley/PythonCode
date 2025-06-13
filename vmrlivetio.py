# Read and plot live data from one VMR using the tio tcp proxy interface
# and pyqtgraph, with a Qt Designer GUI

# 200 Hz is great as long as we don't use the LPF.  need faster LPF!

SR = 200 # VMR Sampling rate
WINDOWSEC = 4 # Seconds of data in plot window
BUFFERSIZE = int(SR*WINDOWSEC)
DATASIZE = 10 # Points of data to get at a time
WELCHFACTOR = 6 # Number of segments for Welch PSD

# Lowpass filter setup
lpforder = 6
lpfcutoff = 20

# SMA (Simple Moving Average) filter window
smawindow = 10

import sys
import argparse
import numpy as np
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont
import pyqtgraph as pg
from scipy import signal
import tldevice
from scipy.signal import butter, filtfilt

# Create lowpass digital filter coefficients
lpfb, lpfa = butter(lpforder, lpfcutoff, fs=SR, btype='low', analog=False)

# Fast alternative filter?
def sma_filter(data, window_size=smawindow):
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

def getTimebase(dev): # Get VMR timebase clock rate
  timebase_id = dev._tio.protocol.streamInfo['stream_timebase_id']
  return dev._tio.protocol.timebases[timebase_id]['timebase_Fs']

def vmrdevice(url,sr): # Open VMR port and set requested sampling rate
  dev = tldevice.Device(url)
  assert(dev.dev.name()=='VMR')
  timebasehz = getTimebase(dev)
  decimation = int(timebasehz/sr) # Set as a U32 integer decimation factor
  dev.vector.data.decimation(decimation)
  return dev

parser = argparse.ArgumentParser(prog='vectorMonitor', description='Vector Field Graphing Monitor')
parser.add_argument("url", nargs='?', default='tcp://localhost', help='URL: tcp://localhost')
args = parser.parse_args()
dev = vmrdevice(args.url,SR)

# GUI control variables
removeMean, showTF, clearPlotFlag, useLPF = [False]*4
showX, showY, showZ = [True]*3

# Load the QT Designer .ui file 
uiclass, baseclass = pg.Qt.loadUiType("VMR.ui")
class MainWindow(uiclass, baseclass):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.checkBoxDC.stateChanged.connect(self.DC_state_changed)
        self.checkBoxTF.stateChanged.connect(self.TF_state_changed)
        self.checkBoxX.stateChanged.connect(self.X_state_changed)
        self.checkBoxY.stateChanged.connect(self.Y_state_changed)
        self.checkBoxZ.stateChanged.connect(self.Z_state_changed)
        self.checkBoxLPF.stateChanged.connect(self.LPF_state_changed)
     
    def LPF_state_changed(self, int):
        global useLPF
        useLPF = self.checkBoxLPF.isChecked()
    def DC_state_changed(self, int):
        global removeMean
        removeMean = not self.checkBoxDC.isChecked()
    def TF_state_changed(self, int):
        global showTF, clearPlotFlag
        showTF = self.checkBoxTF.isChecked()
        clearPlotFlag = True
    def X_state_changed(self, int):
        global showX, clearPlotFlag
        showX = self.checkBoxX.isChecked()
        clearPlotFlag = True
    def Y_state_changed(self, int):
        global showY, clearPlotFlag
        showY = self.checkBoxY.isChecked()
        clearPlotFlag = True
    def Z_state_changed(self, int):
        global showZ, clearPlotFlag
        showZ = self.checkBoxZ.isChecked()
        clearPlotFlag = True

 # Create the main window and set up the UI
app = QApplication(sys.argv)
window = MainWindow() 
w = window.mywidget # This is the promoted GraphicsLayoutWidget used for fast plottting

# Create a modeless dialog box for text data display
dialog = QDialog(None)
dialog.setWindowTitle("Twinleaf VMR Data (latest, mean, peak to peak)")
XValue = QLabel()
YValue = QLabel()
ZValue = QLabel()
TFValue = QLabel()
layout = QVBoxLayout(dialog)
layout.addWidget(XValue)
XValue.setFont(QFont('Arial', 26))
layout.addWidget(YValue)
YValue.setFont(QFont('Arial', 26))
layout.addWidget(ZValue)
ZValue.setFont(QFont('Arial', 26))
layout.addWidget(TFValue)
TFValue.setFont(QFont('Arial', 26))
dialog.setLayout(layout)

tplot = w.addPlot(row=0,col=0) 
tplot.showGrid(True,True)

cx = tplot.plot(pen="r") # Add empty curves to the plot; set the curve data later
cy = tplot.plot(pen="g") 
cz = tplot.plot(pen="b") 
ctf = tplot.plot(pen="y")

splot = w.addPlot(row=1,col=0) 
splot.showGrid(True,True)
splot.setLogMode(True,True)
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

# Get some VMR data points TODO: get all available points
def getVMRdata(dev,DATASIZE): 
    # Get new data from the sensor
    d = dev.data(DATASIZE,timeaxis=False, flush=False)
    return np.array(d) # np.transpose(d) - this was a tio version change?  Working as of 6/11/2024

# Callback function - read data and update the plot when called
def update():
    global dev,cx,cy,cz, sx,sy,sz,stf, Dx,Dy,Dz,Dtf, BUFFERSIZE, DATASIZE, tplot,splot,clearPlotFlag,cx,cy,cz,ctf,sx,sy,sz,stf, XValue,YValue,ZValue,dialog,SR

    mx,my,mz,ax,ay,az,gx,gy,gz,bar,temp = getVMRdata(dev,DATASIZE)

    tf = np.sqrt(mx*mx+my*my+mz*mz) # "*" does point by point multiplication here
    Dx = np.append(Dx, mx)              
    Dy = np.append(Dy, my)              
    Dz = np.append(Dz, mz)  
    Dtf = np.append(Dtf, tf)
    
    if len(Dx) > BUFFERSIZE: # If we have filled the data buffer, keep only the end
        Dx = Dx[-BUFFERSIZE:]
        Dy = Dy[-BUFFERSIZE:]
        Dz = Dz[-BUFFERSIZE:]
        Dtf = Dtf[-BUFFERSIZE:]

    # Filtering is CPU intensive...
    if useLPF:
        if showX:
            # Dx = np.mean(Dx)+filtfilt(lpfb,lpfa,Dx-np.mean(Dx),method="gust") # end effects better with gust
            Dx = sma_filter(Dx)
        if showY:            
            # Dy = np.mean(Dy)+filtfilt(lpfb,lpfa,Dy-np.mean(Dy),method="gust")
            Dy = sma_filter(Dy)
        if showZ:
            # Dz = np.mean(Dz)+filtfilt(lpfb,lpfa,Dz-np.mean(Dz),method="gust")
            Dz = sma_filter(Dz)
        if showTF:
            # Dtf = np.mean(Dtf)+filtfilt(lpfb,lpfa,Dtf-np.mean(Dtf),method="gust")
            Dtf = sma_filter(Dtf)

    if clearPlotFlag:
        tplot.clear()
        splot.clear()        
        cx = tplot.plot(pen="r") # Add empty curves to the plot; set the curve data later
        cy = tplot.plot(pen="g") 
        cz = tplot.plot(pen="b") 
        ctf = tplot.plot(pen="y")
        sx = splot.plot(pen="r") # Add empty curves to the plot; set the curve data later
        sy = splot.plot(pen="g") 
        sz = splot.plot(pen="b") 
        stf = splot.plot(pen="y")
        clearPlotFlag = False

    # Time series plot
    if removeMean:
        if showX:
            cx.setData(Dx-np.mean(Dx))
        if showY:
            cy.setData(Dy-np.mean(Dy))             
        if showZ:
            cz.setData(Dz-np.mean(Dz))    
        if showTF:
            ctf.setData(Dtf-np.mean(Dtf))    
    else:
        if showX:
            cx.setData(Dx) 
        if showY:
            cy.setData(Dy)             
        if showZ:
            cz.setData(Dz)    
        if showTF:
            ctf.setData(Dtf)    

    
    # Spectrum
    if showX:
        # fx, Px = signal.periodogram(Dx,SR,detrend='constant',scaling='density')
        fx, Px = signal.welch(Dx,SR,nperseg=np.floor(BUFFERSIZE/WELCHFACTOR),detrend='constant',scaling='density')
        sx.setData(fx,np.sqrt(Px))
    if showY:
        # fy, Py = signal.periodogram(Dy,SR,detrend='constant',scaling='density')
        fy, Py = signal.welch(Dy,SR,nperseg=np.floor(BUFFERSIZE/WELCHFACTOR),detrend='constant',scaling='density')
        sy.setData(fy,np.sqrt(Py))
    if showZ:    
        # fz, Pz = signal.periodogram(Dz,SR,detrend='constant',scaling='density')
        fz, Pz = signal.welch(Dz,SR,nperseg=np.floor(BUFFERSIZE/WELCHFACTOR),detrend='constant',scaling='density')
        sz.setData(fz,np.sqrt(Pz))
    if showTF:       
        # ftf, Ptf = signal.periodogram(Dtf,SR,detrend='constant',scaling='density')
        ftf, Ptf = signal.welch(Dtf,SR,nperseg=np.floor(BUFFERSIZE/WELCHFACTOR),detrend='constant',scaling='density')
        stf.setData(ftf,np.sqrt(Ptf))

def updatedialog():
    global dev,cx,cy,cz, sx,sy,sz,stf, Dx,Dy,Dz,Dtf, BUFFERSIZE, DATASIZE, tplot,splot,clearPlotFlag,cx,cy,cz,ctf,sx,sy,sz,stf, XValue,YValue,ZValue,dialog

    XValue.setText(f'X: {Dx[-1]:.0f} nT\t {np.mean(Dx):.0f} nT mean\t {np.ptp(Dx):.0f} nT pkpk')
    YValue.setText(f'Y: {Dy[-1]:.0f} nT\t {np.mean(Dy):.0f} nT mean\t {np.ptp(Dy):.0f} nT pkpk')
    ZValue.setText(f'Z: {Dz[-1]:.0f} nT\t {np.mean(Dz):.0f} nT mean\t {np.ptp(Dz):.0f} nT pkpk')
    TFValue.setText(f'TF: {Dtf[-1]:.0f} nT\t {np.mean(Dtf):.0f} nT mean\t {np.ptp(Dtf):.0f} nT pkpk')
    dialog.show()


# Set an update and process Qt events until the window is closed.
plottimer = pg.QtCore.QTimer() # Create a timer
plottimer.timeout.connect(update) # Call the data collect/plot update routine when this timer ticks
dialogtimer = pg.QtCore.QTimer() # Create a timer
dialogtimer.timeout.connect(updatedialog) # Call the dialog text update routine when this timer ticks
plottimer.start(round(SR/DATASIZE)) # milliseconds!  Timer tick set for many (25-50) times a second
# plottimer.start(100) # milliseconds
dialogtimer.start(1000) # Timer tick set for 1 time a second
window.show()
app.exec() # Fall into event loop... exits when both plot and dialog are closed
dialog.close()