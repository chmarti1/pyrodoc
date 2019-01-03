#!/usr/bin/python

import pmcgi
import os
import pyromat as pm
import numpy as np

source = '/var/www/html/live/pointdata.html'
param_line = 32
units_line = 43

# Print the header so the page will display even if something goes wrong
print("Content-type: text/html")
print("")

species, p1, s1, up, uT, uE, uM, uV = pmcgi.argparse([
        ('id',str,'mp.H2O'), 
        ('p1',float,101.325),
        ('s1',float,5),
        ('up',str,'kPa'),
        ('uT',str,'K'),
        ('uE',str,'kJ'),
        ('uM',str,'kg'),
        ('uV',str,'m3') ])

P = pmcgi.PMPage(source)

# Build the substance menu
# Include all multiphase collection members
values = []
for name in pm.dat.data:
    if name.startswith('mp.'):
        values.append(name)
        
# Insert the argument values
line = P.find_line('<!-- inputs -->')
P.insert(\
        pmcgi.html_select(values,select=False, selected=species),\
        (line+3,56), wait=True)

P.insert(str(p1), (line+4,73), wait=True)
P.insert(str(s1), (line+5,72), wait=True)

# Build the available units menu
# Pressure
line = P.find_line('<!-- units -->')
text = pmcgi.html_select(
        pm.units.pressure.get(), selected=up, select=False)
P.insert(text, (line+4, 55), wait=True)
# Temperature
text = pmcgi.html_select(
        pm.units.temperature.get(), selected=uT, select=False)
P.insert(text, (line+5, 58), wait=True)
# Energy
text = pmcgi.html_select(
        pm.units.energy.get(), selected=uE, select=False)
P.insert(text, (line+6, 53), wait=True)
# Matter
text = pmcgi.html_select(\
        pm.units.mass.get() + pm.units.molar.get(), \
        selected=uM, select=False)
P.insert(text, (line+7, 53), wait=True)
# Volume
text = pmcgi.html_select(\
        pm.units.volume.get(), selected=uV, select=False)
P.insert(text, (line+8, 53), wait=True)


# Apply the units
pm.config['unit_temperature'] = uT
pm.config['unit_pressure'] = up
pm.config['unit_matter'] = uM
pm.config['unit_energy'] = uE
pm.config['unit_volume'] = uV


# Find the results line in the original HTML
line = P.find_line('<!-- results -->')

# # # # # # # # # # # # # 
# Calculate the states  #
# # # # # # # # # # # # # 
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

# Insert the cgi call to build the image
# P.insert(
#         '<img class="figure" src="/cgi-bin/live/rankine_plot.py?id={:s}&p1={:f}&p2={:f}&up={:s}&uT={:s}&uE={:s}&uM={:s}&uV={:s}">'.format(
#                 species, float(p1), float(p2), up, uT, uE, uM, uV),\
#         (line+1,0))


# Construct table lists for displaying
# This inspires some future code to automatically collapse the arrays
# to make the float() conversions unnecessary
st = [1]
T = [float(T1)]
p = [float(p1)]
v = [float(v1)]
h = [float(h1)]
s = [float(s1)]
if x1>0:
    x = [float(x1)]
else:
    x = [float(x1)]
    #if (s1>F.ss(p=p1)[1]):
    #    x=['vapor']
    #else:
    #    x=['liquid']

# build label and unit lists
labels = ['','T', 'p', 'v', 'h', 's', 'x']
units = ['', uT, up, uV+'/'+uM, uE+'/'+uM, uE+'/'+uM+uT, '']

P.insert('<h3>Cycle States</h3><center>' +
        pmcgi.html_column_table(labels, units, (st,T,p,v,h,s,x), thousands=',')\
        + '</center>', (line+2,0), wait=True)

P.insert_exec()


P.write()
