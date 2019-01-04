#!/usr/bin/python

import pmcgi
import os
import pyromat as pm
import numpy as np
import pyromat.solve as pmsolve

source = '/var/www/html/live/pointdata.html'
param_line = 32
units_line = 43

# Print the header so the page will display even if something goes wrong
print("Content-type: text/html")
print("")

species, p1, s1, T1, h1, v1, up, uT, uE, uM, uV = pmcgi.argparse([
    ('id', str, 'mp.H2O'),
    ('p1', float, -9999),
    ('s1', float, -9999),
    ('T1', float, -9999),
    ('h1', float, -9999),
    ('v1', float, -9999),
    ('up', str, 'kPa'),
    ('uT', str, 'K'),
    ('uE', str, 'kJ'),
    ('uM', str, 'kg'),
    ('uV', str, 'm3')])

P = pmcgi.PMPage(source)

inpline = P.find_line('<!-- inputs -->')
unitline = P.find_line('<!-- units -->')
resline = P.find_line('<!-- results -->')

# Build the substance menu
# Include all multiphase collection members
values = []
for name in pm.dat.data:
    if name.startswith('mp.'):
        values.append(name)

# Build the available units menu
# Pressure

text = pmcgi.html_select(
    pm.units.pressure.get(), selected=up, select=False)
P.insert(text, (unitline + 4, 55), wait=True)
# Temperature
text = pmcgi.html_select(
    pm.units.temperature.get(), selected=uT, select=False)
P.insert(text, (unitline + 5, 58), wait=True)
# Energy
text = pmcgi.html_select(
    pm.units.energy.get(), selected=uE, select=False)
P.insert(text, (unitline + 6, 53), wait=True)
# Matter
text = pmcgi.html_select( \
    pm.units.mass.get() + pm.units.molar.get(), \
    selected=uM, select=False)
P.insert(text, (unitline + 7, 53), wait=True)
# Volume
text = pmcgi.html_select( \
    pm.units.volume.get(), selected=uV, select=False)
P.insert(text, (unitline + 8, 53), wait=True)

# Apply the units
pm.config['unit_temperature'] = uT
pm.config['unit_pressure'] = up
pm.config['unit_matter'] = uM
pm.config['unit_energy'] = uE
pm.config['unit_volume'] = uV

# # # # # # # # # # # # #
# Calculate the states  #
# # # # # # # # # # # # #
F = pm.get(species)
sval = ''
Tval = ''
pval = ''
hval = ''
vval = ''

if p1 > 0 and s1 > 0:
    pval = p1
    sval = s1
    # We don't know where the state will be exactly
    T1, x1 = F.T_s(p=p1, s=s1, quality=True)  # Saturation temperature
    if x1 > 0:
        d1 = F.d(T=T1, x=x1)
        h1 = F.h(T=T1, x=x1)
    else:
        d1 = F.d(T=T1, p=p1)
        h1 = F.h(T=T1, p=p1)
    v1 = 1 / d1
elif T1 > 0 and s1 > 0:
    Tval = T1
    sval = s1
    P_T = pmsolve.solve1n('p', f=F.T_s, param_init=20)
    p1 = P_T(T1, s=s1)
    T1, x1 = F.T_s(p=p1, s=s1, quality=True)
    if x1 > 0:
        h1, s1, d1 = F.hsd(T=T1, x=x1)
    else:
        h1, s1, d1 = F.hsd(p=p1, T=T1)
    v1 = 1 / d1
    p1 = F.p(T=T1, d=d1)
elif T1 > 0 and p1 > 0:
    Tval = T1
    pval = p1
    h1, s1, d1 = F.hsd(p=p1, T=T1)
    v1 = 1 / d1
    p1 = F.p(T=T1, d=d1)
    x1 = -1
elif T1 > 0 and h1 > 0:
    Tval = T1
    hval = h1
    P_T = pmsolve.solve1n('p', f=F.T_h, param_init=20)
    p1 = P_T(T1, h=h1)
    T1, x1 = F.T_h(p=p1, h=h1, quality=True)
    if x1 > 0:
        h1, s1, d1 = F.hsd(T=T1, x=x1)
    else:
        h1, s1, d1 = F.hsd(p=p1, T=T1)
    v1 = 1 / d1
    p1 = F.p(T=T1, d=d1)
elif p1 > 0 and h1 > 0:
    hval = h1
    pval = p1
    T1, x1 = F.T_h(p=p1, h=h1, quality=True)
    if x1 > 0:
        h1, s1, d1 = F.hsd(T=T1, x=x1)
    else:
        h1, s1, d1 = F.hsd(p=p1, T=T1)
    v1 = 1 / d1
    p1 = F.p(T=T1, d=d1)
