#!/usr/bin/python3
# power benchmark

import timeit
import numpy as np
import matplotlib.pyplot as plt
import os,sys

def testeval(test, N=1, Navg=1000, ca=1., cb=1.):
    setupstr = 'import numpy as np;'
    setupstr += 'a = %f * np.random.random(%d);'%(ca,N)
    setupstr += 'b = %f * np.random.random(%d)'%(cb,N)
    TT = timeit.Timer(test, setup=setupstr)
    return TT.timeit(number=Navg)


with open('benchmark.dat','w') as ff:
    ff.write(repr(os.uname()))

    Navg=20000
    N = [1,2,5,10,20,50,100,200,500,1000,2000,5000,10000]

    ff.write('Navg = %d\n'%Navg)
    ff.write('# Time tables are in the format \n#n:t\nWhere n is the number of array elements\n# and t is the average execution time in seconds\n')

    # Start with a ** b
    ff.write('\n\n# a ** b\n')
    sys.stdout.write('a**b\n')
    t_star = []
    for n in N:
        t = testeval('a**b',n,Navg=Navg)/Navg
        t_star.append(t)
        sys.stdout.write('%d:%f\n'%(n,t))
        ff.write('%d:%f\n'%(n,t))

    ff.write('\n\n# a * b\n')
    sys.stdout.write('a*b\n')
    t_mul = []
    for n in N:
        t = testeval('a*b',n,Navg=Navg)/Navg
        t_mul.append(t)
        sys.stdout.write('%d:%f\n'%(n,t))
        ff.write('%d:%f\n'%(n,t))

    ff.write('\n\n# np.power(a, b)\n')
    sys.stdout.write('np.power(a,b)\n')
    t_pow = []
    for n in N:
        t = testeval('np.power(a,b)',n,Navg=Navg)/Navg
        t_pow.append(t)
        sys.stdout.write('%d:%f\n'%(n,t))
        ff.write('%d:%f\n'%(n,t))


    f = plt.figure(1)
    f.clf()
    ax = f.add_subplot(111)
    ax.loglog(N,t_star,'bo',label='**')
    ax.loglog(N,t_mul,'go',label='*')
    ax.loglog(N,t_pow,'ro',label='np.power')
    ax.legend(loc=0)
    ax.grid('on')
    ax.set_xlabel('Array size')
    ax.set_ylabel('Mean execution time (sec)')
    f.savefig('benchmark.png')
