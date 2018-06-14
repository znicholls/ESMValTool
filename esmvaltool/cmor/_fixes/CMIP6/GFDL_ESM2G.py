"""Fixes for CNRM-CM5 model"""
from ..fix import Fix
import cf_units

class ta(Fix):
    """Fixes for msftmyz"""

    def fix_metadata(self, cube):
        """
        Fix data

        Fixes:
            - reassigns time units from:
              cf_units.Unit('days since 0001-01-01 00:00:00',
                            calendar=cube.coord('time').units.calendar)
              to
              cf_units.Unit('days since 1850-01-01 00:00:00',
                            calendar=cube.coord('time').units.calendar)

        Parameters
        ----------
        cube: iris.cube.Cube

        Returns
        -------
        iris.cube.Cube

        """
        new_t_units = cf_units.Unit('days since 1850-01-01 00:00:00',
                                    calendar=cube.coord('time').units.calendar)
        cube.coord('time').units = new_t_units
        

        return cube
