# power benchmark

import timeit
import numpy as np
import matplotlib.pyplot as plt

def testeval(test, N=1, Navg=1000, ca=1., cb=1.):
    setupstr = 'import numpy as np;'
    setupstr += 'a = %f * np.random.random(%d);'%(ca,N)
    setupstr += 'b = %f * np.random.random(%d)'%(cb,N)
    TT = timeit.Timer(test, setup=setupstr)
    return TT.timeit(number=Navg)
    
Navg=100000
N = [1,2,5,10,20,50,100,200,500,1000,2000,5000,10000]
print 'a**b...'
t_star = [testeval('a**b',n,Navg=Navg)/Navg for n in N]
print 'a*b...'
t_mul = [testeval('a*b',n,Navg=Navg)/Navg for n in N]
print 'power(a,b)...'
t_pow = [testeval('np.power(a,b)',n,Navg=Navg)/Navg for n in N]

f = plt.figure(1)
f.clf()
ax = f.add_subplot(111)
ax.loglog(N,t_star,'bo',label='**')
ax.loglog(N,t_mul,'go',label='*')
ax.loglog(N,t_pow,'ro',label='np.power')
ax.legend(loc=0)
ax.grid('on')
f.savefig('benchmark.png')
