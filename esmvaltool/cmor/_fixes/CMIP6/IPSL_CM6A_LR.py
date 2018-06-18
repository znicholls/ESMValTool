"""Fixes for CNRM-CM5 model"""
from ..fix import Fix
import numpy as np

class ta(Fix):
    """Fixes for msftmyz"""

    def fix_metadata(self, cube):
        """
        Fix data

        Fixes:
            - adds 180 deg to longitude points
            - order latitude points
            - set air_pressure coord name to plev
            - set air_pressure variable name to plev

        Parameters
        ----------
        cube: iris.cube.Cube

        Returns
        -------
        iris.cube.Cube

        """
        # check for CMOR consistency
        if np.min(cube.coord('longitude').points) < 0:
            cube.coord('longitude').points = cube.coord('longitude').points + 180.
        if cube.coord('latitude').points[0] > cube.coord('latitude').points[-1]:
            cube.coord('latitude').points = np.sort(cube.coord('latitude').points)

        # this should work whatever the original names
        cube.coord('air_pressure').attributes['name'] = 'plev'
        cube.coord('air_pressure').var_name = 'plev'

        return cube

class pr(Fix):
    """Fixes for msftmyz"""

    def fix_metadata(self, cube):
        """
        Fix data

        Fixes:
            - adds 180 deg to longitude points
            - order latitude points
            - set air_pressure coord name to plev
            - set air_pressure variable name to plev

        Parameters
        ----------
        cube: iris.cube.Cube

        Returns
        -------
        iris.cube.Cube

        """
        # check for CMOR consistency
        if np.min(cube.coord('longitude').points) < 0:
            cube.coord('longitude').points = cube.coord('longitude').points + 180.
        if cube.coord('latitude').points[0] > cube.coord('latitude').points[-1]:
            cube.coord('latitude').points = np.sort(cube.coord('latitude').points)

        return cube
