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
    "ResourceType": "资源",
    "ResourceClassType": "资源类型",
    "Frequency": "陆地出现权重",
    "SeaFrequency": "海上出现权重",
    "RevealedEra": "显示时代",
    "TerrainType": "地形",
    "FeatureType": "地貌",
    "ImprovementType": "改良设施",
    "YieldType": "产出",
    "YieldChange": "产出变化",
    "Accumulate": "可积累",
    "PowerProvided": "发电量",
    "CO2perkWh": "碳排放",
    "BaseExtractionRate": "未改良每回合获得",
    "ImprovedExtractionRate": "改良后每回合获得",
    "StockpileCap": "基础储量上限",
    "UnitType": "单位",
    "UpgradeUnit": "升级为",
    "StartProductionCost": "启动消耗",
    "BuildWithUnitCost": "建造消耗",
    "PointsPerTurn": "每回合点数",
    "GreatPersonClassType": "伟人类型",
    "TilesRequired": "需要格数",
    "AdjacentDistrict": "相邻区域",
    "AdjacentResource": "相邻资源",
    "AdjacentTerrain": "相邻地形",
    "AdjacentFeature": "相邻地貌",
    "OtherDistrictAdjacent": "相邻其他区域",
    "PrereqResource": "所需资源",
    "MustRemoveFeature": "是否必须移除地貌",
    "RequiredPower": "需要电力",
    "ResourceTypeConvertedToPower": "发电燃料",
    "Amount": "数量",
    "Value": "数值",
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
    "TriggerDescription",
    "TriggerLongDescription",
    "BoostClass",
    "ListType",
    "Kind",
    "AdvisorType",
    "PseudoYieldType",
    "IconString",
    "ActionIcon",
    "ModifierId",
    "ModifierType",
    "SubjectRequirementSetId",
    "RequirementId",
    "RequirementType",
    "RequirementSetId",
    "RequirementSetType",
    "FormationClass",
    "PromotionClass",
    "CanCapture",
    "IgnoreMoves",
    "Stackable",
    "CanTargetAir",
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

ENUM_NAMES = {
    "YIELD_FOOD": "食物",
    "YIELD_PRODUCTION": "生产力",
    "YIELD_GOLD": "金币",
    "YIELD_SCIENCE": "科技值",
    "YIELD_CULTURE": "文化值",
    "YIELD_FAITH": "信仰",
    "YIELD_POWER": "电力",
    "RESOURCECLASS_BONUS": "加成资源",
    "RESOURCECLASS_LUXURY": "奢侈品",
    "RESOURCECLASS_STRATEGIC": "战略资源",
    "DOMAIN_LAND": "陆地",
    "DOMAIN_SEA": "海上",
    "DOMAIN_AIR": "空中",
    "NO_DOMAIN": "无",
    "TERRAIN_COAST": "海岸",
    "TERRAIN_DESERT": "沙漠",
    "TERRAIN_DESERT_HILLS": "沙漠丘陵",
    "TERRAIN_GRASS": "草原",
    "TERRAIN_GRASS_HILLS": "草原丘陵",
    "TERRAIN_PLAINS": "平原",
    "TERRAIN_PLAINS_HILLS": "平原丘陵",
    "TERRAIN_SNOW": "雪地",
    "TERRAIN_SNOW_HILLS": "雪地丘陵",
    "TERRAIN_TUNDRA": "冻土",
    "TERRAIN_TUNDRA_HILLS": "冻土丘陵",
    "FEATURE_MARSH": "沼泽",
    "FEATURE_FLOODPLAINS": "泛滥平原",
    "FEATURE_FLOODPLAINS_PLAINS": "平原泛滥平原",
    "FEATURE_JUNGLE": "雨林",
    "FEATURE_FOREST": "树林",
}

ALLOWED_RELATION_TABLES = {
    "DistrictReplaces",
    "BuildingReplaces",
    "UnitReplaces",
    "Adjacency_YieldChanges",
    "District_GreatPersonPoints",
    "District_TradeRouteYields",
    "District_CitizenYieldChanges",
    "Building_YieldChanges",
    "Building_GreatPersonPoints",
    "Building_CitizenYieldChanges",
    "Improvement_YieldChanges",
    "Improvement_ValidTerrains",
    "Improvement_ValidFeatures",
    "Improvement_ValidResources",
    "Improvement_BonusYieldChanges",
    "Resource_YieldChanges",
    "Resource_ValidTerrains",
    "Resource_ValidFeatures",
    "Resource_Consumption",
    "TechnologyPrereqs",
    "CivicPrereqs",
    "Government_SlotCounts",
    "Unit_BuildingPrereqs",
    "Unit_Upgrades",
    "Unit_ResourceCosts",
    "Project_ResourceCosts",
    "Route_ResourceCosts",
    "Building_ResourceCosts",
    "Building_PowerRequirements",
    "Building_ResourceConversions",
}

