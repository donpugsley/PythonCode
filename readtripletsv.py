# try out different Read and plot...

import sys
from math import sqrt
import pandas as pd
import plotters as p
from plotters import tf, ftmget

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy import signal

# TODO - improve input flexibility
fn = '../testvmr.dat1.tsv'
if len(sys.argv) > 1:
    fn = sys.argv[1]
    # rpcid = sys.argv[2]
else:
    print(f'Usage: readtsv.py filename rpcid ')
    sys.exit()
    
#DEBUG
#fn = 'officetestat200hz.1.tsv'
    
doplots = True
    
# Maybe change backend behavior
# mpl.use('QtAgg')

df = pd.read_csv(fn,delimiter='\t')
# Drop unused columns (sync4 stuff) 
df = df[['t', # '/gps.lat','/gps.lon','/gps.alt',
         '/0/vector.x','/0/vector.y','/0/vector.z',
         '/1/vector.x','/1/vector.y','/1/vector.z',
         '/2/vector.x','/2/vector.y','/2/vector.z']]
data = df.dropna(axis=0) # Drop rows with nan
t = data['t']; # Seconds
B0x = data['/0/vector.x']; B0y = data['/0/vector.y']; B0z = data['/0/vector.z']
B1x = data['/1/vector.x']; B1y = data['/1/vector.y']; B1z = data['/1/vector.z']
B2x = data['/2/vector.x']; B2y = data['/2/vector.y']; B2z = data['/2/vector.z']

# Using three VMRs on George's 3D printed plate; its an equilateral triangle 
# with sides about 9.5" long, so d = 9.5*2.54 = 24.13 cm; sensor 0 is rotated 180 degrees wrt the other two.
# Calculate FTMG matrix while converting axes to Xiu paper geometry: X and Z horizontal, Y down
G = ftmget(24.13,B0z,-B0x,-B0y,-B1z,B1x,-B1y,-B2z,B2x,-B2y)

N = len(t)
secs = (t.iloc[-1]-t.iloc[0])
mins = secs/60
hrs = mins/60
sr = round(N/secs)
print(f'Read {fn}, got {N} points ({secs:.1f} seconds, {mins:.1f} minutes, {hrs:.1f} hours) at {sr} Hz ')
print(f'B0: Mean {np.mean(B0x):.0f}, {np.mean(B0y):.0f}, {np.mean(B0z):.0f}    Pkpk {np.ptp(B0x):.0f}, {np.ptp(B0y):.0f}, {np.ptp(B0z):.0f}')
print(f'B1: Mean {np.mean(B1x):.0f}, {np.mean(B1y):.0f}, {np.mean(B1z):.0f}    Pkpk {np.ptp(B1x):.0f}, {np.ptp(B1y):.0f}, {np.ptp(B1z):.0f}')
print(f'B2: Mean {np.mean(B2x):.0f}, {np.mean(B2y):.0f}, {np.mean(B2z):.0f}    Pkpk {np.ptp(B2x):.0f}, {np.ptp(B2y):.0f}, {np.ptp(B2z):.0f}')

if doplots:
    # plt.close('all') # TODO - Doesn't work
    
    
    p.threeplot(t,B0x,B0y,B0z,'nT','VMR B0')    
    p.threelsd(B0x,B0y,B0z,sr,'nT','VMR B0','B0x','B0y','B0z',6)
    p.threeplot(t,B1x,B1y,B1z,'nT','VMR B1')    
    p.threelsd(B1x,B1y,B1z,sr,'nT','VMR B1','B1x','B1y','B1z',6)
    p.threeplot(t,B2x,B2y,B2z,'nT','VMR B2')    
    p.threelsd(B2x,B2y,B2z,sr,'nT','VMR B2','B2x','B2y','B2z',6)
    

    # FTMG stuff here... TODO - better plot here - use a map!
    # p.threeplot(t,data['/gps.lat'],data['/gps.lon'],data['/gps.alt'],'gps',fn)
    # p.ftmg7plot(t,G,'nT/cm',fn)
    # p.threelsd(G[0,0,:],G[1,1,:],G[2,2,:],sr,'nT/m','VMR FTMG','XX','YY','ZZ',4)

    # p.lsd(t0,y0,sr,'nT','Twinleaf VMR Mag Y')
    # p.sg(x0,sr,'nT','Twinleaf VMR Mag X')
    # p.sg(y0,sr,'nT','Twinleaf VMR Mag Y')
    # p.sg(z0,sr,'nT','Twinleaf VMR Mag Z')

# return t,x,y,z

# seaborn:
# iloc()
# figsize()
# lineplot()
# tick_params()
# tight_layout()
# show()
#
