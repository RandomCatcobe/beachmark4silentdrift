import json, numpy as np
a = np.float32(3) + 3.
b = np.array([3], dtype=np.float32) + np.float64(3)
print(json.dumps({
    "scalar_dtype": str(np.asarray(a).dtype),
    "scalar_value": repr(a),
    "array_dtype": str(b.dtype),
    "array_value": b.tolist(),
}, sort_keys=True))
