Single Model Perfomance Index (SMPI)
====================================

Overview
--------

This diagnostic calculates the Single Model Performance Index (SMPI) following Reichler and Kim (2008). The SMPI (called "I\ :sup:`2`") is based on the comparison of several different climate variables (atmospheric, surface and oceanic) between climate model simulations and observations or reanalyses, and it focuses on the validation of the time-mean state of climate. For I\ :sup:`2` to be determined, the differences between the climatological mean of each model variable and observations at each of the available data grid points are calculated, and scaled to the interannual variance from the validating observations. This interannual variability is determined by performing a bootstrapping method (random selection with replacement) for the creation of a large synthetic ensemble of observational climatologies. The results are then scaled to the average error from a reference ensemble of models, and in a final step the mean over all climate variables and one model is calculated. The plot shows the I\ :sup:`2` values for each model (orange circles) and the multi-model mean (black circle), with the diameter of each circle representing the range of I\ :sup:`2` values encompassed by the 5th and 95th percentiles of the bootstrap ensemble. The I\ :sup:`2` values vary around one, with values greater than one for underperforming models, and values less than one for more accurate models. 

Available recipes and diagnostics
-----------------------------------

Recipes are stored in recipe/

* recipe_reichlerkim08bams.yml

Diagnostics are stored in diag_scripts/

* perfmetrics_grading.ncl: calculates single model perfomance index (Reichler and Kim, 2008). It requires fields precalculated by perfmetrics_main.ncl.
* perfmetrics_grading_collect.ncl: collects results from metrics previously calculated by perfmetrics_grading.ncl and passes them to the plotting functions.
* perfmetrics_main.ncl: calculates time-lat-lon and time-plev-lat fields from monthly 2-d or 3-d ("T2M", "T3Ms") input data. They are used as input to calculate grading metrics (see perfmetrics_grading.ncl).

User settings
-------------

User setting files (cfg files) are stored in nml/cfg_perfmetrics/CMIP5/

#. perfmetrics_grading.ncl

   *Optional diag_script_info attributes*

   * plot_single_mod_perf_index: Calculate and plot the Single Model Performance Index (SMPI)
     for the ensemble of given models
   * smpi_n_bootstrap: number of bootstrap samples for SMPI error estimate (default = 100)
   * smpi_ref_ensemble: model ensemble used for normalizing SMPI (default =  "CMIP5")

   For all other attributes, see :ref:`nml_perfmetrics`.

#. perfmetrics_grading_collect.ncl

   *Optional diag_script_info attributes*

   * plot_single_mod_perf_index: Calculate and plot the Single Model Performance Index (SMPI)
     for the ensemble of given models

   For all other attributes, see :ref:`nml_perfmetrics`.

#. perfmetrics_main.ncl

   *diag_script_info attributes*

   see :ref:`nml_perfmetrics`

Variables
---------

* hfds (ocean, monthly mean, longitude latitude time)
* hus (atmos, monthly mean, longitude latitude lev time)
* pr (atmos, monthly mean, longitude latitude time)
* psl (atmos, monthly mean, longitude latitude time)
* sic (ocean-ice, monthly mean, longitude latitude time)
* ta (atmos, monthly mean, longitude latitude lev time)
* tas (atmos, monthly mean, longitude latitude time)
* tauu (atmos, monthly mean, longitude latitude time)
* tauv (atmos, monthly mean, longitude latitude time)
* tos (ocean, monthly mean, longitude latitude time)
* ua (atmos, monthly mean, longitude latitude lev time)
* va (atmos, monthly mean, longitude latitude lev time)


Observations and reformat scripts
---------------------------------

*Note: (1) obs4mips data can be used directly without any preprocessing; (2) see headers of reformat scripts for non-obs4mips data for download instructions.*

* ERA-Interim (hfds, hus, psl, ta, tas, tauu, tauv, ua, va -- obs4mips)
* HadISST (sic, tos -- reformat_scripts/obs/reformat_obs_ERA-Interim.ncl)
* GPCP monthly (pr -- reformat_scripts/obs/reformat_obs_HadISST.ncl)

References
----------

* Reichler, T. and J. Kim, How well do coupled models simulate today's climate? Bull. Amer. Meteor. Soc., 89, 303-311, doi: 10.1175/BAMS-89-3-303, 2008.

Example plots
-------------

.. figure:: /namelists/figures/reichler_kim/ReichlerKim08bams_SMPI.png
   :width: 70 %
   
   Performance index I\ :sup:`2` for individual models (circles). Circle sizes indicate the length of the 95% confidence intervals. The black circle indicates the I\ :sup:`2` of the multi-model mean (similar to Reichler and Kim (2008), figure 1).
