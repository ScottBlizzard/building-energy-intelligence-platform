# -*- coding: utf-8 -*-
from pathlib import Path

OUT = Path(__file__).resolve().parent


def attr(value):
    text = str(value)
    parts = []
    for ch in text:
        code = ord(ch)
        if ch == "&":
            parts.append("&amp;")
        elif ch == "<":
            parts.append("&lt;")
        elif ch == ">":
            parts.append("&gt;")
        elif ch == '"':
            parts.append("&quot;")
        elif ch == "\n":
            parts.append("&#xa;")
        elif code > 127:
            parts.append(f"&#x{code:X};")
        else:
            parts.append(ch)
    return "".join(parts)


class Diagram:
    def __init__(self, name, width=1000, height=700):
        self.name = name
        self.width = width
        self.height = height
        self.cells = []
        self.n = 2

    def nid(self, prefix="c"):
        value = f"{prefix}{self.n}"
        self.n += 1
        return value

    def vertex(self, value, style, x, y, w, h, id=None):
        id = id or self.nid()
        self.cells.append(
            f'<mxCell id="{id}" value="{attr(value)}" style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" /></mxCell>'
        )
        return id

    def edge(self, source, target, value="", style=None, points=None):
        id = self.nid("e")
        style = style or "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#666666;"
        if points:
            pts = "".join(f'<mxPoint x="{x}" y="{y}" />' for x, y in points)
            geometry = f'<mxGeometry relative="1" as="geometry"><Array as="points">{pts}</Array></mxGeometry>'
        else:
            geometry = '<mxGeometry relative="1" as="geometry" />'
        self.cells.append(
            f'<mxCell id="{id}" value="{attr(value)}" style="{style}" edge="1" parent="1" source="{source}" target="{target}">{geometry}</mxCell>'
        )
        return id

    def write(self, path):
        body = "\n        ".join(self.cells)
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="drawio" version="26.0.0">
  <diagram name="{attr(self.name)}">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.width}" pageHeight="{self.height}" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        {body}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
