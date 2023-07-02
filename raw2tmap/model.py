from pydantic import BaseModel


class Layer(BaseModel):
    name: str
    tile_source: str


class Project(BaseModel):
    filename: str
    layers: list[Layer] = []
