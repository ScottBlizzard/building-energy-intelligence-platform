from __future__ import annotations

from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = ROOT / "final_docs" / "图象重绘" / "源代码"
IMAGE_DIR = ROOT / "final_docs" / "images"


def attr(value: str) -> str:
    return escape(value, quote=True).replace("\\n", "&#xa;").replace("\n", "&#xa;")


def html_value(value: str) -> str:
    return escape(value, quote=True)


class DrawioDoc:
    def __init__(self, title: str, width: int, height: int) -> None:
        self.title = title
        self.width = width
        self.height = height
        self.cells: list[str] = [
            '<mxCell id="0" />',
            '<mxCell id="1" parent="0" />',
        ]
        self.counter = 2

    def _id(self) -> str:
        value = f"id{self.counter}"
        self.counter += 1
        return value

    def vertex(self, value: str, style: str, x: int, y: int, w: int, h: int, cell_id: str | None = None) -> str:
        cid = cell_id or self._id()
        self.cells.append(
            f'<mxCell id="{cid}" value="{value}" style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />'
            f"</mxCell>"
        )
        return cid

    def edge(
        self,
        value: str,
        style: str,
        source: str | None = None,
        target: str | None = None,
        source_point: tuple[int, int] | None = None,
        target_point: tuple[int, int] | None = None,
        points: list[tuple[int, int]] | None = None,
    ) -> str:
        cid = self._id()
        attrs = [
            f'id="{cid}"',
            f'value="{value}"',
            f'style="{style}"',
            'edge="1"',
            'parent="1"',
        ]
        if source:
            attrs.append(f'source="{source}"')
        if target:
            attrs.append(f'target="{target}"')
        geometry = ['<mxGeometry relative="1" as="geometry">']
        if source_point:
            geometry.append(f'<mxPoint x="{source_point[0]}" y="{source_point[1]}" as="sourcePoint" />')
        if target_point:
            geometry.append(f'<mxPoint x="{target_point[0]}" y="{target_point[1]}" as="targetPoint" />')
        if points:
            geometry.append('<Array as="points">')
            for x, y in points:
                geometry.append(f'<mxPoint x="{x}" y="{y}" />')
            geometry.append("</Array>")
        geometry.append("</mxGeometry>")
        self.cells.append(f'<mxCell {" ".join(attrs)}>{"".join(geometry)}</mxCell>')
        return cid

    def xml(self) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<mxfile host="drawio" version="30.0.4">\n'
            f'  <diagram name="{attr(self.title)}">\n'
            f'    <mxGraphModel dx="{self.width}" dy="{self.height}" grid="1" gridSize="10" guides="1" '
            f'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
            f'pageWidth="{self.width}" pageHeight="{self.height}" math="0" shadow="0">\n'
            "      <root>\n"
            + "\n".join(f"        {cell}" for cell in self.cells)
            + "\n      </root>\n"
            "    </mxGraphModel>\n"
            "  </diagram>\n"
            "</mxfile>\n"
        )


CLASS_STYLE = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;"
    "fontColor=#111111;align=left;verticalAlign=top;fontSize=12;spacing=8;"
)
EDGE_STYLE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;"
    "html=1;endArrow=block;endFill=1;strokeColor=#333333;"
)
SEQ_LINE_STYLE = "html=1;endArrow=block;endFill=1;strokeColor=#111111;rounded=0;"
SEQ_RETURN_STYLE = "html=1;endArrow=open;dashed=1;strokeColor=#666666;rounded=0;"
SEQ_SELF_STYLE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;"
    "html=1;endArrow=block;endFill=1;strokeColor=#111111;"
)


def class_label(name: str, attrs: list[str], methods: list[str]) -> str:
    parts = [f'<div style="text-align:center"><b>{escape(name)}</b></div>']
    if attrs:
        parts.append("<hr>")
        parts.append('<div style="text-align:left">' + "<br>".join(escape(item) for item in attrs) + "</div>")
    if methods:
        parts.append("<hr>")
        parts.append('<div style="text-align:left">' + "<br>".join(escape(item) for item in methods) + "</div>")
    return html_value("".join(parts))


