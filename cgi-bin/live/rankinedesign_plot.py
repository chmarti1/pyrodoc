#!/usr/bin/python
#
#   Isobar plot generator

import matplotlib as mpl
# It is vital to set the matplotlib interface to one without a display
# BEFORE loading pyplot!  This makes things work behind Apache.
mpl.use('Agg')
import matplotlib.pyplot as plt
import pmcgi
import pyromat as pm
import numpy as np
import sys

import contextlib
import io
import sys

#Silence STDOUT warnings
#https://stackoverflow.com/questions/2828953/silence-the-stdout-of-a-function-in-python-without-trashing-sys-stdout-and-resto
@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = io.BytesIO()
    yield
    sys.stdout = save_stdout


species, p1, p2, T3, eta_pump, eta_turb, up, uT, uE, uM, uV = pmcgi.argparse([
        ('id'), 
        ('p1',float), 
        ('p2',float),
        ('T3',float),
        ('eta_pump',float),
        ('eta_turb',float),
        ('up'),
        ('uT'),
        ('uE'),
        ('uM'),
        ('uV') ])


# Apply the units
pm.config['unit_temperature'] = uT
pm.config['unit_pressure'] = up
pm.config['unit_matter'] = uM
pm.config['unit_energy'] = uE
pm.config['unit_volume'] = uV

this = pm.get(species)

# Calculate the states
F = pm.get(species)

with nostdout():
    #State 1 is a saturated liquid @ p1
    T1 = F.Ts(p=p1) #Temperature
    h1,null = F.hs(p=p1) #Enthalpy
    s1,null = F.ss(p=p1) #Entropy

    #State 2s is isentropic from p1-p2
    s2s = s1 #isentropic
    T2s = F.T_s(p=p2,s=s2s) #isentropic Temperature
    h2s = F.h(p=p2,T=T2s) #isentropic Enthalpy

    #State 2 is found by applying the isentropic efficiency
    Wps = h2s-h1 #Isentropic work
    Wp = Wps/eta_pump #Actual work
    h2 = Wp+h1 #Actual enthalpy at 2
    T2 = F.T_h(p=p2,h=h2) #Actual Temperature
    s2 = F.s(T=T2,p=p2) #Actual entropy

    #State 3 is based on known p3 & T3
    p3 = p2 #same pressure
    h3 = F.h(p=p3,T=T3) #Enthalpy
    s3 = F.s(p=p3,T=T3) #Entropy

    #State 4s is isentropic from p3-p4
    p4 = p1 #same as initial pressure
    s4s = s3 #isentropic
    T4s,x4s = F.T_s(p=p4,s=s4s,quality=True) #isentropic Temperature (including quality)
    if x4s<0: #superheated vapor quality will be -1
        h4s = F.h(T=T4s,p=p4) #Superheated vapor
    else:
        h4s = F.h(x=x4s,p=p4) #Liq/Vap mixture

    #State 4 is found by applying the isentropic efficiency
    Wts = h3-h4s #Isentropic work
    Wt = Wts*eta_turb #Actual work
    h4 = h3-Wt #Actual enthalpy at 4
    T4,x4 = F.T_h(p=p4,h=h4,quality=True) #Actual Temperature (including quality)
    if x4<0: #superheated vapor quality will be -1
        s4 = F.s(T=T4,p=p4) #Superheated vapor
    else:
        s4 = F.s(x=x4,p=p4) #Liq/Vap mixture

    # Build the T-s plot

    f = plt.figure()
    ax = f.add_subplot(111)
    color = 'r'
    marker = '.'
    smarker = 'x'

    # Draw the saturation bounds
    Tt = F.triple()[0]
    Tc = F.critical()[0]
    temp = (Tc - Tt) * .0001
    T = np.linspace(Tt+temp, Tc-temp, 100)
    sL, sV = F.ss(T)
    ax.plot(sL, T, lw=2,color='k')
    ax.plot(sV, T, lw=2,color='k')

    # Process 1-2s (isentropic compression of a liquid)
    s = np.linspace(s1,s2s,20)
    p = np.linspace(p1,p2,20)
    T = F.T_s(p=p,s=s)
    ax.plot(s,T,color+':',linewidth=1)
    ax.plot(s1,T1,color+marker)
    ax.plot(s2s,T2s,color+smarker)

    # Process 1-2 (actual compression of a liquid)
    s = np.linspace(s1,s2,20)
    p = np.linspace(p1,p2,20)
    T = F.T_s(p=p,s=s)
    ax.plot(s,T,color,linewidth=1.5)
    ax.plot(s2,T2,color+marker)

    #process 2-3 (heat add)
    s = np.linspace(s2,s3,40)
    p = p2*np.ones(s.shape)
    T = F.T_s(p=p,s=s)
    ax.plot(s,T,color,linewidth=1.5)
    ax.plot(s3,T3,color+marker)

    # Process 3-4s (isentropic compression of a liquid)
    s = np.linspace(s3,s4s,20)
    p = np.linspace(p3,p4,20)
    T = F.T_s(p=p,s=s)
    ax.plot(s,T,color+':',linewidth=1)
    ax.plot(s4s,T4s,color+smarker)

    #process 3-4 (actual expansion)
    s = np.linspace(s3,s4,20)
    p = np.linspace(p3,p4,20)
    T = F.T_s(p=p,s=s)
    ax.plot(s,T,color,linewidth=1.5)
    ax.plot(s4,T4,color+marker)

    #process 4-1 (heat rej)
    s = np.linspace(s4,s1,20)
    p = p4*np.ones(s.shape)
    T = F.T_s(p=p,s=s)
    ax.plot(s,T,color,linewidth=1.5)

# Dress up the plot
ax.set_xlabel('Entropy (' + uE + '/' + uM + uT + ')')
ax.set_ylabel('Temperature (' + uT + ')')
ax.grid(True)

# Instead of saving to a file, write directly to stdout!
print("Content-type: image/png")
print("")
f.savefig(sys.stdout, format='png')

