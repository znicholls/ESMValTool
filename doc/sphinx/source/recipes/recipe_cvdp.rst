CVDP Package
============

About
-----

The NCAR Climate Variability Package (CVDP) is a stand alone ncl based application for the analysis of climate variability in models and observations, see [1] and [2]. The CVDP package is also distributed with the ESMValTool.


Available recipes and diagnostics
---------------------------------

Recipes are stored in recipes/

    * recipe_cvdp.yml
 
Diagnostics are stored in diag_scripts/cvdp/

    * cvdp_wrapper.py   
    * cvdp - folder contains the CVDP package itself


User settings
-------------

 * Selection of models

Variables
---------

* Surface temperature (tas)
* Sea level pressure (psl)
* Precipitation (pr)

Indices
-------

* ENSO
* Pacific Decadal Oscillation
* Atlantic Multi-decadal Oscillation
* Northern and Southern Annular Modes
* North Atlantic Oscillation
* Pacific North and South American teleconnection patterns
* etc.

Requirements
------------
+ nco (optional for creating netcdf files)

References
----------

 [1] http://www.cesm.ucar.edu/working_groups/CVC/cvdp/
 [2] https://github.com/NCAR/CVDP-ncl

Example plots
-------------

