import json
import os
import re
import time
import xml.etree.ElementTree as ET


GAME_ROOT = r"D:\Steam\steamapps\common\Sid Meier's Civilization VI"
DATA_DIRS = [
    os.path.join(GAME_ROOT, "Base", "Assets", "Gameplay", "Data"),
    os.path.join(GAME_ROOT, "DLC", "Expansion1", "Data"),
    os.path.join(GAME_ROOT, "DLC", "Expansion2", "Data"),
]
TEXT_FILES = [
    os.path.join(GAME_ROOT, "Base", "Assets", "Text", "Vanilla_zh_Hans_CN.xml"),
    os.path.join(GAME_ROOT, "DLC", "Expansion1", "Text", "Expansion1_Translations_Text.xml"),
    os.path.join(GAME_ROOT, "DLC", "Expansion1", "Text", "Expansion1_Translations_Major_Text.xml"),
    os.path.join(GAME_ROOT, "DLC", "Expansion2", "Text", "Expansion2_Translations_Text.xml"),
]

CATEGORY_SPECS = [
    ("Districts", "DistrictType", "区域"),
    ("Buildings", "BuildingType", "建筑"),
    ("Units", "UnitType", "单位"),
    ("Improvements", "ImprovementType", "改良设施"),
    ("Resources", "ResourceType", "资源"),
    ("Technologies", "TechnologyType", "科技"),
    ("Civics", "CivicType", "市政"),
    ("Governments", "GovernmentType", "政体"),
    ("Policies", "PolicyType", "政策"),
    ("GreatPersonIndividuals", "GreatPersonIndividualType", "伟人"),
]

FIELD_LABELS = {
    "Cost": "生产力/基础成本",
    "Maintenance": "维护费",
    "PrereqTech": "前置科技",
    "PrereqCivic": "前置市政",
    "PrereqDistrict": "前置区域",
    "PrereqBuilding": "前置建筑",
    "PrereqResource": "前置资源",
    "PrereqPopulation": "人口要求",
    "PurchaseYield": "购买资源类型",
    "MustPurchase": "必须购买",
    "BaseMoves": "移动力",
    "BaseSightRange": "视野",
    "ZoneOfControl": "控制区域",
    "Domain": "活动域",
    "FormationClass": "编队类型",
    "PromotionClass": "晋升类型",
    "Combat": "近战战斗力",
    "RangedCombat": "远程战斗力",
    "Bombard": "轰炸战斗力",
    "Range": "射程",
    "AntiAirCombat": "防空战斗力",
    "ReligiousStrength": "宗教战斗力",
    "BuildCharges": "建造次数",
    "SpreadCharges": "传播次数",
    "ReligiousHealCharges": "治疗次数",
    "Housing": "住房",
    "Entertainment": "宜居度/娱乐",
    "CitizenSlots": "专家槽位",
    "OuterDefenseHitPoints": "外防生命值",
    "OuterDefenseStrength": "外防强度",
    "RegionalRange": "区域影响范围",
    "AdvisorType": "顾问分类",
    "TraitType": "特属于",
    "StrategicResource": "战略资源",
    "ResourceCost": "资源消耗",
    "ResourceMaintenanceType": "维护资源",
    "ResourceMaintenanceAmount": "维护资源数量",
    "RequiresPlacement": "需要放置",
    "RequiresPopulation": "需要人口",
    "Coast": "海岸要求",
    "AdjacentToLand": "邻接陆地要求",
    "NoAdjacentCity": "不能邻接城市",
    "OnePerCity": "每城一个",
    "AllowsHolyCity": "允许圣城",
    "CityCenter": "市中心",
    "Aqueduct": "水渠类",
    "AirSlots": "飞机槽位",
    "Appeal": "魅力影响",
    "CityStrengthModifier": "城市强度修正",
    "HitPoints": "生命值",
    "PlunderType": "劫掠类型",
    "PlunderAmount": "劫掠收益",
    "CostProgressionModel": "成本增长模型",
    "CostProgressionParam1": "成本增长参数",
    "Description": "说明键",
    "Name": "名称键",
}

SKIP_FIELDS = {
    "Name",
    "Description",
    "Quote",
    "QuoteAudio",
    "CivilopediaPage",
    "InternalOnly",
    "MustPurchase",
    "EnabledByReligion",
}

TYPE_SUFFIXES = (
    "Type",
    "Tech",
    "Civic",
    "District",
    "Building",
    "Resource",
    "Unit",
    "Government",
    "Policy",
    "YieldType",
    "TraitType",
    "GreatPersonClassType",
)


def rows_from_file(path):
    try:
        root = ET.parse(path).getroot()
    except Exception:
        return []
    result = []
    for parent in root:
        table = parent.tag.split("}")[-1]
        for row in parent:
            if row.tag.split("}")[-1] == "Row":
                result.append((table, dict(row.attrib), path))
    return result


def load_texts():
    texts = {}
    for path in TEXT_FILES:
        if not os.path.exists(path):
            continue
        try:
            root = ET.parse(path).getroot()
        except Exception:
            continue
        for node in root.iter():
            tag_name = node.tag.split("}")[-1]
            if tag_name not in {"Row", "Replace"}:
                continue
            tag = node.attrib.get("Tag")
            lang = node.attrib.get("Language", "")
            text = node.attrib.get("Text")
            if text is None:
                text_node = next((child for child in node if child.tag.split("}")[-1] == "Text"), None)
                text = text_node.text if text_node is not None else None
            if tag and text and (not lang or lang in {"zh_Hans_CN", "zh_CN"}):
                texts[tag] = re.sub(r"\s+", " ", text).strip()
    return texts


