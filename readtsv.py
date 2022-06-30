# try out different Read and plot...

import sys
import pandas as pd
import plotters as p
from plotters import tf

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy import signal

# TODO - pass in fn as argument
# fn = '../testvmr.dat1.tsv'
if len(sys.argv) > 1:
    fn = sys.argv[1]
else:
    fn = '../hotel-floor-more1.tsv'
    
# Maybe change backend behavior
# mpl.use('QtAgg')

data = pd.read_csv(fn,delimiter='\t')
t = data['t']; # Seconds
x = data['/1/vector.x']
y = data['/1/vector.y']
z = data['/1/vector.z']

N = len(t)
secs = (t.iloc[-1]-t.iloc[0])
mins = secs/60
hrs = mins/60
sr = round(N/secs)
print(f'Read {fn}, got {N} points ({secs:.1f} seconds, {mins:.1f} minutes, {hrs:.1f} hours) at {sr} Hz ')

p.threeplot(t,x,y,z,'nT','Twinleaf VMR Mag')
p.oneplot(t,tf(x,y,z),'nT','Twinleaf VMR Mag Total Field')


p.sg(tf(x,y,z),sr,'nT','Twinleaf VMR Mag Total Field')


pass
# seaborn:
# iloc()
# figsize()
# lineplot()
# tick_params()
# tight_layout()
# show()
#
