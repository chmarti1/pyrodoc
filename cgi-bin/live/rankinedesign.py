#!/usr/bin/python

import pmcgi
import os
import pyromat as pm
import numpy as np
import liveutils as lu

source = '/var/www/html/live/rankinedesign.html'

# Print the header so the page will display even if something goes wrong
print("Content-type: text/html")
print("")

# Create the HTML page object
P = pmcgi.PMPage(source)

speciesline = P.find_line('<!-- inputs -->')+3 #line to insert the species spinner
inpline = P.find_line('<!-- inputs -->')+4 #line to begin the input boxes
unitline = P.find_line('<!-- units -->')+4 #line where we begin the unit selector mess
resline = P.find_line('<!-- results -->')+1 #line where we begin the results
errline = P.find_line('<!-- errors -->') +1 #line where we insert errors
chartline = P.find_line('<!-- charts -->')+1 #line where we begin inserting a chart
coordsline = P.find_line('<!-- coordinates -->')+42 #line where we begin inserting chart coords


try:
    species, p1, p2, T3, mdot, syscost, FuelEff, eta_pump, eta_turb, up, uT, uE, uM, uV = pmcgi.argparse([
        ('id',str,'mp.H2O'), 
        ('p1',float,100),
        ('p2',float,8000),
        ('T3',float,450),
        ('mdot',float,5),
        ('syscost',float,1000000),
        ('FuelEff',float,0.85),
        ('eta_pump',float,0.85),
        ('eta_turb',float,0.85),
        ('up',str,'kPa'),
        ('uT',str,'C'),
        ('uE',str,'kJ'),
        ('uM',str,'kg'),
        ('uV',str,'m3') ])
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

# Put the input values back into the input boxes
vals = [str(p1),str(p2),str(T3),str(mdot),str(syscost),str(FuelEff),str(eta_pump),str(eta_turb)]
cols = [83,80,88,81,85,85,86,89]
lu.setinputs(P,vals,cols,inpline)

# # # # # # # # # # # # #
# Calculate the states  #
# # # # # # # # # # # # # 
# #Example (Cheapest Parts, AAAA)
# p1 = 100e3
# p2 = 8e6
# T3 = 450
# mdot = 5.0
# syscost = 1000000
# FuelEff = 0.85
# eta_pump = 0.85
# eta_turb = 0.85

#Parameters of the problem
FuelCost = 7e-6 #$/kJ ($0.007/MJ)
EnergyValue = 2.8e-5 #$/kJ ($0.10/kWh)
nyrs = 5

F = pm.get(species)

# But first, do some error checking
# p2 must be greater than p1
if p1 >= p2:
    err = 'The boiler pressure must be greater than the condenser pressure.'
    lu.perror(P, 'Python error: '+err, errline)


# p1 must be above the triple point
_,pt = F.triple()
if p1 < pt:
    err = 'The condenser pressure was below the triple point pressure.'
    lu.perror(P, 'Python error: ' + err, errline)

#State 1 is a saturated liquid @ p1
T1 = F.Ts(p=p1) #Temperature
h1,null = F.hs(p=p1) #Enthalpy
s1,null = F.ss(p=p1) #Entropy
v1 = 1/F.ds(T=T1)[0]

#State 2s is isentropic from p1-p2
s2s = s1 #isentropic
T2s = F.T_s(p=p2,s=s2s) #isentropic Temperature
h2s = F.h(p=p2,T=T2s) #isentropic Enthalpy
v2s = 1/F.d(T=T2s,p=p2)

#State 2 is found by applying the isentropic efficiency
Wps = h2s-h1 #Isentropic work
Wp = Wps/eta_pump #Actual work
h2 = Wp+h1 #Actual enthalpy at 2
T2 = F.T_h(p=p2,h=h2) #Actual Temperature
s2 = F.s(T=T2,p=p2) #Actual entropy
v2 = 1/F.d(T=T2,p=p2)

#State 3 is based on known p3 & T3
p3 = p2 #same pressure
h3 = F.h(p=p3,T=T3) #Enthalpy
s3 = F.s(p=p3,T=T3) #Entropy
v3 = 1/F.d(T=T3,p=p3)

#State 4s is isentropic from p3-p4
p4 = p1 #same as initial pressure
s4s = s3 #isentropic
T4s,x4s = F.T_s(p=p4,s=s4s,quality=True) #isentropic Temperature (including quality)
if x4s<0: #superheated vapor quality will be -1
    h4s = F.h(T=T4s,p=p4) #Superheated vapor
    v4s = 1/F.d(T=T4s,p=p4)
else:
    h4s = F.h(x=x4s,p=p4) #Liq/Vap mixture
    v4s = 1/F.d(x=x4s,p=p4)

#State 4 is found by applying the isentropic efficiency
Wts = h3-h4s #Isentropic work
Wt = Wts*eta_turb #Actual work
h4 = h3-Wt #Actual enthalpy at 4
T4,x4 = F.T_h(p=p4,h=h4,quality=True) #Actual Temperature (including quality)
if x4<0: #superheated vapor quality will be -1
    s4 = F.s(T=T4,p=p4) #Superheated vapor
    v4 = 1 / F.d(T=T4, p=p4)
else:
    s4 = F.s(x=x4,p=p4) #Liq/Vap mixture
    v4 = 1/F.d(x=x4,p=p4)

#Find the work and heat transfer terms
Qhi = (h3-h2) #kJ/kg
Qlo = (h4-h1) #kJ/kg
Wnet = (Wt-Wp) #kJ/kg
eff = Wnet/Qhi

