import pyromat as pm
import numpy as np
import matplotlib.pyplot as plt

# Rankine cycle analysis
#
#   A Rankine cycle is a closed loop usually using water as the working
# fluid.  A low-pressure reservoir contains liquid.  The liquid is 
# pumped into a high pressure boiler, where steam is generated.  
# Optionally, the steam is further super-heated beyond its saturation
# temperature.  The steam is then passed through a turbine (or piston)
# where useful work is extracted.  Finally, waste heat is rejected and
# the remaining steam is condensed into liquid before being returned
# to the reservoir.
#
#   (1 Reservoir) --> |Feed water pump| --> (2) --> |Boiler| --> (3)
#         ^                                                       |
#         |                                                       |
#    |Condenser| <-- (5) <-- |Turbine| <-- (4) <-- |Superheater| <-
#
#  Given the high and low pressures, this code determines the processes
# so that the turbine exit (5) is precisely saturated steam.
#
#  There are multiple ways to approach a Rankine model.  In this one, 
# we'll assume that the liquid exiting the condensor does not cool 
# further than the saturation line, so T1 is the saturated liquid 
# temperature at p1.
#
#  We'll approach the superheater design to attempt to place state 5 
# precisely on the vapor saturation line. Reality will not be so kind,
# and users may want to use different assumptions here.  After all, 
# this is only a demo.


# Use different color codes to change the color of the plots
color = 'r'    # Red
#color = 'b'   # Blue
# This is a True/False flag to deactivate the plot text
show_text = True
# This is a True/False flag to allow over-plotting of previous results
clear_plots = False
# Liquid water reservoir is at ambient pressure
p1 = 1.013
# Operating pressure of the boiler
p2 = 18.3   # 18.3 bar is roughly 250 psig
#p2 = 11.4  # 11.4 bar is roughly 150 psig

# How much work do we need?
Wnet = 100. # Let's make a 100kW engine


# Get the steam data
steam = pm.get('mp.H2O')

# (1) Calculate the reservoir state
# This will be saturated liquid at atmospheric pressure
state1 = steam.state(p=p1, x=0.)

# (2) Calculate the pump outlet state
# This will be isentropic compression of the liquid
state2 = steam.state(p=p2, s=state1['s'])

# (2s) Let state 2s be the point where the boiler heats the liquid to 
# a saturated liquid.  It will be very close to (2).
state2s = steam.state(p=p2, x=0.)

# (3) The boiler will span the dome
state3 = steam.state(p=p2, x=1.)

# (4,5) Next, the superheater will further heat the steam until it 
# reaches the desired temperature.  To determine the amount of super-
# heating required, first we establish the desired state 5.
state5 = steam.state(p=p1, x=1.)
state4 = steam.state(p=p2, s=state5['s'])


# All the states are known, now.
#
# How much work did the feed water pump do?
# This might also be approximated as volume flow times
# pressure change.
w12 = state1['h'] - state2['h']

# How much heat did the boiler add?
q23 = state3['h'] - state2['h']

# How much heat did the superheater add?
q34 = state4['h'] - state3['h']

# How much work did the turbine produce
w45 = state4['h'] - state5['h']

# How much heat is rejected by the condenser?
q51 = state1['h'] - state5['h']

# calculate the net work per kg of water
wnet = w45 + w12
# calculate the total heat addition
qh = q23 + q34
# calculate the mass flow required to size the engine
mdot = Wnet/wnet
# calculate the engine's efficiency
n = wnet/qh
# heats
Qboil = q23 * mdot
Qsuper = q34 * mdot

#####################################
# Generate some diagrams
#   Many users won't need to do this.
#   It's just as valid to query the
#   variables in the interpreter.
#####################################
# Let figure 1 be a T-s diagram
f1 = plt.figure(1)
if clear_plots:
    plt.clf()
ax1 = f1.add_subplot(111)
ax1.set_xlabel('Entropy, s (kJ/kg/K)')
ax1.set_ylabel('Temperature, T (K)')
ax1.set_title('Rankine Cycle T-s Diagram')

# Let figure 2 be a P-v diagram
f2 = plt.figure(2)
if clear_plots:
    plt.clf()
ax2 = f2.add_subplot(111)
ax2.set_ylabel('Pressure, p (bar)')
ax2.set_xlabel('Volume, v (m$^3$/kg)')
ax2.set_title('Rankine Cycle p-v Diagram')

# Generate the dome on both plots
Tt,pt = steam.triple()
Tc,pc = steam.critical()
T = np.arange(Tt,Tc,2.5)
p = steam.ps(T)
dL,dV = steam.ds(T=T)
sL,sV = steam.ss(T=T)
ax1.plot(sL,T,'k')
ax1.plot(sV,T,'k')
ax2.plot(1./dL,p,'k')
ax2.plot(1./dV,p,'k')

# Process 1-2 (isentropic compression of a liquid)
p = np.array([state1['p'],state2['p']])
T = np.array([state1['T'],state2['T']])
v = np.array([state1['v'],state2['v']])
s = np.array([state1['s'],state2['s']])
ax1.plot(s,T,color,linewidth=1.5)
ax2.plot(v,p,color,linewidth=1.5)

