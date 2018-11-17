#!/usr/bin/python
#
#   Isobar plot generator

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import cgi
import pyromat as pm
import numpy as np
import sys


print("Content-type: image/png")
print("")

args = cgi.FieldStorage()

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

f.savefig(sys.stdout, format='png')
