from typing import Union

from pydantic import BaseModel


class Layer(BaseModel):
    name: str
    tileSource: str


class Project(BaseModel):
    filename: str
    layers: list[Layer] = []
    mpp: Union[float, None] = None
