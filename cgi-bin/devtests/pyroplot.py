"""PYroPlot: The PYroMat plotting module

ts()        Temperature-entropy diagrams
ph()        Pressure-enthalpy diagrams

"""

import matplotlib.pyplot as plt
import matplotlib.figure
import numpy as np
import pyromat as pm



config = {
    'sat_color':'k',
    'sat_width':2,
    'sat_style':'-',
    'p_color':[1.0,0.5,0.5],
    'p_width':1,
    'p_style':'-',
    'd_color':[0.5,0.5,1.0],
    'd_width':1,
    'd_style':'-',
    'h_color':[0.3,0.6,0.3],
    'h_width':1,
    'h_style':'-',
}

def _slope_ratio(figure,axis):
    """Get the ratio of the mathematical derivative to the geometric
    slope on any given figure axis.

    ratio = _slope_ratio(figure,axis)

    Result can be used as: geom_slope = math_slope * ratio"""

    # Ratio of plot axes
    size = figure.get_size_inches() * figure.dpi
    w = size[0]
    h = size[1]
    origin = axis.get_position()
    originx_pct = origin.get_points()[0][0]
    originy_pct = origin.get_points()[0][1]
    maxx_pct = origin.get_points()[1][0]
    maxy_pct = origin.get_points()[1][1]
    xlim_low = axis.get_xlim()[0]
    xlim_hi = axis.get_xlim()[1]
    ylim_low = axis.get_ylim()[0]
    ylim_hi = axis.get_ylim()[1]
    xpix = w * (maxx_pct - originx_pct)
    ypix = h * (maxy_pct - originy_pct)
    xrange = xlim_hi - xlim_low
    yrange = ylim_hi - ylim_low
    r = (xrange / xpix) / (yrange / ypix)  # dydx*r where r= (xrange/xpix)/(yrange/ypix)
    return r

def _slope_ratio_logx(figure,axis):
    """Get the ratio of the mathematical derivative to the geometric
    slope on any given figure axis, based on a semilog-x scale.

    ratio = _slope_ratio_logx(figure,axis)

    Result can be used as: geom_slope = math_slope * ratio"""

    # Ratio of plot axes
    size = figure.get_size_inches() * figure.dpi
    w = size[0]
    h = size[1]
    origin = axis.get_position()
    originx_pct = origin.get_points()[0][0]
    originy_pct = origin.get_points()[0][1]
    maxx_pct = origin.get_points()[1][0]
    maxy_pct = origin.get_points()[1][1]
    xlim_low = axis.get_xlim()[0]
    xlim_hi = axis.get_xlim()[1]
    ylim_low = axis.get_ylim()[0]
    ylim_hi = axis.get_ylim()[1]
    xpix = w * (maxx_pct - originx_pct)
    ypix = h * (maxy_pct - originy_pct)
    xrange = np.log10(xlim_hi/xlim_low)
    yrange = ylim_hi - ylim_low
    r = (xrange / xpix) / (yrange / ypix)  # dydx*r where r= (xrange/xpix)/(yrange/ypix)
    return r

def _interval(start, stop, count, inc=[1,2,5]):
    """Auto-generate conveniently spaced values in a range
    array = _interval(start, stop, count)
    
Generates an array of approximately uniformly spaced values beginning 
after start, and stopping before stop.  Unlike arange() or linspace(),
this function chooses values that are rounded to a nearest convenient 
interval.  This is commonly done for plotting.

The optional 'inc' parameter indicates the intervals that may be used
in any given decade.  They should be values larger than or equal to 1
and smaller than 10.  By default, inc=[1,2,5], which indicates that 
valid step sizes might be .01, .02, .05, .1, .2, .5, 1, 2, 5, 10, 20, 50
etc... 

To produce elegantly roundable numbers, the start value will be rounded
up to the nearest integer multiple of the selected incrementer.
"""
    # Calculate an increment that is the next largerst value in inc
    # scaled to the relevant decade
    dx = abs(stop-start) / count
    power = np.floor(np.log10(dx))
    dx /= 10**power
    inc.sort(reverse=True)
    for ii in inc:
        if ii<=dx:
            break
    dx = ii * 10**power
    
    # Round to the nearest incrementer
    start = dx * np.ceil(start / dx)
    return np.arange(start, stop, dx)
    
