#!/usr/bin/python

import pmcgi
import os
import pyromat as pm
import numpy as np

source = 'rankine.html'
param_line = 32
units_line = 43


# Print the header so the page will display even if something goes wrong
print("Content-type: text/html")
print("")

species, p1, p2, up, uT, uE, uM, uV = pmcgi.argparse([
        ('id',str,'mp.H2O'), 
        ('p1',float,1.01325), 
        ('p2',float,10),
        ('up',str,'bar'),
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
        
P.insert(\
        pmcgi.html_select(values,select=False, selected=species),\
        (param_line,56), wait=True)

# Insert the argument values
P.insert(str(p1), (param_line+1,83), wait=True)
P.insert(str(p2), (param_line+2,80), wait=True)

# Build the available units menu
# Pressure
text = pmcgi.html_select(
        pm.units.pressure.get(), selected=up, select=False)
P.insert(text, (units_line, 55), wait=True)
# Temperature
text = pmcgi.html_select(
        pm.units.temperature.get(), selected=uT, select=False)
P.insert(text, (units_line+1, 58), wait=True)
# Energy
text = pmcgi.html_select(
        pm.units.energy.get(), selected=uE, select=False)
P.insert(text, (units_line+2, 53), wait=True)
# Matter
text = pmcgi.html_select(\
        pm.units.mass.get() + pm.units.molar.get(), \
        selected=uM, select=False)
P.insert(text, (units_line+3, 53), wait=True)
# Volume
text = pmcgi.html_select(\
        pm.units.volume.get(), selected=uV, select=False)
P.insert(text, (units_line+4, 53), wait=True)


# Apply the units
pm.config['unit_temperature'] = uT
pm.config['unit_pressure'] = up
pm.config['unit_matter'] = uM
pm.config['unit_energy'] = uE
pm.config['unit_volume'] = uV

# Calculate the states
F = pm.get(species)

# The condenser exit will be on the dome
T1 = F.Ts(p1)           # Saturation temperature
d1,_ = F.ds(T=T1)       # Saturation density (faster by temperature)
s1,_ = F.ss(T=T1)       # Saturation entropy
h1,_ = F.hs(T=T1)       # Saturation enthalpy

# The feed pump exit will be isentropic
s2 = s1
T2 = F.T_s(s=s2, p=p2)
h2 = F.h(T2,p2)
d2 = F.d(T2,p2)

# The boiler exit will be on the dome and isobaric
p3 = p2
T3 = F.Ts(p=p3)
_,s3 = F.ss(T=T3)       # Saturation entropy
_,h3 = F.hs(T=T3)       # Saturaiton enthalpy
_,d3 = F.ds(T=T3)       # Saturation density

# The piston exit wll be isentropic and at the condenser pressure
p4 = p1
s4 = s3
T4,x4 = F.T_s(s=s3, p=p4, quality=True)
h4 = F.h(T=T4,x=x4)
d4 = F.d(T=T4,x=x4)

P.insert(\
"""
<br>
<b>(1) Condenser Exit - Pump Inlet</b><br>
p<sub>1</sub> = {5:f} {0:s}<br>
T<sub>1</sub> = {6:f} {1:s}<br>
&rho;<sub>1</sub> = {7:f} {3:s}/{4:s}<br>
h<sub>1</sub> = {8:f} {2:s}/{3:s}<br>
s<sub>1</sub> = {9:f} {2:s}/{3:s}{1:s}<br>
<br>
<b>(2) Pump Exit - Boiler Inlet</b><br>
p<sub>2</sub> = {10:f} {0:s}<br>
T<sub>2</sub> = {11:f} {1:s}<br>
&rho;<sub>2</sub> = {12:f} {3:s}/{4:s}<br>
h<sub>2</sub> = {13:f} {2:s}/{3:s}<br>
s<sub>2</sub> = {14:f} {2:s}/{3:s}{1:s}<br>
<br>
<b>(3) Boiler Exit - Piston/Turbine Inlet</b><br>
p<sub>3</sub> = {15:f} {0:s}<br>
T<sub>3</sub> = {16:f} {1:s}<br>
&rho;<sub>3</sub> = {17:f} {3:s}/{4:s}<br>
h<sub>3</sub> = {18:f} {2:s}/{3:s}<br>
s<sub>3</sub> = {19:f} {2:s}/{3:s}{1:s}<br>
<br>
<b>(4) Piston/Turbine Exit - Condernser Inlet</b><br>
p<sub>4</sub> = {20:f} {0:s}<br>
T<sub>4</sub> = {21:f} {1:s}<br>
&rho;<sub>4</sub> = {22:f} {3:s}/{4:s}<br>
h<sub>4</sub> = {23:f} {2:s}/{3:s}<br>
s<sub>4</sub> = {24:f} {2:s}/{3:s}{1:s}<br>
""".format(\
        up,uT,uE,uM,uV,\
        float(p1),float(T1),float(d1),float(h1),float(s1),\
        float(p2),float(T2),float(d2),float(h2),float(s2),\
        float(p3),float(T3),float(d3),float(h3),float(s3),\
        float(p4),float(T4),float(d4),float(h4),float(s4) ), (58,0), wait=True)

P.insert_exec()


P.write()
