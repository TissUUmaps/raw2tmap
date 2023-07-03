from pydantic import BaseModel


class Layer(BaseModel):
    name: str
    tileSource: str


class Project(BaseModel):
    filename: str
    layers: list[Layer] = []
