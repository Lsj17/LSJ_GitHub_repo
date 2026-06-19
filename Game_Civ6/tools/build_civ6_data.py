from urllib.request import Request, urlopen
from urllib.parse import urljoin
from html import unescape
import json
import re
import time


BASE = "https://www.civilopedia.net"
LANG = "/zh-CN/gathering-storm/"

CATEGORIES = {
    "districts": "区域",
    "buildings": "建筑",
    "wonders": "奇观",
    "units": "单位",
    "improvements": "改良设施",
    "resources": "资源",
    "governments": "政体",
    "technologies": "科技",
    "civics": "市政",
    "features": "地貌",
}

SEEDS = [
    "/zh-CN/gathering-storm/districts/district_harbor/",
    "/zh-CN/gathering-storm/buildings/building_lighthouse/",
    "/zh-CN/gathering-storm/wonders/building_great_lighthouse/",
    "/zh-CN/gathering-storm/units/unit_warrior/",
    "/zh-CN/gathering-storm/improvements/improvement_farm/",
    "/zh-CN/gathering-storm/resources/resource_horses/",
    "/zh-CN/gathering-storm/governments/government_chiefdom/",
    "/zh-CN/gathering-storm/technologies/tech_celestial_navigation/",
    "/zh-CN/gathering-storm/civics/civic_code_of_laws/",
    "/zh-CN/gathering-storm/features/feature_floodplains/",
]

MAX_PAGES = 360

KEEP_SECTION_HINTS = (
    "特点",
    "要求",
    "成本",
    "维护",
    "用法",
    "移动力",
    "战斗",
    "远程",
    "射程",
    "轰炸",
    "防空",
    "产出",
    "相邻",
    "公民",
    "贸易",
    "槽位",
    "效果",
    "加成",
    "资源",
    "地形",
    "科技",
    "市政",
    "政体",
    "可建造",
    "取代者",
    "取代",
)

SKIP_VALUE_PREFIXES = (
    "简介",
    "历史",
    "背景",
)


def fetch(path):
    url = urljoin(BASE, path)
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=25) as response:
        return response.read().decode("utf-8", "replace")


def clean_text(fragment):
    fragment = re.sub(r"<img\b[^>]*>", " ", fragment)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    fragment = unescape(fragment)
    fragment = re.sub(r"\s+", " ", fragment).strip()
    return fragment


def page_title(html):
    match = re.search(r"<title>(.*?)</title>", html, re.S)
    if not match:
        return "未知"
    title = clean_text(match.group(1))
    return title.split(" - ")[0].strip() or title


def page_description(html):
    match = re.search(r'<meta name="description" content="([^"]*)"', html)
    if not match:
        return ""
    return clean_text(match.group(1))


def category_from_path(path):
    match = re.search(r"/gathering-storm/([^/]+)/", path)
    if not match:
        return "其他"
    return CATEGORIES.get(match.group(1), match.group(1))


def key_from_path(path):
    return path.strip("/").split("/")[-1]


def discover_links(html):
    links = set()
    for href in re.findall(r'href="(/zh-CN/gathering-storm/[^"#]+/)"', html):
        if "/intro/" in href:
            continue
        if any(f"/{cat}/" in href for cat in CATEGORIES):
            links.add(href)
    return links


def parse_side_panels(html):
    token_re = re.compile(
        r'<(?P<tag>p|div)\b[^>]*class="(?P<class>[^"]*(?:_8lp4s91|_8lp4s94|_8lp4s95|_8lp4s98)[^"]*)"[^>]*>(?P<body>.*?)</(?P=tag)>',
        re.S,
    )
    sections = []
    current = None
    current_group = None

    for match in token_re.finditer(html):
        classes = match.group("class")
        text = clean_text(match.group("body"))
        if not text:
            continue

        if "_8lp4s91" in classes:
            if any(hint in text for hint in KEEP_SECTION_HINTS):
                current = {"title": text, "groups": []}
                sections.append(current)
                current_group = None
            else:
                current = None
                current_group = None
            continue

        if current is None:
            continue

        if "_8lp4s94" in classes:
            if text.startswith(SKIP_VALUE_PREFIXES):
                current_group = None
                continue
            current_group = {"label": text, "values": []}
            current["groups"].append(current_group)
            continue

        if "_8lp4s95" in classes or "_8lp4s98" in classes:
            if text.startswith(SKIP_VALUE_PREFIXES):
                continue
            if current_group is None:
                current_group = {"label": "", "values": []}
                current["groups"].append(current_group)
            if text not in current_group["values"]:
                current_group["values"].append(text)

    return [
        section for section in sections
        if any(group["values"] or group["label"] for group in section["groups"])
    ]


def main():
    queue = list(SEEDS)
    seen = set()
    items = []

    while queue and len(seen) < MAX_PAGES:
        path = queue.pop(0)
        if path in seen:
            continue
        seen.add(path)

        try:
            html = fetch(path)
        except Exception as exc:
            print(f"skip {path}: {exc}")
            continue

        for link in sorted(discover_links(html)):
            if link not in seen and link not in queue:
                queue.append(link)

        panels = parse_side_panels(html)
        if not panels:
            continue

        items.append({
            "id": key_from_path(path),
            "name": page_title(html),
            "category": category_from_path(path),
            "summary": page_description(html),
            "source": urljoin(BASE, path),
            "sections": panels,
        })
        print(f"{len(items):03d} {category_from_path(path)} {page_title(html)}")
        time.sleep(0.01)

    items.sort(key=lambda item: (item["category"], item["name"]))
    payload = {
        "generatedAt": time.strftime("%Y-%m-%d"),
        "ruleset": "Gathering Storm",
        "sourceName": "civilopedia.net zh-CN",
        "sourceHome": "https://www.civilopedia.net/zh-CN/gathering-storm/",
        "items": items,
    }

    output = "../assets/civ6-data.js"
    with open(output, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("window.CIV6_DATA = ")
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write(";\n")

    print(f"wrote {len(items)} items to {output}")


if __name__ == "__main__":
    main()
