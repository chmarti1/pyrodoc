# Thermodynamic Properties in Python

### Synopsis
There is a _massive_ body of high quality models for the thermodynamic properties of substances, and their implementations are mostly in proprietary codes. What projects are available in the open-source domain?

**Audience**: Intermediate to advanced users.  This talk is for people with at least some familiarity with the Python language with an interest in the dark arts of thermodynamics.

**Speaker**: Chris Martin PhD  
Associate Professor of Mechanical Engineering
Penn State University, Altoona College  
[crm28@psu.edu](mailto:crm28@psu.edu)

**Co-Authors** (Partners in OSS and teaching):
Joe Ranalli PhD (PSU Hazelton)  
Jacob Moore PhD (PSU Mont Alto)

**Our Project**: PYroMat :: [pyromat.org](http://pyromat.org) :: [PYroMat Git](https://github.com/chmarti1/pyromat)

### What are we talking about?
- **The problem**: how do substances heat up, expand, contract, boil, condense, etc.? (5 min)
    - Basic Properties are pressure, temperature, density, volume
    - Less intuitive properties are internal energy, enthalpy, entropy, specific heat, and many more...
- Geek out about the **history of codes** (5min)
    - Stanjan (Fortran)
    - GRI Mech (Data Set)
    - Chemkin (Proprietary)
    - Cantera (Open Source)
    - NIST Webbook (web)
    - REFPROP (semi-proprietary)
    - CoolProp (semi-proprietary)
    - PYroMat (Open Source)
    - MANY proprietary codes
- **What do these code do?** (5 min)
    - Where do their data come from? JANAF, NIST, Journals
    - What do the models look like?
- **Ten Minutes with PYroMat** (10min)
    - Import: `import pyromat as pm`
    - Search: `pm.search(name='carbonyl sulfide')`
    - Info: `pm.info('mp.H2O')`
    - Get: `h2o = pm.get('mp.H2O')`
    - Have some fun ... `h2o.h(T=400, s=3.4)`
    - Change our units: `pm.config['unit_temperature'] = 'F'`
    - Find the docs!  [PYroMat Docs](http://pyromat.org/documentation.html)
- **Let the audience lead**: Time for questions, answers, and discussion (5min)