INTERNAL_VALUE_MARKERS = (
    "LOC_",
    "BOOST_",
    "KIND_",
    "MODIFIER_",
    "REQUIREMENT_",
    "PSEUDOYIELD_",
    "ADVISOR_",
    "ICON_",
    "FORMATION_CLASS_",
    "PROMOTION_CLASS_",
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
            row_tag = row.tag.split("}")[-1]
            if row_tag == "Row":
                attrs = dict(row.attrib)
                for child in row:
                    child_name = child.tag.split("}")[-1]
                    if child.text and child.text.strip():
                        attrs[child_name] = child.text.strip()
                attrs["__op"] = "Row"
                result.append((table, attrs, path))
            elif row_tag == "Update":
                attrs = {}
                for child in row:
                    child_name = child.tag.split("}")[-1]
                    if child_name not in {"Where", "Set"}:
                        continue
                    attrs.update(child.attrib)
                    for grandchild in child:
                        grandchild_name = grandchild.tag.split("}")[-1]
                        if grandchild.text and grandchild.text.strip():
                            attrs[grandchild_name] = grandchild.text.strip()
                if attrs:
                    attrs["__op"] = "Update"
                    result.append((table, attrs, path))
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
    if value in ENUM_NAMES:
        return ENUM_NAMES[value]
    if value in type_names:
        return type_names[value]
    if value.startswith("LOC_"):
        return value
    return value.replace("_", " ")


def human_value(key, value, type_names):
    if value.lower() in {"true", "false"}:
        return "是" if value.lower() == "true" else "否"
    if value in ENUM_NAMES:
        return ENUM_NAMES[value]
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
        "Resource_ValidTerrains": "资源可出现地形",
        "Resource_ValidFeatures": "资源可出现地貌",
        "Resource_Consumption": "资源积累/发电",
        "TechnologyPrereqs": "科技前置",
        "CivicPrereqs": "市政前置",
        "Government_SlotCounts": "政体政策槽",
        "Unit_BuildingPrereqs": "单位建筑要求",
        "Unit_Upgrades": "单位升级",
        "Unit_ResourceCosts": "单位资源消耗",
        "Project_ResourceCosts": "项目资源消耗",
        "Route_ResourceCosts": "路线资源消耗",
        "Building_ResourceCosts": "建筑资源消耗",
        "Building_PowerRequirements": "建筑电力需求",
        "Building_ResourceConversions": "建筑燃料转换",
    }
    return mapping.get(table, table)


def row_summary(attrs, type_names):
    parts = []
    for key, value in attrs.items():
        if key.startswith("__"):
            continue
        if key in SKIP_FIELDS or value == "":
            continue
        human = human_value(key, value, type_names)
        if any(marker in human for marker in INTERNAL_VALUE_MARKERS):
            continue
        parts.append(f"{label(key)}：{human}")
    return parts


def rows_by_table(rows, table):
    return [attrs for row_table, attrs, _ in rows if row_table == table]


def values_for(table_rows, key, value, out_key, type_names):
    found = []
    for attrs in table_rows:
        if attrs.get(key) == value and attrs.get(out_key):
            found.append(human_value(out_key, attrs[out_key], type_names))
    return sorted(set(found))


