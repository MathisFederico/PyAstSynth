from pydantic import BaseModel


class GeneratedProgram(BaseModel):
    name: str
    source: str

    def __len__(self):
        return len(self.source)
