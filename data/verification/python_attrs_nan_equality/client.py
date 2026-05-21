import json
import math

import attrs


@attrs.define
class Box:
    value: float


shared_nan = math.nan
left = Box(shared_nan)
right = Box(shared_nan)

print(json.dumps({
    "attrs_version": attrs.__version__,
    "same_nan_object": left.value is right.value,
    "equal": left == right,
}))
