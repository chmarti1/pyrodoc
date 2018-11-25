#!/usr/bin/python

import pmcgi
import os
import pyromat as pm
import numpy as np

source = '/var/www/html/live/rankine.html'
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
        
# Insert the argument values
line = P.find_line('<!-- inputs -->')
P.insert(\
        pmcgi.html_select(values,select=False, selected=species),\
        (line+3,56), wait=True)

P.insert(str(p1), (line+4,83), wait=True)
P.insert(str(p2), (line+5,80), wait=True)

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

# But first, do some error checking
# p2 must be greater than p1
if p1 >= p2:
    P.insert("""<div class="error">
ERROR<br>The boiler pressure must be greater than the condenser pressure
</div>""",
            (line+1,0))
    P.write()
    exit()

# p1 must be above the triple point
_,pt = F.triple()
if p1 < pt:
    P.insert("""<div class="error">
ERROR<br>The condenser pressure was below the triple point pressure, {:f} {:s}
</div>""".format(pt, up), (line+1,0))
    P.write()
    exit()
    
# p2 must be below the critical point
_,pc = F.critical()
if p2 > pc:
    P.insert("""<div class="error">
ERROR<br>The boiler pressure was above the critical pressure, {:f} {:s}
</div>""".format(\
            pc, up), (line+1,0))
    P.write()
    exit()

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

# Calculate performance characteristics
W12 = float(h1 - h2)
Q23 = float(h3 - h2)
W34 = float(h3 - h4)
Q41 = float(h1 - h4)
n = float(W34 / Q23)

# Insert the cgi call to build the image
P.insert(
        '<img class="figure" src="/cgi-bin/live/rankine_plot.py?id={:s}&p1={:f}&p2={:f}&up={:s}&uT={:s}&uE={:s}&uM={:s}&uV={:s}">'.format(
                species, float(p1), float(p2), up, uT, uE, uM, uV),\
        (line+1,0))


# Construct table lists for displaying
# This inspires some future code to automatically collapse the arrays
# to make the float() conversions unnecessary
st = [1,2,3,4]
T = [float(T1), float(T2), float(T3), float(T4)]
p = [float(p1), float(p2), float(p3), float(p4)]
d = [float(d1), float(d2), float(d3), float(d4)]
h = [float(h1), float(h2), float(h3), float(h4)]
s = [float(s1), float(s2), float(s3), float(s4)]
# build label and unit lists
labels = ['','T', 'p', '&rho;', 'h', 's']
units = ['', uT, up, uM+'/'+uV, uE+'/'+uM, uE+'/'+uM+uT]

P.insert('<h3>Cycle States</h3><center>' + 
        pmcgi.html_column_table(labels, units, (st,T,p,d,h,s), thousands=',')\
        + '</center>', (line+2,0), wait=True)

P.insert("""<h3>Performance</h3>
<center><table>
<tr><th>Parameter</th><th>Symb.</th><th>Value</th><th>Units</th></tr>
<tr><td>Pump Work</td><td>W<sub>1-2</sub></td><td>{5:f}</td><td>{2:s}/{3:s}</td></tr>
<tr><td>Boiler Heat</td><td>Q<sub>2-3</sub></td><td>{6:f}</td><td>{2:s}/{3:s}</td></tr>
<tr><td>Work Out</td><td>W<sub>3-4</sub></td><td>{7:f}</td><td>{2:s}/{3:s}</td></tr>
<tr><td>Condenser Heat</td><td>Q<sub>4-1</sub></td><td>{8:f}</td><td>{2:s}/{3:s}</td></tr>
<tr><td>Efficiency</td><td>&eta;</sub></td><td>{9:.2f}</td><td>%</td></tr>
</table></center>""".format(up,uT,uE,uM,uV,W12,Q23,W34,Q41,100*n), (line+3,0), wait=True)

P.insert_exec()


P.write()
