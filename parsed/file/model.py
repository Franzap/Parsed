import os
from abc import ABC
from typing import Optional, Union, Any

from pydantic import BaseModel, computed_field


class File(BaseModel):
    filename: str
    content: Optional[Union[str, bytes]] = None
    encoding: Optional[str] = None

    @computed_field
    @property
    def extension(self) -> str:
        return os.path.splitext(self.filename)[-1].lower()


class ParsableFile(File, ABC):
    parsed_obj: Any


