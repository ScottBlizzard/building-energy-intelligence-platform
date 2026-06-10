from typing import Dict, Iterable, List, Optional

import pandas as pd

from app.services.analysis_service import (
    build_anomaly_summary,
    build_anomaly_work_orders,
    build_cop_ranking,
    build_equipment_summary,
    build_floor_summary,
    build_optimization_recommendations,
    build_overview,
)
from app.services.budget_service import build_budget_analysis, build_budget_kpi
from app.services.data_loader import get_building_options, get_visible_dataset
from app.services.roi_service import build_equipment_audit


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


def _filter_dataset(dataset: pd.DataFrame, building_name: Optional[str]) -> pd.DataFrame:
    if not building_name:
        return dataset
    return dataset[dataset["building_name"] == building_name].copy()


def _format_building_list(buildings: List[Dict[str, str]]) -> str:
    return "、".join(item["building_name"] for item in buildings)


def _building_id_for_name(buildings: List[Dict[str, str]], building_name: Optional[str]) -> Optional[str]:
    if not building_name:
        return None
    match = next((item for item in buildings if item.get("building_name") == building_name), None)
    return match.get("building_id") if match else None


def _latest_year_month(dataset: pd.DataFrame) -> tuple[int, int]:
    if dataset.empty:
        now = pd.Timestamp.now()
    else:
        now = pd.Timestamp(dataset["timestamp"].max())
    return int(now.year), int(now.month)


def _top_budget_risk(year: int, month: int, building_id: Optional[str] = None) -> Optional[Dict]:
    analysis = build_budget_analysis(year, month)
    items = analysis.get("buildings", [])
    if building_id:
        items = [item for item in items if item.get("building_id") == building_id]
    if not items:
        return None
    return max(
        items,
        key=lambda item: (
            float(item.get("projected_execution_rate", 0)),
            int(item.get("anomaly_count", 0)),
        ),
    )


