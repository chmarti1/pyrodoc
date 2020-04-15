#!/usr/bin/python

import pmcgi
import os
import pyromat as pm
import numpy as np
import pyromat.solve as pmsolve
import liveutils as lu

source = '/var/www/html/live/satdata.html'

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
chartline = P.find_line('<!-- charts -->') +1

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
    lu.perror(P,'Unable to parse one of the inputs. Make sure you are using valid numbers.',errline)

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

#Set blank labels for each of the properties.
#These will be reset by each of the methods for re-entry into the input boxes.
Tval = pval = ''

#check for cases where too few or too many properties are specified (zero specified results in defaults)
ins = np.array([p1,T1]) #test array for counting how many properties were specified
if (sum(ins>=0)==0):
    p1 = 101.325
elif (sum(ins>=0)!=1):
    lu.perror(P,'Must specify pressure or temperature, but not both.', errline)


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
        lu.perror(P,"There was a problem and we're not sure how you got here.",errline)
except (pm.utility.PMParamError,pm.utility.PMAnalysisError) as e:  # This means we ran into a pyromat error, show the user
    lu.perror(P, 'Pyromat produced an error: ' + str(e), errline)
except Exception as e:  # This means that one of the typical pyromat errors wasn't encountered
    lu.perror(P, 'Python error: ' + str(e), errline)

# Put the input values back into the input boxes
vals = [str(pval),str(Tval)]
cols = [73,76]
lu.setinputs(P,vals,cols,inpline)

# Construct table lists for displaying, funky typing required for pmcgi code
st = ['liquid','vapor'] #1 is liq, 2 is vap
T = [float(T1), float(T1)]
p = [float(p1), float(p1)]
v = [float(vf), float(vg)]
e = [float(ef), float(eg)]
h = [float(hf), float(hg)]
s = [float(sf), float(sg)]

# build label and unit lists
labels = ['Phase', 'T', 'p', 'v', 'u', 'h', 's']
units = ['', uT, up, uV + '/' + uM, uE + '/' + uM, uE + '/' + uM, uE + '/' + uM + uT]

P.insert('<h3>Saturation Properties</h3><center>' +
         pmcgi.html_column_table(labels, units, (st, T, p, v, e, h, s), thousands=',')
         + '</center>', (resline, 0), wait=True)

# Insert the cgi call to build the image
P.insert(
    '<img class="figure" src="/cgi-bin/live/satdata_plot.py?id={:s}&T1={:f}&up={:s}&uT={:s}&uE={:s}&uM={:s}&uV={:s}">'.format(
        species, float(T1), up, uT, uE, uM, uV),
    (chartline, 0))


#Perform the write operation
P.insert_exec()
P.write()
