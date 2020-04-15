#!/usr/bin/python

import pmcgi
import os, sys
from pyromat.aps import cycle
import pyromat as pm
import numpy as np

source = '/var/www/html/live/rankinesh.html'
param_line = 32
units_line = 43


# Print the header so the page will display even if something goes wrong
print("Content-type: text/html")
print("")

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

P.insert(str(p1), (line+4,81), wait=True)
P.insert(str(p2), (line+5,78), wait=True)
P.insert(str(eta12), (line+6,78), wait=True)
P.insert(str(eta23), (line+7,80), wait=True)
P.insert(str(eta34), (line+8,82), wait=True)
P.insert(str(eta45), (line+9,81), wait=True)

# Insert the optional values
line = P.find_line('<!-- superheat -->')
P.insert(T4, (line+3,79), wait=True)
P.insert(q34, (line+4,79), wait=True)

# Deal with T4 and q34 specially
if T4:
    T4 = float(T4)
else:
    T4 = None
    
if q34:
    q34 = float(q34)
else:
    q34 = None
    


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
try:
    RC = cycle.RankineSHCycle()
    RC.param['fluid'] = species
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
    P.insert('<div class="error">\nERROR<br>\n' + repr(sys.exc_info()[1]) + '</div>',
            (line+1,0))
    P.write()
    exit(0)

#Build the plot
P.insert('<div class="figure"><img src="rankinesh_plot.py' + pmcgi.buildget() + '"></div>',
        (line+1,0), wait=True)

# build label and unit lists
labels = ['','T', 'p', '&rho;', 'x', 'h', 's']
units = ['', uT, up, uM+'/'+uV, '-', uE+'/'+uM, uE+'/'+uM+uT]


st = [1,2,3,4,5]

P.insert('<h3>Cycle States</h3><center>' + 
        pmcgi.html_column_table(labels, units, (st,RC.T,RC.p,RC.d, RC.x, RC.h,RC.s), thousands=',')\
        + '</center>', (line+2,0), wait=True)

P.insert("""<h3>Performance</h3>
<center><table>
<tr><th>Parameter</th><th>Symb.</th><th>Value</th><th>Units</th></tr>
<tr><td>Pump Work</td><td>W<sub>1-2</sub></td><td>{5:f}</td><td>{2:s}/{3:s}</td></tr>
<tr><td>Boiler Heat</td><td>Q<sub>2-3</sub></td><td>{6:f}</td><td>{2:s}/{3:s}</td></tr>
<tr><td>Super Heat</td><td>Q<sub>2-3</sub></td><td>{7:f}</td><td>{2:s}/{3:s}</td></tr>
<tr><td>Work Out</td><td>W<sub>3-4</sub></td><td>{8:f}</td><td>{2:s}/{3:s}</td></tr>
<tr><td>Condenser Heat</td><td>Q<sub>4-1</sub></td><td>{9:f}</td><td>{2:s}/{3:s}</td></tr>
<tr><td>Efficiency</td><td>&eta;</sub></td><td>{10:.2f}</td><td>%</td></tr>
</table></center>""".format(
        up, uT, uE, uM, uV, float(RC.w[0]), float(RC.q[1]), 
        float(RC.q[2]), float(RC.w[3]), float(RC.q[4]),
        100*float(RC.meta['eta'])), (line+3,0), wait=True)

P.insert_exec()


P.write()
