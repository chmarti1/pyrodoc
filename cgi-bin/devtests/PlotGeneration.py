import pyromat as pm
import matplotlib.pyplot as plt
import numpy as np

uT = 'K'
up = 'kPa'
uM = 'kg'
uE = 'kJ'
uV = 'm3'

pm.config['unit_temperature'] = uT
pm.config['unit_pressure'] = up
pm.config['unit_matter'] = uM
pm.config['unit_energy'] = uE
pm.config['unit_volume'] = uV

F = pm.get('mp.H2O')
f = plt.figure()
ax = f.add_subplot(111)

#Saturation Curves
Tt = F.triple()[0]
Tc = F.critical()[0]
eps = (Tc - Tt) * .0001
T = np.linspace(Tt+eps, Tc-eps, 100)
sL, sV = F.ss(T)
ax.plot(sL, T, lw=2,color='k')
ax.plot(sV, T, lw=2,color='k')

#Add an isobar
for p1 in np.logspace(1,6,10):
    smin = F.s(T=F.Tlim()[0],p=p1)
    smax = F.s(T=F.Tlim()[1],p=p1)
    s = np.linspace(smin,smax,100)
    T = F.T_s(p=p1,s=s)
    ax.plot(s,T,lw=2,color='b',linestyle=':')

#Add an isoenth(?)
psp = np.logspace(1,6,20)
for h1 in np.linspace(100,5000,15):
    try:
        Th, xh = F.T_h(p=psp, h=h1, quality=True)
        sh = F.s(T=Th, p=psp)
        if max(xh) > 0:
            sh[xh > 0] = F.s(T=Th[xh > 0], x=xh[xh > 0])
        ax.plot(sh,Th,lw=2,color='r',linestyle='--')
    except:
        print('h=',h1,' failed')

#Add an isochor?

# Dress up the plot
ax.set_xlabel('Entropy (' + uE + '/' + uM + uT + ')')
ax.set_ylabel('Temperature (' + uT + ')')
ax.grid(True)

plt.show()
