from typing import Dict, Iterable, List, Optional

from app.services.analysis_service import (
    build_anomaly_summary,
    build_cop_ranking,
    build_overview,
)
from app.services.data_loader import get_building_options, read_dataset


BUILDING_KEYWORDS = {
    "综合教学楼a": "综合教学楼A",
    "教学楼": "综合教学楼A",
    "行政办公楼b": "行政办公楼B",
    "办公楼": "行政办公楼B",
    "图书信息楼c": "图书信息楼C",
    "图书馆": "图书信息楼C",
    "图书信息楼": "图书信息楼C",
    "科研实验楼d": "科研实验楼D",
    "实验楼": "科研实验楼D",
    "科研实验楼": "科研实验楼D",
}


def _citation(title: str, path: str) -> Dict[str, str]:
    return {"title": title, "path": path}


def _build_citations(items: Iterable[tuple[str, str]]) -> List[Dict[str, str]]:
    return [_citation(title, path) for title, path in items]


def _has_any(text: str, keywords: Iterable[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _find_target_building(question_text: str) -> Optional[str]:
    for keyword, building_name in BUILDING_KEYWORDS.items():
        if keyword in question_text:
            return building_name
    return None


def _format_building_list(buildings: List[Dict[str, str]]) -> str:
    return "、".join(item["building_name"] for item in buildings)


def build_assistant_reply(question: str) -> Dict[str, List]:
    dataset = read_dataset()
    overview = build_overview(dataset)
    buildings = get_building_options()
    question_text = question.lower().strip()

    if _has_any(question_text, ["知识库", "rag", "大模型", "检索增强"]):
        answer = (
            "当前问答模块已经具备第一轮知识素材基础：数据质量报告、指标规则、异常诊断、设备维护手册"
            "和结构化问答库都已经入库。下一步建议把这些 Markdown 文档切分为知识片段，建立向量索引，"
            "再由大模型基于检索结果生成回答。"
        )
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("知识库入口", "knowledge_base/README.md"),
                    ("问答素材库 Round 1", "knowledge_base/faq/qa_bank_round1.md"),
                    ("技术方案", "docs/02-technical-solution.md"),
                ]
            ),
            "follow_up": [
                "现在已经有哪些可直接引用的知识文件",
                "哪些问题最适合课堂演示",
                "后续如何把知识库接入 RAG",
            ],
        }

    if _has_any(question_text, ["数据质量", "数据来源", "覆盖", "真实性", "真实数据", "模拟数据", "随机"]):
        answer = (
            "当前样例数据共覆盖 {0} 栋建筑、{1} 条记录，时间范围为 {2} 至 {3}。"
            "它不是纯随机生成，而是按照 BDG2、SHIFDR、NYC LL84、AlphaBuilding 等公开资料"
            "定义口径后生成的演示级结构化数据。"
        ).format(
            overview["building_count"],
            overview["total_records"],
            overview["time_range"]["start"],
            overview["time_range"]["end"],
        )
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("数据质量报告 Round 1", "data/processed/data_quality_report_round1.md"),
                    ("外部数据源简表 Round 1", "data/processed/external_source_shortlist_round1.md"),
                ]
            ),
            "follow_up": [
                "当前数据最值得第二轮补什么字段",
                "有哪些场景已经覆盖，哪些还没覆盖",
                "为什么同时采集电耗和水耗",
            ],
        }

    if "异常" in question_text:
        anomalies = build_anomaly_summary(dataset)
        target_building = _find_target_building(question_text)
        filtered = [
            item for item in anomalies if item["building_name"] == target_building
        ] if target_building else anomalies
        count = len(filtered)
        if count == 0:
            answer = "当前筛选范围内没有识别到明显异常记录。后续可以补充阈值规则和更细的设备级分析。"
        else:
            latest = filtered[0]
            if target_building:
                answer = (
                    "{0} 当前共识别到 {1} 条异常记录。最近一条发生在 {2}，设备 {3} 的异常原因为“{4}”。"
                    "建议优先对照异常诊断指南检查非工作时段高能耗、低 COP 和设备状态偏离。"
                ).format(
                    target_building,
                    count,
                    latest["timestamp"],
                    latest["equipment_id"],
                    latest["anomaly_reason"],
                )
            else:
                answer = (
                    "当前样例数据共识别到 {0} 条异常记录。最近一条发生在 {1}，"
                    "建筑 {2} 的设备 {3} 被标记为“{4}”。"
                ).format(
                    count,
                    latest["timestamp"],
                    latest["building_name"],
                    latest["equipment_id"],
                    latest["anomaly_reason"],
                )
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("电耗异常诊断指南", "knowledge_base/manuals/anomaly_diagnosis_guide.md"),
                    ("问答素材库 Round 1", "knowledge_base/faq/qa_bank_round1.md"),
                    ("数据质量报告 Round 1", "data/processed/data_quality_report_round1.md"),
                ]
            ),
            "follow_up": [
                "继续查看异常明细列表",
                "解释某一栋建筑为什么会出现异常",
                "继续查看 COP 排名和异常原因分布",
            ],
        }

    if _has_any(question_text, ["维护", "保养", "巡检", "冷却塔", "冷水机组", "空气处理机组", "风机盘管", "ahu", "ch", "ct", "fcu"]):
        answer = (
            "当前知识库已经整理了 AHU、冷水机组、冷却塔和风机盘管四类设备的日常巡检、每周检查、"
            "每月保养和常见故障处理表。若你关注制冷效率下降，优先看冷水机组与冷却塔章节；"
            "若是教学楼深夜高电耗，优先排查 AHU 是否未关机。"
        )
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("设备维护运营手册", "knowledge_base/manuals/equipment_maintenance_playbook.md"),
                    ("电耗异常诊断指南", "knowledge_base/manuals/anomaly_diagnosis_guide.md"),
                ]
            ),
            "follow_up": [
                "冷却塔应该多久维护一次",
                "制冷效率下降应该怎么排查",
                "实验楼的 FCU 有哪些巡检重点",
            ],
        }

    if "cop" in question_text or "能效" in question_text or "制冷效率" in question_text:
        ranking = build_cop_ranking(dataset)
        best = ranking[0] if ranking else None
        answer = (
            "当前样例数据计算得到的整体平均 COP 为 {0}。按照第一轮知识库规则，"
            "COP 低于 2.5 就应视为告警。{1}"
        ).format(
            overview["average_cop"],
            "目前 COP 最高的建筑是 {0}，平均 COP 为 {1}。".format(
                best["building_name"],
                best["average_cop"],
            ) if best else "当前没有足够数据生成建筑级 COP 排名。",
        )
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("指标与判定规则", "knowledge_base/glossary/metrics_and_rules.md"),
                    ("问答素材库 Round 1", "knowledge_base/faq/qa_bank_round1.md"),
                ]
            ),
            "follow_up": [
                "查看分建筑 COP 对比",
                "按日统计 COP 趋势",
                "解释 COP 为什么会偏低",
            ],
        }

    if _has_any(question_text, ["实验楼", "教学楼", "办公楼", "图书馆", "图书信息楼", "建筑差异", "建筑类型"]):
        target_building = _find_target_building(question_text)
        if target_building == "科研实验楼D":
            answer = (
                "科研实验楼D 是当前样例数据里能耗最高的建筑。它的高能耗主要来自高功率实验设备、"
                "更严格的温湿度控制需求，以及风机盘管按房间独立调温带来的更高 HVAC 复杂度。"
            )
        elif target_building == "图书信息楼C":
            answer = (
                "图书信息楼C 的运行时间比教学楼和办公楼更长，而且有 IT 设备底部负荷，"
                "因此夜间仍会保持一定电耗；同时冷却塔状态会直接影响它的 COP 表现。"
            )
        elif target_building == "行政办公楼B":
            answer = (
                "行政办公楼B 的能耗在四栋建筑中最低，主要因为办公时间窗口规律、夜间快速降载，"
                "整体更接近标准 Office 建筑的负荷曲线。"
            )
        elif target_building == "综合教学楼A":
            answer = (
                "综合教学楼A 的能耗呈明显教学时段波动，09:00 至 15:00 峰值最明显，"
                "异常通常出现在非工作时段 AHU 未及时关机。"
            )
        else:
            answer = (
                "当前 4 栋建筑的能耗差异很明显：办公楼最规律，教学楼受课表影响最强，"
                "图书馆运行时段更长，而实验楼整体能耗最高、波动也最大。"
            )
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("建筑类型能耗特性说明", "knowledge_base/manuals/building_type_notes.md"),
                    ("外部数据源简表 Round 1", "data/processed/external_source_shortlist_round1.md"),
                ]
            ),
            "follow_up": [
                "哪栋建筑的电耗最高",
                "为什么实验楼的能耗更高",
                "各建筑应该怎样分别设告警阈值",
            ],
        }

    if "耗电" in question_text or "电耗" in question_text or "能耗" in question_text:
        answer = (
            "当前样例数据覆盖 {0} 栋建筑、{1} 条记录，总电耗为 {2} kWh。"
            "这部分数据可作为前后端联调和演示脚本的基础。"
        ).format(
            overview["building_count"],
            overview["total_records"],
            overview["totals"].get("electricity_kwh", 0),
        )
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("数据字典", "data/dictionaries/energy_records_dictionary.csv"),
                    ("数据质量报告 Round 1", "data/processed/data_quality_report_round1.md"),
                ]
            ),
            "follow_up": [
                "按时间查看能耗汇总",
                "按建筑对比电耗",
                "导出筛选后的原始记录",
            ],
        }

    if "建筑" in question_text:
        answer = "当前样例数据包含 {0} 栋建筑，分别是：{1}。".format(
            len(buildings),
            _format_building_list(buildings),
        )
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("数据字典", "data/dictionaries/energy_records_dictionary.csv"),
                    ("建筑类型能耗特性说明", "knowledge_base/manuals/building_type_notes.md"),
                ]
            ),
            "follow_up": [
                "查看各建筑 COP 排名",
                "查看建筑对比统计",
                "筛选某一栋建筑的记录",
            ],
        }

    if "字段" in question_text or "数据字典" in question_text:
        answer = (
            "当前样例数据已经固定了建筑、时间、能耗、环境和设备状态相关字段。"
            "核心字段包括 building_id、timestamp、electricity_kwh、hvac_kwh、"
            "cooling_load_kwh 和 equipment_status。"
        )
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("数据字典", "data/dictionaries/energy_records_dictionary.csv"),
                    ("数据质量报告 Round 1", "data/processed/data_quality_report_round1.md"),
                ]
            ),
            "follow_up": [
                "查看全部字段说明",
                "确认字段是否允许新增",
                "导出数据字典给组员",
            ],
        }

    if "模块" in question_text or "系统" in question_text:
        answer = (
            "当前系统已经拆成数据管理、统计分析、可视化展示和智能问答四个主模块，"
            "适合前后端与 AI 任务并行开发。"
        )
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("需求分析", "docs/01-requirements.md"),
                    ("协作规则", "docs/07-collaboration-rules.md"),
                ]
            ),
            "follow_up": [
                "第一次任务怎么分配",
                "哪些文件不能随便改",
                "接口契约在哪里看",
            ],
        }

    if "排名" in question_text or ("cop" in question_text and "建筑" in question_text):
        ranking = build_cop_ranking(dataset)
        if ranking:
            top = ranking[0]
            answer = "当前样例数据里 COP 最高的建筑是 {0}，平均 COP 为 {1}。".format(
                top["building_name"],
                top["average_cop"],
            )
        else:
            answer = "当前没有可用于计算 COP 排名的数据。"
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("指标与判定规则", "knowledge_base/glossary/metrics_and_rules.md"),
                    ("建筑类型能耗特性说明", "knowledge_base/manuals/building_type_notes.md"),
                ]
            ),
            "follow_up": [
                "查看完整 COP 排名",
                "解释 COP 计算方式",
                "按时间查看 COP 趋势",
            ],
        }

    return {
        "answer": (
            "当前问答模块已经接入第一轮知识素材的规则化引用能力，"
            "可以先询问数据来源、能耗概况、COP、异常诊断、设备维护或建筑类型差异。"
        ),
        "citations": _build_citations(
            [
                ("知识库入口", "knowledge_base/README.md"),
                ("问答素材库 Round 1", "knowledge_base/faq/qa_bank_round1.md"),
                ("技术方案", "docs/02-technical-solution.md"),
            ]
        ),
        "follow_up": [
            "数据为什么不是纯随机生成",
            "图书信息楼最近有什么异常",
            "冷却塔应该多久维护一次",
        ],
    }
