"""
Forum utilities — load and save expert posts for a model.

Data is stored in `posts.json` inside the model's directory.

Schema:
[
  {
    "id": "<uuid4>",
    "username": "Alice",
    "timestamp": "2026-05-21T14:32:00",
    "title": "Post title",
    "text": "Post body text",
    "comments": [
      {
        "id": "<uuid4>",
        "username": "Bob",
        "timestamp": "2026-05-21T15:00:00",
        "text": "Comment text",
        "replies": [
          {
            "id": "<uuid4>",
            "username": "Charlie",
            "timestamp": "2026-05-21T15:10:00",
            "text": "Reply text"
          }
        ]
      }
    ]
  }
]
"""

from __future__ import annotations

import json
from pathlib import Path


def posts_path(model_filepath: str) -> Path:
    return Path(model_filepath).parent / "posts.json"


def load_posts(model_filepath: str) -> list[dict]:
    path = posts_path(model_filepath)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_posts(model_filepath: str, posts: list[dict]) -> None:
    path = posts_path(model_filepath)
    path.write_text(
        json.dumps(posts, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
