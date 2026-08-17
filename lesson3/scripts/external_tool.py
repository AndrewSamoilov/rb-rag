from __future__ import annotations

import json
from urllib.parse import quote
from urllib.request import urlopen


GIN_REPO_API_URL = "https://api.github.com/repos/gin-gonic/gin"


def get_gin_release_info() -> dict:
    url = f"{GIN_REPO_API_URL}/releases"

    with urlopen(url) as response:
        releases = json.load(response)

    if not releases:
        raise ValueError("GitHub returned no Gin releases")

    latest_release = releases[0]
    required_fields = ["tag_name", "published_at", "html_url", "body"]
    for field in required_fields:
        if field not in latest_release:
            raise ValueError(f"GitHub release is missing required field: {field}")

    return {
        "tag_name": latest_release["tag_name"],
        "published_at": latest_release["published_at"],
        "html_url": latest_release["html_url"],
        "body": latest_release["body"],
    }


def get_gin_open_issues_count() -> dict:
    query = "repo:gin-gonic/gin is:issue is:open"
    url = "https://api.github.com/search/issues?q=" + quote(query)

    with urlopen(url) as response:
        search_result = json.load(response)

    if "total_count" not in search_result:
        raise ValueError("GitHub search response is missing total_count")

    return {
        "repository": "gin-gonic/gin",
        "open_issues_count": search_result["total_count"],
        "html_url": "https://github.com/gin-gonic/gin/issues",
    }


def call_release_tool() -> dict:
    try:
        return get_gin_release_info()
    except Exception as error:
        return {"error": str(error)}


def call_issues_tool() -> dict:
    try:
        return get_gin_open_issues_count()
    except Exception as error:
        return {"error": str(error)}


if __name__ == "__main__":
    release = call_release_tool()
    print(json.dumps(release, indent=2))