def _log_interval(start, stop, count, inc=[1,2,5]):
    """Auto-generate conveniently spaced values in a range
    array = _log_interval(start, stop, count)
    
Generates an array of approximately count values beginning after start, 
and stopping before stop.  Just like _interval(), this function does not
strictly respect the start, stop, or count parameters, but rounds to
the nearest conveniently represented decimal value. 

Unlike _interval(), _log_interval() adjusts the incrementer as the 
series progresses, so that it will always match the decade of the 
current value.

The optional 'inc' parameter indicates the intervals that may be used
in any given decade.  They should be values larger than or equal to 1
and smaller than 10.  By default, inc=[1,2,5], which indicates that 
valid step sizes might be .01, .02, .05, .1, .2, .5, 1, 2, 5, 10, 20, 50
etc... 

To produce elegantly roundable numbers, the start value will be rounded
up to the nearest integer multiple of the selected incrementer.
"""
    inc = np.asarray(inc)
    # transform the problem to a log-space
    log_start = np.log(start)
    log_stop = np.log(stop)
    log_dx = abs(log_stop - log_start) / count
    # produce an evenly spaced logarithmic series
    out = np.exp(np.arange(log_start, log_stop, log_dx))
    dx = out * log_dx
    for ii in range(out.size):
        # Calculate a nominal spacing
        dx = np.abs(out[ii] * log_dx)
        power = np.floor(np.log10(dx))
        dx /= 10**power
        # Adjust it to the nearest inc value
        dx = inc[np.argmin(np.abs(inc-dx))] * 10 ** power
        # Round out to the nearest integer multiple of the dx value
        out[ii] = dx * np.round(out[ii]/dx)
        
    # eliminate any points outside of start and stop
    out = out[np.logical_and(
            out <= max(start,stop),
            out >= min(start,stop)
            )]
    return out


def _dlines(mpobj):
    """Returns the default density lines for a given mpobject"""
    Tc,pc,dc = mpobj.critical(density=True)
    dlim = [dc / 1000., 2 * dc]
    DLINES = np.flip(_log_interval(dlim[0], dlim[1], 10, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]), 0)
    DLINES = np.flip(1/np.logspace(-3,1,10))
    return DLINES

def _plines(mpobj):
    """Returns the default pressure lines for a given mpobject"""
    plim = mpobj.plim()
    Tt,pt = mpobj.triple()
    # Force plim to be greater than pt
    plim[0] = max(pt, plim[0])
    PLINES = _log_interval(plim[0], plim[1], 10)
    return PLINES

def _hlines(mpobj):
    """Returns the default enthalpy lines for a given mpobject"""
    plim = mpobj.plim()
    Tt,pt = mpobj.triple()
    # Force plim to be greater than pt
    plim[0] = max(pt, plim[0])
    Tlim = mpobj.Tlim()
    hlim = [mpobj.h(T=1.05 * Tlim[0], p=0.95 * plim[1]), mpobj.h(T=0.95 * Tlim[1], p=0.95 * plim[1])]
    HLINES = np.linspace(hlim[0], hlim[1], 15)
    return HLINES

def _slines(mpobj):
    """Returns the default entropy lines for a given mpobject"""
    plim = mpobj.plim()
    Tt,pt = mpobj.triple()
    # Force plim to be greater than pt
    plim[0] = max(pt, plim[0])
    Tlim = mpobj.Tlim()
    slim = [mpobj.s(T=1.05 * Tlim[0], p= 1.05* plim[0]), mpobj.s(T=0.95 * Tlim[1], p=1.05 * plim[0])]
    SLINES = np.linspace(slim[0], slim[1], 15)
    return SLINES