LifeFuelCost = (mdot * Qhi/FuelEff * FuelCost * 60*60*24*365)*nyrs
LifeCosts = LifeFuelCost + syscost
LifeSavings = (mdot * Wnet * EnergyValue * 60*60*24*365)*nyrs

# Insert the cgi call to build the image
P.insert(
        '<img class="figure" src="/cgi-bin/live/rankinedesign_plot.py?id={:s}&p1={:f}&p2={:f}&T3={:f}&eta_pump={:f}&eta_turb={:f}&up={:s}&uT={:s}&uE={:s}&uM={:s}&uV={:s}">'.format(
                species, float(p1), float(p2), float(T3), float(eta_pump), float(eta_turb), up, uT, uE, uM, uV),\
        (chartline,0))


# Construct table lists for displaying
# This inspires some future code to automatically collapse the arrays
# to make the float() conversions unnecessary
st = [1,2,3,4]
T = [float(T1), float(T2), float(T3), float(T4)]
p = [float(p1), float(p2), float(p3), float(p4)]
v = [float(v1), float(v2), float(v3), float(v4)]
h = [float(h1), float(h2), float(h3), float(h4)]
s = [float(s1), float(s2), float(s3), float(s4)]
x = ['0', 'liquid', 'vapor', float(x4)]
# build label and unit lists
labels = ['','T', 'p', 'v', 'h', 's', 'x']
units = ['', uT, up, uV+'/'+uM, uE+'/'+uM, uE+'/'+uM+uT,'']

P.insert('<h3>Cycle States</h3><center>' + 
        pmcgi.html_column_table(labels, units, (st,T,p,v,h,s,x), thousands=',')\
        + '</center>', (resline,0), wait=True)


Qhi = Qhi[0]
Qlo = Qlo[0]
Wp = Wp[0]
Wt = Wt[0]
Wnet = Wnet[0]
eff = eff[0]
LifeFuelCost = LifeFuelCost[0]
LifeCosts = LifeCosts[0]
LifeSavings = LifeSavings[0]

P.insert("""<h3>Performance per unit Mass</h3>
<center><table>
<tr><th>Parameter</th><th>Symb.</th><th>Value</th><th>Units</th></tr>
<tr><td>Pump Work</td><td>W<sub>1-2</sub></td><td>{5:.2f}</td><td>{2:s}/{3:s}</td></tr>
<tr><td>Boiler Heat</td><td>Q<sub>2-3</sub></td><td>{6:.2f}</td><td>{2:s}/{3:s}</td></tr>
<tr><td>Work Out</td><td>W<sub>3-4</sub></td><td>{7:.2f}</td><td>{2:s}/{3:s}</td></tr>
<tr><td>Condenser Heat</td><td>Q<sub>4-1</sub></td><td>{8:.2f}</td><td>{2:s}/{3:s}</td></tr>
</table></center>""".format(up,uT,uE,uM,uV,Wp,Qhi,Wt,Qlo), (resline+1,0), wait=True)

P.insert("""<h3>Cycle Net Performance</h3>
<center><table>
<tr><th>Parameter</th><th>Symb.</th><th>Value</th><th>Units</th></tr>
<tr><td>Efficiency</td><td>&eta;</td><td>{5:.2f}</td><td>%</td></tr>
<tr><td>Net Specific Power</td><td>W<sub>net</sub>/m<sub>dot</sub></td><td>{6:.2f}</td><td>{2:s}/{3:s}</td></tr>
<tr><td>Net Power</td><td>W<sub>net</sub></td><td>{7:.2f}</td><td>kW</td></tr>
<tr><td>Ann Energy</td><td>E<sub>ann</sub></td><td>{8:,.2f}</td><td>kWh</td></tr>
<tr><td>Ann Energy</td><td>E<sub>ann</sub></td><td>{9:,.2f}</td><td>kJ</td></tr>
</table></center>""".format(up,uT,uE,uM,uV,100*eff,Wnet,Wnet*mdot,Wnet*mdot* 24*365,Wnet*mdot* 60*60*24*365), (resline+2,0), wait=True)

P.insert("""<h3>Financial Performance</h3>
<center><table>
<tr><th>Parameter</th><th>Value</th><th>Units</th></tr>
<tr><td>Annual Fuel Cost</td><td>{5:,.2f}</td><td>$/yr</td></tr>
<tr><td>Lifetime Fuel Cost</td><td>{6:,.2f}</td><td>$</td></tr>
<tr><td>System Cost</td><td>{7:,.2f}</td><td>$</td></tr>
<tr><td>Total Lifetime Cost</td><td>{8:,.2f}</td><td>$</td></tr>
<tr><td>Annual Earnings</td><td>{9:,.2f}</td><td>$/year</td></tr>
<tr><td>Lifetime Earnings</td><td>{10:,.2f}</td><td>$</td></tr>
<tr><td>Annual Operating Profit</td><td>{11:,.2f}</td><td>$/year</td></tr>
<tr><td>Lifetime Profit</td><td>{12:,.2f}</td><td>$</td></tr>
</table></center>""".format(up,uT,uE,uM,uV,LifeFuelCost/nyrs,LifeFuelCost,syscost,LifeCosts,LifeSavings/nyrs,LifeSavings,LifeSavings/nyrs-LifeFuelCost/nyrs, LifeSavings-LifeCosts), (resline+3,0), wait=True)


P.insert_exec()


P.write()
