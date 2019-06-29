.. _recipes_flato13ipcc:

IPCC AR5 Chapter 9
==================

Overview
--------

The goal of this effort is to code up routines to reproduce Chapter 9 of AR5,
so that the plots can be readily reproduced and compared to previous CMIP
versions. In this way we can next time start with what was available in the
previous round and can focus on developing more innovative methods of analysis
rather than constantly having to "re-invent the wheel".

The plots will be done based on a collection of individual namelists. The
following figures from Flato et al. (2013) can currently be reproduced:

* Figure 9.14: Sea surface temperature plots for zonal mean error, equatorial
  (5 deg north to 5 deg south) mean error, and multi model mean for zonal error
  and equatorial mean.


Available recipes and diagnostics
-----------------------------------

Recipes are stored in recipes/

* namelist_flato13ipcc.yml

Diagnostics are stored in diag_scripts/ipcc_ar5

* ch09_fig09_14.py (fig. 9.14: Zonally averaged and equatorial SST)


Variables
---------

* tos (ocean, monthly mean, longitude, latitude, time)


Observations and reformat scripts
---------------------------------

.. note::
   * obs4mips data can be used directly without any preprocessing
   * see headers of cmorizers for non-obs4mips data for download instructions.

* HadISST (tos -- cmorizers/obs/cmorize_obs_hadisst.ncl)


References
----------

* Flato, G., J. Marotzke, B. Abiodun, P. Braconnot,
  S.C. Chou, W. Collins, P. Cox, F. Driouech, S. Emori, V. Eyring, C. Forest,
  P. Gleckler, E. Guilyardi, C. Jakob, V. Kattsov, C. Reason
  and M. Rummukainen, 2013: Evaluation of Climate Models. In: Climate Change
  2013: The Physical Science Basis. Contribution of Working Group I to the
  Fifth Assessment Report of the Intergovernmental Panel on Climate Change
  [Stocker, T.F., D. Qin, G.-K. Plattner, M. Tignor,
  S.K. Allen, J. Boschung, A. Nauels, Y. Xia, V. Bex and P.M. Midgley
  (eds.)]. Cambridge University Press, Cambridge, United Kingdom and New York,
  NY, USA.


Example plots
-------------

.. figure:: /recipes/figures/flato13ipcc/ch09_fig09_14.png
   :align: center
   :width: 80%

   Resembling Flato et al. (2013), Fig. 9.14.
