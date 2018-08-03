"""Climate Modelling Part 2 (Bremen, 2018): Diagnostic for exercise 3."""

import logging
import os

import iris

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from esmvaltool.diag_scripts.shared import (run_diagnostic, group_metadata,
                                            select_metadata)


logger = logging.getLogger(os.path.basename(__file__))


def main(cfg):
    """Execute the diagnostic."""
    plot_path = os.path.join(cfg['plot_dir'], 'exercise_3.png')

    # Group data
    input_data = cfg['input_data'].values()
    grouped_input_data = group_metadata(input_data, 'dataset')

    # Iterate over data and subtract historical data from rcp85
    for (dataset, data) in grouped_input_data.items():
        hist_data = select_metadata(data, exp='historical')[0]
        rcp26_data = select_metadata(data, exp='rcp26')[0]
        rcp85_data = select_metadata(data, exp='rcp85')[0]
        hist_file = hist_data['filename']
        rcp26_file = rcp26_data['filename']
        rcp85_file = rcp85_data['filename']

        # Load cubes
        hist_cube = iris.load_cube(hist_file)
        rcp26_cube = iris.load_cube(rcp26_file)
        rcp85_cube = iris.load_cube(rcp85_file)
        logger.info("Reading %s", hist_file)
        logger.info("Reading %s", rcp26_file)
        logger.info("Reading %s", rcp85_file)

        # Process data
        hist_cube = hist_cube.collapsed('time', iris.analysis.MEAN)
        rcp26_cube = rcp26_cube.aggregated_by('year', iris.analysis.MEAN)
        rcp85_cube = rcp85_cube.aggregated_by('year', iris.analysis.MEAN)
        rcp26_cube = rcp26_cube - hist_cube
        rcp85_cube = rcp85_cube - hist_cube
        rcp26_cube.rename('Anomalies in surface air temperature relative to '
                          '1961-1990')
        rcp85_cube.rename('Anomalies in surface air temperature relative to '
                          '1961-1990')

        # Plot
        iris.quickplot.plot(rcp26_cube.coord('year'), rcp26_cube,
                            label=dataset + ' (RCP 2.6)')
        iris.quickplot.plot(rcp85_cube.coord('year'), rcp85_cube,
                            label=dataset + ' (RCP 8.5)')

    # Add legend and save plot
    plt.ylabel('Anomaly in surface air temperature / K')
    plt.legend()
    plt.savefig(plot_path)
    logger.info("Writing %s", plot_path)
    plt.close()


# Call the main function when the script is called
if __name__ == '__main__':

    with run_diagnostic() as config:
        main(config)
