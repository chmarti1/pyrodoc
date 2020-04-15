#!/usr/bin/python

import matplotlib as mpl
# It is vital to set the matplotlib interface to one without a display
# BEFORE loading pyplot!  This makes things work behind Apache.
mpl.use('Agg')
import matplotlib.pyplot as plt

import pmcgi
import os
import pyromat as pm
import numpy as np
import pyromat.solve as pmsolve
import liveutils as lu

source = '/var/www/html/live/idealgasdata.html'

# Print the header so the page will display even if something goes wrong
print("Content-type: text/html")
print("")

# Create the HTML page object
P = pmcgi.PMPage(source)

#find critical lines in the
speciesline = P.find_line('<!-- inputs -->')+3 #line to insert the species spinner
inpline = P.find_line('<!-- inputs -->')+4 #line to begin the input boxes
unitline = P.find_line('<!-- units -->')+4 #line where we begin the unit selector mess
resline = P.find_line('<!-- results -->')+1 #line where we begin the results
errline = P.find_line('<!-- errors -->') +1 #line where we insert errors
#coordsline = 112

#Try to parse the user's inputs
try:
    species, T1, h1, up, uT, uE, uM, uV = pmcgi.argparse([
        ('id', str, 'ig.air'),
        ('T1', float, -999999),
        ('h1', float, -999999),
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
lu.setspeciesselect_ig(P,species,speciesline,56)

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
sval = Tval = pval = hval = vval = xval = ''

#check for cases where too few or too many properties are specified (zero specified results in defaults)
ins = np.array([T1,h1]) #test array for counting how many properties were specified
if (sum(ins>=-900000)>1):
    lu.perror(P,'Must specify exactly one of T or h for an ideal gas.', errline)
elif (sum(ins>=-900000)==0):
    T1 = 300

#Determine which two properties were chosen, calculate the state
try:
    if T1 >= -900000: #T
        #Set the input box labels
        Tval = T1
        h1 = F.h(T=T1)
        cv1 = F.cv(T=T1)
        cp1 = F.cp(T=T1)
        gamma1 = F.gam(T=T1)
        
    elif h1 >= -900000: #h
        #set the input box labels
        hval = h1
        T1 = F.T_h(h=h1)
        cv1 = F.cv(T=T1)
        cp1 = F.cp(T=T1)
        gamma1 = F.gam(T=T1)
    else:  #not supported
        lu.perror(P,'Specifying this property is not supported by pyromat. ', errline)
except (pm.utility.PMParamError) as e: #This means we ran into a pyromat error, show the user
    lu.perror(P, 'Pyromat produced an error: '+str(e), errline)
except Exception as e: #This means that one of the typical pyromat errors wasn't encountered
    lu.perror(P, 'Python error: ' + str(e), errline)

# Put the input values back into the input boxes
vals = [str(Tval),str(hval)]
cols = [76,82]
lu.setinputs(P,vals,cols,inpline)


# # # # # # # # # # # # #
# Display Output Values #
# # # # # # # # # # # # #

# Construct table lists for displaying, funky typing required for pmcgi code
T = [float(T1)]
h = [float(h1)]
cv = [float(cv1)]
cp = [float(cp1)]
gamma = [float(gamma1)]

# build label and unit lists
labels = ['T', 'h', 'cv', 'cp', 'gamma']
units = [uT, uE + '/' + uM, uE + '/' + uM + uT, uE + '/' + uM + uT, '-']

P.insert('<h3>State Properties</h3><center>' +
         pmcgi.html_column_table(labels, units, (T, h, cv, cp, gamma), thousands=',')
         + '</center>', (resline, 0), wait=True)


#Perform the write operation
P.insert_exec()
P.write()
