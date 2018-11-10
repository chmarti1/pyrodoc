#!/usr/bin/python
import pmcgi
import os
import cgi
import pyromat as pm
import numpy as np

# Print the header so the page will display even if something goes wrong
print("Content-type: text/html")
print("")

args = cgi.FieldStorage()

Tmin = float(args['Tmin'].value)
Tmax = float(args['Tmax'].value)


T = np.linspace(Tmin, Tmax, 50)
s = pm.get('mp.H2O')
h,s,d = s.hsd(T=T)

unit_T = pm.config['unit_temperature']
unit_d = pm.config['unit_matter'] + '/' + pm.config['unit_volume']
unit_h = pm.config['unit_energy'] + '/' + pm.config['unit_matter']
unit_s = pm.config['unit_energy'] + '/' + pm.config['unit_matter'] + ' ' + pm.config['unit_temperature']

labels = ['T', 'd', 'h', 's']
units = [unit_T, unit_d, unit_h, unit_s]

tab_text = pmcgi.html_column_table(labels, units, (T,d,h,s))

P = pmcgi.PMPage('../html/live.html')
P.replace(tab_text, start="<table", stop="</table>", incl=True)

P.write()
