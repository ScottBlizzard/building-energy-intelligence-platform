from typing import Dict, List

from app.services.analysis_service import (
    build_anomaly_summary,
    build_cop_ranking,
    build_overview,
)
from app.services.data_loader import get_building_options, read_dataset


def _citation(title: str, path: str) -> Dict[str, str]:
    return {"title": title, "path": path}


def build_assistant_reply(question: str) -> Dict[str, List]:
    dataset = read_dataset()
    overview = build_overview(dataset)
    buildings = get_building_options()
    question_text = question.lower()

    if "异常" in question_text:
        anomalies = build_anomaly_summary(dataset)
        count = len(anomalies)
        if count == 0:
            answer = "当前样例数据中没有识别到明显异常记录。后续可以补充阈值规则和更细的设备级分析。"
        else:
            latest = anomalies[0]
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
            "citations": [
                _citation("运维手册占位", "knowledge_base/manuals/operation_guide.md"),
                _citation("常见问题示例", "knowledge_base/faq/typical_questions.md"),
            ],
            "follow_up": [
                "继续查看异常明细列表",
                "增加按建筑筛选的异常分析",
                "接入大模型后补充异常原因解释",
            ],
        }

    if "cop" in question_text or "能效" in question_text:
        answer = "当前样例数据计算得到的整体平均 COP 为 {0}。后续应按建筑、时段和设备进一步分层分析。".format(
            overview["average_cop"]
        )
        return {
            "answer": answer,
            "citations": [
                _citation("能耗术语表", "knowledge_base/glossary/energy_terms.md")
            ],
            "follow_up": [
                "查看分建筑 COP 对比",
                "按日统计 COP 趋势",
                "补充 COP 计算公式说明",
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
            "citations": [
                _citation("样例数据字典", "data/dictionaries/energy_records_dictionary.csv")
            ],
            "follow_up": [
                "按时间查看能耗汇总",
                "按建筑对比电耗",
                "导出筛选后的原始记录",
            ],
        }

    if "建筑" in question_text:
        answer = "当前样例数据包含 {0} 栋建筑，分别是：{1}。".format(
            len(buildings),
            "、".join(item["building_name"] for item in buildings),
        )
        return {
            "answer": answer,
            "citations": [
                _citation("样例数据字典", "data/dictionaries/energy_records_dictionary.csv")
            ],
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
            "citations": [
                _citation("数据字典", "data/dictionaries/energy_records_dictionary.csv")
            ],
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
            "citations": [
                _citation("需求分析", "docs/01-requirements.md"),
                _citation("协作规则", "docs/07-collaboration-rules.md"),
            ],
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
            "citations": [
                _citation("能耗术语表", "knowledge_base/glossary/energy_terms.md")
            ],
            "follow_up": [
                "查看完整 COP 排名",
                "解释 COP 计算方式",
                "按时间查看 COP 趋势",
            ],
        }

    return {
        "answer": (
            "当前问答模块还是规则化占位实现，已经预留出后续接入知识库和大模型的结构。"
            "你可以先询问能耗概况、COP 或异常分析相关问题。"
        ),
        "citations": [
            _citation("知识库入口", "knowledge_base/README.md"),
            _citation("技术方案", "docs/02-technical-solution.md"),
        ],
        "follow_up": [
            "系统当前有哪些模块",
            "样例数据里有哪些字段",
            "后续如何接入 RAG",
        ],
    }
