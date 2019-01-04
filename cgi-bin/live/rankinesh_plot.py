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
from pyromat.aps import cycle
import numpy as np
import sys


species, p1, p2, T4, q34, eta12, eta23, eta34, eta45, up, uT, uE, uM, uV = pmcgi.argparse([
        ('id',str,'mp.H2O'), 
        ('p1',float,1.01325), 
        ('p2',float,10),
        ('T4',str,""),
        ('q34',str,""),
        ('eta12',float,1),
        ('eta23',float,1),
        ('eta34',float,1),
        ('eta45',float,1),
        ('up',str,'bar'),
        ('uT',str,'K'),
        ('uE',str,'kJ'),
        ('uM',str,'kg'),
        ('uV',str,'m3') ])

if q34:
    q34 = float(q34)
else:
    q34 = None
    
if T4:
    T4 = float(T4)
else:
    T4 = None


# Apply the units
pm.config['unit_temperature'] = uT
pm.config['unit_pressure'] = up
pm.config['unit_matter'] = uM
pm.config['unit_energy'] = uE
pm.config['unit_volume'] = uV


# # # # # # # # # # # # # 
# Calculate the states  #
# # # # # # # # # # # # # 
try:
    RC = cycle.RankineSHCycle()
    RC.param['p1'] = p1
    RC.param['p2'] = p2
    RC.param['q34'] = q34
    RC.param['T4'] = T4
    RC.param['eta12'] = eta12
    RC.param['eta23'] = eta23
    RC.param['eta34'] = eta34
    RC.param['eta45'] = eta45
    RC.update()
except:
    print("Content-type: text/html")
    print("")
    print(repr(sys.exc_info()[1]))
    exit(0)

# Build the T-s plot

f = plt.figure()
RC.tsplot(fig=f)

# Instead of saving to a file, write directly to stdout!
print("Content-type: image/png")
print("")
#f.savefig('test.png')
f.savefig(sys.stdout, format='png')

