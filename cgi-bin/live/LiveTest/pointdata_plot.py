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


species, p1, s1, up, uT, uE, uM, uV = pmcgi.argparse([
        ('id'), 
        ('p1',float), 
        ('s1',float),
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

# We don't know where the state will be exactly
T1,x1 = F.T_s(p=p1,s=s1,quality=True)  # Saturation temperature
if x1>0:
    d1 = F.d(T=T1,x=x1)
    h1 = F.h(T=T1,x=x1)
else:
    d1 = F.d(T=T1,p=p1)
    h1 = F.h(T=T1,p=p1)
v1 = 1/d1

# Build the T-s plot

f = plt.figure()
ax = f.add_subplot(111)


# Draw the saturation bounds
Tt = F.triple()[0]
Tc = F.critical()[0]
temp = (Tc - Tt) * .0001
T = np.linspace(Tt+temp, Tc-temp, 100)
sL, sV = F.ss(T)
ax.plot(sL, T, lw=2,color='k')
ax.plot(sV, T, lw=2,color='k')

#Add the point
ax.plot(s1,T1,lw=2,color='r',marker='x')

#Add an isobar
Tmin = F.Tlim()[0]
Tmax = F.Tlim()[1]
smin = F.s(T=Tmin,p=p1)
smax = F.s(T=Tmax,p=p1)
s = np.linspace(smin,smax,100)
#T = F.T_s(p=p1,s=s)
#ax.plot(s,T,lw=2,color='b',linestyle=':')

# Dress up the plot
ax.set_xlabel('Entropy (' + uE + '/' + uM + uT + ')')
ax.set_ylabel('Temperature (' + uT + ')')
ax.grid(True)

# Instead of saving to a file, write directly to stdout!
print("Content-type: image/png")
print("")
f.savefig(sys.stdout, format='png')