def resource_player_guide(item, attrs, rows, type_names):
    resource_id = item["id"]
    resource_name = item["name"]
    sections = []

    consumption = next((r for r in rows_by_table(rows, "Resource_Consumption") if r.get("ResourceType") == resource_id), {})
    improvements = values_for(rows_by_table(rows, "Improvement_ValidResources"), "ResourceType", resource_id, "ImprovementType", type_names)
    terrains = values_for(rows_by_table(rows, "Resource_ValidTerrains"), "ResourceType", resource_id, "TerrainType", type_names)
    features = values_for(rows_by_table(rows, "Resource_ValidFeatures"), "ResourceType", resource_id, "FeatureType", type_names)
    yields = []
    for r in rows_by_table(rows, "Resource_YieldChanges"):
        if r.get("ResourceType") == resource_id:
            yields.append(f"+{r.get('YieldChange', '0')} {human_value('YieldType', r.get('YieldType', ''), type_names)}")

    obtain = []
    prereq = attrs.get("PrereqTech") or attrs.get("PrereqCivic")
    if prereq:
        obtain.append(f"先研究/解锁：{human_value('PrereqTech', prereq, type_names)}，之后地图上才会显示{resource_name}。")
    if improvements:
        obtain.append(f"在资源格上建造改良设施：{'、'.join(improvements)}。")
    if terrains:
        obtain.append(f"可能出现地形：{'、'.join(terrains)}。")
    if features:
        obtain.append(f"可能出现地貌：{'、'.join(features)}。")
    if not obtain:
        obtain.append("通过占有对应资源格、改良资源、交易、城邦或特殊能力获得。")

    rate = []
    if consumption:
        base = consumption.get("BaseExtractionRate")
        improved = consumption.get("ImprovedExtractionRate")
        cap = consumption.get("StockpileCap")
        power = consumption.get("PowerProvided")
        if improved is not None:
            rate.append(f"改良后每个资源通常每回合 +{improved}。")
        if base is not None and base != "0":
            rate.append(f"未改良基础每回合 +{base}。")
        if cap:
            rate.append(f"基础储量上限：{cap}。")
        if power:
            rate.append(f"作为燃料发电时，每点可提供 {power} 电力。")
    if not rate:
        rate.append("非积累型资源通常不是按回合进库存，而是改良后提供地块产出、宜居度或解锁条件。")
    if yields:
        rate.append(f"资源地块产出：{'、'.join(yields)}。")

    uses = []
    unit_uses = []
    for unit in primary_units_using_resource(rows, resource_id, type_names):
        unit_uses.append(unit)
    if unit_uses:
        uses.append(f"用于训练、升级或维护相关单位：{'、'.join(unit_uses[:12])}{' 等' if len(unit_uses) > 12 else ''}。")
    building_uses = []
    for r in rows_by_table(rows, "Building_ResourceCosts"):
        if r.get("ResourceType") == resource_id and r.get("BuildingType"):
            building_uses.append(human_value("BuildingType", r["BuildingType"], type_names))
    for r in rows_by_table(rows, "Building_GreatWorks"):
        if r.get("ResourceType") == resource_id and r.get("BuildingType"):
            building_uses.append(human_value("BuildingType", r["BuildingType"], type_names))
    if building_uses:
        uses.append(f"建筑/项目相关消耗：{'、'.join(sorted(set(building_uses)))}。")
    if resource_id == "RESOURCE_OIL":
        uses.append("常见用途：现代/信息时代军事单位、燃油发电厂、部分后期项目和单位维护。")
    elif attrs.get("ResourceClassType") == "RESOURCECLASS_STRATEGIC":
        uses.append("战略资源通常用于军事单位、项目或发电，并可能有库存上限。")
    elif attrs.get("ResourceClassType") == "RESOURCECLASS_LUXURY":
        uses.append("奢侈品主要提供宜居度，并可通过交易换金币或其他资源。")
    else:
        uses.append("加成资源主要改善地块产出，可被对应改良设施利用。")

    sections.append({
        "title": "玩家速查",
        "groups": [
            {"label": "怎么获得", "values": obtain},
            {"label": "获得多少", "values": rate},
            {"label": "如何查看", "values": [
                "看屏幕顶部资源栏：战略资源会显示当前库存和每回合增减。",
                "打开报告/资源列表可以查看每种资源的来源、消耗和交易情况。",
                "地图上资源图标出现后，把鼠标移到资源格或资源栏图标上，可看该资源和地块产出。"
            ]},
            {"label": "作用", "values": uses},
        ],
    })
    return sections


def primary_units_using_resource(rows, resource_id, type_names):
    units = set()
    for attrs in rows_by_table(rows, "Units"):
        if attrs.get("StrategicResource") == resource_id and attrs.get("UnitType"):
            units.add(human_value("UnitType", attrs["UnitType"], type_names))
    for attrs in rows_by_table(rows, "Unit_ResourceCosts"):
        if attrs.get("ResourceType") == resource_id and attrs.get("UnitType"):
            units.add(human_value("UnitType", attrs["UnitType"], type_names))
    return sorted(units)


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
    primary_attrs = {}
    type_names = {}
    for table, key, category in CATEGORY_SPECS:
        for row_table, attrs, path in rows:
            if row_table != table or key not in attrs:
                continue
            if attrs.get("__op") == "Update":
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
            primary_attrs[item_id] = dict(attrs)
            type_names[item_id] = name

    for table, key, _ in CATEGORY_SPECS:
        for row_table, attrs, _ in rows:
            if row_table != table or key not in attrs or attrs.get("__op") != "Update":
                continue
            item_id = attrs[key]
            if item_id not in primary_attrs:
                continue
            for update_key, update_value in attrs.items():
                if update_key.startswith("__") or update_key == key:
                    continue
                primary_attrs[item_id][update_key] = update_value

    # Rebuild primary base sections now that type names are known.
    for item_id, attrs in primary_attrs.items():
        primary[item_id]["sections"][0]["groups"][0]["values"] = row_summary(attrs, type_names)

    relation_fields = set(primary)
    for table, attrs, _ in rows:
        if table not in ALLOWED_RELATION_TABLES:
            continue
        hits = []
        for key, value in attrs.items():
            if key.startswith("__"):
                continue
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

    for table, key, _ in CATEGORY_SPECS:
        if table != "Resources":
            continue
        for row_table, attrs, _ in rows:
            if row_table == "Resources" and attrs.get("__op") != "Update" and key in attrs and attrs[key] in primary:
                item = primary[attrs[key]]
                item["sections"] = resource_player_guide(item, primary_attrs[attrs[key]], rows, type_names) + item["sections"]

    items = sorted(primary.values(), key=lambda item: (item["category"], item["name"]))
    payload = {
        "generatedAt": time.strftime("%Y-%m-%d"),
        "ruleset": "Base + Rise and Fall + Gathering Storm official XML",
        "sourceName": "Sid Meier's Civilization VI local XML",
        "sourceHome": "D:/Steam/steamapps/common/Sid Meier's Civilization VI",
        "notes": "由本机游戏官方 XML 数据生成，过滤内部调试字段，重点展示玩家可读的数值、资源获得方式和用途；不包含文明百科长篇背景介绍。",
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
