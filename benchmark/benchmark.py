#!../../bin/python

import matplotlib.pyplot as plt
import pyromat as pm
import test
import time
import numpy as np

NDEF = [1, 10, 100, 1000, 10000, 100000]
RDEF = [1000, 1000, 100, 10, 10, 10]


def generate(subst, N=10000):
    if subst.pmclass() in ['mp1', 'mp2']:
        Tmin, Tmax = subst.Tlim()
        _,pmax = subst.plim()
        dmax = subst.d(T=Tmin, p=pmax)
        T = np.random.random(N) * (Tmax - Tmin) + Tmin
        d = np.random.random(N) * dmax
        p = subst.p(T=T, d=d)
        I = p > pmax
        while I.any():
            dd = np.random.random(np.sum(I)) * dmax
            d[I] = dd
            p = subst.p(T=T[I], d=dd)
            I[I] = p > pmax
        state = subst.state(T=T, d=d)
    else:
        Tmin,Tmax = subst.Tlim()
        pmax = 1000.
        T = np.random.random(N) * (Tmax-Tmin) + Tmin
        p = np.random.random(N) * pmax
        state = subst.state(T=T,p=p)

        
    return state


def benchmark(subst, number=NDEF, repeat=RDEF):

    print(subst)
    filename = subst.sid() + '.benchmark'
    with open(filename, 'w') as fd:
        fd.write('# Benchmarking data for substance ' + subst.sid() + '\n')
        fd.write('# Each entry is a duration (in seconds) to complete an operation.\n')
        fd.write('# Each column represents the same operation, each row represents the same dataset size.\n')
        fd.write('# The operations are: _argparse(T,d), state(T,d), _argparse(T,p), state(T,p), _argparse(s,p), state(s,p)\n')
        fd.write('# Array sizes are: ' + repr(number) + '\n')
        for N,Navg in zip(number, repeat):
            print(f'->array size:{N}')
            state = generate(subst, N)
            
            print(f'  ->_argparse(T,d)')
            duration = 0
            for count in range(Navg):
                start = time.time()
                subst._argparse(T=state['T'], d=state['d'])
                duration += (time.time() - start)
            duration /= Navg
            fd.write(f'{duration:e}\t')
            
            print(f'  ->state(T,d)')
            duration = 0
            for count in range(Navg):
                start = time.time()
                subst.state(T=state['T'], d=state['d'])
                duration += (time.time() - start)
            duration /= Navg
            fd.write(f'{duration:e}\t')
        
            print(f'  ->_argparse(T,p)')
            duration = 0
            for count in range(Navg):
                start = time.time()
                subst._argparse(T=state['T'], p=state['p'])
                duration += (time.time() - start)
            duration /= Navg
            fd.write(f'{duration:e}\t')
            
            print(f'  ->state(T,p)')
            duration = 0
            for count in range(Navg):
                start = time.time()
                subst.state(T=state['T'], p=state['p'])
                duration += (time.time() - start)
            duration /= Navg
            fd.write(f'{duration:e}\t')

            print(f'  ->_argparse(s,p)')
            duration = 0
            for count in range(Navg):
                start = time.time()
                subst._argparse(s=state['s'], p=state['p'])
                duration += (time.time() - start)
            duration /= Navg
            fd.write(f'{duration:e}\t')
            
            print(f'  ->state(s,p)')
            duration = 0
            for count in range(Navg):
                start = time.time()
                subst.state(s=state['s'], p=state['p'])
                duration += (time.time() - start)
            duration /= Navg
            fd.write(f'{duration:e}\n')


def plot(filename, ax=None, number=NDEF, marker='o'):
    if ax is None:
        fig,ax = plt.subplots(1,1)
        ax.set_xlabel('Dataset size')
        ax.set_ylabel('Execution time (s)')
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.grid(True)
    
    linestyle = ['--', '-']
    color = ['k', 'b', 'r']
    
    # Load the raw data    
    data = []
    with open(filename, 'r') as fd:
        for thisline in fd:
            if not thisline.startswith('#'):
                data.append([float(this) for this in thisline.split()])
    data = np.array(data)
    
    for index in range(6):
        ls = linestyle[index%2]
        c = color[index//2]
        ax.plot(number, data[:,index], linestyle=ls, color=c, marker=marker, mec=c, mfc='w')

    return ax
