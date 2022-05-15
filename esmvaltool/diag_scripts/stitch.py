# %load_ext nb_black

# +
"""Stitch experiments to ancestors and make illustrative plot"""
import logging
import os
from pathlib import Path

import cftime
import iris
import iris.plot
import iris.util
import matplotlib.pyplot as plt

import esmvalcore.esgf.facets
from esmvalcore._data_finder import _select_drs
from esmvaltool.diag_scripts.shared import (
    #     group_metadata,
    run_diagnostic,
    save_data,
    save_figure,
    select_metadata,
    #     sorted_metadata,
)
# -

# unclear why this has to be called but ok
esmvalcore._config.load_config_developer()

# unclear why my log messages won't come through...
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

    def _get_path_template(self):
        return _select_drs("input_dir", {self._project: "ESGF"}, self._project)

    def get_ids_from_path(self, path, root_dir):
        path_template = self._get_path_template()
        ids = {
            k.strip("{}"): v
            for k, v in zip(
                path_template.split(os.sep), path.relative_to(root_dir).parts
            )
        }

        return ids


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
    key_stop_string = cfg.get("stitch_stop_string", "piControl")
    logger.debug("key_stop_string: %s", key_stop_string)
    stop_criterion = lambda x: key_stop_string in x

    out_units = cfg["units"]["target_unit"]
    logger.debug("out_units: %s", out_units)
    area_multiplied_preprocessor = cfg["units"].get("area_multiplied_preprocessor", False)
    logger.debug("area_multiplied_preprocessor: %s", area_multiplied_preprocessor)
    mass_kind = cfg["units"].get("mass_kind", None)
    logger.debug("mass_kind: %s", mass_kind)

    input_data = cfg["input_data"].values()

    for ds_meta in input_data:
        exp = ds_meta["exp"]
        project = ds_meta["project"]
#         if exp.endswith("piControl"):
#             continue

#         if exp == "historical":
#             continue

#         if "esm-1pct-brch" not in exp:
#             continue

        child_file = ds_meta["filename"]
        child_cube = iris.load_cube(child_file)
        child_cube.attributes["exp"] = exp
        child_ds = _get_local_dataset(project)(child_cube)

        ids = [ds_meta[k] for k in child_ds._key_attributes_for_stitching]
        out_file_base = f"stitched_{'_'.join(ids)}"

        to_concatenate = [child_cube]
        to_concatenate_full = [child_cube]
        tree = [child_file]
        tree_exp = [ds_meta["exp"]]
        parent_ids = child_ds._get_parent_ids()
        i = 0
        while not stop_criterion(parent_ids["exp"]):
            parent = select_metadata(input_data, **parent_ids)
            
            if parent:
                assert len(parent) == 1, parent
                parent = parent[0]
                
            else:
                check_key = "activity"
                attribute_val = parent_ids[check_key]
                parent_ids_no_activity = {k: v for k, v in parent_ids.items() if k not in [check_key]}
                parent = select_metadata(input_data, **parent_ids_no_activity)
                
                if not parent:
                    logger.error(
                        "For %s, could not find parent, %s",
                        child_file,
                        parent_ids,
                    )
                    raise ValueError("Could not find parent")
                else:
                    assert len(parent) == 1, parent
                    parent = parent[0]
                    logger.warning(
                        "Incorrect parent %s metadata for %s. "
                        "Value in attributes: %s; "
                        "Correct value: %s; ",
                        check_key,
                        child_file,
                        attribute_val,
                        parent["activity"],
                    )

            parent_file = parent["filename"]
            parent_cube = iris.load_cube(parent_file)
            # consistent metadata name for use later
            parent_cube.attributes["exp"] = parent["exp"]
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
                tree.append(parent_file)
                tree_exp.append(parent["exp"])

            to_concatenate_full.append(parent_cube)

            child_file = parent_file
            child_cube = parent_cube
            child_ds = parent_ds

            parent_ids = child_ds._get_parent_ids()

            i += 1
            if i > 10:
                logger.error("Very deep recursion for %s", child_file)
                break

        to_concatenate_cubelist = iris.cube.CubeList([c.copy() for c in to_concatenate])
        dropped_attrs = iris.util.equalise_attributes(to_concatenate_cubelist)
        logger.debug(
            "Dropping the following attributes in order to concatenate cubes, %s",
            dropped_attrs,
        )

        joint = iris.util.squeeze(to_concatenate_cubelist.concatenate_cube())
        joint.attributes["exp-stitched"] = exp
        joint_target_unit = convert_cube_units(
            joint, out_units, mass_kind, area_multiplied_preprocessor
        )

        provenance = get_provenance_record(joint_target_unit.attributes, tree, tree_exp)
        save_data(
            out_file_base,
            provenance,
            cfg,
            joint_target_unit,
        )

        fig = create_stitching_figure(
            joint_target_unit,
            joint,
            to_concatenate,
            to_concatenate_full,
        )
        save_figure(
            out_file_base,
            provenance,
            cfg,
            figure=None,
            close=True,
            #             # TODO: pass through other arguments e.g. transparent
            #             **kwargs,
        )


