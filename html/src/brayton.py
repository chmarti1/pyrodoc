#
#   Brayton cycle demo
#   GPL v3.0
#   Enjoy!
#

import pyromat as pm
import numpy as np
import matplotlib.pyplot as plt

air = pm.get('ig.air')
# Force the unit system into kJ,kg,bar,K
pm.config['unit_energy'] = 'kJ'
pm.config['unit_matter'] = 'kg'
pm.config['unit_pressure'] = 'bar'
pm.config['unit_temperature'] = 'K'

# Let's design a gas turbine with a 100kW power output
Wnet = 100.
# There are three processes separating four states in a brayton cycle.
# 
# (1) ---|Compressor|---> (2) ---|Combustor|---> (3) ---|Turbine|---> (4)
#
#(1) The inlet is ambient temperature and pressure.  In our example, we will
#   use 1.013bar and 300K for p1 and T1
state1 = air.state(T=300.,p=1.01325)   # Establish the state of the inlet air

#|Compressor| is ideally an isentropic process designed to compress the 
# incoming air to a certain pressure ratio, pr.  Let's use pr=12.
pr = 12.

#(2) Nothing about the compressor outlet is explicitly prescribed by design.
# We'll have to calculate our way here.
state2 = air.state(s=state1['s'], p=state1['p']*pr)

# How much work did that require?
wc = state2['h'] - state1['h']

#|Combustor| is where we add heat.  We have to be careful not to damage
#  the engine by adding too much heat.  We are limited by a maximum T3.
#  For argument's sake, let's use 1700K.  That's pretty darn hot.
state3 = air.state(T=1700, p=state2['p'])

# How much heat did that take?
qh = state3['h'] - state2['h']

#|Turbine| is where we finally get our useful work.  Some of it will have to
# go to the compressor to keep things going.  The rest of it, we keep.
# The turbine outlet (4) is ambient pressure again, but its temperature
# will be based on the turbine performance.
state4 = air.state(s=state3['s'], p=state1['p'])

# How much work did we get?
wt = state3['h'] - state4['h']
# How much is left after we keep the compressor running?
wnet = wt - wc

# How much mass flow do we need to hit our target power output?
mdot = Wnet / wnet

# What is our efficiency?
n = wnet / qh

# Generate some process diagrams
# First isolate the T,s coordinates
s1 = state1['s']
s2 = state2['s']
s3 = state3['s']
s4 = state4['s']
T1 = state1['T']
T2 = state2['T']
T3 = state3['T']
T4 = state4['T']
p1 = state1['p']
p2 = state2['p']
p3 = state3['p']
p4 = state4['p']

plt.close('all')
plt.figure(1)
# isentropic compression is a vertical line
plt.plot([s1,s1],[T1,T2],'r',linewidth=1.5)
# constant pressure heat addition
T = np.linspace(T2,T3,20)
plt.plot(air.s(T=T,p=p2),T,'r',linewidth=1.5)
# isentropic expansion
plt.plot([s3,s3],[T3,T4],'r',linewidth=1.5)
# The pseudo heat rejction process 
T = np.linspace(T1,T4,20)
plt.plot(air.s(T=T,p=p1),T,'r--',linewidth=1.5)
# broaden the axes ranges
ax = plt.gca()
ax.set_xlim([6.1,8.5])
ax.set_ylim([200,2000])
# add labels and turn on the grid
plt.xlabel('Entropy, s (kJ/kg/K)')
plt.ylabel('Temperature, T (K)')
plt.grid('on')
# Add state labels
plt.text(s1-.1,T1,'(1)\nT={:.1f}\np={:.3f}'.format(float(T1),float(p1)),
    ha='right',backgroundcolor='white')
plt.text(s1-.1,T2,'(2)\nT={:.1f}\np={:.3f}'.format(float(T2),float(p2)),
    ha='right',backgroundcolor='white')
plt.text(s3+.1,T3,'(3)\nT={:.1f}\np={:.3f}'.format(float(T3),float(p3)),
    ha='left',backgroundcolor='white')
plt.text(s3+.1,T4,'(4)\nT={:.1f}\np={:.3f}'.format(float(T4),float(p4)),
    ha='left',backgroundcolor='white')
# Add a summary
plt.text(6.5,1200,
"""$\\dot{{m}}$ = {:.3f}kg/s
$p_r$={:.1f}
$\\eta$={:.3f}
$\\dot{{W}}_{{net}}$={:1}kW""".format(float(mdot),float(pr),float(n),float(Wnet)),
    backgroundcolor='white')
plt.title('Brayton Cycle T-s Diagram')

plt.show()
#plt.show(block=False)
