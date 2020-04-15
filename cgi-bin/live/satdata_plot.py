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


species, T1, up, uT, uE, uM, uV = pmcgi.argparse([
        ('id'), 
        ('T1',float),
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
sf,sg = F.ss(T=T1)
# Build the T-s plot

f = plt.figure()
ax = f.add_subplot(111)


# Draw the saturation bounds
Tt = F.triple()[0]
Tc = F.critical()[0]
temp = (Tc - Tt) * .00001
T = np.linspace(Tt+temp, Tc-temp, 100)
sL, sV = F.ss(T)
ax.plot(sL, T, lw=2,color='k')
ax.plot(sV, T, lw=2,color='k')

#Add the point
ax.plot(sf,T1,lw=2,color='r',marker='x')
ax.plot(sg,T1,lw=2,color='r',marker='x')

# Dress up the plot
ax.set_xlabel('Entropy (' + uE + '/' + uM + uT + ')')
ax.set_ylabel('Temperature (' + uT + ')')
ax.grid(True)

# Instead of saving to a file, write directly to stdout!
print("Content-type: image/png")
print("")
f.savefig(sys.stdout, format='png')