#         assert False, "plot"


def _plot_set(set_cubes, ax):
    units = []
    var_names = []
    for cube in set_cubes:
        iris.plot.plot(cube, label=f"{cube.attributes['exp']}", axes=ax)
        units.append(str(cube.units))
        var_names.append(cube.var_name)

    units = set(units)
    assert len(units) == 1, units
    unit = list(units)[0]

    var_names = set(var_names)
    assert len(var_names) == 1, var_names
    var_name = list(var_names)[0]

    ax.set_ylabel(f"{var_name} [{unit}]")

    return ax


def create_stitching_figure(out_target_unit, out, to_concatenate, to_concatenate_full):
    fig, axes = plt.subplots(nrows=4, figsize=(9, 9), sharex=True)

    _plot_set(to_concatenate_full, axes[0])
    _plot_set(to_concatenate, axes[1])

    iris.plot.plot(
        out, label=f"Stitched {out.attributes['exp-stitched']}", axes=axes[2]
    )
    axes[2].set_ylabel(f"{out.var_name} [{str(out.units)}]")

    iris.plot.plot(
        out_target_unit,
        label=f"Stitched {out_target_unit.attributes['exp-stitched']}",
        axes=axes[3],
    )
    axes[3].set_ylabel(
        f"{out_target_unit.var_name} [{out_target_unit.attributes['units_full']}]"
    )

    for ax in axes:
        ax.legend(loc="best")

    return fig


def _log_unit_conversion(
    in_units_str, target_unit, conv_factor, mass_kind, area_multiplied_preprocessor
):
    msg = "Converting from %s to %s using conversion factor %f."
    call_args = [in_units_str, target_unit, conv_factor]

    if mass_kind:
        msg = f"{msg} Assuming that inputs units are mass of %s."
        call_args.append(mass_kind)

    if area_multiplied_preprocessor:
        msg = f"{msg} Assuming that we have already multiplied with areas of units m^2."

    logger.debug(msg, *call_args)


def convert_cube_units(
    inp, target_unit, mass_kind=None, area_multiplied_preprocessor=False
):
    # does iris have unit aware operations?
    # TODO: get per m2 dealth with upstream
    import openscm_units

    ur = openscm_units.unit_registry

    # TODO: remove this hard-coding
    in_units_str = str(inp.units).replace("-", "^-")
    in_units = ur(in_units_str)

    if mass_kind:
        in_units = in_units * (1 * ur(mass_kind))

    if area_multiplied_preprocessor:
        in_units = in_units * (1 * ur("m^2"))

    conv_factor = in_units.to(target_unit).magnitude
    _log_unit_conversion(
        in_units_str, target_unit, conv_factor, mass_kind, area_multiplied_preprocessor
    )

    out = inp * conv_factor
    out.rename(inp.name())
    out.var_name = inp.var_name
    out.attributes["units_full"] = target_unit

    if mass_kind:
        units_iris = target_unit.replace(mass_kind, "")
    else:
        units_iris = target_unit

    out.units = units_iris

    return out


def get_provenance_record(attributes, ancestor_files, tree_exp):
    """Create a provenance record describing the diagnostic data and plot."""
    caption = (
        f"{tree_exp[0]} output, stitched using the following family tree: "
        f"{tree_exp}"
    )
    record = {
        "caption": caption,
        #         "statistics": ["mean"],
        #         "domains": ["global"],
        "authors": [
            "nicholls_zebedee",
        ],
        "references": [
            "esm2025",
        ],
        "ancestors": ancestor_files,
    }
    return record


# -

if __name__ == "__main__":
    with run_diagnostic() as config:
        main(config)
