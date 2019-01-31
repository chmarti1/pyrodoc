#!/usr/bin/python

import pmcgi
import os
import pyromat as pm
import numpy as np
import pyromat.solve as pmsolve
import liveutils as lu

source = '/var/www/html/live/propdiags.html'

# Print the header so the page will display even if something goes wrong
print("Content-type: text/html")
print("")

#Create the HTML page object
P = pmcgi.PMPage(source)

#find critical lines in the
speciesline = P.find_line('<!-- inputs -->')+3
inpline = P.find_line('<!-- inputs -->')+4
unitline = P.find_line('<!-- units -->')+4
resline = P.find_line('<!-- results -->')+1
errline = P.find_line('<!-- errors -->') +1
chartline = P.find_line('<!-- charts -->') +2

# Build the substance menu
# Include all multiphase collection members
values = []
for name in pm.dat.data:
    if name.startswith('mp.'):
        values.append(name)

#Try to parse the user's inputs
try:
    species, plin, Tlin, vlin, hlin, slin, up, uT, uE, uM, uV = pmcgi.argparse([
        ('id', str, 'mp.H2O'),
        ('plines', str, 'false'),
        ('Tlines', str, 'false'),
        ('vlines', str, 'false'),
        ('hlines', str, 'false'),
        ('slines', str, 'false'),
        ('up', str, 'kPa'),
        ('uT', str, 'K'),
        ('uE', str, 'kJ'),
        ('uM', str, 'kg'),
        ('uV', str, 'm3')])
except:
    #should be impossible to get here
    pass


#Set up the unit selector
lu.unitsetup(P,up,uT,uE,uM,uV,unitline)

#Set up the species spinner
lu.setspeciesselect(P,species,speciesline,56)

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

#Determine which two properties were chosen, calculate the state
try:
    pass
except (pm.utility.PMParamError,pm.utility.PMAnalysisError) as e:  # This means we ran into a pyromat error, show the user
    lu.perror(P, 'Pyromat produced an error: ' + str(e), errline)
except Exception as e:  # This means that one of the typical pyromat errors wasn't encountered
    lu.perror(P, 'Python error: ' + str(e), errline)

# Insert the cgi call to build the image
P.insert(
    '<img class="figure" src="/cgi-bin/live/propdiags_plot.py?id={:s}&type={:s}&plin={:s}&Tlin={:s}&vlin={:s}&hlin={:s}&slin={:s}&up={:s}&uT={:s}&uE={:s}&uM={:s}&uV={:s}">'.format(
        species, 'Ts', plin, Tlin, vlin, hlin, slin, up, uT, uE, uM, uV),
    (chartline, 0))
P.insert(
    '<img class="figure" src="/cgi-bin/live/propdiags_plot.py?id={:s}&type={:s}&plin={:s}&Tlin={:s}&vlin={:s}&hlin={:s}&slin={:s}&up={:s}&uT={:s}&uE={:s}&uM={:s}&uV={:s}">'.format(
        species, 'Tv', plin, Tlin, vlin, hlin, slin, up, uT, uE, uM, uV),
    (chartline+2, 0))
P.insert(
    '<img class="figure" src="/cgi-bin/live/propdiags_plot.py?id={:s}&type={:s}&plin={:s}&Tlin={:s}&vlin={:s}&hlin={:s}&slin={:s}&up={:s}&uT={:s}&uE={:s}&uM={:s}&uV={:s}">'.format(
        species, 'pv', plin, Tlin, vlin, hlin, slin, up, uT, uE, uM, uV),
    (chartline+4, 0))
# Put the input values back into the input boxes
plin = 'checked="true"' if plin=='true' else ''
Tlin = 'checked="true"' if Tlin=='true' else ''
vlin = 'checked="true"' if vlin=='true' else ''
hlin = 'checked="true"' if hlin=='true' else ''
slin = 'checked="true"' if slin=='true' else ''
vals = [plin,Tlin,vlin,hlin,slin]
cols = [94,97,101,94,93]
lu.setinputs(P,vals,cols,inpline)

# build label and unit lists
labels = ['Phase', 'T', 'p', 'v', 'u', 'h', 's']
units = ['', uT, up, uV + '/' + uM, uE + '/' + uM, uE + '/' + uM, uE + '/' + uM + uT]




#Perform the write operation
P.insert_exec()
P.write()
