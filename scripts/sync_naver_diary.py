#!/usr/bin/env python3
"""네이버 블로그 RSS를 _data/naver_diary.json으로 동기화한다.

RSS에는 최근 글만 노출되므로 기존 데이터에 새 글을 병합(guid 기준 중복 제거)해
과거 글이 유실되지 않도록 누적 저장한다.
"""
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

RSS_URL = "https://rss.blog.naver.com/kimmusic_.xml"
DATA_FILE = Path(__file__).resolve().parent.parent / "_data" / "naver_diary.json"
EXCERPT_LENGTH = 200


def clean_link(link: str) -> str:
    return link.split("?")[0]


def clean_text(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    req = urllib.request.Request(RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        root = ET.fromstring(resp.read())

    entries = {}
    if DATA_FILE.exists():
        for e in json.loads(DATA_FILE.read_text(encoding="utf-8")):
            entries[e["guid"]] = e

    for item in root.iter("item"):
        text = lambda tag: (item.findtext(tag) or "").strip()
        guid = text("guid") or clean_link(text("link"))
        entries[guid] = {
            "guid": guid,
            "title": text("title"),
            "link": clean_link(text("link")),
            "category": text("category"),
            "date": parsedate_to_datetime(text("pubDate")).strftime("%Y-%m-%d"),
            "excerpt": clean_text(text("description"))[:EXCERPT_LENGTH],
        }

    merged = sorted(entries.values(), key=lambda e: e["date"], reverse=True)
    new_json = json.dumps(merged, ensure_ascii=False, indent=2) + "\n"
    old_json = DATA_FILE.read_text(encoding="utf-8") if DATA_FILE.exists() else ""
    if new_json != old_json:
        DATA_FILE.write_text(new_json, encoding="utf-8")
        print(f"updated: {len(merged)} entries")
    else:
        print("no changes")


if __name__ == "__main__":
    main()
