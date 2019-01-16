import pyroplot
import pyromat as pm

water = pm.get('mp.H2O')
R134 = pm.get('mp.C2H2F4')

pm.config['unit_pressure'] = 'MPa'

#pyroplot.Ts(R134)
#pyroplot.Ts(water)
#pyroplot.Tv(water)
#pyroplot.Tv(R134)
pyroplot.pv(water)
