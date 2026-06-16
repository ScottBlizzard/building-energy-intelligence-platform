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
    def __init__(self, name, width, height):
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

    def edge(self, source, target, value="", style=None):
        id = self.nid("e")
        style = style or EDGE_CALL
        self.cells.append(
            f'<mxCell id="{id}" value="{attr(value)}" style="{style}" edge="1" parent="1" source="{source}" target="{target}">'
            '<mxGeometry relative="1" as="geometry" /></mxCell>'
        )
        return id

    def write(self, path):
        body = "\n        ".join(self.cells)
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="drawio" version="26.0.0">
  <diagram name="{attr(self.name)}">
    <mxGraphModel dx="1300" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.width}" pageHeight="{self.height}" math="0" shadow="0">
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


FONT = "fontFamily=Microsoft YaHei;"
TITLE = f"text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=18;fontStyle=1;{FONT}"
HEADER = f"rounded=1;arcSize=8;whiteSpace=wrap;html=1;align=center;verticalAlign=middle;fillColor=#e1d5e7;strokeColor=#666666;fontSize=13;{FONT}"
ACTOR = f"shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#ffffff;strokeColor=#333333;fontSize=13;{FONT}"
DB = f"shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;fillColor=#f5f5f5;strokeColor=#333333;fontSize=12;{FONT}"
ANCHOR = "ellipse;html=1;opacity=0;strokeOpacity=0;fillOpacity=0;"
ACTIVATION = "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#111111;"
FRAME = f"rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#111111;strokeWidth=2;{FONT}"
FRAME_TAB = f"rounded=0;whiteSpace=wrap;html=1;align=left;verticalAlign=middle;fillColor=#ffffff;strokeColor=#111111;strokeWidth=2;fontStyle=1;fontSize=12;{FONT}"
EDGE_CALL = f"edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=0;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#111111;fontSize=12;verticalAlign=bottom;labelBackgroundColor=#ffffff;{FONT}"
EDGE_RETURN = f"edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=0;jettySize=auto;html=1;endArrow=open;endFill=0;dashed=1;strokeColor=#666666;fontSize=12;verticalAlign=bottom;labelBackgroundColor=#ffffff;{FONT}"
EDGE_LIFELINE = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=0;jettySize=auto;html=1;endArrow=none;dashed=1;strokeColor=#999999;"


def seq(code, title, participants, messages, frames=None):
    gap = 185
    left = 75
    top_y = 88
    line_top = 150
    msg_y0 = 178
    step = 54
    bottom_line = msg_y0 + step * (len(messages) + 1)
    bottom_label_y = bottom_line + 20
    width = max(760, left * 2 + gap * (len(participants) - 1) + 80)
    height = bottom_label_y + 95

    d = Diagram(f"{code} {title} 时序图", width, height)
    d.vertex(f"{title}", TITLE, 20, 18, width - 40, 30)

    xs = {}
    kinds = {}
    for i, p in enumerate(participants):
        key, label, kind = p
        x = left + i * gap
        xs[key] = x
        kinds[key] = kind
        if kind == "actor":
            d.vertex(label, ACTOR, x - 30, 58, 60, 86)
            d.vertex(label, ACTOR, x - 30, bottom_label_y, 60, 86)
        elif kind == "db":
            d.vertex(label, DB, x - 42, 58, 84, 86)
            d.vertex(label, DB, x - 42, bottom_label_y, 84, 86)
        else:
            d.vertex(label, HEADER, x - 66, top_y, 132, 42)
            d.vertex(label, HEADER, x - 66, bottom_label_y + 20, 132, 42)

        top_anchor = d.vertex("", ANCHOR, x - 1, line_top, 2, 2)
        bottom_anchor = d.vertex("", ANCHOR, x - 1, bottom_line, 2, 2)
        d.edge(top_anchor, bottom_anchor, "", EDGE_LIFELINE)

    if frames:
        for frame in frames:
            y1 = msg_y0 + step * frame["start"] - 28
            y2 = msg_y0 + step * frame["end"] + 26
            x1 = min(xs.values()) - 48
            x2 = max(xs.values()) + 48
            d.vertex("", FRAME, x1, y1, x2 - x1, y2 - y1)
            d.vertex(frame["label"], FRAME_TAB, x1, y1, 155, 28)

    for i, message in enumerate(messages):
        src, dst, label = message[:3]
        kind = message[3] if len(message) > 3 else "call"
        y = msg_y0 + i * step
        sx = xs[src]
        tx = xs[dst]
        source_anchor = d.vertex("", ANCHOR, sx - 1, y - 1, 2, 2)
        target_anchor = d.vertex("", ANCHOR, tx - 1, y - 1, 2, 2)
        if kind == "return":
            d.edge(source_anchor, target_anchor, label, EDGE_RETURN)
        else:
            if kinds.get(dst) != "actor":
                d.vertex("", ACTIVATION, tx - 6, y - 16, 12, 42)
            d.edge(source_anchor, target_anchor, label, EDGE_CALL)

    d.write(OUT / f"{code.lower()}_sequence.drawio")


