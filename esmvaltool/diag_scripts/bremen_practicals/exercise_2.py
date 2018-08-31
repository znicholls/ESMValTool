"""Climate Modelling Part 2 (Bremen, 2018): Diagnostic for exercise 2."""

import logging
import os

import iris

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from esmvaltool.diag_scripts.shared import run_diagnostic


logger = logging.getLogger(os.path.basename(__file__))


def main(cfg):
    """Execute the diagnostic."""
    plot_type = cfg['output_file_type']
    plot_path = os.path.join(cfg['plot_dir'], 'exercise_2.' + plot_type)

    # Read datasets and plot them
    for (path, attr) in cfg['input_data'].items():
        logger.info("Reading %s", path)
        cube = iris.load_cube(path)
        cube = cube.aggregated_by('year', iris.analysis.MEAN)
        cube.convert_units('celsius')
        iris.quickplot.plot(cube.coord('year'), cube, label=attr['dataset'])

    # Add legend and save plot
    plt.legend()
    plt.savefig(plot_path)
    logger.info("Writing %s", plot_path)
    plt.close()


# Call the main function when the script is called
if __name__ == '__main__':

    with run_diagnostic() as config:
        main(config)
