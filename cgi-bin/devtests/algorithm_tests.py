import pyromat as pm
import pyromat.solve as pmsolve
import numpy as np
import matplotlib.pyplot as plt


steam = pm.get('mp.H2O')

up = 'kPa'
uT = 'K'
uE = 'kJ'
uM = 'kg'
uV = 'm3'

pm.config['unit_temperature'] = uT
pm.config['unit_pressure'] = up
pm.config['unit_matter'] = uM
pm.config['unit_energy'] = uE
pm.config['unit_volume'] = uV

#P&s
p1 = 100
s1 = 1

T1,x1 = steam.T_s(p=p1,s=s1,quality=True)
if x1>0:
    h1,s1,d1 = steam.hsd(T=T1,x=x1)
else:
    h1,s1,d1 = steam.hsd(p=p1,T=T1)
v1 = 1/d1
p1 = steam.p(T=T1,d=d1)
#Summary
print('P&s: T={T:0.2f}, p={p:0.2f}, v={v:0.2g}, h={h:0.2f}, s={s:0.2f}, x={x:0.2f}'.format(T=T1[0],p=p1[0],x=x1[0],v=v1[0],h=h1[0],s=s1[0]))

#P&h
p1 = 200
h1 = 4000

T1,x1 = steam.T_h(p=p1,h=h1,quality=True)
if x1>0:
    h1,s1,d1 = steam.hsd(T=T1,x=x1)
else:
    h1,s1,d1 = steam.hsd(p=p1,T=T1)
v1 = 1/d1
p1 = steam.p(T=T1,d=d1)
#Summary
print('P&h: T={T:0.2f}, p={p:0.2f}, v={v:0.2g}, h={h:0.2f}, s={s:0.2f}, x={x:0.2f}'.format(T=T1[0],p=p1[0],x=x1[0],v=v1[0],h=h1[0],s=s1[0]))

#P&v
p1 = 400
v1 = 1.3
d1 = 1/v1
h1 = steam.h(p=p1,d=d1)
T1,x1 = steam.T_h(p=p1,h=h1,quality=True)
if x1>0:
    h1,s1,d1 = steam.hsd(T=T1,x=x1)
else:
    h1,s1,d1 = steam.hsd(p=p1,T=T1)
v1 = 1/d1
p1 = steam.p(T=T1,d=d1)
#Summary
print('P&v: T={T:0.2f}, p={p:0.2f}, v={v:0.2g}, h={h:0.2f}, s={s:0.2f}, x={x:0.2f}'.format(T=T1[0],p=p1[0],x=x1[0],v=v1[0],h=h1[0],s=s1[0]))


#T&s
T1 = 400
s1 = 5

P_T = pmsolve.solve1n('p', f=steam.T_s, param_init=20)
p1 = P_T(T1,s=s1)
T1,x1 = steam.T_s(p=p1,s=s1,quality=True)
if x1>0:
    h1,s1,d1 = steam.hsd(T=T1,x=x1)
else:
    h1,s1,d1 = steam.hsd(p=p1,T=T1)
v1 = 1/d1
p1 = steam.p(T=T1,d=d1)
#Summary
print('T&s: T={T:0.2f}, p={p:0.2f}, v={v:0.2g}, h={h:0.2f}, s={s:0.2f}, x={x:0.2f}'.format(T=T1[0],p=p1[0],x=x1[0],v=v1[0],h=h1[0],s=s1[0]))

#T&h
T1 = 400
h1 = 2100

P_T = pmsolve.solve1n('p', f=steam.T_h, param_init=20)
p1 = P_T(T1,h=h1)
T1,x1 = steam.T_h(p=p1,h=h1,quality=True)
if x1>0:
    h1,s1,d1 = steam.hsd(T=T1,x=x1)
else:
    h1,s1,d1 = steam.hsd(p=p1,T=T1)
v1 = 1/d1
p1 = steam.p(T=T1,d=d1)
#Summary
print('T&h: T={T:0.2f}, p={p:0.2f}, v={v:0.2g}, h={h:0.2f}, s={s:0.2f}, x={x:0.2f}'.format(T=T1[0],p=p1[0],x=x1[0],v=v1[0],h=h1[0],s=s1[0]))