elif p1 > 0 and v1 > 0:
    pval = p1
    vval = v1
    d1 = 1 / v1
    h1, pp, pp = F.hsd(p=p1, d=d1)
    T1, x1 = F.T_h(p=p1, h=h1, quality=True)
    if x1 > 0:
        h1, s1, d1 = F.hsd(T=T1, x=x1)
    else:
        h1, s1, d1 = F.hsd(p=p1, T=T1)
    v1 = 1 / d1
    p1 = F.p(T=T1, d=d1)
elif T1 > 0 and v1 > 0:
    Tval = T1
    vval = v1
    d1 = 1/v1
    P_v = pmsolve.solve1n('p', f=F.T, param_init=400)  # Extremely sensitive to guess
    p1 = P_v(T1, d=d1)
    T1 = F.T(p=p1, d=d1)
    if T1 < F.critical()[0]:
        ds = F.ds(T=T1)
        x1 = (1 / d1 - 1 / ds[0]) / (1 / ds[1] - 1 / ds[0])
    else:
        x1 = -1
    if x1 > 0 and x1 <= 1:
        h1, s1, d1 = F.hsd(T=T1, x=x1)
    else:
        h1, s1, d1, x1 = F.hsd(p=p1, T=T1, quality=True)
    v1 = 1 / d1
    p1 = F.p(T=T1, d=d1)
elif h1 > 0 and v1 > 0:
    hval = h1
    vval = v1
    d1 = 1 / v1
    P_v = pmsolve.solve1n('p', f=F.h, param_init=300)  # Extremely sensitive to guess
    p1 = P_v(h1, d=d1)
    T1, x1 = F.T_h(p=p1, h=h1, quality=True)
    if x1 > 0:
        h1, s1, d1 = F.hsd(T=T1, x=x1)
    else:
        h1, s1, d1 = F.hsd(p=p1, T=T1)
    v1 = 1 / d1
    p1 = F.p(T=T1, d=d1)
elif s1 > 0 and v1 > 0:
    sval = s1
    vval = v1
    d1 = 1 / v1
    P_v = pmsolve.solve1n('p', f=F.s, param_init=300)  # Extremely sensitive to guess
    p1 = P_v(s1, d=d1)
    T1, x1 = F.T_s(p=p1, s=s1, quality=True)
    if x1 > 0:
        h1, s1, d1 = F.hsd(T=T1, x=x1)
    else:
        h1, s1, d1 = F.hsd(p=p1, T=T1)
    v1 = 1 / d1
    p1 = F.p(T=T1, d=d1)
else:  # use default p&s vals:
    p1 = 101.325
    s1 = 4
    pval = p1
    sval = s1
    # We don't know where the state will be exactly
    T1, x1 = F.T_s(p=p1, s=s1, quality=True)  # Saturation temperature
    if x1 > 0:
        d1 = F.d(T=T1, x=x1)
        h1 = F.h(T=T1, x=x1)
    else:
        d1 = F.d(T=T1, p=p1)
        h1 = F.h(T=T1, p=p1)
    v1 = 1 / d1

# Insert the argument values
P.insert( \
    pmcgi.html_select(values, select=False, selected=species), \
    (inpline + 3, 56), wait=True)

P.insert(str(pval), (inpline + 4, 73), wait=True)
P.insert(str(sval), (inpline + 5, 72), wait=True)
P.insert(str(Tval), (inpline + 6, 76), wait=True)
P.insert(str(hval), (inpline + 7, 73), wait=True)
P.insert(str(vval), (inpline + 8, 80), wait=True)

# Find the results line in the original HTML

# Construct table lists for displaying
# This inspires some future code to automatically collapse the arrays
# to make the float() conversions unnecessary
st = [1]
T = [float(T1)]
p = [float(p1)]
v = [float(v1)]
h = [float(h1)]
s = [float(s1)]
if x1 > 0:
    x = [float(x1)]
else:
    x = [float(x1)]
    # if (s1>F.ss(p=p1)[1]):
    #    x=['vapor']
    # else:
    #    x=['liquid']

# build label and unit lists
labels = ['', 'T', 'p', 'v', 'h', 's', 'x']
units = ['', uT, up, uV + '/' + uM, uE + '/' + uM, uE + '/' + uM + uT, '']

P.insert('<h3>Cycle States</h3><center>' +
         pmcgi.html_column_table(labels, units, (st, T, p, v, h, s, x), thousands=',') \
         + '</center>', (resline + 2, 0), wait=True)

# Insert the cgi call to build the image
P.insert(
    '<img class="figure" src="/cgi-bin/live/pointdata_plot.py?id={:s}&p1={:f}&s1={:f}&up={:s}&uT={:s}&uE={:s}&uM={:s}&uV={:s}">'.format(
        species, float(p1), float(s1), up, uT, uE, uM, uV), \
    (resline + 1, 0))

P.insert_exec()


P.write()
