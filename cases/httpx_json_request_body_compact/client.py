from __future__ import annotations

import json
import httpx


def main() -> None:
    request = httpx.Request(
        "POST",
        "https://example.test/submit",
        json={"a": 1, "b": 2},
    )
    print(
        json.dumps(
            {
                "httpx_version": httpx.__version__,
                "content": request.content.decode("utf-8"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