def main():
    diagrams = [
        (
            "UC-00",
            "用户登录与权限管理",
            [
                ("user", "用户", "actor"),
                ("web", "Web前端", "object"),
                ("api", "认证API", "object"),
                ("auth", "认证与权限服务", "object"),
                ("guard", "前端路由守卫", "object"),
            ],
            [
                ("user", "web", "输入账号密码"),
                ("web", "api", "POST /auth/login"),
                ("api", "auth", "校验账号、密码、角色"),
                ("auth", "api", "返回用户与角色", "return"),
                ("api", "web", "返回 token 和用户信息", "return"),
                ("web", "guard", "根据角色生成导航"),
                ("guard", "web", "返回可访问页面", "return"),
                ("web", "user", "展示对应工作台/失败提示", "return"),
            ],
        ),
        (
            "UC-01",
            "管理样例数据与演示状态",
            [
                ("admin", "管理员", "actor"),
                ("web", "Web前端", "object"),
                ("demo", "演示数据API", "object"),
                ("data", "数据服务", "object"),
                ("store", "持久化存储", "db"),
                ("kb", "知识库/沙盘服务", "object"),
            ],
            [
                ("admin", "web", "点击重置演示/加载数据"),
                ("web", "demo", "POST /demo/reset"),
                ("demo", "data", "清空或装载样例数据"),
                ("data", "store", "写入演示基线"),
                ("store", "data", "返回重置结果", "return"),
                ("data", "kb", "重置知识库与沙盘状态"),
                ("kb", "data", "返回可用状态", "return"),
                ("data", "demo", "返回演示基线", "return"),
                ("demo", "web", "返回操作结果", "return"),
                ("web", "admin", "显示重置完成", "return"),
            ],
        ),
        (
            "UC-02",
            "查看能源总览与数据查询",
            [
                ("user", "管理员/AI客户端", "actor"),
                ("client", "Web/MCP客户端", "object"),
                ("api", "数据API", "object"),
                ("sim", "沙盘服务", "object"),
                ("loader", "数据加载服务", "object"),
            ],
            [
                ("user", "client", "设置筛选条件/工具参数"),
                ("client", "api", "GET /records 或 query_energy_records"),
                ("api", "sim", "获取业务日期边界"),
                ("sim", "api", "返回可见时间范围", "return"),
                ("api", "loader", "执行筛选与派生字段计算"),
                ("loader", "api", "返回记录与元信息", "return"),
                ("api", "client", "返回 items/meta/CSV", "return"),
                ("client", "user", "展示表格或导出结果", "return"),
            ],
        ),
        (
            "UC-03",
            "统计分析与异常诊断",
            [
                ("user", "管理员/AI客户端", "actor"),
                ("client", "Web/MCP客户端", "object"),
                ("analytics", "分析API", "object"),
                ("data", "数据服务", "object"),
                ("engine", "异常分析引擎", "object"),
            ],
            [
                ("user", "client", "打开统计分析/调用异常工具"),
                ("client", "analytics", "GET /analytics/anomalies"),
                ("analytics", "data", "获取可见记录和基线数据"),
                ("data", "analytics", "返回记录集", "return"),
                ("analytics", "engine", "计算基线/风险/原因"),
                ("engine", "analytics", "返回异常、解释与SLA", "return"),
                ("analytics", "client", "返回图表与异常详情", "return"),
                ("client", "user", "展示统计和处置建议", "return"),
            ],
        ),
        (
            "UC-05",
            "处理现场工单",
            [
                ("worker", "工人", "actor"),
                ("page", "我的工单页", "object"),
                ("api", "工单API", "object"),
                ("auth", "权限服务", "object"),
                ("state", "工单状态机", "object"),
                ("store", "持久化存储", "db"),
            ],
            [
                ("worker", "page", "打开我的工单"),
                ("page", "api", "GET /work-orders?assignee=me"),
                ("api", "auth", "校验工单归属"),
                ("auth", "api", "权限通过", "return"),
                ("api", "store", "读取本人工单"),
                ("store", "api", "返回工单列表", "return"),
                ("api", "page", "返回任务详情", "return"),
                ("worker", "page", "接单/填写处理结果"),
                ("page", "api", "PATCH /work-orders/{id}/submit"),
                ("api", "state", "校验流转并置为待复核"),
                ("state", "store", "保存处理材料与时间线"),
                ("store", "api", "返回保存结果", "return"),
                ("api", "page", "返回待复核工单", "return"),
                ("page", "worker", "展示提交成功", "return"),
            ],
        ),
        (
            "UC-07",
            "时间沙盘与反事实",
            [
                ("admin", "管理员", "actor"),
                ("web", "Web前端", "object"),
                ("api", "沙盘API", "object"),
                ("sim", "沙盘服务", "object"),
                ("engine", "异常分析引擎", "object"),
                ("decision", "决策服务", "object"),
            ],
            [
                ("admin", "web", "启动或推进沙盘"),
                ("web", "api", "POST /sim/start 或 /advance"),
                ("api", "sim", "设置/推进业务日期"),
                ("sim", "engine", "按可见数据重算异常"),
                ("engine", "sim", "返回异常风险", "return"),
                ("sim", "decision", "刷新预算与报告上下文"),
                ("decision", "sim", "返回刷新结果", "return"),
                ("sim", "api", "返回沙盘状态", "return"),
                ("api", "web", "返回状态与指标", "return"),
                ("admin", "web", "请求反事实比较"),
                ("web", "api", "POST /sim/counterfactual"),
                ("api", "sim", "复制状态并计算三种策略"),
                ("sim", "api", "返回未来损失差异", "return"),
                ("api", "web", "返回反事实结果", "return"),
                ("web", "admin", "展示沙盘与策略对比", "return"),
            ],
            [{"label": "opt 反事实计算", "start": 10, "end": 13}],
        ),
        (
            "UC-08",
            "预算执行与闭环改善",
            [
                ("admin", "管理员", "actor"),
                ("page", "预算页面", "object"),
                ("api", "预算API", "object"),
                ("budget", "预算服务", "object"),
                ("work", "工单服务", "object"),
                ("store", "持久化存储", "db"),
            ],
            [
                ("admin", "page", "选择建筑月份"),
                ("page", "api", "GET/POST /budget/budgets"),
                ("api", "budget", "生成或读取预算"),
                ("budget", "store", "读取能耗与预算基线"),
                ("store", "budget", "返回预算数据", "return"),
                ("budget", "work", "汇总已关闭工单节省"),
                ("work", "budget", "返回闭环改善摘要", "return"),
                ("budget", "api", "返回执行率/KPI/风险", "return"),
                ("api", "page", "返回预算看板", "return"),
                ("page", "admin", "展示预算结果", "return"),
            ],
        ),
        (
            "UC-09",
            "ROI 改造与运营报告",
            [
                ("admin", "管理员", "actor"),
                ("page", "ROI/报告页", "object"),
                ("api", "ROI API", "object"),
                ("roi", "ROI决策服务", "object"),
                ("engine", "异常分析引擎", "object"),
                ("report", "报告/问答上下文", "object"),
            ],
            [
                ("admin", "page", "选择建筑设备方案"),
                ("page", "api", "POST /roi/analyze"),
                ("api", "roi", "执行设备审计与投资计算"),
                ("roi", "engine", "获取异常和能效证据"),
                ("engine", "roi", "返回异常证据", "return"),
                ("roi", "api", "返回 NPV/IRR/EAA/候选方案", "return"),
                ("api", "page", "返回 ROI 结果", "return"),
                ("admin", "page", "请求运营报告"),
                ("page", "api", "GET /operation-report"),
                ("api", "roi", "汇总风险、工单、预算与ROI"),
                ("roi", "report", "生成报告上下文与引用标签"),
                ("report", "roi", "返回可引用摘要", "return"),
                ("roi", "api", "返回运营报告", "return"),
                ("api", "page", "返回报告与行动项", "return"),
                ("page", "admin", "展示ROI和报告", "return"),
            ],
        ),
    ]

    for args in diagrams:
        seq(*args)


if __name__ == "__main__":
    main()
