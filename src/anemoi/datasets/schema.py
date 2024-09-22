# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import json
from enum import Enum
from typing import Annotated
from typing import Union

from anemoi.utils.dates import frequency_to_timedelta
from pydantic import BaseModel
from pydantic import Discriminator
from pydantic import Field
from pydantic import Tag
from pydantic import ValidationError
from pydantic import create_model
from pydantic import field_validator

from anemoi.datasets.create.functions import function_schemas


class GroupByEnum(str, Enum):
    monthly = "monthly"
    daily = "daily"
    weekly = "weekly"
    MMDD = "MMDD"


class Dates(BaseModel):
    class Config:
        extra = "forbid"

    missing: list[datetime.datetime] = None

    # Deprecated fields
    group_by: Union[int, GroupByEnum] = "monthly"


class Interval(Dates):
    start: datetime.datetime = None
    end: datetime.datetime = None
    frequency: datetime.timedelta = None

    @field_validator("frequency", mode="before")
    def parse_frequency(cls, value):
        return frequency_to_timedelta(value)


class DateList(Dates):
    values: list[datetime.datetime] = None


def _dates_discriminator(input):
    if "values" in input:
        return "values"
    return "interval"


class Step(BaseModel):
    pass


class Output(BaseModel):
    class Config:
        extra = "forbid"

    statistics_end: Union[datetime.datetime, int] = None

    chunking: dict = None
    dtype: str = "float32"
    flatten_grid: bool = True
    order_by: list[str] = None
    remapping: dict = None
    statistics: Union[dict, str] = None


class Build(BaseModel):
    class Config:
        extra = "forbid"

    group_by: Union[int, GroupByEnum] = "monthly"
    use_grib_paramid: bool = False
    variable_naming: str = None


class Common(BaseModel):
    pass


class Statistics(BaseModel):
    class Config:
        extra = "forbid"

    end: Union[datetime.datetime, int] = None
    allow_nans: list[str] = []


def init():

    def _input_discriminator(input):
        return list(input.keys())[0]

    union = []

    for name, schema in function_schemas("sources"):
        if schema is None:
            schema = dict
        model = create_model(name, **{name: (schema, ...)}, __base__=Step)
        a = Annotated[model, Tag(name)]
        union.append(a)

    for name, schema in function_schemas("filters"):
        if schema is None:
            schema = dict
        model = create_model(name, **{name: (schema, ...)}, __base__=Step)
        a = Annotated[model, Tag(name)]
        union.append(a)

    simple_steps = Annotated[Union[tuple(union)], Discriminator(_input_discriminator)]

    Pipe = create_model("Pipe", pipe=(list[simple_steps], ...))

    simple_steps_and_pipe = Annotated[
        Union[tuple(union + [Annotated[Pipe, Tag("pipe")]])],
        Discriminator(_input_discriminator),
    ]

    Dates = create_model("Dates", dates=(Interval, ...), join=(list[simple_steps_and_pipe], ...))

    union.append(Annotated[Pipe, Tag("pipe")])
    union.append(Annotated[Dates, Tag("dates")])

    simple_steps_and_dates = Annotated[
        Union[tuple(union + [Annotated[Dates, Tag("dates")]])], Discriminator(_input_discriminator)
    ]

    Concat = create_model("Concat", concat=(list[simple_steps_and_dates], ...))
    Join = create_model("Join", join=(list[simple_steps_and_pipe], ...))

    union.extend(
        [
            Annotated[Concat, Tag("concat")],
            Annotated[Join, Tag("join")],
        ]
    )

    Input = create_model(
        "Input",
        input=(Annotated[Union[tuple(union)], Discriminator(_input_discriminator)], ...),
        __base__=Recipe,
    )

    return Input


class Recipe(BaseModel):
    class Config:
        extra = "forbid"

    description: str = None
    name: str = None

    copyright: str = Annotated[int, Field(deprecated="This is deprecated. Set `attribution` instead")]
    licence: str = "unknown"
    attribution: str = "unknown"

    dates: Annotated[
        Union[
            Annotated[Interval, Tag("interval")],
            Annotated[DateList, Tag("values")],
        ],
        Discriminator(_dates_discriminator),
    ]

    # https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions-with-callable-discriminator
    # input: Annotated[actions, Discriminator(_input_discriminator)]

    output: Output = Output()
    build: Build = Build()
    statistics: Statistics = Statistics()
    common: Common = None
    sources: Common = None

    # Legacy fields

    purpose: str = Annotated[int, Field(deprecated="This is deprecated")]

    aliases: Union[Common, list] = None

    flatten_grid: bool = True
    ensemble_dimension: int = 2

    config_format_version: int = Annotated[int, Field(deprecated="This is deprecated")]
    status: str = Annotated[int, Field(deprecated="This is deprecated")]
    dataset_status: str = Annotated[int, Field(deprecated="This is deprecated")]

def expand(config):
    return config
    model = init()
    recipe = model(**config)
    return recipe.model_dump()

def validate(config, schema=False):

    model = init()

    try:
        recipe = model(**config)
        print("Validation successful!")
        if schema:
            print(json.dumps(recipe.model_json_schema(), default=str, indent=4))
        else:
            print(json.dumps(recipe.model_dump(), default=str, indent=4))
        return True
    except ValidationError as e:
        print("Validation failed:")
        print(e)
        return False