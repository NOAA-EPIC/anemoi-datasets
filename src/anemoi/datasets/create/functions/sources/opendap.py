# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from typing import Any
from typing import Union

from pydantic import BaseModel

from .xarray import load_many


class OpenDAP(BaseModel):
    class Config:
        extra = "forbid"

    url: Union[str, list[str]]
    param: Union[str, list[str]]
    level: Any = None


def execute(context, dates, url, *args, **kwargs):
    return load_many("🌐", context, dates, url, *args, **kwargs)


schema = OpenDAP