'''
        path.write_text(xml, encoding="utf-8")


STYLE = {
    "title": "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=20;fontStyle=1;",
    "actor": "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#ffffff;strokeColor=#333333;",
    "boundary": "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#666666;dashed=1;fontStyle=1;align=center;verticalAlign=top;spacingTop=8;",
    "usecase": "ellipse;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=13;",
    "secondary": "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=12;",
    "lane": "swimlane;startSize=34;html=1;horizontal=0;fillColor=#f5f5f5;strokeColor=#666666;fontStyle=1;",
    "process": "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=12;",
    "decision": "rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=12;",
    "start": "ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=12;",
    "end": "ellipse;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=12;",
}


def make_usecase(code, title, primaries, secondaries):
    width, height = 1120, max(520, 180 + max(len(primaries), len(secondaries)) * 105)
    d = Diagram(f"{code} UML用例图", width, height)
    d.vertex(f"{code} {title} - UML用例图", STYLE["title"], 20, 20, width - 40, 34)
    d.vertex("建筑能源智能管理与运维优化系统", STYLE["boundary"], 220, 90, 520, height - 150)
    uc = d.vertex(f"{code}\n{title}", STYLE["usecase"], 385, 230, 190, 82)
    for i, label in enumerate(["登录/权限校验", "记录操作日志"]):
        support = d.vertex(
            label,
            STYLE["usecase"].replace("#dae8fc", "#e1d5e7").replace("#6c8ebf", "#9673a6"),
            370 + i * 210,
            370,
            170,
            58,
        )
        d.edge(uc, support, "<<include>>", "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;dashed=1;endArrow=open;strokeColor=#9673a6;")
    for i, actor in enumerate(primaries):
        actor_id = d.vertex(actor, STYLE["actor"], 60, 130 + i * 120, 90, 100)
        d.edge(actor_id, uc, "", "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=none;strokeColor=#333333;")
    for i, sec in enumerate(secondaries):
        sec_id = d.vertex(sec, STYLE["secondary"], 810, 110 + i * 88, 230, 56)
        d.edge(uc, sec_id, "<<include>>", "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;dashed=1;endArrow=open;strokeColor=#666666;")
    d.write(OUT / f"{code.lower()}_usecase.drawio")


def n(id, lane, y, label, type="process", w=170, h=54):
    return {"id": id, "lane": lane, "y": y, "label": label, "type": type, "w": w, "h": h}


def make_swimlane(code, title, lanes, nodes, edges):
    lane_w = 240
    x0 = 40
    top = 78
    max_y = max(node["y"] for node in nodes) + 170
    width = x0 * 2 + lane_w * len(lanes)
    height = max(620, max_y + 70)
    d = Diagram(f"{code} UML泳道活动图", width, height)
    d.vertex(f"{code} {title} - UML泳道活动图", STYLE["title"], 20, 20, width - 40, 34)
    for i, lane in enumerate(lanes):
        d.vertex(lane, STYLE["lane"], x0 + i * lane_w, top, lane_w, height - top - 40)
    ids = {}
    for node in nodes:
        w = node.get("w", 170)
        h = node.get("h", 54)
        x = x0 + node["lane"] * lane_w + (lane_w - w) / 2
        ids[node["id"]] = d.vertex(node["label"], STYLE[node.get("type", "process")], x, node["y"], w, h)
    for edge in edges:
        d.edge(ids[edge[0]], ids[edge[1]], edge[2] if len(edge) > 2 else "", edge[3] if len(edge) > 3 else None)
    d.write(OUT / f"{code.lower()}_swimlane.drawio")


def main():
    usecases = [
        ("UC-00", "用户登录与权限管理", ["所有用户", "系统管理员"], ["认证与权限服务", "前端路由守卫"]),
        ("UC-01", "管理样例数据与演示状态", ["系统管理员", "数据维护者"], ["数据加载与查询服务", "持久化存储", "可信问答引擎"]),
        ("UC-02", "查看能源总览与数据查询", ["能源运营管理员", "AI客户端"], ["数据加载与查询服务", "沙盘服务引擎", "MCP Server"]),
        ("UC-03", "统计分析与异常诊断", ["能源运营管理员", "AI客户端"], ["异常分析引擎", "数据加载与查询服务", "沙盘服务引擎"]),
        ("UC-04", "派发维修工单", ["能源运营管理员"], ["异常分析引擎", "工单状态机引擎", "认证与权限服务", "持久化存储"]),
        ("UC-05", "处理现场工单", ["现场工人"], ["认证与权限服务", "工单状态机引擎", "持久化存储"]),
        ("UC-06", "复核关闭工单", ["能源运营管理员"], ["工单状态机引擎", "沙盘服务引擎", "预算与ROI决策引擎", "持久化存储"]),
        ("UC-07", "时间沙盘与反事实", ["能源运营管理员"], ["沙盘服务引擎", "异常分析引擎", "工单状态机引擎", "预算与ROI决策引擎"]),
        ("UC-08", "预算执行与闭环改善", ["能源运营管理员"], ["预算与ROI决策引擎", "工单状态机引擎", "沙盘服务引擎", "持久化存储"]),
        ("UC-09", "ROI改造与运营报告", ["能源运营管理员"], ["预算与ROI决策引擎", "异常分析引擎", "沙盘服务引擎", "可信问答引擎"]),
        ("UC-10", "可信智能问答", ["能源运营管理员", "现场工人"], ["可信问答引擎", "业务服务层", "外部大模型服务"]),
        ("UC-11", "MCP工具调用", ["AI客户端"], ["MCP Server", "数据加载与查询服务", "异常分析引擎", "工单状态机引擎", "可信问答引擎"]),
    ]
    for usecase in usecases:
        make_usecase(*usecase)

    swims = [
        ("UC-00", "用户登录与权限管理", ["用户", "Web前端", "认证与权限服务"], [
            n("s", 0, 120, "开始", "start", 70, 40), n("open", 0, 190, "打开登录页"), n("input", 0, 270, "输入账号密码"), n("submit", 1, 350, "提交登录请求"), n("check", 2, 430, "校验凭证"), n("valid", 2, 510, "凭证有效?", "decision", 130, 80), n("fail", 1, 620, "显示失败提示"), n("token", 2, 620, "生成token和用户信息"), n("route", 1, 720, "按角色跳转工作台"), n("end", 1, 820, "结束", "end", 70, 40)
        ], [("s", "open"), ("open", "input"), ("input", "submit"), ("submit", "check"), ("check", "valid"), ("valid", "fail", "否"), ("valid", "token", "是"), ("token", "route"), ("fail", "end"), ("route", "end")]),
        ("UC-01", "管理样例数据与演示状态", ["系统/管理员", "数据服务", "持久化/知识库"], [
            n("s", 0, 120, "开始", "start", 70, 40), n("csv", 1, 190, "读取样例CSV"), n("dict", 1, 270, "加载数据字典"), n("kb", 2, 350, "加载知识库"), n("state", 2, 430, "读取运行期状态"), n("reset", 0, 510, "是否执行重置?", "decision", 140, 80), n("keep", 2, 620, "保持当前状态"), n("clear", 2, 620, "清空工单预算状态"), n("sim", 1, 720, "重置沙盘状态"), n("base", 1, 820, "提供演示基线"), n("end", 1, 920, "结束", "end", 70, 40)
        ], [("s", "csv"), ("csv", "dict"), ("dict", "kb"), ("kb", "state"), ("state", "reset"), ("reset", "keep", "否"), ("reset", "clear", "是"), ("clear", "sim"), ("sim", "base"), ("keep", "base"), ("base", "end")]),
        ("UC-02", "查看能源总览与数据查询", ["管理员/AI客户端", "数据查询服务", "沙盘服务"], [
            n("s", 0, 120, "开始", "start", 70, 40), n("req", 0, 190, "发起查询"), n("filter", 1, 270, "读取筛选条件"), n("sim", 2, 350, "沙盘启用?", "decision", 130, 80), n("date", 2, 470, "追加业务日期过滤"), n("all", 1, 470, "使用全量范围"), n("query", 1, 580, "执行记录查询"), n("derive", 1, 680, "生成派生字段"), n("return", 1, 780, "返回记录和元信息"), n("export", 0, 880, "是否导出CSV?", "decision", 130, 80), n("csv", 1, 1000, "生成CSV"), n("show", 0, 1000, "展示结果"), n("end", 0, 1100, "结束", "end", 70, 40)
        ], [("s", "req"), ("req", "filter"), ("filter", "sim"), ("sim", "date", "是"), ("sim", "all", "否"), ("date", "query"), ("all", "query"), ("query", "derive"), ("derive", "return"), ("return", "export"), ("export", "csv", "是"), ("export", "show", "否"), ("csv", "end"), ("show", "end")]),
        ("UC-03", "统计分析与异常诊断", ["管理员/AI客户端", "数据服务", "异常分析引擎"], [
            n("s", 0, 120, "开始", "start", 70, 40), n("page", 0, 190, "进入统计分析"), n("data", 1, 270, "获取可见记录"), n("base", 2, 350, "计算建筑小时基线"), n("summary", 2, 450, "生成汇总和对比"), n("detect", 2, 550, "识别异常记录"), n("risk", 2, 650, "计算风险分和SLA"), n("choose", 0, 760, "选择单条异常?", "decision", 140, 80), n("list", 0, 880, "展示异常列表"), n("explain", 2, 880, "生成异常解释"), n("end", 1, 1000, "结束", "end", 70, 40)
        ], [("s", "page"), ("page", "data"), ("data", "base"), ("base", "summary"), ("summary", "detect"), ("detect", "risk"), ("risk", "choose"), ("choose", "list", "否"), ("choose", "explain", "是"), ("list", "end"), ("explain", "end")]),
        ("UC-04", "派发维修工单", ["管理员", "Web前端", "工单状态机", "持久化存储"], [
            n("s", 0, 120, "开始", "start", 70, 40), n("view", 0, 190, "查看异常/派单建议"), n("select", 0, 270, "选择异常记录"), n("risk", 1, 350, "展示风险和损失"), n("need", 0, 450, "需要现场处理?", "decision", 140, 80), n("ignore", 3, 560, "记录忽略原因"), n("worker", 0, 560, "选择目标工人"), n("dup", 2, 660, "检查设备重复工单"), n("dupq", 2, 760, "重复?", "decision", 120, 75), n("conflict", 1, 870, "返回冲突提示"), n("busy", 2, 870, "检查工人忙闲"), n("busyq", 2, 970, "忙碌?", "decision", 120, 75), n("change", 1, 1080, "提示更换工人"), n("save", 3, 1080, "保存工单和时间线"), n("show", 1, 1190, "工人端可见任务"), n("end", 1, 1290, "结束", "end", 70, 40)
        ], [("s", "view"), ("view", "select"), ("select", "risk"), ("risk", "need"), ("need", "ignore", "否"), ("need", "worker", "是"), ("worker", "dup"), ("dup", "dupq"), ("dupq", "conflict", "是"), ("dupq", "busy", "否"), ("busy", "busyq"), ("busyq", "change", "是"), ("busyq", "save", "否"), ("save", "show"), ("ignore", "end"), ("conflict", "end"), ("change", "end"), ("show", "end")]),
        ("UC-05", "处理现场工单", ["现场工人", "Web前端", "工单状态机", "持久化存储"], [
            n("s", 0, 120, "开始", "start", 70, 40), n("login", 0, 190, "登录我的工单"), n("auth", 1, 270, "校验身份和归属"), n("list", 3, 350, "读取本人任务"), n("detail", 0, 450, "查看工单详情"), n("accept", 0, 550, "接单"), n("doing", 2, 650, "状态变为处理中"), n("site", 0, 750, "现场排查设备"), n("fill", 0, 850, "填写处理结果和附件"), n("complete", 1, 960, "信息完整?", "decision", 130, 80), n("warn", 1, 1080, "提示补充信息"), n("submit", 2, 1080, "状态变为待复核"), n("admin", 3, 1180, "管理员端可见"), n("end", 2, 1280, "结束", "end", 70, 40)
        ], [("s", "login"), ("login", "auth"), ("auth", "list"), ("list", "detail"), ("detail", "accept"), ("accept", "doing"), ("doing", "site"), ("site", "fill"), ("fill", "complete"), ("complete", "warn", "否"), ("complete", "submit", "是"), ("warn", "fill"), ("submit", "admin"), ("admin", "end")]),
        ("UC-06", "复核关闭工单", ["管理员", "工单状态机", "沙盘服务", "决策服务"], [
            n("s", 0, 120, "开始", "start", 70, 40), n("open", 0, 190, "打开待复核工单"), n("check", 0, 280, "核对现场材料"), n("pass", 0, 380, "复核通过?", "decision", 130, 80), n("reject", 1, 500, "记录驳回原因"), n("redo", 1, 600, "状态回到处理中"), n("close", 1, 500, "关闭工单并写时间线"), n("inter", 2, 620, "登记维修干预"), n("merge", 1, 740, "联动关闭同设备工单"), n("refresh", 3, 860, "刷新预算和报告"), n("end", 2, 980, "结束", "end", 70, 40)
        ], [("s", "open"), ("open", "check"), ("check", "pass"), ("pass", "reject", "否"), ("reject", "redo"), ("redo", "end"), ("pass", "close", "是"), ("close", "inter"), ("inter", "merge"), ("merge", "refresh"), ("refresh", "end")]),
        ("UC-07", "时间沙盘与反事实", ["管理员", "沙盘服务", "异常分析引擎", "决策服务"], [
            n("s", 0, 120, "开始", "start", 70, 40), n("start", 0, 190, "启动沙盘"), n("date", 1, 270, "设置业务日期"), n("hide", 1, 370, "隐藏未来记录"), n("anom", 2, 470, "计算当前异常"), n("interq", 1, 580, "存在维修干预?", "decision", 140, 80), n("fault", 1, 700, "按原始/定时故障演化"), n("apply", 1, 700, "应用维修干预"), n("advance", 0, 820, "推进日期"), n("recalc", 2, 920, "重算异常和风险"), n("report", 3, 1020, "刷新预算和报告"), n("cf", 0, 1120, "请求反事实?", "decision", 140, 80), n("show", 0, 1240, "展示沙盘状态"), n("clone", 1, 1240, "复制状态不污染计算"), n("compare", 3, 1360, "比较三种策略损失"), n("end", 2, 1480, "结束", "end", 70, 40)
        ], [("s", "start"), ("start", "date"), ("date", "hide"), ("hide", "anom"), ("anom", "interq"), ("interq", "fault", "否"), ("interq", "apply", "是"), ("fault", "advance"), ("apply", "advance"), ("advance", "recalc"), ("recalc", "report"), ("report", "cf"), ("cf", "show", "否"), ("cf", "clone", "是"), ("clone", "compare"), ("compare", "end"), ("show", "end")]),
        ("UC-08", "预算执行与闭环改善", ["管理员", "预算决策引擎", "工单服务", "持久化存储"], [
            n("s", 0, 120, "开始", "start", 70, 40), n("enter", 0, 190, "进入预算管理"), n("select", 0, 270, "选择建筑和月份"), n("exist", 1, 360, "预算已存在?", "decision", 130, 80), n("gen", 1, 480, "生成月度预算"), n("read", 3, 480, "读取已有预算"), n("actual", 1, 600, "计算实际电耗执行率"), n("forecast", 1, 700, "预测月末执行率"), n("kpi", 1, 800, "计算年度KPI"), n("closed", 2, 900, "汇总已关闭工单节省"), n("summary", 1, 1010, "生成风险和改善摘要"), n("show", 0, 1120, "展示预算结果"), n("end", 0, 1220, "结束", "end", 70, 40)
        ], [("s", "enter"), ("enter", "select"), ("select", "exist"), ("exist", "gen", "否"), ("exist", "read", "是"), ("gen", "actual"), ("read", "actual"), ("actual", "forecast"), ("forecast", "kpi"), ("kpi", "closed"), ("closed", "summary"), ("summary", "show"), ("show", "end")]),
        ("UC-09", "ROI改造与运营报告", ["管理员", "ROI决策引擎", "异常分析引擎", "可信问答"], [
            n("s", 0, 120, "开始", "start", 70, 40), n("enter", 0, 190, "进入ROI或报告"), n("select", 0, 270, "选择建筑设备"), n("audit", 1, 360, "执行能效审计"), n("candidate", 2, 470, "存在改造候选?", "decision", 140, 80), n("none", 0, 590, "提示暂无建议"), n("plan", 0, 590, "选择改造方案"), n("calc", 1, 700, "计算NPV IRR EAA"), n("compare", 1, 800, "多方案比较"), n("report", 1, 900, "汇总风险工单预算ROI"), n("cite", 3, 1010, "供AI助手引用"), n("end", 2, 1120, "结束", "end", 70, 40)
        ], [("s", "enter"), ("enter", "select"), ("select", "audit"), ("audit", "candidate"), ("candidate", "none", "否"), ("candidate", "plan", "是"), ("plan", "calc"), ("calc", "compare"), ("compare", "report"), ("report", "cite"), ("none", "end"), ("cite", "end")]),
        ("UC-10", "可信智能问答", ["用户", "可信问答引擎", "业务服务层", "外部大模型"], [
            n("s", 0, 120, "开始", "start", 70, 40), n("ask", 0, 190, "提出问题"), n("intent", 1, 270, "识别意图和实体"), n("type", 1, 370, "问题类型?", "decision", 140, 80), n("ctx", 2, 500, "检索业务上下文"), n("kb", 2, 600, "检索知识库"), n("assemble", 1, 710, "组装事实上下文"), n("llmq", 1, 820, "外部模型启用?", "decision", 140, 80), n("local", 1, 940, "生成本地可信回答"), n("call", 3, 940, "调用外部模型增强"), n("verify", 1, 1060, "事实校验通过?", "decision", 140, 80), n("return1", 0, 1180, "返回本地回答和引用"), n("return2", 0, 1180, "返回增强回答和引用"), n("end", 0, 1300, "结束", "end", 70, 40)
        ], [("s", "ask"), ("ask", "intent"), ("intent", "type"), ("type", "ctx", "数据/工单/预算"), ("type", "kb", "知识解释"), ("ctx", "assemble"), ("kb", "assemble"), ("assemble", "llmq"), ("llmq", "local", "否"), ("llmq", "call", "是"), ("call", "verify"), ("verify", "local", "否"), ("verify", "return2", "是"), ("local", "return1"), ("return1", "end"), ("return2", "end")]),
        ("UC-11", "MCP工具调用", ["AI客户端", "MCP Server", "工具路由", "后端服务层"], [
            n("s", 0, 120, "开始", "start", 70, 40), n("connect", 0, 190, "建立MCP连接"), n("list", 1, 270, "返回Tools和Resources"), n("call", 0, 370, "调用Tool并传参"), n("validate", 2, 470, "校验工具名和参数"), n("valid", 2, 570, "参数有效?", "decision", 130, 80), n("err", 1, 700, "返回结构化错误"), n("service", 3, 700, "调用业务服务层"), n("result", 3, 800, "生成结构化业务结果"), n("wrap", 1, 900, "封装MCP响应"), n("return", 0, 1000, "客户端接收结果"), n("end", 0, 1100, "结束", "end", 70, 40)
        ], [("s", "connect"), ("connect", "list"), ("list", "call"), ("call", "validate"), ("validate", "valid"), ("valid", "err", "否"), ("valid", "service", "是"), ("service", "result"), ("result", "wrap"), ("wrap", "return"), ("err", "end"), ("return", "end")]),
    ]

    for swim in swims:
        make_swimlane(*swim)


if __name__ == "__main__":
    main()
