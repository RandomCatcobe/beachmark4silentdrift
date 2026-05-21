import json, polars as pl
left = pl.DataFrame({"k": [None, 1], "lv": ["left_null", "left_one"]})
right = pl.DataFrame({"k": [None, 1], "rv": ["right_null", "right_one"]})
out = left.join(right, on="k", how="inner")
print(json.dumps({"shape": out.shape, "rows": out.to_dicts()}, sort_keys=True, default=str))
