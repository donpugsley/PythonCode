# try out different Read and plot...

import sys
import pandas as pd
import plotters as p
from plotters import tf

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy import signal

# TODO - improve input flexibility
# fn = '../testvmr.dat1.tsv'
if len(sys.argv) > 1:
    fn = sys.argv[1]
    rpcid = sys.argv[2]
else:
    print(f'Usage: readtsv.py filename rpcid ')
    sys.exit()
    
# DEBUG
#    fn = '../homeoffice2.tsv'
#    rpcid = 0
    
doplots = True
    
# Maybe change backend behavior
# mpl.use('QtAgg')

df = pd.read_csv(fn,delimiter='\t')
# Drop unused columns (sync4 stuff) that might contain nans
df = df[['t',f'/{rpcid}/vector.x',f'/{rpcid}/vector.y',f'/{rpcid}/vector.z']]
data = df.dropna(axis=0) # Drop rows with nan
t = data['t']; # Seconds
x = data[f'/{rpcid}/vector.x']
y = data[f'/{rpcid}/vector.y']
z = data[f'/{rpcid}/vector.z']

N = len(t)
secs = (t.iloc[-1]-t.iloc[0])
mins = secs/60
hrs = mins/60
sr = round(N/secs)
print(f'Read {fn}, got {N} points ({secs:.1f} seconds, {mins:.1f} minutes, {hrs:.1f} hours) at {sr} Hz ')

if doplots:
    plt.close('all') # TODO - Doesn't work
    
    p.threeplot(t,x,y,z,'nT','Twinleaf VMR Mag')
    
    p.oneplot(t,tf(x,y,z),'nT','Twinleaf VMR Mag Total Field')
    
    p.threelsd(x,y,z,sr,'nT','Twinleaf VMR Mag','X','Y','Z',4)

    p.lsd(t,y,sr,'nT','Twinleaf VMR Mag Y')
    
    p.sg(x,sr,'nT','Twinleaf VMR Mag X')
    p.sg(y,sr,'nT','Twinleaf VMR Mag Y')
    p.sg(z,sr,'nT','Twinleaf VMR Mag Z')

# return t,x,y,z

# seaborn:
# iloc()
# figsize()
# lineplot()
# tick_params()
# tight_layout()
# show()
#
