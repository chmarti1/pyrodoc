import pyroplot
import pyromat as pm

F = pm.get('mp.H2O')

pm.config['unit_pressure'] = 'MPa'

pyroplot.Ts(F)
