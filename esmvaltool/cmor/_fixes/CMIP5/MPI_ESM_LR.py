# pylint: disable=invalid-name, no-self-use, too-few-public-methods
"""Fixes for MPI ESM LR model."""
from ..fix import Fix
import iris.cube


class pctisccp(Fix):
    """Fixes for pctisccp."""

    def fix_data(self, cube):
        """
        Fix data.

        Fixes discrepancy between declared units and real units

        Parameters
        ----------
        cube: iris.cube.Cube

        Returns
        -------
        iris.cube.Cube

        """
        metadata = cube.metadata
        cube *= 100
        cube.metadata = metadata
        return cube

class cl(Fix):
    """Fixes for cl."""

    def fix_metadata(self, cubes):
        cube = self.get_cube_from_list(cubes)
        cubes = iris.cube.CubeList()
        cubes.append(cube)
        return cubes 
        
