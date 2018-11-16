#!/usr/bin/python

import pmcgi
import os
import cgi
import pyromat as pm
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

# Print the header so the page will display even if something goes wrong
print("Content-type: text/html")
print("")


args = cgi.FieldStorage()

species = args['id'].value
Tmin = float(args['Tmin'].value)
Tmax = float(args['Tmax'].value)
Tstep = float(args['Tstep'].value)
p = float(args['p'].value)

unit_T = pm.config['unit_temperature']
unit_d = pm.config['unit_matter'] + '/' + pm.config['unit_volume']
unit_h = pm.config['unit_energy'] + '/' + pm.config['unit_matter']
unit_s = pm.config['unit_energy'] + '/' + pm.config['unit_matter'] + ' ' + pm.config['unit_temperature']
unit_cp = unit_s

T = np.arange(Tmin, Tmax+Tstep, Tstep)
SS = pm.get(species)
h,s,d = SS.hsd(T=T,p=p)
cp = SS.cp(T=T,p=p)

#f = plt.figure()
#ax = f.add_subplot(111)
#ax.plot(T,h)
#
#ax.xlabel('Temperature (' + unit_T + ')')
#ax.ylabel('Enthalpy (' + unit_h + ')')
#f.savefig('dat/isobar.png')

labels = ['Temperature', 'Density', 'Specific Heat', 'Enthalpy', 'Entropy']
units = [unit_T, unit_d, unit_cp, unit_h, unit_s]

tab_text = pmcgi.html_column_table(labels, units, (T,d,cp,h,s))

P = pmcgi.PMPage('test.html')
P.replace(tab_text, start='<table id="isobar_table"', stop="</table>", incl=True)

plotsrc = ' class="figure" src="isobar_plot.py?id={:s}&Tmax={:f}&Tmin={:f}&p={:f}"'.format(species,Tmax,Tmin,p)
P.replace(plotsrc, start='<img id="isobar_plot"', stop='>')

P.write()

