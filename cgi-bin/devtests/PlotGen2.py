import pyroplot_local as pyroplot
import pyromat as pm

water = pm.get('mp.H2O')
R134 = pm.get('mp.C2H2F4')

pm.config['unit_pressure'] = 'MPa'
sz = (11,8.25)
#pyroplot.Ts(water,plines = None,size=sz)
#pyroplot.Ts(R134,size=sz)
#pyroplot.Tv(water,size=sz)
#pyroplot.Tv(R134,size=sz)
#pyroplot.pv(water,size=sz)
#pyroplot.pv(R134,size=sz)

#import matplotlib.pyplot as plt
#ax = pyroplot.Ts(water,size=sz,display=False)
#f = ax.get_figure()
#f.show()

#generate PDF
from matplotlib.backends.backend_pdf import PdfPages
pp = PdfPages('test.pdf')
ax1=pyroplot.Ts(water,size=sz,display=False)
ax2=pyroplot.Tv(water,size=sz,display=False)
ax3=pyroplot.pv(water,size=sz,display=False)
pp.savefig(ax1.get_figure())
pp.savefig(ax2.get_figure())
pp.savefig(ax3.get_figure())
pp.close()
