from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from urllib.parse import urljoin
from html import unescape
import json
import os
import re
import time


BASE = "https://www.civilopedia.net"
SEED = "/zh-CN/gathering-storm/districts/district_harbor/"


def fetch(path, timeout=12):
    request = Request(urljoin(BASE, path), headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


def clean_text(fragment):
    fragment = re.sub(r"<img\b[^>]*>", " ", fragment)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    fragment = unescape(fragment)
    return re.sub(r"\s+", " ", fragment).strip()


def title(html):
    match = re.search(r"<title>(.*?)</title>", html, re.S)
    return clean_text(match.group(1)).split(" - ")[0] if match else "未知"


def description(html):
    match = re.search(r'<meta name="description" content="([^"]*)"', html)
    return clean_text(match.group(1)) if match else ""


def parse_panels(html):
    token_re = re.compile(
        r'<(?P<tag>p|div)\b[^>]*class="(?P<class>[^"]*(?:_8lp4s91|_8lp4s94|_8lp4s95|_8lp4s98)[^"]*)"[^>]*>(?P<body>.*?)</(?P=tag)>',
        re.S,
    )
    sections = []
    current = None
    group = None

    for match in token_re.finditer(html):
        classes = match.group("class")
        text = clean_text(match.group("body"))
        if not text:
            continue
        if "_8lp4s91" in classes:
            if text in {"特点", "要求", "成本", "维护"} or "收益" in text or "加成" in text:
                current = {"title": text, "groups": []}
                sections.append(current)
                group = None
            else:
                current = None
                group = None
            continue
        if current is None:
            continue
        if "_8lp4s94" in classes:
            group = {"label": text, "values": []}
            current["groups"].append(group)
            continue
        if "_8lp4s95" in classes or "_8lp4s98" in classes:
            if group is None:
                group = {"label": "", "values": []}
                current["groups"].append(group)
            if text not in group["values"]:
                group["values"].append(text)

    return [s for s in sections if any(g["label"] or g["values"] for g in s["groups"])]


def parse_item(path):
    html = fetch(path)
    return {
        "id": path.strip("/").split("/")[-1],
        "name": title(html),
        "category": "区域",
        "summary": description(html),
        "source": urljoin(BASE, path),
        "sections": parse_panels(html),
    }


def main():
    seed_html = fetch(SEED)
    links = sorted(set(re.findall(r'href="(/zh-CN/gathering-storm/districts/[^"#]+/)"', seed_html)))
    links = [link for link in links if "/intro/" not in link]
    items = []
    failures = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_map = {executor.submit(parse_item, link): link for link in links}
        for future in as_completed(future_map):
            link = future_map[future]
            try:
                item = future.result()
                if item["sections"]:
                    items.append(item)
                    print(f"{len(items):02d} {item['name']}", flush=True)
            except Exception as exc:
                failures.append({"path": link, "error": str(exc)})
                print(f"skip {link}: {exc}", flush=True)

    items.sort(key=lambda item: item["name"])
    payload = {
        "generatedAt": time.strftime("%Y-%m-%d"),
        "ruleset": "Gathering Storm",
        "sourceName": "civilopedia.net zh-CN",
        "sourceHome": "https://www.civilopedia.net/zh-CN/gathering-storm/",
        "notes": "首版重点抓取文明百科右侧数值面板中的区域数据：特点、要求、相邻加成、公民收益、贸易收益等；不抓取中间背景介绍。",
        "failures": failures,
        "items": items,
    }

    out_path = os.path.join(os.path.dirname(__file__), "..", "assets", "civ6-data.js")
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("window.CIV6_DATA = ")
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write(";\n")
    print(f"wrote {len(items)} items, failures {len(failures)}", flush=True)


if __name__ == "__main__":
    main()
