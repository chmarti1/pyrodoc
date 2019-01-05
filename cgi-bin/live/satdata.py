#!/usr/bin/python

import pmcgi
import os
import pyromat as pm
import numpy as np
import pyromat.solve as pmsolve

source = '/var/www/html/live/satdata.html'
param_line = 32
units_line = 43

# Print the header so the page will display even if something goes wrong
print("Content-type: text/html")
print("")

#Create the HTML page object
P = pmcgi.PMPage(source)

#find critical lines in the
inpline = P.find_line('<!-- inputs -->')
unitline = P.find_line('<!-- units -->')
resline = P.find_line('<!-- results -->')

# Build the substance menu
# Include all multiphase collection members
values = []
for name in pm.dat.data:
    if name.startswith('mp.'):
        values.append(name)

#Try to parse the user's inputs
try:
    species, p1, T1, up, uT, uE, uM, uV = pmcgi.argparse([
        ('id', str, 'mp.H2O'),
        ('p1', float, -9999), #-9999 indicates no value was entered
        ('T1', float, -9999),
        ('up', str, 'kPa'),
        ('uT', str, 'K'),
        ('uE', str, 'kJ'),
        ('uM', str, 'kg'),
        ('uV', str, 'm3')])
except:
    #An example way to get here is by entering letters into the boxes
    P.insert("""<div class="error">
    ERROR<br>Unable to parse one of the inputs. Make sure you are using numbers.""",
             (resline + 1, 0))
    P.write()
    exit()

# Build the available units menu based on the user's selections
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
text = pmcgi.html_select(
    pm.units.mass.get() + pm.units.molar.get(),
    selected=uM, select=False)
P.insert(text, (unitline + 7, 53), wait=True)
# Volume
text = pmcgi.html_select(
    pm.units.volume.get(), selected=uV, select=False)
P.insert(text, (unitline + 8, 53), wait=True)

# Apply the units within pyromat
pm.config['unit_temperature'] = uT
pm.config['unit_pressure'] = up
pm.config['unit_matter'] = uM
pm.config['unit_energy'] = uE
pm.config['unit_volume'] = uV

# # # # # # # # # # # # #
# Calculate the states  #
# # # # # # # # # # # # #
#Get the substance object
F = pm.get(species)

#Set blank labels for each of the properties.
#These will be reset by each of the methods for re-entry into the input boxes.
Tval = pval = ''

#check for cases where too few or too many properties are specified (zero specified results in defaults)
ins = np.array([p1,T1]) #test array for counting how many properties were specified
if (sum(ins>=0)==0):
    p1 = 101.325
elif (sum(ins>=0)!=1):
    P.insert("""<div class="error">
    ERROR<br>Must specify pressure or temperature but not both""",
             (resline + 1, 0))
    P.write()
    exit()


#Determine which two properties were chosen, calculate the state
try:
    if p1 >= 0: #p
        pval = p1
        T1 = F.Ts(p=p1)
        ef,eg = F.es(p=p1)
        hf,hg = F.hs(p=p1)
        sf,sg = F.ss(p=p1)
        df,dg = F.ds(p=p1)
        vf = 1/df
        vg = 1/dg
    elif T1 >= 0:
        Tval = T1
        p1 = F.ps(T=T1)
        ef,eg = F.es(T=T1)
        hf,hg = F.hs(T=T1)
        sf,sg = F.ss(T=T1)
        df,dg = F.ds(T=T1)
        vf = 1/df
        vg = 1/dg
    else:  #not sure how you'd get here
        P.insert("""<div class="error">
                ERROR<br>There was a problem and we're not sure how you got here. """,
                 (resline + 1, 0))
        P.write()
        exit()
except (pm.utility.PMParamError, pm.utility.PMAnalysisError) as e: #This means we ran into a pyromat error, show the user
    P.insert("""<div class="error">
        ERROR<br>Pyromat produced an error: """+str(e),
             (resline + 1, 0))
    P.write()
    exit()
except Exception as e: #This means that one of the typical pyromat errors wasn't encountered
    P.insert("""<div class="error">
        ERROR<br>Python error: """+str(e),
             (resline + 1, 0))
    P.write()
    exit()


# Put the input values back into the input boxes
P.insert(
            pmcgi.html_select(values, select=False, selected=species),
                (inpline + 3, 56), wait=True)

P.insert(str(pval), (inpline + 4, 73), wait=True)
P.insert(str(Tval), (inpline + 5, 76), wait=True)

# Construct table lists for displaying, funky typing required for pmcgi code
st = [1,2] #1 is liq, 2 is vap #TODO make this work with text
T = [float(T1), float(T1)]
p = [float(p1), float(p1)]
v = [float(vf), float(vg)]
e = [float(ef), float(eg)]
h = [float(hf), float(hg)]
s = [float(sf), float(sg)]

# build label and unit lists
labels = ['', 'T', 'p', 'v', 'u', 'h', 's']
units = ['', uT, up, uV + '/' + uM, uE + '/' + uM, uE + '/' + uM, uE + '/' + uM + uT]

P.insert('<h3>Saturation Properties</h3><center>' +
         pmcgi.html_column_table(labels, units, (st, T, p, v, e, h, s), thousands=',')
         + '</center>', (resline + 1, 0), wait=True)

# Insert the cgi call to build the image
P.insert(
    '<img class="figure" src="/cgi-bin/live/satdata_plot.py?id={:s}&T1={:f}&up={:s}&uT={:s}&uE={:s}&uM={:s}&uV={:s}">'.format(
        species, float(T1), up, uT, uE, uM, uV),
    (resline + 2, 0))


#Perform the write operation
P.insert_exec()
P.write()
