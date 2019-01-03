import pyromat as pm
import pyromat.solve as pmsolve
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

def P_h(T,h):
    P_h = pmsolve.solve1n('p', f=F.T_h, param_init=100)
    return P_h(T, h=h)

def P_d(T,d):
    P_d = pmsolve.solve1n('p', f=F.ds, param_init = 1)
    return P_d(d,T=T)

def Psat_d(d):
    def dsv(p):
        return F.ds(p=p)[1]
    Ps_d = pmsolve.solve1n('p', f=dsv, param_init = 1)
    try:
        return Ps_d(d)
    except pm.utility.PMParamError:
        print('Selected density does not intersect the steam dome.')
        return None

#Saturation Curves
Tt = F.triple()[0]
Tc = F.critical()[0]
eps = (Tc - Tt) * .0001
T = np.linspace(Tt+eps, Tc-eps, 100)
sL, sV = F.ss(T)
ax.plot(sL, T, lw=2,color='k')
ax.plot(sV, T, lw=2,color='k')

#Absolute Temperature limits
Tmin = F.Tlim()[0]
Tmax = F.Tlim()[1]

#Add an isobar
for p1 in np.logspace(1,6,10):
    smin = F.s(T=Tmin,p=p1)
    smax = F.s(T=Tmax,p=p1)
    s = np.linspace(smin,smax,100)
    T = F.T_s(p=p1,s=s)
    ax.plot(s,T,lw=2,color='b',linestyle=':')

#Add an isoenth(?)
for h1 in np.linspace(100,5000,15):
#for h1 in [np.linspace(100, 5000, 15)[6]]:
    try:
        psp = np.logspace(1, 6, 20)
        Th, xh = F.T_h(p=psp, h=h1, quality=True)
        sh = F.s(T=Th, p=psp)
        if max(xh) > 0:
            sh[xh > 0] = F.s(T=Th[xh > 0], x=xh[xh > 0])
        ax.plot(sh,Th,lw=2,color='r',linestyle='--')
    except:
        print('h=',h1,' failed')

#Add an isochor?
for v1 in np.logspace(-3,1,10):
    try:
        dv = 1 / v1
        pv = np.logspace(1, 6, 30)
        pmax = F.p(T=Tmax,d=dv)
        pmin = F.p(T=Tmin,d=dv)
        psatv = Psat_d(dv)
        if psatv is not None:
            pv = np.sort(np.insert(pv,0,psatv))
        pv = pv[(pv<pmax) & (pv>pmin)]
        Tv = F.T(p=pv, d=dv)
        sv,xv = F.s(p=pv,d=dv, quality=True)
        if max(xv) > 0:
            sv[xv > 0] = F.s(T=Tv[xv > 0], x=xv[xv > 0])
        ax.plot(sv,Tv,lw=2,color='g',linestyle='--')
    except:
        print('v=',v1,' failed')


# Dress up the plot
ax.set_xlabel('Entropy (' + uE + '/' + uM + uT + ')')
ax.set_ylabel('Temperature (' + uT + ')')
ax.grid(True)

plt.show()
