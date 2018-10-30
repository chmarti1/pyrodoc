from django.http import HttpResponse
import pyromat as pm


def test(request, name=None):

    if name is None:
        name = 'mp.CO2'
    c = pm.get(name)
    Tc, pc, dc = c.critical(density=True)
    Tt, pt = c.triple()

    u_temperature = pm.config['unit_temperature']
    u_pressure = pm.config['unit_pressure']
    u_matter = pm.config['unit_matter']
    u_volume = pm.config['unit_volume']
    u_density = u_matter + '/' + u_volume

    return HttpResponse(\
"""<http>
<head>
<title>{0:}</title>
</head>
<body>
<h1>{0:}</h1>

<h2>Critical Point</h2>

T = {4:.2f}{1:}<br>
p = {5:.3f}{2:}<br>
d = {6:.1f}{3:}<br>

<h2>Triple Point</h2>

T = {7:.2f}{0:}<br>
p = {8:.3f}{1:}<br>

</body>
</http>""".format(\
        name,\
        u_temperature, u_pressure, u_density,\
        Tc, pc, dc,\
        Tt, pt))
