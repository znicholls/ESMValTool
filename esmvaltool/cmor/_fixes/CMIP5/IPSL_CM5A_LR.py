# pylint: disable=invalid-name, no-self-use, too-few-public-methods
"""Fixes for IPSL CM5A LR model."""
from ..fix import Fix
import iris.cube


class cl(Fix):
    """Fixes for cl."""

    def fix_metadata(self, cubes):
        cube = self.get_cube_from_list(cubes)
        cubes = iris.cube.CubeList()
        cubes.append(cube)
        return cubes 
        
