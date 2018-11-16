#!/usr/bin/python
#
#   Isobar plot generator

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import cgi
import pyromat as pm
import pmcgi
import numpy as np
import sys


args = cgi.FieldStorage()
        

# Parse the options
if 'id' in args:
    species = args['id'].value
else:
    error_response("T-S plots require an ID argument to specify the substance")
    
if 'Tmin' in args:
    try:
        Tmin = float(args['id'

species = args['id'].value
Tmin = float(args['Tmin'].value)
Tmax = float(args['Tmax'].value)
p = float(args['p'].value)

this = pm.get(species)

T = np.linspace(Tmin,Tmax,50)
h = this.h(T=T,p=p)
f = plt.figure()
ax = f.add_subplot(111)
ax.plot(T,h)

# Write the output
print("Content-type: image/png")
print("")
f.savefig(sys.stdout, format='png')