def human_type(value, type_names):
    if not value:
        return value
    if value in type_names:
        return type_names[value]
    return value.replace("_", " ")


def human_value(key, value, type_names):
    if value in {"true", "false"}:
        return "是" if value == "true" else "否"
    if key == "PurchaseYield":
        return human_type(value, type_names)
    if key.endswith(TYPE_SUFFIXES) or value.startswith(("TECH_", "CIVIC_", "DISTRICT_", "BUILDING_", "UNIT_", "RESOURCE_", "GOVERNMENT_", "POLICY_", "YIELD_", "TRAIT_")):
        return human_type(value, type_names)
    return value


def label(key):
    return FIELD_LABELS.get(key, key)


def table_label(table):
    mapping = {
        "DistrictReplaces": "替代关系",
        "BuildingReplaces": "替代关系",
        "UnitReplaces": "替代关系",
        "District_Adjacencies": "相邻加成定义",
        "Adjacency_YieldChanges": "相邻加成数值",
        "Building_YieldChanges": "建筑产出",
        "Building_GreatPersonPoints": "伟人点数",
        "Building_CitizenYieldChanges": "专家/公民收益",
        "BuildingModifiers": "建筑效果",
        "Improvement_YieldChanges": "改良产出",
        "Improvement_ValidTerrains": "可建地形",
        "Improvement_ValidFeatures": "可建地貌",
        "Improvement_ValidResources": "可建资源",
        "Improvement_BonusYieldChanges": "改良加成产出",
        "Resource_YieldChanges": "资源产出",
        "TechnologyPrereqs": "科技前置",
        "CivicPrereqs": "市政前置",
        "Government_SlotCounts": "政体政策槽",
        "PolicyModifiers": "政策效果",
        "Unit_BuildingPrereqs": "单位建筑要求",
        "Unit_Upgrades": "单位升级",
        "Unit_ResourceCosts": "单位资源消耗",
        "UnitAiInfos": "单位 AI 分类",
        "GreatPersonIndividualActionModifiers": "伟人效果",
        "GreatPersonIndividualActionCharges": "伟人次数",
    }
    return mapping.get(table, table)


def row_summary(attrs, type_names):
    parts = []
    for key, value in attrs.items():
        if key in SKIP_FIELDS or value == "":
            continue
        parts.append(f"{label(key)}：{human_value(key, value, type_names)}")
    return parts


def main():
    texts = load_texts()
    rows = []
    for data_dir in DATA_DIRS:
        if not os.path.isdir(data_dir):
            continue
        for name in os.listdir(data_dir):
            if name.lower().endswith(".xml"):
                rows.extend(rows_from_file(os.path.join(data_dir, name)))

    primary = {}
    type_names = {}
    for table, key, category in CATEGORY_SPECS:
        for row_table, attrs, path in rows:
            if row_table != table or key not in attrs:
                continue
            item_id = attrs[key]
            name_key = attrs.get("Name")
            name = texts.get(name_key, item_id.replace("_", " "))
            if row_table == "Buildings":
                category = "奇观" if attrs.get("MaxWorldInstances") == "1" or attrs.get("IsWonder") == "true" else "建筑"
            primary[item_id] = {
                "id": item_id,
                "name": name,
                "category": category,
                "source": "official-xml",
                "sourceFile": os.path.relpath(path, GAME_ROOT).replace("\\", "/"),
                "sections": [{
                    "title": "基础数值",
                    "groups": [{"label": "字段", "values": row_summary(attrs, type_names)}],
                }],
            }
            type_names[item_id] = name

    # Rebuild primary base sections now that type names are known.
    for table, key, _ in CATEGORY_SPECS:
        for row_table, attrs, _ in rows:
            if row_table == table and key in attrs and attrs[key] in primary:
                primary[attrs[key]]["sections"][0]["groups"][0]["values"] = row_summary(attrs, type_names)

    relation_fields = set(primary)
    for table, attrs, _ in rows:
        hits = []
        for key, value in attrs.items():
            if value in relation_fields:
                hits.append(value)
        if not hits:
            continue
        values = row_summary(attrs, type_names)
        if not values:
            continue
        for item_id in set(hits):
            if item_id not in primary:
                continue
            item = primary[item_id]
            section = next((s for s in item["sections"] if s["title"] == "关联数值"), None)
            if section is None:
                section = {"title": "关联数值", "groups": []}
                item["sections"].append(section)
            group_name = table_label(table)
            group = next((g for g in section["groups"] if g["label"] == group_name), None)
            if group is None:
                group = {"label": group_name, "values": []}
                section["groups"].append(group)
            value = "；".join(values)
            if value not in group["values"]:
                group["values"].append(value)

    items = sorted(primary.values(), key=lambda item: (item["category"], item["name"]))
    payload = {
        "generatedAt": time.strftime("%Y-%m-%d"),
        "ruleset": "Base + Rise and Fall + Gathering Storm official XML",
        "sourceName": "Sid Meier's Civilization VI local XML",
        "sourceHome": "D:/Steam/steamapps/common/Sid Meier's Civilization VI",
        "notes": "由本机游戏官方 XML 数据生成，重点展示游戏数值字段和关联表；不包含文明百科长篇背景介绍。",
        "failures": [],
        "items": items,
    }

    out_path = os.path.join(os.path.dirname(__file__), "..", "assets", "civ6-data.js")
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("window.CIV6_DATA = ")
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write(";\n")
    print(f"wrote {len(items)} items")
    counts = {}
    for item in items:
        counts[item["category"]] = counts.get(item["category"], 0) + 1
    print(counts)


if __name__ == "__main__":
    main()