def build_assistant_reply(question: str) -> Dict[str, List]:
    dataset = get_visible_dataset()
    overview = build_overview(dataset)
    buildings = get_building_options()
    question_text = question.lower().strip()
    target_building = _find_target_building(question_text)
    scoped_dataset = _filter_dataset(dataset, target_building)
    target_building_id = _building_id_for_name(buildings, target_building)

    if _has_any(question_text, ["预算", "超支", "费用控制", "kpi", "考核", "执行率"]):
        year, month = _latest_year_month(scoped_dataset if target_building else dataset)
        risk = _top_budget_risk(year, month, target_building_id)
        if risk:
            kpi = build_budget_kpi(str(risk["building_id"]), year)
            answer = (
                f"{risk['building_name']} {year}年{month}月预算为 {risk['budget_kwh']:,.0f} kWh，"
                f"当前已用 {risk['actual_kwh']:,.0f} kWh，月末预计执行率 {risk['projected_execution_rate']}%。"
                f"KPI 等级为 {kpi.get('grade', '-')}，预算控制率 {kpi.get('budget_control_rate', 0)}%，"
                f"异常响应及时率 {kpi.get('anomaly_response_timely_rate', 0)}%。"
            )
            if risk.get("status") == "over":
                answer += " 该楼栋存在超预算风险，建议优先执行夜间关机、异常工单复核和重点设备改造评估。"
            elif risk.get("status") == "warning":
                answer += " 该楼栋处于预算预警区间，建议提前压降可调负荷并持续观察。"
            else:
                answer += " 当前预算风险可控，可以维持常规巡检。"
        else:
            answer = "当前可见数据范围内还没有可用预算基线，建议先自动生成本月预算。"
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("预算管理接口", "docs/06-api-contract.md"),
                    ("业务逻辑升级任务", "docs/22-business-logic-upgrade-todo.md"),
                ]
            ),
            "follow_up": [
                "哪栋楼预算超支风险最高？",
                "实验楼本月 KPI 怎么样？",
                "预算风险对应哪些工单？",
            ],
        }

    if _has_any(question_text, ["roi", "npv", "irr", "投资", "回本", "回收期", "改造方案", "经济性"]):
        year, month = _latest_year_month(scoped_dataset if target_building else dataset)
        risk = _top_budget_risk(year, month, target_building_id)
        building_id = target_building_id or (risk.get("building_id") if risk else None)
        if not building_id and buildings:
            building_id = buildings[0]["building_id"]

        if building_id:
            audit = build_equipment_audit(str(building_id))
            candidates = []
            for equipment in audit.get("equipment_list", []):
                for option in equipment.get("retrofit_candidates", [])[:3]:
                    candidates.append({"equipment_type": equipment.get("equipment_type"), **option})
            best = max(candidates, key=lambda item: float(item.get("npv_yuan", 0))) if candidates else None
            if best:
                answer = (
                    f"{audit['building_name']} 当前最值得优先评估的是 {best['equipment_type']} 的"
                    f"{best['option']}：投资约 {best['investment_yuan']:,.0f} 元，"
                    f"年节省约 {best['annual_saving_yuan']:,.0f} 元，"
                    f"静态回收期 {best['payback_years']} 年，NPV {best['npv_yuan']:,.0f} 元，"
                    f"IRR {best['irr_pct']}%。"
                )
            else:
                answer = "当前楼栋没有生成可比较的改造候选方案。"
        else:
            answer = "当前没有可用于 ROI 分析的楼栋数据。"
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("ROI 分析接口", "docs/06-api-contract.md"),
                    ("业务逻辑升级任务", "docs/22-business-logic-upgrade-todo.md"),
                ]
            ),
            "follow_up": [
                "比较三种节能改造方案",
                "哪个方案回本最快？",
                "实验楼改造的 NPV 是多少？",
            ],
        }

    if _has_any(question_text, ["楼层", "哪一层", "区域", "分层", "逐层"]):
        floors = sorted(
            build_floor_summary(scoped_dataset),
            key=lambda item: (item["anomaly_count"], item["electricity_kwh"]),
            reverse=True,
        )
        if floors:
            top = floors[0]
            scope = target_building or "当前筛选范围"
            answer = (
                f"{scope} 异常和能耗最需要关注的是 {top['floor_label']} {top['zone_name']}，"
                f"该区域电耗 {top['electricity_kwh']} kWh，平均 COP {top['average_cop']}，"
                f"异常 {top['anomaly_count']} 条，异常率 {top['anomaly_rate']}%。"
                "建议先从该楼层的设备运行状态、夜间排程和末端设定温度开始排查。"
            )
        else:
            answer = "当前范围没有可用于楼层分析的数据。"
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("楼层区域分析接口", "docs/06-api-contract.md"),
                    ("建筑类型能耗特性说明", "knowledge_base/manuals/building_type_notes.md"),
                ]
            ),
            "follow_up": [
                "科研实验楼D哪一层异常最多？",
                "哪些楼层需要优先巡检？",
                "楼层分析和设备工单有什么关系？",
            ],
        }

    if _has_any(question_text, ["工单", "处置", "处理建议", "派单", "异常处置"]):
        work_orders = build_anomaly_work_orders(scoped_dataset)
        if work_orders:
            first = work_orders[0]
            answer = (
                f"当前应优先处理工单 {first['work_order_id']}，优先级为{first['priority']}。"
                f"位置是 {first['building_name']} {first['floor_label']} {first['zone_name']}，"
                f"设备为 {first['equipment_id']}（{first['equipment_type']}），"
                f"异常原因为{first['anomaly_reason']}。建议动作：{first['recommended_action']}。"
            )
        else:
            answer = "当前范围没有生成异常工单，可以继续观察趋势和 COP 变化。"
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("异常工单接口", "docs/06-api-contract.md"),
                    ("电耗异常诊断指南", "knowledge_base/manuals/anomaly_diagnosis_guide.md"),
                    ("设备维护运营手册", "knowledge_base/manuals/equipment_maintenance_playbook.md"),
                ]
            ),
            "follow_up": [
                "生成当前异常处置建议",
                "哪些设备需要优先维护？",
                "异常工单应该按什么顺序处理？",
            ],
        }

    if _has_any(question_text, ["优化", "节能", "降耗", "节能建议", "运营建议"]):
        recommendations = build_optimization_recommendations(scoped_dataset)
        if recommendations:
            first = recommendations[0]
            answer = (
                f"当前最优先的优化方向是{first['building_name']}的“{first['category']}”。"
                f"依据：{first['finding']} 建议：{first['action']} "
                f"预期效果：{first['expected_impact']}。"
            )
        else:
            answer = "当前范围没有明显节能告警，建议保持日报监测并关注夜间负荷、COP 和设备状态。"
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("优化建议接口", "docs/06-api-contract.md"),
                    ("指标与判定规则", "knowledge_base/glossary/metrics_and_rules.md"),
                ]
            ),
            "follow_up": [
                "有什么节能优化建议？",
                "哪个建筑最应该先降耗？",
                "夜间负荷偏高应该怎么处理？",
            ],
        }

    if _has_any(question_text, ["优先维护", "优先巡检", "哪些设备", "设备优先级", "设备需要"]):
        equipment = build_equipment_summary(scoped_dataset)
        high_priority = [item for item in equipment if item["priority"] == "高"]
        target_items = high_priority or equipment[:3]
        if target_items:
            first = target_items[0]
            answer = (
                f"当前优先维护设备是 {first['building_name']} 的 {first['equipment_id']}，"
                f"类型为{first['equipment_type']}，位于 {first['floor_label']} {first['zone_name']}，"
                f"优先级{first['priority']}，异常 {first['anomaly_count']} 条。"
                f"维护建议：{first['maintenance_hint']}。"
            )
        else:
            answer = "当前范围没有可排序的设备运行数据。"
        return {
            "answer": answer,
            "citations": _build_citations(
                [
                    ("设备监测接口", "docs/06-api-contract.md"),
                    ("设备维护运营手册", "knowledge_base/manuals/equipment_maintenance_playbook.md"),
                ]
            ),
            "follow_up": [
                "哪些设备需要优先维护？",
                "冷水机组需要检查什么？",
                "冷却塔应该多久维护一次？",
            ],
        }

    if _has_any(question_text, ["知识库", "rag", "大模型", "检索增强"]):
        answer = (
            "当前问答模块已经具备规则问答和外部大模型兜底能力，知识素材包括数据质量报告、指标规则、"
            "异常诊断、设备维护手册和结构化问答库。后续如果要做标准 RAG，可以把这些 Markdown 文档切分为知识片段，"
            "建立向量索引，再由大模型基于检索结果生成回答。"
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
                "现在已经有哪些可直接引用的知识文件？",
                "哪些问题最适合课堂演示？",
                "后续如何把知识库接入 RAG？",
            ],
        }

    if _has_any(
        question_text,
        ["数据质量", "数据来源", "覆盖", "真实性", "真实数据", "模拟数据", "随机", "记录数", "多少条", "时间范围"],
    ):
        answer = (
            f"当前样例数据共覆盖 {overview['building_count']} 栋建筑、{overview['total_records']} 条记录，"
            f"其中异常记录 {overview['abnormal_record_count']} 条。"
            f"时间范围为 {overview['time_range']['start']} 至 {overview['time_range']['end']}。"
            "它不是纯随机生成，而是参考 BDG2、SHIFDR、NYC LL84、AlphaBuilding 等公开资料的字段口径和运行规律，"
            "再生成适合课程演示的结构化数据。"
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
                "当前数据最值得补充什么字段？",
                "这些数据为什么不是纯随机生成？",
                "为什么同时采集电耗和水耗？",
            ],
        }

    if "异常" in question_text:
        anomalies = build_anomaly_summary(scoped_dataset)
        count = len(anomalies)
        if count == 0:
            answer = "当前筛选范围内没有识别到明显异常记录。"
        else:
            latest = anomalies[0]
            scope = target_building or "当前样例数据"
            answer = (
                f"{scope} 共识别到 {count} 条近期异常。最近一条发生在 {latest['timestamp']}，"
                f"建筑为 {latest['building_name']}，设备 {latest['equipment_id']}，"
                f"位置 {latest['floor_label']} {latest['zone_name']}，原因是“{latest['anomaly_reason']}”。"
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
                "生成当前异常处置建议",
                "科研实验楼D哪一层异常最多？",
                "继续查看 COP 排名和异常原因分布",
            ],
        }

    if _has_any(question_text, ["维护", "保养", "巡检", "冷却塔", "冷水机组", "空气处理机组", "风机盘管", "ahu", "ch", "ct", "fcu"]):
        answer = (
            "当前知识库整理了 AHU、冷水机组、冷却塔和风机盘管四类设备的日常巡检、每周检查、"
            "每月保养和常见故障处理表。若关注制冷效率下降，优先看冷水机组与冷却塔；"
            "若是教学楼深夜高电耗，优先排查 AHU 是否未按排程关机。"
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
                "冷却塔应该多久维护一次？",
                "制冷效率下降应该怎么排查？",
                "实验楼的 FCU 有哪些巡检重点？",
            ],
        }

    if "cop" in question_text or "能效" in question_text or "制冷效率" in question_text:
        ranking = build_cop_ranking(dataset)
        best = ranking[0] if ranking else None
        best_text = (
            f"目前 COP 最高的建筑是 {best['building_name']}，平均 COP 为 {best['average_cop']}。"
            if best
            else "当前没有足够数据生成建筑级 COP 排名。"
        )
        answer = (
            f"当前样例数据计算得到的整体平均 COP 为 {overview['average_cop']}。"
            f"按照知识库规则，COP 低于 2.5 应视为告警。{best_text}"
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
        if target_building == "科研实验楼D":
            answer = (
                "科研实验楼D 是当前样例数据里能耗最高的建筑。高能耗主要来自高功率实验设备、"
                "更严格的温湿度控制需求，以及风机盘管按房间独立调温带来的更高 HVAC 复杂度。"
            )
        elif target_building == "图书信息楼C":
            answer = (
                "图书信息楼C 的运行时间比教学楼和办公楼更长，并且存在 IT 设备底部负荷，"
                "因此夜间仍会保持一定电耗；冷却塔状态会直接影响它的 COP 表现。"
            )
        elif target_building == "行政办公楼B":
            answer = (
                "行政办公楼B 的能耗在四栋建筑中最低，主要因为办公时间窗口规律、夜间快速降载，"
                "整体更接近标准 Office 建筑的负荷曲线。"
            )
        elif target_building == "综合教学楼A":
            answer = (
                "综合教学楼A 的能耗呈明显教学时段波动，9:00 至 15:00 峰值最明显，"
                "异常通常出现在非工作时段 AHU 未及时关机。"
            )
        else:
            answer = (
                "当前 4 栋建筑的能耗差异明显：办公楼最规律，教学楼受课表影响最强，"
                "图书信息楼运行时段更长，实验楼整体能耗最高、波动也最大。"
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
                "哪栋建筑的电耗最高？",
                "为什么实验楼的能耗更高？",
                "各建筑应该怎样分别设置告警阈值？",
            ],
        }

    if "耗电" in question_text or "电耗" in question_text or "能耗" in question_text:
        answer = (
            f"当前样例数据覆盖 {overview['building_count']} 栋建筑、{overview['total_records']} 条记录，"
            f"总电耗为 {overview['totals'].get('electricity_kwh', 0)} kWh。"
            "这部分数据可用于数据浏览、趋势分析、建筑对比、楼层分析、设备监测、异常工单和智能问答演示。"
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
        answer = f"当前样例数据包含 {len(buildings)} 栋建筑，分别是：{_format_building_list(buildings)}。"
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
            "当前样例数据已经固定了建筑、时间、能耗、水耗、环境、占用率和设备状态相关字段。"
            "核心字段包括 building_id、timestamp、electricity_kwh、hvac_kwh、cooling_load_kwh、"
            "equipment_id 和 equipment_status。系统还会在分析阶段派生楼层、区域和设备类型。"
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
                "派生楼层字段是怎么来的？",
                "导出数据字典给组员",
            ],
        }

    if "模块" in question_text or "系统" in question_text:
        answer = (
            "当前系统分为数据管理、统计分析、楼层区域分析、设备监测、异常工单、优化建议和智能问答几个主模块。"
            "演示时建议按“总览 -> 数据筛选 -> 趋势和对比 -> 楼层/设备 -> 工单/建议 -> AI 问答”的顺序讲。"
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
                "演示时应该展示哪些内容？",
                "哪些功能最能体现业务逻辑？",
                "接口契约在哪里看？",
            ],
        }

    if "排名" in question_text or ("cop" in question_text and "建筑" in question_text):
        ranking = build_cop_ranking(dataset)
        if ranking:
            top = ranking[0]
            answer = f"当前样例数据里 COP 最高的建筑是 {top['building_name']}，平均 COP 为 {top['average_cop']}。"
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
            "当前问答模块可以回答数据来源、能耗概况、COP、异常诊断、楼层区域、设备维护、异常工单、"
            "优化建议和建筑类型差异。你可以直接问：科研实验楼D哪一层异常最多、哪些设备需要优先维护、"
            "生成当前异常处置建议、有什么节能优化建议。"
        ),
        "citations": _build_citations(
            [
                ("知识库入口", "knowledge_base/README.md"),
                ("问答素材库 Round 1", "knowledge_base/faq/qa_bank_round1.md"),
                ("技术方案", "docs/02-technical-solution.md"),
            ]
        ),
        "follow_up": [
            "科研实验楼D哪一层异常最多？",
            "哪些设备需要优先维护？",
            "生成当前异常处置建议",
        ],
    }