#T&v
T1 = 800
v1 = .1
d1 = 1/v1
P_v = pmsolve.solve1n('p', f=steam.T, param_init=400) #Extremely sensitive to guess
p1 = P_v(T1,d=d1)
T1 = steam.T(p=p1,d=d1)
if T1<steam.critical()[0]:
    ds = steam.ds(T=T1)
    x1 = (1/d1-1/ds[0])/(1/ds[1]-1/ds[0])
else:
    x1 = -1
if x1>0 and x1<=1:
    h1,s1,d1 = steam.hsd(T=T1,x=x1)
else:
    h1,s1,d1,x1 = steam.hsd(p=p1,T=T1,quality=True)
v1 = 1/d1
p1 = steam.p(T=T1,d=d1)
#Summary
print('T&v: T={T:0.2f}, p={p:0.2f}, v={v:0.2g}, h={h:0.2f}, s={s:0.2f}, x={x:0.2f}'.format(T=T1[0],p=p1[0],x=x1[0],v=v1[0],h=h1[0],s=s1[0]))

#d&h
h1 = 2100
v1 = 0.5
d1 = 1/v1
P_v = pmsolve.solve1n('p', f=steam.h, param_init=300) #Extremely sensitive to guess
p1 = P_v(h1,d=d1)
T1,x1 = steam.T_h(p=p1,h=h1,quality=True)
if x1>0:
    h1,s1,d1 = steam.hsd(T=T1,x=x1)
else:
    h1,s1,d1 = steam.hsd(p=p1,T=T1)
v1 = 1 / d1
p1 = steam.p(T=T1,d=d1)
print('d&h: T={T:0.2f}, p={p:0.2f}, v={v:0.2g}, h={h:0.2f}, s={s:0.2f}, x={x:0.2f}'.format(T=T1[0],p=p1[0],x=x1[0],v=v1[0],h=h1[0],s=s1[0]))

#d&s
s1 = 7
v1 = 0.5
d1 = 1/v1
P_v = pmsolve.solve1n('p', f=steam.s, param_init=300) #Extremely sensitive to guess
p1 = P_v(s1,d=d1)
T1,x1 = steam.T_s(p=p1,s=s1,quality=True)
if x1>0:
    h1,s1,d1 = steam.hsd(T=T1,x=x1)
else:
    h1,s1,d1 = steam.hsd(p=p1,T=T1)
v1 = 1 / d1
p1 = steam.p(T=T1,d=d1)
print('d&s: T={T:0.2f}, p={p:0.2f}, v={v:0.2g}, h={h:0.2f}, s={s:0.2f}, x={x:0.2f}'.format(T=T1[0],p=p1[0],x=x1[0],v=v1[0],h=h1[0],s=s1[0]))

#s&h - can't be done without a new function?
print('s&h: impossible without new function?')

# Build the T-s plot
f = plt.figure()
ax = f.add_subplot(111)


# Draw the saturation bounds
Tt = steam.triple()[0]
Tc = steam.critical()[0]
#temp = (Tc - Tt) * .001
temp = 1e-10
T = np.linspace(Tt+temp, Tc-temp, 100)
sL, sV = steam.ss(T)
ax.plot(sL, T, lw=2,color='k')
ax.plot(sV, T, lw=2,color='k')

#Add the point
ax.plot(s1,T1,'rx',lw=2)

#Add an isobar
plim = steam.plim()
Tlim = steam.Tlim()
smin = steam.s(T = Tlim[0],p=p1)
smax = steam.s(T = Tlim[1],p=p1)
s = np.linspace(smin,smax,100)
T = steam.T_s(p=p1,s=s)
ax.plot(s,T,'b:',lw=1)

# Dress up the plot
ax.set_xlabel('Entropy (' + uE + '/' + uM + uT + ')')
ax.set_ylabel('Temperature (' + uT + ')')
ax.grid(True)

#f.show()