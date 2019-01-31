import pyroplot_local as pyroplot
import pyromat as pm

water = pm.get('mp.H2O')
R134 = pm.get('mp.C2H2F4')

pm.config['unit_pressure'] = 'MPa'
sz = (11,8.25)
#pyroplot.Ts(water,size=sz)
#pyroplot.Ts(R134,size=sz)
#pyroplot.Tv(water,size=sz)
#pyroplot.Tv(R134,size=sz)
#pyroplot.pv(water,size=sz)
#pyroplot.pv(R134,size=sz)

import matplotlib.pyplot as plt
f = plt.figure()
ax = pyroplot.Ts(water,size=sz,display=False)
f.axes.append(ax)
f.show()