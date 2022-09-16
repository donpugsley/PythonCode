#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 29 08:40:15 2022

@author: pugsley

Analysis plot functions
"""
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy import signal

def threeplot(t,x,y,z,units,title):
    fig, ax = plt.subplots()
    mx = np.mean(x)
    my = np.mean(y)
    mz = np.mean(z)
    ax.plot(t, x-mx,label=f'X {mx:.0f} DC')
    ax.plot(t, y-my,label=f'Y {my:.0f} DC')
    ax.plot(t, z-mz,label=f'Z {mz:.0f} DC')
    ax.legend()
    ax.set_title(title)
    ax.set_ylabel(units)
    ax.set_xlabel('Time (seconds)', fontsize=12)
    plt.tick_params(axis='both', which='major', labelsize=12)
    # plt.axis([0, 1100, 0, 1100000])
    plt.grid(visible='true')
    plt.show()

def tf(x,y,z):
    return np.sqrt(x*x+y*y+z*z)

def oneplot(t,v,units,title):
    fig, ax = plt.subplots()
    mv = np.mean(v)
    ax.plot(t, v,label=f'{mv:.0f} DC')
    ax.legend()
    ax.set_title(title)
    ax.set_ylabel(units)
    ax.set_xlabel('Time (seconds)', fontsize=12)
    plt.tick_params(axis='both', which='major', labelsize=12)
    # plt.axis([0, 1100, 0, 1100000])
    plt.grid(visible='true')
    plt.show()

def lsd(t,v,sr,units,title):
    freqs, psd = signal.welch(v,fs=sr,nperseg=len(v)//2)
    lsd = np.sqrt(psd) 
    lsfreqs = freqs[1]+freqs[1:] # Duplicate first nonzero point, LS doesn't like 0 freq
    lspsd = signal.lombscargle(t,v,lsfreqs/(2*np.pi)) # Convert from Hz to rads/sec
    lslsd = np.sqrt(lspsd)
    plt.figure(figsize=(5, 4))
    plt.loglog(freqs, lsd, label='Welch')
    plt.loglog(lsfreqs, lslsd, label='Lomb-Scargle')
    plt.title('LSD  '+title)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel(units+'/rtHz')
    plt.tight_layout()
    plt.grid(visible='true')
    plt.show()

def threelsd(x,y,z,sr,units,title,lx,ly,lz,welchfactor):
    xfreqs, xpsd = signal.welch(x,fs=sr,nperseg=len(x)//welchfactor)
    lsdx = np.sqrt(xpsd)
    yfreqs, ypsd = signal.welch(y,fs=sr,nperseg=len(y)//welchfactor)
    lsdy = np.sqrt(ypsd)
    zfreqs, zpsd = signal.welch(z,fs=sr,nperseg=len(z)//welchfactor)
    lsdz = np.sqrt(zpsd)
    plt.figure(figsize=(5, 4))
    plt.loglog(xfreqs,lsdx, label='X')
    plt.loglog(yfreqs,lsdy, label='Y')
    plt.loglog(zfreqs,lsdz, label='Z')
    plt.legend()
    plt.title('LSD  '+title)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel(units+'/rtHz')
    plt.tight_layout()
    plt.grid(visible='true')
    plt.show()

def sg(v,sr,units,title):
    freqs, times, spectrogram = signal.spectrogram(v,fs=sr)
    plt.figure(figsize=(5, 4))
    plt.imshow(spectrogram, aspect='auto', origin='lower') # cmap='hot_r', 
    plt.title(title)
    plt.ylabel('Frequency')
    plt.xlabel('Time')
    plt.tight_layout()
    plt.ylim([0, sr/2])
    plt.show()
