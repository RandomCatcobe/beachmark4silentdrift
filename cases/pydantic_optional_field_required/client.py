"""Client for Pydantic Optional field required drift."""
from __future__ import annotations

import json
from typing import Optional

import pydantic
from pydantic import BaseModel, ValidationError


class Profile(BaseModel):
    nickname: Optional[str]


def main() -> None:
    try:
        profile = Profile()
    except ValidationError as exc:
        result = {
            "created": False,
            "errors": [
                {
                    "loc": list(error.get("loc", ())),
                    "type": error.get("type"),
                }
                for error in exc.errors()
            ],
            "pydantic_version": pydantic.VERSION,
        }
    else:
        dump = profile.model_dump() if hasattr(profile, "model_dump") else profile.dict()
        result = {
            "created": True,
            "payload": dump,
            "pydantic_version": pydantic.VERSION,
        }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