def write_class_diagram(
    file_stem: str,
    title: str,
    classes: list[dict],
    edges: list[tuple[str, str, str]],
    width: int = 980,
    height: int = 620,
) -> None:
    doc = DrawioDoc(title, width, height)
    title_style = "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=16;fontStyle=1;"
    doc.vertex(attr(title), title_style, 0, 15, width, 30)
    ids: dict[str, str] = {}
    for item in classes:
        ids[item["name"]] = doc.vertex(
            class_label(item["name"], item.get("attrs", []), item.get("methods", [])),
            CLASS_STYLE,
            item["x"],
            item["y"],
            item.get("w", 230),
            item.get("h", 130),
        )
    for source, target, label in edges:
        doc.edge("", EDGE_STYLE, ids[source], ids[target])
    (SOURCE_DIR / f"{file_stem}.drawio").write_text(doc.xml(), encoding="utf-8")
    (SOURCE_DIR / f"{file_stem}.md").write_text(class_plantuml(title, classes, edges), encoding="utf-8")


def class_plantuml(title: str, classes: list[dict], edges: list[tuple[str, str, str]]) -> str:
    lines = ["@startuml", f"title {title}", ""]
    for item in classes:
        lines.append(f"class {item['name']} {{")
        for field in item.get("attrs", []):
            lines.append(f"  {field}")
        for method in item.get("methods", []):
            lines.append(f"  {method}")
        lines.append("}")
        lines.append("")
    for source, target, label in edges:
        lines.append(f"{source} --> {target}")
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def write_flow_diagram(file_stem: str, title: str) -> None:
    doc = DrawioDoc(title, 1160, 660)
    title_style = "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=16;fontStyle=1;"
    process_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=13;"
    store_style = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#e8e8f4;strokeColor=#6b6b82;fontSize=13;"
    output_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=13;"
    edge_style = EDGE_STYLE
    doc.vertex(attr(title), title_style, 0, 15, 1160, 30)
    source = doc.vertex(attr("CSV / MySQL\nenergy_readings"), store_style, 40, 220, 130, 90)
    load = doc.vertex(attr("data_loader\nread_dataset"), process_style, 225, 225, 150, 70)
    filtr = doc.vertex(attr("get_filtered_dataset\n建筑/时间/limit"), process_style, 430, 225, 170, 70)
    sim = doc.vertex(attr("simulation_service\n窗口/干预"), process_style, 660, 225, 160, 70)
    enrich = doc.vertex(attr("analysis_service\nbuild_analysis_frame"), process_style, 890, 225, 180, 70)
    charts = doc.vertex(attr("KPI / 趋势 / 对比\nCOP / 楼层 / 设备"), output_style, 250, 430, 190, 80)
    anomaly = doc.vertex(attr("异常列表\n异常解释"), output_style, 480, 430, 150, 80)
    drafts = doc.vertex(attr("异常工单草稿"), output_style, 670, 430, 150, 80)
    report = doc.vertex(attr("运营报告 / MCP\nAI 接地上下文"), output_style, 860, 430, 180, 80)
    export = doc.vertex(attr("CSV 导出\nexport_service"), output_style, 475, 80, 170, 70)
    for a, b in [(source, load), (load, filtr), (filtr, sim), (sim, enrich)]:
        doc.edge("", edge_style, a, b)
    doc.edge("", edge_style, filtr, export)
    for out, waypoint_x in [(charts, 350), (anomaly, 555), (drafts, 745), (report, 950)]:
        doc.edge("", edge_style, enrich, out, points=[(980, 350), (waypoint_x, 350)])
    (SOURCE_DIR / f"{file_stem}.drawio").write_text(doc.xml(), encoding="utf-8")
    (SOURCE_DIR / f"{file_stem}.md").write_text(
        "\n".join(
            [
                "@startuml",
                f"title {title}",
                "start",
                ":CSV / MySQL energy_readings;",
                ":data_loader.read_dataset();",
                ":get_filtered_dataset(building, start, end, limit);",
                ":simulation_service.apply_window/apply_interventions;",
                ":analysis_service.build_analysis_frame();",
                "fork",
                "  :KPI / 趋势 / 对比 / COP;",
                "fork again",
                "  :异常列表 / 异常解释 / 工单草稿;",
                "fork again",
                "  :运营报告 / MCP / AI 接地上下文;",
                "end fork",
                "stop",
                "@enduml",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_sequence_diagram(
    file_stem: str,
    title: str,
    participants: list[dict],
    messages: list[dict],
    width: int,
    height: int,
) -> None:
    doc = DrawioDoc(title, width, height)
    title_style = "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=16;fontStyle=1;"
    header_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#e8e8f4;strokeColor=#6b6b82;fontSize=13;"
    db_style = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#e8e8f4;strokeColor=#6b6b82;fontSize=13;"
    actor_style = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#f5f5f5;strokeColor=#666666;fontSize=13;"
    line_style = "endArrow=none;dashed=1;html=1;strokeColor=#888888;"
    activation_style = "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#333333;"
    doc.vertex(attr(title), title_style, 0, 15, width, 30)
    ids: dict[str, str] = {}
    centers: dict[str, int] = {}
    top_y, bottom_y = 115, height - 55
    for index, part in enumerate(participants):
        x = part.get("x", 45 + index * 165)
        centers[part["id"]] = x + 60
        if part.get("type") == "actor":
            ids[part["id"]] = doc.vertex(attr(part["label"]), actor_style, x + 25, 55, 70, 70)
        elif part.get("type") == "database":
            ids[part["id"]] = doc.vertex(attr(part["label"]), db_style, x + 20, 58, 80, 62)
        else:
            ids[part["id"]] = doc.vertex(attr(part["label"]), header_style, x, 72, 120, 34)
        doc.edge("", line_style, source_point=(centers[part["id"]], top_y), target_point=(centers[part["id"]], bottom_y))
        if part.get("footer", True):
            if part.get("type") == "actor":
                doc.vertex(attr(part["label"]), actor_style, x + 25, bottom_y - 25, 70, 70)
            elif part.get("type") == "database":
                doc.vertex(attr(part["label"]), db_style, x + 20, bottom_y - 25, 80, 62)
            else:
                doc.vertex(attr(part["label"]), header_style, x, bottom_y + 5, 120, 34)

    for msg in messages:
        y = msg["y"]
        source = centers[msg["from"]]
        target = centers[msg["to"]]
        if msg["from"] == msg["to"]:
            doc.edge(
                attr(msg["label"]),
                SEQ_SELF_STYLE,
                source_point=(source, y),
                target_point=(target, y + 35),
                points=[(source + 52, y), (source + 52, y + 35)],
            )
        else:
            style = SEQ_RETURN_STYLE if msg.get("return") else SEQ_LINE_STYLE
            doc.edge(attr(msg["label"]), style, source_point=(source, y), target_point=(target, y))
        if msg.get("activate"):
            ax = target - 6
            doc.vertex("", activation_style, ax, y + 3, 12, msg.get("activation_h", 52))

    (SOURCE_DIR / f"{file_stem}.drawio").write_text(doc.xml(), encoding="utf-8")
    (SOURCE_DIR / f"{file_stem}.md").write_text(sequence_plantuml(title, participants, messages), encoding="utf-8")


def sequence_plantuml(title: str, participants: list[dict], messages: list[dict]) -> str:
    lines = ["@startuml", f"title {title}", ""]
    for part in participants:
        kind = "actor" if part.get("type") == "actor" else "database" if part.get("type") == "database" else "participant"
        lines.append(f'{kind} "{part["label"]}" as {part["id"]}')
    lines.append("")
    for msg in messages:
        arrow = "-->" if msg.get("return") else "->"
        lines.append(f'{msg["from"]} {arrow} {msg["to"]} : {msg["label"]}')
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    write_flow_diagram(
        "SDD-5.1.2-数据分析处理流程图",
        "数据分析处理流程图",
    )

    write_class_diagram(
        "SDD-5.1.3-数据与分析核心类图",
        "数据与分析子系统核心类图",
        [
            {"name": "DataLoader", "x": 40, "y": 90, "attrs": ["- dataset_cache"], "methods": ["+ read_dataset()", "+ get_filtered_dataset()", "+ get_dataset_meta()"]},
            {"name": "AnalysisService", "x": 375, "y": 90, "attrs": ["- baseline_rules", "- risk_formula"], "methods": ["+ build_analysis_frame()", "+ build_overview()", "+ build_anomaly_summary()", "+ build_operation_report()"], "w": 250, "h": 155},
            {"name": "ExportService", "x": 720, "y": 90, "methods": ["+ build_csv_content()", "+ build_export_filename()"]},
            {"name": "SimulationService", "x": 40, "y": 325, "methods": ["+ apply_window()", "+ apply_interventions()"]},
            {"name": "AnalysisFrame", "x": 375, "y": 325, "attrs": ["+ floor_label", "+ equipment_type", "+ risk_score", "+ business_impact"]},
            {"name": "OperationReport", "x": 720, "y": 325, "attrs": ["+ energy_summary", "+ anomaly_summary", "+ work_order_summary", "+ decision_summary"]},
        ],
        [
            ("DataLoader", "SimulationService", "applies"),
            ("AnalysisService", "DataLoader", "reads"),
            ("AnalysisService", "AnalysisFrame", "builds"),
            ("AnalysisService", "OperationReport", "builds"),
            ("ExportService", "AnalysisService", "uses display frame"),
        ],
    )

    write_class_diagram(
        "SDD-5.2.2-工单核心类图",
        "工单与权限子系统核心类图",
        [
            {"name": "WorkOrder", "x": 40, "y": 120, "attrs": ["- work_order_id", "- source_record_id", "- equipment_id", "- status", "- assignee_id", "- timeline"], "w": 230, "h": 165},
            {"name": "WorkOrderStore", "x": 365, "y": 95, "methods": ["+ list_work_orders()", "+ create_work_order()", "+ assign_work_order()", "+ accept_work_order()", "+ submit_work_order()", "+ review_work_order()", "+ ignore_work_order()"], "w": 255, "h": 190},
            {"name": "PermissionService", "x": 720, "y": 95, "methods": ["+ require_admin_operator()", "+ require_worker_operator()", "+ build_worker_support()"], "w": 240, "h": 145},
            {"name": "TimelineEvent", "x": 40, "y": 370, "attrs": ["+ action", "+ operator_id", "+ at", "+ note"]},
            {"name": "WorkerSupport", "x": 365, "y": 370, "attrs": ["+ active_orders", "+ standard_guidance", "+ similar_cases"]},
            {"name": "SimulationService", "x": 720, "y": 370, "methods": ["+ register_intervention()"]},
        ],
        [
            ("WorkOrderStore", "WorkOrder", "manages"),
            ("WorkOrder", "TimelineEvent", "contains"),
            ("WorkOrderStore", "PermissionService", "checks"),
            ("PermissionService", "WorkerSupport", "builds"),
            ("WorkOrderStore", "SimulationService", "registers repair"),
        ],
    )

    write_class_diagram(
        "SDD-5.3.4-时间沙盘与决策核心类图",
        "时间沙盘与决策子系统核心类图",
        [
            {"name": "SimulationService", "x": 365, "y": 80, "methods": ["+ get_state()", "+ start_simulation()", "+ advance_day()", "+ register_intervention()", "+ apply_window()", "+ apply_interventions()"], "w": 260, "h": 180},
            {"name": "SimulationState", "x": 55, "y": 320, "attrs": ["+ active", "+ current_date", "+ start_date", "+ interventions"]},
            {"name": "ScenarioService", "x": 365, "y": 320, "methods": ["+ build_counterfactual_scenarios()"]},
            {"name": "DecisionService", "x": 675, "y": 320, "methods": ["+ rank_open_work_orders()", "+ recommend_dispatch_plan()", "+ worker_status_overview()"], "w": 255, "h": 135},
            {"name": "WorkOrderStore", "x": 675, "y": 80, "methods": ["+ list_work_orders()", "+ review_work_order()"]},
            {"name": "DispatchPlan", "x": 365, "y": 500, "attrs": ["+ selected", "+ deferred", "+ worker_status", "+ summary"]},
        ],
        [
            ("SimulationService", "SimulationState", "persists"),
            ("ScenarioService", "SimulationService", "uses state"),
            ("DecisionService", "WorkOrderStore", "reads"),
            ("DecisionService", "DispatchPlan", "builds"),
            ("WorkOrderStore", "SimulationService", "registers intervention"),
        ],
        height=680,
    )

    write_class_diagram(
        "SDD-5.4.4-预算ROI核心类图",
        "预算与 ROI 子系统核心类图",
        [
            {"name": "BudgetService", "x": 40, "y": 90, "methods": ["+ auto_generate_budgets()", "+ set_budget()", "+ build_budget_analysis()", "+ build_budget_kpi()"], "w": 260, "h": 160},
            {"name": "DecisionService", "x": 365, "y": 90, "methods": ["+ summarize_budget_impact_from_closures()", "+ find_roi_candidates_from_repeated_anomalies()"], "w": 290, "h": 130},
            {"name": "ROIService", "x": 720, "y": 90, "methods": ["+ build_equipment_audit()", "+ analyze_roi_project()", "+ compare_scenarios()"], "w": 245, "h": 145},
            {"name": "Budget", "x": 40, "y": 330, "attrs": ["+ building_id", "+ year", "+ month", "+ budget_kwh"]},
            {"name": "BudgetAnalysis", "x": 285, "y": 330, "attrs": ["+ execution_rate", "+ forecast_rate", "+ risk_level"]},
            {"name": "EquipmentAudit", "x": 530, "y": 330, "attrs": ["+ equipment_type", "+ sample_count", "+ current_cop"]},
            {"name": "ROIProject", "x": 775, "y": 330, "attrs": ["+ investment", "+ npv", "+ irr", "+ eaa", "+ payback"]},
        ],
        [
            ("BudgetService", "Budget", "persists"),
            ("BudgetService", "BudgetAnalysis", "builds"),
            ("DecisionService", "BudgetAnalysis", "uses"),
            ("DecisionService", "EquipmentAudit", "candidates"),
            ("ROIService", "EquipmentAudit", "audits"),
            ("ROIService", "ROIProject", "calculates"),
        ],
        width=1040,
    )

    write_class_diagram(
        "SDD-5.5.2-核心服务子系统类图",
        "智能服务子系统核心类图",
        [
            {"name": "MCPServer", "x": 380, "y": 70, "methods": ["+ ask_energy_assistant()", "+ search_energy_knowledge()"]},
            {"name": "AssistantService", "x": 365, "y": 220, "methods": ["+ build_assistant_reply(question)"], "w": 260, "h": 110},
            {"name": "GroundingService", "x": 40, "y": 420, "methods": ["+ classify_assistant_question()", "+ build_work_order_grounding_context()", "+ validate_grounded_answer()"], "w": 290, "h": 145},
            {"name": "KnowledgeSearchService", "x": 365, "y": 420, "methods": ["+ search_knowledge()", "+ search_and_format_citations()"], "w": 280, "h": 125},
            {"name": "LLMClient", "x": 700, "y": 420, "methods": ["+ list_llm_model_options()", "+ build_external_assistant_answer()"], "w": 275, "h": 125},
        ],
        [
            ("MCPServer", "AssistantService", "calls"),
            ("AssistantService", "GroundingService", "grounds"),
            ("AssistantService", "KnowledgeSearchService", "retrieves"),
            ("AssistantService", "LLMClient", "enhances"),
        ],
        width=1040,
        height=650,
    )

    write_class_diagram(
        "SDD-5.6.3-前端展示核心组件类图",
        "前端展示子系统核心组件类图",
        [
            {"name": "DashboardView", "x": 385, "y": 80, "attrs": ["- currentUser", "- activeTab", "- simClock", "- analytics", "- workOrderState"], "methods": ["+ bootstrapAuthenticatedApp()", "+ refreshBusinessState()", "+ handleAsk()", "+ handleExport()"], "w": 275, "h": 180},
            {"name": "ApiClient", "x": 40, "y": 350, "methods": ["+ request()", "+ setApiOperator()", "+ buildApiUrl()"]},
            {"name": "StateStores", "x": 385, "y": 350, "attrs": ["+ loading", "+ errors", "+ decisionState", "+ assistantReply"]},
            {"name": "BusinessPanels", "x": 705, "y": 350, "methods": ["+ BudgetPanel", "+ ROIPanel", "+ AssistantPanel"]},
            {"name": "VisualizationComponents", "x": 40, "y": 520, "methods": ["+ TrendChart", "+ BuildingComparisonChart", "+ BuildingRiskScene"]},
            {"name": "TableAndFeedback", "x": 705, "y": 520, "methods": ["+ DataTable", "+ StatusBanner", "+ EmptyState", "+ LoadingSpinner"]},
        ],
        [
            ("DashboardView", "ApiClient", "calls"),
            ("DashboardView", "StateStores", "updates"),
            ("DashboardView", "BusinessPanels", "renders"),
            ("DashboardView", "VisualizationComponents", "renders"),
            ("DashboardView", "TableAndFeedback", "renders"),
        ],
        width=1040,
        height=720,
    )

    write_sequence_diagram(
        "SDD-5.3.2-关闭工单影响未来时序图",
        "管理员关闭工单并影响未来",
        [
            {"id": "Admin", "label": "管理员", "type": "actor", "x": 35},
            {"id": "API", "label": "WorkOrder API", "x": 190},
            {"id": "Store", "label": "work_order_store", "type": "database", "x": 365},
            {"id": "Sim", "label": "simulation_service", "x": 575},
            {"id": "Data", "label": "data_loader/analysis", "x": 740},
            {"id": "UI", "label": "前端报告", "x": 910},
        ],
        [
            {"from": "Admin", "to": "API", "label": "PATCH /work-orders/{id}/review\\napproved=true", "y": 155, "activate": True, "activation_h": 120},
            {"from": "API", "to": "Store", "label": "review_work_order()", "y": 205, "activate": True, "activation_h": 210},
            {"from": "Store", "to": "Store", "label": "状态置为 closed\\n写入 timeline", "y": 250},
            {"from": "Store", "to": "Sim", "label": "register_intervention(equipment_id)", "y": 320, "activate": True, "activation_h": 58},
            {"from": "Sim", "to": "Sim", "label": "保存维修干预", "y": 365},
            {"from": "Admin", "to": "API", "label": "POST /sim/advance", "y": 455, "activate": True, "activation_h": 90},
            {"from": "API", "to": "Sim", "label": "advance_day()", "y": 495, "activate": True, "activation_h": 120},
            {"from": "UI", "to": "Data", "label": "查询未来可见数据", "y": 555, "activate": True, "activation_h": 75},
            {"from": "Data", "to": "Sim", "label": "apply_interventions()", "y": 600, "activate": True, "activation_h": 40},
            {"from": "Data", "to": "UI", "label": "已修复设备异常减少", "y": 655, "return": True},
        ],
        width=1080,
        height=780,
    )

    write_sequence_diagram(
        "SDD-5.3.2-资源约束派单时序图",
        "资源约束派单",
        [
            {"id": "Admin", "label": "管理员", "type": "actor", "x": 35},
            {"id": "Decision", "label": "decision_service", "x": 235},
            {"id": "Store", "label": "work_order_store", "type": "database", "x": 455},
            {"id": "Auth", "label": "auth_service", "x": 670},
            {"id": "UI", "label": "管理员界面", "x": 865},
        ],
        [
            {"from": "Admin", "to": "Decision", "label": "GET /decisions/dispatch-plan", "y": 160, "activate": True, "activation_h": 250},
            {"from": "Decision", "to": "Store", "label": "list_work_orders()", "y": 225, "activate": True, "activation_h": 70},
            {"from": "Decision", "to": "Auth", "label": "list_demo_users()", "y": 315, "activate": True, "activation_h": 70},
            {"from": "Decision", "to": "Decision", "label": "计算忙闲、风险、损失、SLA、碳排", "y": 410},
            {"from": "Decision", "to": "UI", "label": "selected + deferred + summary", "y": 505, "return": True},
        ],
        width=1060,
        height=650,
    )

    write_sequence_diagram(
        "SDD-5.2.3-工单派单处理复核时序图",
        "管理员派单、工人提交、管理员复核",
        [
            {"id": "Admin", "label": "管理员", "type": "actor", "x": 35},
            {"id": "Worker", "label": "工人", "type": "actor", "x": 190},
            {"id": "API", "label": "WorkOrder API", "x": 355},
            {"id": "Perm", "label": "permission_service", "x": 525},
            {"id": "Store", "label": "work_order_store", "type": "database", "x": 725},
            {"id": "Sim", "label": "simulation_service", "x": 925},
        ],
        [
            {"from": "Admin", "to": "API", "label": "POST /work-orders 或 PATCH /assign", "y": 155, "activate": True, "activation_h": 90},
            {"from": "API", "to": "Perm", "label": "require_admin_operator()", "y": 205, "activate": True, "activation_h": 45},
            {"from": "API", "to": "Store", "label": "create/assign_work_order()", "y": 260, "activate": True, "activation_h": 330},
            {"from": "Store", "to": "Store", "label": "校验同设备工单与工人忙闲锁", "y": 315},
            {"from": "Store", "to": "Admin", "label": "assigned 工单", "y": 380, "return": True},
            {"from": "Worker", "to": "API", "label": "PATCH /accept", "y": 445, "activate": True, "activation_h": 45},
            {"from": "API", "to": "Store", "label": "accept_work_order()", "y": 490},
            {"from": "Worker", "to": "API", "label": "PATCH /submit", "y": 545, "activate": True, "activation_h": 45},
            {"from": "API", "to": "Store", "label": "submit_work_order(...)", "y": 590},
            {"from": "Store", "to": "Admin", "label": "pending_review 工单", "y": 645, "return": True},
            {"from": "Admin", "to": "API", "label": "PATCH /review approved=true", "y": 700, "activate": True, "activation_h": 45},
            {"from": "API", "to": "Store", "label": "review_work_order()", "y": 745},
            {"from": "Store", "to": "Sim", "label": "register_intervention(equipment_id)", "y": 800, "activate": True, "activation_h": 50},
            {"from": "Store", "to": "Admin", "label": "closed 工单和 timeline", "y": 865, "return": True},
        ],
        width=1120,
        height=990,
    )

    write_sequence_diagram(
        "SDD-5.2.3-自动待确认队列时序图",
        "自动待确认队列",
        [
            {"id": "Admin", "label": "管理员", "type": "actor", "x": 40},
            {"id": "API", "label": "/work-orders/auto-confirm", "x": 245},
            {"id": "Analysis", "label": "analysis_service", "x": 505},
            {"id": "Store", "label": "work_order_store", "type": "database", "x": 745},
        ],
        [
            {"from": "Admin", "to": "API", "label": "POST /work-orders/auto-confirm", "y": 160, "activate": True, "activation_h": 220},
            {"from": "API", "to": "Analysis", "label": "build_anomaly_work_order_drafts()", "y": 235, "activate": True, "activation_h": 65},
            {"from": "API", "to": "Store", "label": "create_pending_confirm_drafts()", "y": 325, "activate": True, "activation_h": 120},
            {"from": "Store", "to": "Store", "label": "跳过同设备未关闭工单和已修复设备", "y": 395},
            {"from": "Store", "to": "Admin", "label": "created / skipped / total", "y": 485, "return": True},
        ],
        width=980,
        height=630,
    )

    write_sequence_diagram(
        "SDD-5.4.3-预算生成闭环改善与ROI候选时序图",
        "预算生成、闭环改善与 ROI 候选",
        [
            {"id": "Admin", "label": "管理员", "type": "actor", "x": 30},
            {"id": "Budget", "label": "budget_service", "x": 205},
            {"id": "Decision", "label": "decision_service", "x": 385},
            {"id": "ROI", "label": "roi_service", "x": 565},
            {"id": "Analysis", "label": "analysis_service", "x": 745},
            {"id": "Store", "label": "work_order_store", "type": "database", "x": 925},
        ],
        [
            {"from": "Admin", "to": "Budget", "label": "POST /budget/budgets/generate", "y": 155, "activate": True, "activation_h": 170},
            {"from": "Budget", "to": "Analysis", "label": "读取沙盘可见数据", "y": 220, "activate": True, "activation_h": 55},
            {"from": "Budget", "to": "Admin", "label": "月度预算列表", "y": 315, "return": True},
            {"from": "Admin", "to": "Decision", "label": "GET /decisions/budget-impact", "y": 385, "activate": True, "activation_h": 230},
            {"from": "Decision", "to": "Store", "label": "list_work_orders(status=closed)", "y": 450, "activate": True, "activation_h": 55},
            {"from": "Decision", "to": "Admin", "label": "节省与预测改善", "y": 525, "return": True},
            {"from": "Admin", "to": "Decision", "label": "GET /decisions/roi-candidates", "y": 595},
            {"from": "Decision", "to": "Analysis", "label": "识别重复异常设备", "y": 650},
            {"from": "Decision", "to": "Admin", "label": "改造候选池", "y": 715, "return": True},
            {"from": "Admin", "to": "ROI", "label": "POST /roi/analyze", "y": 780, "activate": True, "activation_h": 70},
            {"from": "ROI", "to": "Admin", "label": "NPV / IRR / EAA / 回收期 / 敏感性", "y": 845, "return": True},
        ],
        width=1100,
        height=970,
    )

    write_sequence_diagram(
        "SDD-5.5.3-智能问答服务时序图",
        "智能问答服务交互",
        [
            {"id": "User", "label": "用户/MCP客户端", "type": "actor", "x": 30},
            {"id": "API", "label": "Assistant API / MCP Tool", "x": 215},
            {"id": "Local", "label": "assistant_service", "x": 435},
            {"id": "KB", "label": "knowledge_search_service", "x": 635},
            {"id": "Ground", "label": "grounding_service", "x": 855},
            {"id": "LLM", "label": "llm_client", "x": 1055},
        ],
        [
            {"from": "User", "to": "API", "label": "question + provider/model", "y": 155, "activate": True, "activation_h": 350},
            {"from": "API", "to": "Local", "label": "build_assistant_reply(question)", "y": 220, "activate": True, "activation_h": 55},
            {"from": "API", "to": "KB", "label": "search_and_format_citations(question)", "y": 295, "activate": True, "activation_h": 55},
            {"from": "API", "to": "Ground", "label": "build_work_order_grounding_context(question)", "y": 370, "activate": True, "activation_h": 55},
            {"from": "API", "to": "LLM", "label": "build_external_assistant_answer(...)", "y": 445, "activate": True, "activation_h": 70},
            {"from": "LLM", "to": "API", "label": "external_answer 或失败", "y": 520, "return": True},
            {"from": "API", "to": "Ground", "label": "validate_grounded_answer() / fallback", "y": 590, "activate": True, "activation_h": 55},
            {"from": "API", "to": "User", "label": "AssistantResponse", "y": 675, "return": True},
        ],
        width=1220,
        height=800,
    )


if __name__ == "__main__":
    main()
