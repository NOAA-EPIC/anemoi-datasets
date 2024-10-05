# (C) Copyright 2024 European Centre for Medium-Range Weather Forecasts.
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import pytest
import requests
import xarray as xr

from anemoi.datasets.create.functions.sources.xarray import XarrayFieldList
from anemoi.datasets.testing import assert_field_list

URL = "https://object-store.os-api.cci1.ecmwf.int/ml-tests/test-data/samples/"

SAMPLES = list(range(19))
SKIP = [0, 1, 2, 3, 4]


def _test_samples(n):

    r = requests.get(f"{URL}sample-{n:04d}.json")
    if r.status_code not in [200, 404]:
        r.raise_for_status()

    if r.status_code == 404:
        kwargs = {}
    else:
        kwargs = r.json()

    ds = xr.open_zarr(f"{URL}sample-{n:04d}.zarr", consolidated=True)

    print(ds)

    fs = XarrayFieldList.from_xarray(ds)

    assert_field_list(fs, **kwargs)


@pytest.mark.parametrize("n", SAMPLES)
def test_samples(n):
    _test_samples(n)


if __name__ == "__main__":
    for s in SAMPLES:
        if s in SKIP:
            continue
        _test_samples(s)