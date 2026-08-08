#!/usr/bin/python3

import pyromat as pm
import numpy as np
import matplotlib.pyplot as plt

ar = pm.get('ig.Ar')
he = pm.get('ig.He')
o2 = pm.get('ig.O2')
n2 = pm.get('ig.N2')
h2o = pm.get('ig.H2O')
co2 = pm.get('ig.CO2')
#c3h8 = pm.get('ig.C3H8')


T = np.linspace(200, 6000,200)
f,ax = plt.subplots(1,1)
f.set_size_inches(8,6)
ax.plot(T, 2*ar.cv(T)/ar.R(), 'k', label='Ar')
ax.plot(T, 2*he.cv(T)/he.R(), 'k--', label='He')
ax.plot(T, 2*o2.cv(T)/o2.R(), 'b', label='O2')
ax.plot(T, 2*n2.cv(T)/n2.R(), 'b--', label='N2')
ax.plot(T, 2*h2o.cv(T)/h2o.R(), 'r', label='H2O')
ax.plot(T, 2*co2.cv(T)/co2.R(), 'r--', label='CO2')
#ax.plot(T, 2*c3h8.e(T)/c3h8.R(), 'g', label='C3H8')

ax.set_xlabel('Tempreature, T / K', fontsize=14)
ax.set_ylabel('$2 c_v / R$', fontsize=14)
#ax.set_xlim([0,6000])
#ax.set_ylim([0,14])
ax.set_yticks(np.arange(0,15))
ax.legend(loc='lower right', fontsize=14)
ax.grid(True)

f.savefig('dof.png')