def Tp(mpobj, fig=None, ax=None, Tlim=None, plim=None, dlines=None):
    """Temperature-pressure diagram
"""

    # Select a figure
    if fig is None:
        if ax is not None:
            fig = ax.get_figure()
        else:
            fig = plt.figure()
    elif isinstance(fig, matplotlib.figure.Figure):
        pass
    else:
        fig = plt.figure(fig)
    
    # Select an axes
    if ax is None:
        fig.clf()
        ax = fig.add_subplot(111)
    
    if Tlim is None:
        Tlim = mpobj.Tlim()
        
    if plim is None:
        plim = mpobj.plim()
    
    Tc,pc,dc = mpobj.critical(density=True)
    Tt,pt = mpobj.triple()
    
    plim[0] = max(plim[0], pt)
    
    if dlines is None:
        dlim = [dc / 1000., dc]
        DLINES = np.flip(_log_interval(dlim[0], dlim[1], 10), 0)
    else:
        DLINES = np.asarray(dlines)
    
    Tn = (Tc - Tt) / 1000.

    # Generate lines
    T = np.linspace(Tlim[0]+Tn, Tlim[1]-Tn, 151)
    
    # Lines of constant density
    for d in DLINES:
        p = mpobj.p(T=T,d=d)
        ax.loglog(p,T,
                config['d_style'],
                color=config['d_color'],
                lw=config['d_width'])
                
    # Generate the dome
    T = np.linspace(Tt+Tn,Tc-Tn,101)
    p = mpobj.ps(T)

    ax.loglog(p,T,
            ls=config['sat_style'],
            color=config['sat_color'],
            lw=config['sat_width'])
        
    # Label the s-axis
    ax.set_xlabel('p [%s]'%(pm.config['unit_pressure']))
            
    # Label the T-axis
    ax.set_ylabel('T [%s]'%(
            pm.config['unit_temperature']))
        
    # Label the figure
    ax.set_title('%s T-p Diagram'%(mpobj.data['id']))
        
    plt.show(block=False)
    return ax


def Ts(mpobj, fig=None, ax=None, satlines=True, Tlim=None, dlines=None, plines=None, hlines=None):
    """Temperature-enthalpy diagram
    ax = TS(mpobj)
    
"""
    # Select a figure
    if fig is None:
        if ax is not None:
            fig = ax.get_figure()
        else:
            fig = plt.figure()
    elif isinstance(fig, matplotlib.figure.Figure):
        pass
    else:
        fig = plt.figure(fig)
    
    # Select an axes
    if ax is None:
        fig.clf()
        ax = fig.add_subplot(111)
    
    if Tlim is None:
        Tlim = mpobj.Tlim()

    plim = mpobj.plim()

    Tc,pc,dc = mpobj.critical(density=True)
    Tt,pt = mpobj.triple()
    
    if dlines is None:
        DLINES = _dlines(mpobj)
    else:
        DLINES = np.asarray(dlines)
    
    if plines is None:
        PLINES = _plines(mpobj)
    else:
        PLINES = np.asarray(plines)

    if hlines is None:
        HLINES = _hlines(mpobj)
    else:
        HLINES = np.asarray(hlines)

    Tn = (Tc - Tt) / 1000.

    # Generate lines
    T = np.linspace(Tlim[0]+Tn, Tlim[1]-Tn, 151)
    
    # Lines of constant pressure
    for p in PLINES:
        s = mpobj.s(T=T,p=p)
        ax.plot(s,T,
                config['p_style'],
                color=config['p_color'], 
                lw=config['p_width'])
    
    # Lines of constant density
    for d in DLINES:
        s = mpobj.s(T=T,d=d)
        ax.plot(s,T,
                config['d_style'],
                color=config['d_color'],
                lw=config['d_width'])


    # Lines of constant enthalpy
    for h in HLINES[:]: #Copy HLINES for the iteration, so that we can remove ones that fail
        try:
            psp = np.logspace(np.log10(1e-5*plim[1]),np.log10(0.95*plim[1]),20)
            Th, xh = mpobj.T_h(p=psp, h=h, quality=True)
            sh = mpobj.s(T=Th, p=psp)
            if (max(xh) > 0):
                sh[xh > 0] = mpobj.s(T=Th[xh > 0], x=xh[xh > 0])
            ax.plot(sh, Th,
                    config['h_style'],
                    color=config['h_color'],
                    lw=config['h_width'])
        except pm.utility.PMAnalysisError:
            HLINES.remove(h)
            print('h=',h,' failed due to iter1_() guess error')

    # Generate the dome
    T = np.linspace(Tt+Tn,Tc-Tn,101)
    ssL,ssV = mpobj.ss(T)

    ax.plot(ssL,T,
            ls=config['sat_style'],
            color=config['sat_color'],
            lw=config['sat_width'])
    ax.plot(ssV,T,
            ls=config['sat_style'],
            color=config['sat_color'],
            lw=config['sat_width'])

    # Get the scaling ratio for slopes
    r = _slope_ratio(fig,ax)

    # LABELS of constant pressure
    for p in PLINES:
        if p==PLINES[0] or p==PLINES[-1]:
            unit = '%s' % (pm.config['unit_pressure'])
        else:
            unit = ''
        T = Tlim[1]
        s = mpobj.s(T=T,p=p)
        Tl = T - (Tlim[1] - Tlim[0]) /4
        sl = mpobj.s(T=Tl,p=p)
        dTds = (T-Tl)/(s-sl)
        ang = np.arctan(dTds*r)#*1/1.4*s/(Tlim[1]-Tlim[0]))
        slope = np.degrees(ang)
        label = '%s '%(str(p))+unit
        ax.text(s, T, label,
                color=config['p_color'],
                ha='right',
                va='top',
                #backgroundcolor='w',
                rotation=slope[0])
        
    # LABELS of constant volume
    T = Tlim[1] - .25*(Tlim[1] - Tlim[0]) #T position
    for d in DLINES:
        if d==DLINES[0] or d==DLINES[-1]:
            unit = '%s/%s' % (pm.config['unit_volume'], pm.config['unit_matter'])
        else:
            unit = ''
        s = mpobj.s(T, d=d)
        Tl = T - (Tlim[1] - Tlim[0]) /4
        sl = mpobj.s(T=Tl, d=d)
        dTds = (T - Tl) / (s - sl)
        ang = np.arctan(dTds * r)  # *1/1.4*s/(Tlim[1]-Tlim[0]))
        slope = np.degrees(ang)
        label = '%0.2g '%(1/d)+unit
        ax.text(s, T, label,
                color=config['d_color'],
                ha='right',
                va='top',
                rotation=slope[0])
        #T-=dT

    # LABELS of constant enthalpy
    dT = 0.8 * (Tc - Tt) / len(HLINES)
    for h in HLINES:
        if h==HLINES[0] or h==HLINES[-1]:
            unit = '%s/%s' % (pm.config['unit_energy'], pm.config['unit_matter'])
        else:
            unit = ''

        p = psp[0]
        pl = psp[2]
        try:
            T, x = mpobj.T_h(p=p, h=h, quality=True)
            s = mpobj.s(T=T, p=p)
            if x > 0:
                s = mpobj.s(T=T, x=x)
            Tl, xl = mpobj.T_h(p=pl, h=h, quality=True)
            sl = mpobj.s(T=Tl, p=pl)
            if xl > 0:
                sl = mpobj.s(T=Tl, x=xl)
            dTds = (T - Tl) / (s - sl)
            ang = np.arctan(dTds * r)  # *1/1.4*s/(Tlim[1]-Tlim[0]))
            slope = np.degrees(ang)
            label = '%d ' % (h) + unit
            ax.text(s, T, label,
                    color=config['h_color'],
                    ha='left',
                    va='top',
                    rotation=slope[0])
        except:
            print('h=',h,' failed')


    # Label the s-axis
    ax.set_xlabel('s [%s/(%s%s)]'%(
            pm.config['unit_energy'],
            pm.config['unit_matter'],
            pm.config['unit_temperature']))
            
    # Label the T-axis
    ax.set_ylabel('T [%s]'%(
            pm.config['unit_temperature']))
        
    # Label the figure
    ax.set_title('%s T-S Diagram'%(mpobj.data['id']))
        
    plt.show(block=False)
    return ax


