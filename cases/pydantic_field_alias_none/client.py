"""Client for Pydantic Field.alias default drift."""
from __future__ import annotations

import json

import pydantic
from pydantic import BaseModel


class User(BaseModel):
    name: str


def main() -> None:
    fields = getattr(User, "model_fields", None) or getattr(User, "__fields__")
    field = fields["name"]
    print(
        json.dumps(
            {
                "alias": field.alias,
                "pydantic_version": pydantic.VERSION,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
