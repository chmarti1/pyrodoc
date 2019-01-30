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

source = '/var/www/html/live/pointdata2.html'

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
chartline = P.find_line('<!-- charts -->')+1 #line where we begin inserting a chart
#coordsline = P.find_line('<!-- coordinates -->')+1 #line where we begin inserting chart coords
coordsline = 112

#Try to parse the user's inputs
try:
    species, p1, s1, T1, h1, v1, x1, up, uT, uE, uM, uV = pmcgi.argparse([
        ('id', str, 'mp.H2O'),
        ('p1', float, -9999), #-9999 indicates no value was entered
        ('s1', float, -9999),
        ('T1', float, -9999),
        ('h1', float, -9999),
        ('v1', float, -9999),
        ('x1', float, -9999),
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
lu.setspeciesselect(P,species,speciesline,52)

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
ins = np.array([p1,T1,s1,v1,h1,x1]) #test array for counting how many properties were specified
if (sum(ins>=-9000)==1) or (sum(ins>=-9000)>2):
    lu.perror(P,'Must specify exactly two properties to define a state.', errline)
elif (sum(ins>=-9000)==0):
    p1 = 101.325
    T1 = 300

#Determine which two properties were chosen, calculate the state
try:
    if p1 >= -9000 and s1 >= -9000: #P&s
        #Set the input box labels
        pval = p1
        sval = s1

        T1, x1 = F.T_s(p=p1, s=s1, quality=True)
        if x1 > 0: #Check if saturated
            d1 = F.d(T=T1, x=x1)
            h1 = F.h(T=T1, x=x1)
        else:
            d1 = F.d(T=T1, p=p1)
            h1 = F.h(T=T1, p=p1)
        v1 = 1 / d1
    elif T1 >= -9000 and s1 >= -9000: #T&s
        # Set the input box labels
        Tval = T1
        sval = s1

        #Must find P iteratively
        P_T = pmsolve.solve1n('p', f=F.T_s, param_init=20)
        p1 = P_T(T1, s=s1)
        T1, x1 = F.T_s(p=p1, s=s1, quality=True)
        if x1 > 0: #check if saturated
            h1, s1, d1 = F.hsd(T=T1, x=x1)
        else:
            h1, s1, d1 = F.hsd(p=p1, T=T1)
        v1 = 1 / d1
        p1 = F.p(T=T1, d=d1)
    elif T1 >= -9000 and p1 >= -9000: #T&p
        #set the input box labels
        Tval = T1
        pval = p1

        h1, s1, d1 = F.hsd(p=p1, T=T1)
        v1 = 1 / d1
        p1 = F.p(T=T1, d=d1)
        x1 = -1 #P&T will always fall outside the dome
    elif T1 >= -9000 and h1 >= -9000: #T&h
        #set the input box labels
        Tval = T1
        hval = h1

        #Must solve for P iteratively
        P_T = pmsolve.solve1n('p', f=F.T_h, param_init=20)
        p1 = P_T(T1, h=h1)
        T1, x1 = F.T_h(p=p1, h=h1, quality=True)
        if x1 > 0: #check if saturated
            h1, s1, d1 = F.hsd(T=T1, x=x1)
        else:
            h1, s1, d1 = F.hsd(p=p1, T=T1)
        v1 = 1 / d1
        p1 = F.p(T=T1, d=d1)
    elif p1 >= -9000 and h1 >= -9000: #P&h
        #set the input box labels
        hval = h1
        pval = p1

        T1, x1 = F.T_h(p=p1, h=h1, quality=True)
        if x1 > 0: #check if saturated
            h1, s1, d1 = F.hsd(T=T1, x=x1)
        else:
            h1, s1, d1 = F.hsd(p=p1, T=T1)
        v1 = 1 / d1
        p1 = F.p(T=T1, d=d1)
    elif p1 >= -9000 and v1 >= -9000: #P&v
        #set the input box labels
        pval = p1
        vval = v1

        d1 = 1 / v1
        h1, pp, pp = F.hsd(p=p1, d=d1)
        T1, x1 = F.T_h(p=p1, h=h1, quality=True)
        if x1 > 0: #check if saturated
            h1, s1, d1 = F.hsd(T=T1, x=x1)
        else:
            h1, s1, d1 = F.hsd(p=p1, T=T1)
        v1 = 1 / d1
        p1 = F.p(T=T1, d=d1)
    elif T1 >= -9000 and v1 >= -9000: #T&v
        #Set the input box labels
        Tval = T1
        vval = v1

        d1 = 1/v1
        P_v = pmsolve.solve1n('p', f=F.T, param_init=400)  # Extremely sensitive to guess
        p1 = P_v(T1, d=d1)
        T1 = F.T(p=p1, d=d1)
        if T1 < F.critical()[0]: #figure out where we were at, because we can't find x easily
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
    elif h1 >= -9000 and v1 >= -9000: #h&v
        #set the input box labels
        hval = h1
        vval = v1

        d1 = 1 / v1
        #P must be found iteratively
        P_v = pmsolve.solve1n('p', f=F.h, param_init=300)  # Extremely sensitive to guess
        p1 = P_v(h1, d=d1)
        T1, x1 = F.T_h(p=p1, h=h1, quality=True)
        if x1 > 0: #check if saturated
            h1, s1, d1 = F.hsd(T=T1, x=x1)
        else:
            h1, s1, d1 = F.hsd(p=p1, T=T1)
        v1 = 1 / d1
        p1 = F.p(T=T1, d=d1)
    elif s1 >= -9000 and v1 >= -9000: #s&v
        #set the input box labels
        sval = s1
        vval = v1

        d1 = 1 / v1
        #P must be found iteratively
        P_v = pmsolve.solve1n('p', f=F.s, param_init=300)  # Extremely sensitive to guess
        p1 = P_v(s1, d=d1)
        T1, x1 = F.T_s(p=p1, s=s1, quality=True)
        if x1 > 0:#check if saturated
            h1, s1, d1 = F.hsd(T=T1, x=x1)
        else:
            h1, s1, d1 = F.hsd(p=p1, T=T1)
        v1 = 1 / d1
        p1 = F.p(T=T1, d=d1)
    elif x1 >=-9000 and T1 >= -9000: #T&x
        #set the input box labels
        Tval = T1
        xval = x1

        p1 = F.ps(T=T1)
        h1, s1, d1 = F.hsd(T=T1, x=x1)
        v1 = 1/d1
    elif x1 >=-9000 and p1 >= -9000: #P&x
        #set the input box labels
        pval = p1
        xval = x1

        T1 = F.Ts(p=p1)
        h1, s1, d1 = F.hsd(T=T1, x=x1)
        v1 = 1/d1
    else:  #not supported
        lu.perror(P,'Specifying this pair of properties is not supported by pyromat. ', errline)
except (pm.utility.PMParamError) as e: #This means we ran into a pyromat error, show the user
    lu.perror(P, 'Pyromat produced an error: '+str(e), errline)
except (pm.utility.PMAnalysisError) as e:
    lu.perror(P, 'Pyromat produced a PMAnalysisError: Often this occurs when a value for v, h or s would '+
                 'result in temperature or pressure falling outside acceptable limits.', errline)
except Exception as e: #This means that one of the typical pyromat errors wasn't encountered
    lu.perror(P, 'Python error: ' + str(e), errline)

# Put the input values back into the input boxes
vals = [str(pval),str(Tval),str(hval),str(sval),str(vval),str(xval)]
cols = [73,76,82,81,80,72]
lu.setinputs(P,vals,cols,inpline)


# # # # # # # # # # # # #
# Display Output Values #
# # # # # # # # # # # # #

# Construct table lists for displaying, funky typing required for pmcgi code
T = [float(T1)]
p = [float(p1)]
v = [float(v1)]
h = [float(h1)]
s = [float(s1)]
if x1 >= 0:
    x = [float(x1)]
else:
    #x = [float(x1)]
    Tc,pc,dc = F.critical(density=True)
    if (p1>pc and T1>Tc):
        x = ['supercritical']
    elif (d1<dc):
        x=['vapor']
    else:
        x=['liquid']

# build label and unit lists
labels = ['T', 'p', 'v', 'h', 's', 'x']
units = [uT, up, uV + '/' + uM, uE + '/' + uM, uE + '/' + uM + uT, '-']

P.insert('<h3>State Properties</h3><center>' +
         pmcgi.html_column_table(labels, units, (T, p, v, h, s, x), thousands=',')
         + '</center>', (resline, 0), wait=True)

# Insert the cgi call to build the image
# """<canvas id="myCanvas"  style="cursor:crosshair;background: url('/cgi-bin/live/pointdata_plot.py?id={:s}&p1={:f}&s1={:f}&up={:s}&uT={:s}&uE={:s}&uM={:s}&uV={:s}')" width="640" height="480"></canvas>""".format(
#        species, float(p1), float(s1), up, uT, uE, uM, uV)
P.insert(
    """/cgi-bin/live/pointdata_plot.py?id={:s}&p1={:f}&s1={:f}&up={:s}&uT={:s}&uE={:s}&uM={:s}&uV={:s}""".format(
        species, float(p1), float(s1), up, uT, uE, uM, uV),
    (chartline, 63))

#insert the chartcoordinates


def getChartCoords():
    f = plt.figure()
    ax = f.add_subplot(111)
    Tt = F.triple()[0]
    Tc = F.critical()[0]
    temp = (Tc - Tt) * .00001
    T = np.linspace(Tt + temp, Tc - temp, 5)
    sL, sV = F.ss(T)
    ax.plot(sL, T, lw=2, color='k')
    ax.plot(sV, T, lw=2, color='k')

    # Add an isobar
    Tmin = F.Tlim()[0]
    Tmax = F.Tlim()[1]
    smin = F.s(T=Tmin, p=p1)
    smax = F.s(T=Tmax, p=p1)
    s = np.linspace(smin, smax, 5)
    try:
        with lu.nostdout():
            T = F.T_s(p=p1, s=s)
            ax.plot(s, T, lw=2, color='b', linestyle=':')
    except:
        pass

    origin = ax.get_position()
    originx_pct = str(origin.get_points()[0][0])
    originy_pct = str(origin.get_points()[0][1])
    maxx_pct = str(origin.get_points()[1][0])
    maxy_pct = str(origin.get_points()[1][1])
    xlim_low = str(ax.get_xlim()[0])
    xlim_hi = str(ax.get_xlim()[1])
    ylim_low = str(ax.get_ylim()[0])
    ylim_hi = str(ax.get_ylim()[1])
    P.insert(originx_pct, (coordsline, 23), wait=True)
    P.insert(originy_pct, (coordsline+1, 23), wait=True)
    P.insert(maxx_pct, (coordsline+2, 23), wait=True)
    P.insert(maxy_pct, (coordsline+3, 23), wait=True)
    P.insert(xlim_low, (coordsline+4, 23), wait=True)
    P.insert(xlim_hi, (coordsline+5, 23), wait=True)
    P.insert(ylim_low, (coordsline+6, 23), wait=True)
    P.insert(ylim_hi, (coordsline+7, 23), wait=True)
getChartCoords()

#Perform the write operation
P.insert_exec()
P.write()