def Tv(mpobj, fig=None, ax=None, satlines=True, Tlim=None, slines=None, plines=None, hlines=None):
    """Temperature-enthalpy diagram
    ax = TS(mpobj)

"""
    # Select a figure
    if fig is None:
        if ax is not None:
            fig = ax.get_figure()
        else:
            fig = plt.figure()
    elif isinstance(fig, matplotlib.figure.Figure):
        pass
    else:
        fig = plt.figure(fig)

    # Select an axes
    if ax is None:
        fig.clf()
        ax = fig.add_subplot(111)

    if Tlim is None:
        Tlim = mpobj.Tlim()

    plim = mpobj.plim()

    Tc, pc, dc = mpobj.critical(density=True)
    Tt, pt = mpobj.triple()

    if slines is None:
        SLINES = _slines(mpobj)
    else:
        SLINES = np.asarray(slines)

    if plines is None:
        PLINES = _plines(mpobj)
    else:
        PLINES = np.asarray(plines)

    if hlines is None:
        HLINES = _hlines(mpobj)
    else:
        HLINES = np.asarray(hlines)

    Tn = (Tc - Tt) / 1000.

    # Generate lines
    T = np.linspace(Tlim[0] + Tn, Tlim[1] - Tn, 151)

    # Lines of constant pressure
    for p in PLINES:
        d = mpobj.d(T=T, p=p)
        ax.semilogx(1/d, T,
                config['p_style'],
                color=config['p_color'],
                lw=config['p_width'])

    # Lines of constant entropy
    for s in SLINES[:]:
        try:
            psp = np.logspace(np.log10(1e-5 * plim[1]), np.log10(0.95 * plim[1]), 20)
            T, xh = mpobj.T_s(p=psp, s=s, quality=True)
            v = 1 / mpobj.d(T=T, p=psp)
            if (max(xh) > 0):
                v[xh > 0] = 1 / mpobj.d(T=T[xh > 0], x=xh[xh > 0])
            ax.plot(v, T,
                    config['d_style'],
                    color=config['d_color'],
                    lw=config['d_width'])
        except pm.utility.PMAnalysisError:
            #SLINES.remove(s)
            print('s=', s, ' failed due to iter1_() guess error')

    # Lines of constant enthalpy
    for h in HLINES[:]:  # Copy HLINES for the iteration, so that we can remove ones that fail
        try:
            psp = np.logspace(np.log10(1e-5*plim[1]),np.log10(0.95*plim[1]),20)
            Th, xh = mpobj.T_h(p=psp, h=h, quality=True)
            vh = 1/mpobj.d(T=Th, p=psp)
            if (max(xh) > 0):
                vh[xh > 0] = 1/mpobj.d(T=Th[xh > 0], x=xh[xh > 0])
            ax.plot(vh, Th,
                    config['h_style'],
                    color=config['h_color'],
                    lw=config['h_width'])
        except pm.utility.PMAnalysisError:
            HLINES.remove(h)
            print('h=',h,' failed due to iter1_() guess error')

    # Generate the dome
    T = np.linspace(Tt + Tn, Tc - Tn, 101)
    dsL, dsV = mpobj.ds(T)

    ax.semilogx(1/dsL, T,
            ls=config['sat_style'],
            color=config['sat_color'],
            lw=config['sat_width'])
    ax.semilogx(1/dsV, T,
            ls=config['sat_style'],
            color=config['sat_color'],
            lw=config['sat_width'])

    # Get the scaling ratio for slopes
    r = _slope_ratio_logx(fig, ax)

    # LABELS of constant pressure
    for p in PLINES:
        if p == PLINES[0] or p == PLINES[-1]:
            unit = '%s' % (pm.config['unit_pressure'])
        else:
            unit = ''
        T = Tlim[1]
        v = 1/mpobj.d(T=T, p=p)
        Tl = T - (Tlim[1] - Tlim[0]) / 4
        vl = 1/mpobj.d(T=Tl, p=p)
        dTdv = (T - Tl) / np.log10(v/vl)
        ang = np.arctan(dTdv * r)  # *1/1.4*s/(Tlim[1]-Tlim[0]))
        slope = np.degrees(ang)
        label = '%s ' % (str(p)) + unit
        ax.text(v, T, label,
                color=config['p_color'],
                ha='right',
                va='top',
                # backgroundcolor='w',
                rotation=slope[0])

        # LABELS of constant enthalpy
        dT = 0.8 * (Tc - Tt) / len(HLINES)
        for h in HLINES:
            if h == HLINES[0] or h == HLINES[-1]:
                unit = '%s/%s' % (pm.config['unit_energy'], pm.config['unit_matter'])
            else:
                unit = ''

            p = psp[0]
            pl = psp[2]
            try:
                T, x = mpobj.T_h(p=p, h=h, quality=True)
                v = 1/mpobj.d(T=T, p=p)
                if x > 0:
                    v = 1/mpobj.d(T=T, x=x)
                Tl, xl = mpobj.T_h(p=pl, h=h, quality=True)
                vl = 1/mpobj.d(T=Tl, p=pl)
                if xl > 0:
                    vl = 1/mpobj.d(T=Tl, x=xl)
                dTdv = (T - Tl) / np.log10(v/vl)
                ang = np.arctan(dTdv * r)  # *1/1.4*s/(Tlim[1]-Tlim[0]))
                slope = np.degrees(ang)
                label = '%d ' % (h) + unit
                ax.text(v, T, label,
                        color=config['h_color'],
                        ha='left',
                        va='top',
                        rotation=slope[0])
            except:
                print('h=', h, ' failed')

        # Label the v-axis
    ax.set_xlabel('v [%s/%s]' % (
        pm.config['unit_volume'],
        pm.config['unit_matter'],
        ))

    # Label the T-axis
    ax.set_ylabel('T [%s]' % (
        pm.config['unit_temperature']))

    # Label the figure
    ax.set_title('%s T-v Diagram' % (mpobj.data['id']))

    plt.show(block=False)
    return ax