# Process 2-2s (constant-p heat until saturation)
T = np.linspace(state2['T'],state2s['T'],10)
p = state2['p'] * np.ones(T.shape)
curve = steam.state(T=T,p=p)
curve['s'][-1] = state2s['s'] # force the last points to be liquid - not vapor
curve['v'][-1] = state2s['v'] # force the last points to be liquid - not vapor

ax1.plot(curve['s'],T,color,linewidth=1.5)
ax2.plot(curve['v'],curve['p'],color,linewidth=1.5)

# Process 2s-3 (constant-p boiling)
s = np.array([state2s['s'], state3['s']])
T = np.array([state2s['T'], state3['T']])
v = np.array([state2s['v'], state3['v']])
p = np.array([state2s['p'], state3['p']])
ax1.plot(s,T,color,linewidth=1.5)
ax2.plot(v,p,color,linewidth=1.5)

# Process 3-4 (constant-p superheating)
T = np.linspace(state3['T'],state4['T'],20)
p = state3['p']*np.ones(T.shape)
curve = steam.state(T=T,p=p)
ax1.plot(curve['s'],T,color,linewidth=1.5)
ax2.plot(curve['v'],p,color,linewidth=1.5)

# process 4-5 (isentropic expansion)
s = np.array([state4['s'], state5['s']])
T = np.array([state4['T'], state5['T']])
v = np.array([state4['v'], state5['v']])
p = np.array([state4['p'], state5['p']])
ax1.plot(s,T,color,linewidth=1.5)
ax2.plot(v,p,color,linewidth=1.5)
#p = np.linspace(p4,p5,20)
#T = np.zeros(p.shape)
#for index in range(p.size):
#    T[index],_ = steam.psolve(p=p[index],s=s4)
#d = steam.d(T=T,p=p)
#s = steam.s(T=T,p=p)
#ax1.plot(s,T,'r',linewidth=1.5)
#ax2.plot(1./d,p,'r',linewidth=1.5)

# process 5-1 (constant-p heat rejection)
# add the line across the dome
s = np.array([state1['s'], state5['s']])
T = np.array([state1['T'], state5['T']])
v = np.array([state1['v'], state5['v']])
p = np.array([state1['p'], state5['p']])
ax1.plot(s,T,color,linewidth=1.5)
ax2.plot(v,p,color,linewidth=1.5)


# Add some labels
if show_text:
    ax1.text(state1['s']-2.5,state1['T'],
    """(1) 
T={0:.1f}K
s={1:.3f}kJ/kg/K
(2)
T={2:.1f}K
s={3:.3f}kJ/kg/K""".format(float(state1['T']),float(state1['s']),float(state2['T']),float(state2['s'])))
    ax1.text(state3['s']-3,state3['T']+20,
    """(3) 
T={0:.1f}K
s={1:.3f}kJ/kg/K""".format(float(state3['T']),float(state3['s'])))
    ax1.text(state4['s']+.2,state4['T']-100,
    """(4) 
T={0:.1f}K
s={1:.3f}kJ/kg/K""".format(float(state4['T']),float(state4['s'])))
    ax1.text(state5['s']+.2,state5['T'],
    """(5) 
T={0:.1f}K
s={1:.3f}kJ/kg/K""".format(float(state5['T']),float(state5['s'])))
    
    ax2.text(state1['v'],state1['p']/5.,
    """(1) 
p={0:.2f}bar
v={1:f}m$^3$/kg""".format(float(state1['p']),float(state1['v'])))
    
    ax2.text(state2['v']*1.5,state2['p']*1.1,
    """(2) 
p={0:.2f}bar
v={1:f}m$^3$/kg""".format(float(state2['p']),float(state2['v'])))
    
    ax2.text(state3['v'],state3['p'],
    """(3) 
p={0:.2f}bar
v={1:f}m$^3$/kg
(4)
p={2:.2f}bar
v={3:f}m$^3$/kg""".format(float(state3['p']),float(state3['v']),float(state4['p']),float(state4['v'])))

    ax2.text(state5['v']/5,state5['p']/5,
    """(5) 
p={0:.2f}bar
v={1:f}m$^3$/kg""".format(float(state5['p']),float(state5['v'])))
    
    ax1.text(-.5,575,"""$\\dot{{m}}$ = {0:.3f}kg/s
$\\eta$ = {1:.3f}
$\\dot{{W}}_{{NET}}$ = {2:.0f}kW
$\\dot{{Q}}_{{BOIL}}$ = {3:.1f}kW
$\\dot{{Q}}_{{SUPER}}$ = {4:.1f}kW""".format(float(mdot),float(n),float(Wnet),float(Qboil),float(Qsuper)))

ax1.grid('on')
ax2.grid('on')
ax2.set_xscale('log')
ax2.set_yscale('log')

ax1.set_xlim([-2,10])
ax1.set_ylim([300,800])
# adjust the volume scale
ax2.set_xlim([5e-4, 10])
ax2.set_ylim([.01,1000.])

plt.show()
#plt.show(block=False)
