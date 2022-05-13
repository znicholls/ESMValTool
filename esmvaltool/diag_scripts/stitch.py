# %load_ext nb_black

# +
"""Stitch experiments to ancestors and make illustrative plot"""
import logging

import cftime
import iris
import iris.util

import esmvalcore.esgf.facets
from esmvaltool.diag_scripts.shared import (
    #     group_metadata,
    run_diagnostic,
    #     save_data,
    #     save_figure,
    select_metadata,
    #     sorted_metadata,
)
# -

logger = logging.getLogger(__name__)


# +
class LocalDataset:
    _project = None
    _attrs_to_esmvaltool_map = {}

    def __init__(self, cube):
        self._cube = cube
        self._init_esmvaltool_to_attrs_map()

    def _data_attributes(self):
        return self._cube.attributes

    def _init_esmvaltool_to_attrs_map(self):
        self._esmvaltool_to_attrs_map = {
            v: k for k, v in self._attrs_to_esmvaltool_map.items()
        }

    def _get_parent_ids(self):
        parent_ids = {
            k: self._data_attributes()[
                f"{self._parent_prefix}{self._esmvaltool_to_attrs_map[k]}"
            ]
            for k in self._parent_id_keys
        }

        return parent_ids


class LocalDatasetCMIP6(LocalDataset):
    _project = "CMIP6"
    # TODO: decide whether facets needs updating
    _attrs_to_esmvaltool_map = {
        **{v: k for k, v in esmvalcore.esgf.facets.FACETS["CMIP6"].items()},
        **{
            "activity_id": "activity",
            "variant_label": "ensemble",
            "variable_id": "short_name",
        },
    }
    _parent_prefix = "parent_"
    _parent_id_keys = (
        "activity",
        "exp",
        "dataset",
        "ensemble",
    )
    _key_attributes_for_stitching = (
        "activity",
        "exp",
        "dataset",
        "ensemble",
        "mip",
        "short_name",
        "grid",
    )


def _get_local_dataset(project):
    if project == "CMIP6":
        return LocalDatasetCMIP6

    searcher = LocalDataset


def main(cfg):
    # not sure how to pass something like this from recipe...
    stop_criterion = lambda x: "piControl" in x

    input_data = cfg["input_data"].values()

    for ds_meta in input_data:
        exp = ds_meta["exp"]
        project = ds_meta["project"]
        if exp.endswith("piControl"):
            continue

        if exp == "historical":
            continue

        child_file = ds_meta["filename"]
        child_cube = iris.load_cube(child_file)
        child_ds = _get_local_dataset(project)(child_cube)

        to_concatenate = [child_cube]
        parent_ids = child_ds._get_parent_ids()
        i = 0
        while not stop_criterion(parent_ids["exp"]):
            parent = select_metadata(input_data, **parent_ids)
            assert len(parent) == 1, parent
            parent = parent[0]

            parent_file = parent["filename"]
            parent_cube = iris.load_cube(parent_file)
            parent_ds = _get_local_dataset(project)(parent_cube)

            if (
                child_ds._cube.coords("time")[0].units.calendar
                != parent_ds._cube.coords("time")[0].units.calendar
            ):
                raise NotImplementedError("Different calendars")
                child_ds._data_attributes()["branch_time_in_child"]

            branch_time_in_parent = cftime.num2date(
                child_ds._data_attributes()["branch_time_in_parent"],
                child_ds._data_attributes()["parent_time_units"],
                child_ds._cube.coords("time")[0].units.calendar,
                only_use_cftime_datetimes=True,
            )
            constraint = iris.Constraint(time=lambda t: t.point < branch_time_in_parent)
            parent_cut = parent_cube.extract(constraint)
            if parent_cut is None:
                logger.warning(
                    "Branch time in parent is before start of parent for child %s and parent %s",
                    child_file,
                    parent_file,
                )
            else:
                to_concatenate.append(parent_cut)

            child_file = parent_file
            child_cube = parent_cube
            child_ds = parent_ds

            parent_ids = child_ds._get_parent_ids()

            i += 1
            if i > 10:
                logger.error("Very deep recursion for %s", child_file)
                break

        to_concatenate_cubelist = iris.cube.CubeList(to_concatenate)
        dropped_attrs = iris.util.equalise_attributes(to_concatenate_cubelist)
        logger.debug("Dropping the following attributes in order to concatenate cubes, %s", dropped_attrs)
        
        joint = to_concatenate_cubelist.concatenate_cube()
        
#         assert False, "unit conversion"
#         assert False, "save (update metadata?)"
#         assert False, "plot"


# -

if __name__ == "__main__":
    with run_diagnostic() as config:
        main(config)
