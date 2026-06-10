from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from litestar.response import Redirect


class FixedLink(BaseModel):
    url: Optional[str] = Field(None)
    redirect: Optional[Redirect] = Field(None)
    is_error: bool = Field(False)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class CachedResult(BaseModel):
    is_result: bool = Field(False)
    is_error: bool = Field(False)
    content: str
    fixed_link: Optional[FixedLink] = Field(None)
