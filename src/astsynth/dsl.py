from pydantic import BaseModel, Field

from astsynth.blanks_and_content import Input, Operation, Constant


class DomainSpecificLanguage(BaseModel):
    inputs: list[Input] = Field(default_factory=list)
    constants: list[Constant] = Field(default_factory=list)
    operations: list[Operation] = Field(default_factory=list)
