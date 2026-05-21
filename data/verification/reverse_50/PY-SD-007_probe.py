import json
from pydantic import BaseModel
class Base(BaseModel):
    a: int
class Sub(Base):
    b: int
class Wrap(BaseModel):
    x: Base
w = Wrap(x=Sub(a=1, b=2))
out = w.model_dump() if hasattr(w, "model_dump") else w.dict()
print(json.dumps(out, sort_keys=True))
