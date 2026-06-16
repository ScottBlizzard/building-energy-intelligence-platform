"""Build formal LaTeX delivery documents for the final course submission.

The generated documents use the same ctexart-based style as the course
experiment template and compile with XeLaTeX.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs" / "final-latex"
TEX_DIR = DOCS_DIR / "tex"
BUILD_DIR = DOCS_DIR / "build"
PDF_DIR = DOCS_DIR / "pdf"
SUBMISSION_LATEX_DIR = ROOT / "期末提交材料" / "documents" / "latex"
SUBMISSION_PDF_DIR = ROOT / "期末提交材料" / "documents" / "pdf-latex"


PREAMBLE = r"""
\documentclass[12pt,a4paper]{ctexart}

\usepackage[margin=2.3cm]{geometry}
\usepackage{amsmath}
\usepackage{array}
\usepackage{booktabs}
\usepackage{caption}
\usepackage{enumitem}
\usepackage{etoolbox}
\usepackage{fancyhdr}
\usepackage{float}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{longtable}
\usepackage{tabularx}
\usepackage[table]{xcolor}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,fit,calc}

\hypersetup{hidelinks}
\urlstyle{same}
\setlist{nosep}
\captionsetup{font=small}
\renewcommand{\arraystretch}{1.25}
\setlength{\parindent}{2em}
\setlength{\parskip}{0.3em}
\setlength{\tabcolsep}{4pt}
\emergencystretch=3em
\sloppy
\makeatletter
\g@addto@macro{\UrlBreaks}{\do\/\do\-\do\_\do\.\do\:}
\makeatother
\AtBeginEnvironment{longtable}{\small\setlength{\tabcolsep}{3pt}}
\AtBeginEnvironment{tabularx}{\small\setlength{\tabcolsep}{3pt}}
\AtBeginEnvironment{tabular}{\small\setlength{\tabcolsep}{3pt}}

\newcommand{\studentname}{许奕}
\newcommand{\studentid}{2351441}
\newcommand{\teamname}{许奕、王天一、马源胜、周由}
\newcommand{\coursename}{软件工程管理与经济}
\newcommand{\projectname}{基于大模型的建筑能源智能管理与运维优化系统}
\newcommand{\docversion}{V2.0}
\newcommand{\docdate}{2026年5月31日}
\newcommand{\code}[1]{{\footnotesize\nolinkurl{#1}}}
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}

\tikzset{
  box/.style={rectangle, rounded corners, draw=cyan!55!black, fill=cyan!8, thick, minimum height=8mm, align=center, inner sep=5pt},
  process/.style={rectangle, rounded corners, draw=teal!55!black, fill=teal!8, thick, minimum height=8mm, align=center, inner sep=5pt},
  data/.style={cylinder, shape border rotate=90, aspect=0.25, draw=orange!70!black, fill=orange!10, thick, minimum height=12mm, align=center, inner sep=5pt},
  risk/.style={diamond, draw=red!60!black, fill=red!8, thick, aspect=2, align=center, inner sep=2pt},
  arrow/.style={-{Stealth[length=2.4mm]}, thick, draw=gray!70!black},
  note/.style={rectangle, draw=gray!60, fill=gray!6, rounded corners, align=left, inner sep=6pt}
}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\coursename}
\fancyhead[R]{\reporttitle}
\fancyfoot[C]{\thepage}
\setlength{\headheight}{15pt}

\title{
    \vspace{-2em}
    \heiti \zihao{2} \reporttitle \\
    \vspace{1em}
    \zihao{4} 课程期末项目正式交付文档
}
\author{
    \songti \zihao{4}
    项目名称：\projectname \\
    项目组成员：\teamname \\
    负责人：\studentname \quad 学号：\studentid
}
\date{\docdate}
"""


def wrap_document(report_title: str, abstract: str, body: str) -> str:
    return (
        PREAMBLE
        + "\n"
        + rf"\newcommand{{\reporttitle}}{{{report_title}}}"
        + "\n"
        + r"\begin{document}"
        + "\n\n"
        + r"\maketitle"
        + "\n"
        + r"\thispagestyle{fancy}"
        + "\n\n"
        + r"\begin{abstract}"
        + "\n"
        + abstract.strip()
        + "\n"
        + r"\end{abstract}"
        + "\n\n"
        + r"\tableofcontents"
        + "\n"
        + r"\newpage"
        + "\n\n"
        + body.strip()
        + "\n\n"
        + r"\end{document}"
        + "\n"
    )


SRS_ABSTRACT = r"""
本文档为课程期末项目《\projectname》的软件需求规格说明书，采用正式 SRS 结构描述系统目标、业务背景、用户角色、系统边界、功能需求、非功能需求、数据需求、外部接口和验收标准。本文档的需求基线来自项目最终实现版本：系统已形成 FastAPI 后端、Vue 前端、建筑能耗样例数据、异常分析、三维楼层态势、工单闭环、知识库问答、可选外部大模型和 MCP Server。文档中的功能项与代码仓库、测试脚本和最终演示路径保持一致，可作为课程评审、系统验收和后续维护的需求依据。
"""


SRS_BODY = r"""
\section{文档控制}
\begin{longtable}{p{4cm}p{10.5cm}}
\toprule
项目 & 内容 \\
\midrule
文档名称 & SRS 软件需求规格说明书 \\
文档版本 & \docversion \\
适用阶段 & 期末项目最终提交、系统演示、验收评审、后续维护 \\
项目范围 & Web 前端、FastAPI 后端、MCP Server、样例数据集、知识库、测试脚本和交付文档 \\
关联文档 & SDD 软件设计说明书、SEE 软件经济分析与评价、SEM 软件工程管理说明、测试与验收报告、用户手册与部署说明 \\
参考资料 & IEEE 风格 SRS 文档结构；同类课程项目文档组织方式参考 \url{https://github.com/L-Dramatic/Intelligent-Contract-Management-System} \\
\bottomrule
\end{longtable}

\section{引言}
\subsection{编写目的}
本文档用于明确本系统的业务问题、用户需求、软件功能、外部接口、数据约束、非功能要求和验收标准。它解决三个问题：第一，系统到底要完成哪些业务任务；第二，哪些功能属于本次课程项目边界，哪些属于后续扩展；第三，评审人员如何根据文档检查系统是否已经满足课程项目要求。

\subsection{项目背景}
校园建筑能源管理通常存在数据分散、异常发现滞后、设备状态难以追踪、人工巡检依赖经验、节能措施缺少量化依据等问题。传统的表格统计方式能够记录用电、用水和设备运行数据，但很难支撑快速定位“哪栋楼、哪一层、哪类设备、什么时段出现异常”。本项目以校园建筑能源管理为场景，构建一个可运行的智能管理与运维优化平台，将数据查询、统计分析、异常解释、三维风险态势、工单处理、决策报告和智能问答组合成完整业务闭环。

\subsection{系统目标}
系统目标不是单纯展示几张图表，而是完成从数据到处置的闭环。具体目标如下：
\begin{enumerate}
    \item 建立标准化建筑能耗样例数据集，覆盖多建筑、多时段、多设备和多指标。
    \item 提供按建筑、楼层、时间范围的查询和导出能力，支撑数据追溯。
    \item 提供总览、趋势、建筑对比、COP 排名、异常原因、楼层分析和设备分析。
    \item 使用可解释规则定位异常，并输出触发规则、指标证据和处理建议。
    \item 使用三维楼宇视图展示楼层健康状态，并与统计分析页面联动。
    \item 建立异常工单闭环，使异常能够被分派、跟踪和完成。
    \item 提供本地知识库问答和可选外部大模型增强，提升运维解释能力。
    \item 提供 MCP Server，使 AI 客户端能够通过协议调用项目数据和分析能力。
\end{enumerate}

\section{产品范围与业务边界}
\subsection{产品定位}
本系统定位为课程项目级“建筑能源智能管理与运维优化原型系统”。它不直接接入真实楼宇自控系统，也不承担法定能源审计责任；它面向教学演示、工程管理课程评审和后续原型扩展，重点体现软件工程中的需求、设计、实现、测试、部署、经济分析和项目管理闭环。

\subsection{业务边界}
\begin{table}[H]
\centering
\caption{系统业务边界}
\begin{tabularx}{\textwidth}{p{3.2cm}YY}
\toprule
类别 & 纳入本期范围 & 不纳入本期范围 \\
\midrule
数据来源 & 样例 CSV 数据、数据字典、知识库 Markdown、运行期工单 JSON & 实时电表、真实楼宇自控系统、真实收费账单 \\
业务功能 & 查询、统计、异常、工单、报告、问答、MCP 接入 & 多租户权限、组织审批流、企业级审计 \\
算法能力 & 可解释规则、COP 计算、建筑基线、楼层聚合 & 大规模模型训练、在线学习、真实预测竞赛模型 \\
部署形态 & 本地开发部署、课程演示部署、MCP 本地接入 & 高可用生产集群、移动端 App、IoT 边缘网关 \\
\bottomrule
\end{tabularx}
\end{table}

\subsection{系统上下文图}
\begin{figure}[H]
\centering
\resizebox{0.96\textwidth}{!}{%
\begin{tikzpicture}[node distance=12mm and 16mm]
\node[box, minimum width=29mm] (manager) {能源管理人员};
\node[box, below=of manager, minimum width=29mm] (worker) {运维人员};
\node[box, below=of worker, minimum width=29mm] (teacher) {评审人员};
\node[process, right=32mm of worker, minimum width=42mm, minimum height=24mm] (system) {建筑能源智能\\管理平台};
\node[data, right=30mm of system, minimum width=32mm] (dataset) {能耗 CSV\\工单 JSON};
\node[data, above=of dataset, minimum width=32mm] (kb) {知识库\\Markdown};
\node[box, below=of dataset, minimum width=32mm] (llm) {外部大模型\\可选};
\node[box, below=of system, minimum width=42mm] (mcp) {支持 MCP 的\\AI 客户端};
\draw[arrow] (manager) -- node[above, sloped]{查看报表} (system);
\draw[arrow] (worker) -- node[above, sloped]{处理异常} (system);
\draw[arrow] (teacher) -- node[above, sloped]{验收演示} (system);
\draw[arrow] (system) -- node[above]{读写} (dataset);
\draw[arrow] (system) -- node[right]{检索} (kb);
\draw[arrow] (system) -- node[right]{增强问答} (llm);
\draw[arrow] (mcp) -- node[right]{协议调用} (system);
\end{tikzpicture}
}
\caption{系统上下文与外部角色}
\end{figure}

\section{用户角色与使用场景}
\begin{longtable}{p{3.2cm}p{4.4cm}p{6.8cm}}
\caption{用户角色定义}\\
\toprule
角色 & 核心诉求 & 典型任务 \\
\midrule
\endfirsthead
\toprule
角色 & 核心诉求 & 典型任务 \\
\midrule
\endhead
能源管理人员 & 掌握整体能耗、异常趋势和节能空间 & 查看总览 KPI、建筑对比、COP 排名、运营报告和节能建议 \\
运维人员 & 快速定位异常并形成处理记录 & 查看异常明细、解释异常、创建工单、更新工单状态、确认处理结果 \\
项目管理者 & 评估系统价值和交付完整性 & 查看经济分析、工程管理、测试报告和最终交付材料 \\
任课教师与评审人员 & 验证系统是否满足期末项目要求 & 按 README 运行系统，核验 SRS、SDD、SEE、SEM、源码和系统展示路径 \\
AI 客户端或智能体 & 通过标准协议调用项目能力 & 使用 MCP Tools 查询数据、获取异常解释、生成运营报告和检索知识库 \\
\bottomrule
\end{longtable}

\section{业务流程需求}
\subsection{核心业务流程}
\begin{figure}[H]
\centering
\resizebox{0.98\textwidth}{!}{%
\begin{tikzpicture}[x=1cm,y=1cm,every node/.style={font=\small}]
\node[process, minimum width=2.4cm, minimum height=0.9cm] (data) at (0,0) {1 数据读取\\字段校验};
\node[process, minimum width=2.7cm, minimum height=0.9cm] (query) at (3.0,0) {2 查询筛选\\建筑/楼层/时间};
\node[process, minimum width=2.8cm, minimum height=0.9cm] (analysis) at (6.2,0) {3 统计分析\\趋势/COP/对比};
\node[risk, minimum width=2.3cm, minimum height=1.0cm] (risk) at (9.4,0) {4 异常\\判断};
\node[process, minimum width=2.7cm, minimum height=0.9cm] (explain) at (9.4,-2.1) {5 异常解释\\证据与建议};
\node[process, minimum width=2.7cm, minimum height=0.9cm] (order) at (6.2,-2.1) {6 生成工单\\分派负责人};
\node[process, minimum width=2.7cm, minimum height=0.9cm] (finish) at (3.0,-2.1) {7 处理完成\\状态持久化};
\node[process, minimum width=2.8cm, minimum height=0.9cm] (report) at (0,-2.1) {8 运营报告\\管理建议};

\draw[arrow] (data) -- (query);
\draw[arrow] (query) -- (analysis);
\draw[arrow] (analysis) -- (risk);
\draw[arrow] (risk) -- node[right, fill=white, inner sep=1pt]{异常} (explain);
\draw[arrow] (explain) -- (order);
\draw[arrow] (order) -- (finish);
\draw[arrow] (finish) -- (report);
\draw[arrow, dashed] (analysis.south) -- node[right, fill=white, inner sep=1pt]{统计结果} (order.north);
\end{tikzpicture}
}
\caption{从数据到工单的业务闭环}
\end{figure}

\subsection{用例列表}
\begin{longtable}{p{2cm}p{3.2cm}p{3cm}p{5.8cm}}
\caption{主要用例}\\
\toprule
编号 & 用例名称 & 主要参与者 & 成功结果 \\
\midrule
\endfirsthead
\toprule
编号 & 用例名称 & 主要参与者 & 成功结果 \\
\midrule
\endhead
UC-01 & 查看系统总览 & 能源管理人员 & 展示记录数、建筑数、平均 COP、异常数量和总能耗 \\
UC-02 & 浏览能耗记录 & 能源管理人员 & 按建筑、楼层、时间和数量筛选记录，表格字段完整 \\
UC-03 & 导出查询数据 & 能源管理人员 & 下载当前筛选范围 CSV，文件可被表格软件打开 \\
UC-04 & 查看统计分析 & 管理人员 & 展示趋势、异常、楼层、设备、推荐和全局对比 \\
UC-05 & 查看健康楼层 & 管理人员 & 绿色楼层只显示健康结论，不出现无意义空模块 \\
UC-06 & 点击三维楼层 & 运维人员 & 跳转统计分析并自动锁定对应建筑和楼层 \\
UC-07 & 解释异常记录 & 运维人员 & 输出触发规则、关键指标、结论和建议动作 \\
UC-08 & 创建异常工单 & 运维人员 & 选择异常、分配负责人，生成处理中工单 \\
UC-09 & 完成异常工单 & 运维人员 & 工单变为已完成并持久化，刷新后仍保留 \\
UC-10 & 生成决策报告 & 管理人员 & 输出风险摘要、工单状态、优化建议和收益测算 \\
UC-11 & 使用智能问答 & 管理人员 & 基于知识库和项目数据回答能源运维问题 \\
UC-12 & MCP 查询项目能力 & AI 客户端 & 通过 MCP Tools 获取数据、统计、异常解释和报告 \\
\bottomrule
\end{longtable}

\subsection{用例图}
\begin{figure}[H]
\centering
\resizebox{0.98\textwidth}{!}{%
\begin{tikzpicture}[every node/.style={font=\scriptsize}]
\tikzstyle{actorbox}=[draw=teal!75!black, rounded corners=3pt, fill=teal!6,
    minimum width=23mm, minimum height=8mm, align=center]
\tikzstyle{usecase}=[ellipse, draw=teal!70!black, fill=teal!7,
    minimum width=27mm, minimum height=8mm, align=center]
\tikzstyle{riskcase}=[ellipse, draw=red!65!black, fill=red!7,
    minimum width=27mm, minimum height=8mm, align=center]
\tikzstyle{workcase}=[ellipse, draw=orange!80!black, fill=orange!9,
    minimum width=27mm, minimum height=8mm, align=center]
\tikzstyle{aicase}=[ellipse, draw=cyan!70!black, fill=cyan!7,
    minimum width=27mm, minimum height=8mm, align=center]
\tikzstyle{verifycase}=[ellipse, draw=gray!70, fill=gray!8,
    minimum width=27mm, minimum height=8mm, align=center]

\draw[rounded corners=6pt, draw=gray!60, fill=gray!3] (0,-4.95) rectangle (10.5,2.55);
\node[font=\small] at (5.25,2.25) {建筑能源智能管理平台};

\node[actorbox] (energy) at (-1.65,0.75) {能源管理\\人员};
\node[actorbox] (reviewer) at (-1.65,-3.7) {评审人员};
\node[actorbox] (operator) at (12.15,-0.8) {运维人员};
\node[actorbox] (agent) at (12.15,-3.3) {AI 客户端};

\node[usecase] (uc01) at (2.0,1.35) {查看总览};
\node[usecase] (uc02) at (2.0,0.25) {查询与导出};
\node[usecase] (uc03) at (2.0,-0.85) {统计分析};
\node[aicase] (uc07) at (2.0,-1.95) {决策报告};
\node[verifycase] (uc10) at (2.0,-3.7) {测试与验收};

\node[workcase] (uc05) at (7.6,0.65) {三维楼层};
\node[riskcase] (uc04) at (7.6,-0.55) {异常解释};
\node[workcase] (uc06) at (7.6,-1.75) {工单闭环};
\node[aicase] (uc08) at (7.6,-3.0) {智能问答};
\node[aicase] (uc09) at (7.6,-4.15) {MCP 调用};

\draw[-{Stealth[length=2mm]}, thick] (energy.east) -- (-0.25,0.75) |- (uc01.west);
\draw[-{Stealth[length=2mm]}, thick] (energy.east) -- (-0.25,0.75) |- (uc02.west);
\draw[-{Stealth[length=2mm]}, thick] (energy.east) -- (-0.25,0.75) |- (uc03.west);
\draw[-{Stealth[length=2mm]}, thick] (energy.east) -- (-0.25,0.75) |- (uc07.west);
\draw[-{Stealth[length=2mm]}, thick] (operator.west) -- (10.75,-0.8) |- (uc05.east);
\draw[-{Stealth[length=2mm]}, thick] (operator.west) -- (10.75,-0.8) |- (uc04.east);
\draw[-{Stealth[length=2mm]}, thick] (operator.west) -- (10.75,-0.8) |- (uc06.east);
\draw[-{Stealth[length=2mm]}, thick] (reviewer.east) -- (-0.25,-3.7) |- (uc10.west);
\draw[-{Stealth[length=2mm]}, thick] (agent.west) -- (10.75,-3.3) |- (uc08.east);
\draw[-{Stealth[length=2mm]}, thick] (agent.west) -- (10.75,-3.3) |- (uc09.east);

\draw[-{Stealth[length=2mm]}, dashed] (uc04.south) -- node[right, font=\tiny]{支撑} (uc06.north);
\node[font=\tiny, align=center, text=gray!70] at (5.25,-4.72)
{说明：三维楼层联动统计分析；异常解释支撑工单闭环；智能问答可调用 MCP 工具。};
\end{tikzpicture}
}
\caption{系统用例图}
\end{figure}

\subsection{关键用例详细说明}
\begin{longtable}{L{1.5cm}L{2.6cm}L{3.4cm}L{3.4cm}L{3.2cm}}
\caption{关键用例规约}\\
\toprule
编号 & 触发条件 & 主成功场景 & 异常或替代场景 & 验收标准 \\
\midrule
\endfirsthead
\toprule
编号 & 触发条件 & 主成功场景 & 异常或替代场景 & 验收标准 \\
\midrule
\endhead
UC-01 & 用户进入总览页 & 系统加载总览、建筑、楼层风险和趋势数据 & 后端未启动时显示接口错误提示 & KPI 与接口返回一致 \\
UC-02 & 用户设置查询条件 & 系统按建筑、楼层、时间和数量返回记录 & 条件为空时返回默认范围；无数据时显示空状态 & 表格字段完整且数量正确 \\
UC-03 & 用户点击导出 & 后端按筛选条件生成 CSV 下载 & 无数据时导出空结果或提示无记录 & CSV 可打开且字段一致 \\
UC-04 & 用户切换统计范围 & 系统刷新异常、趋势、楼层、设备和建议模块 & 健康楼层只显示健康结论 & 异常条数与筛选范围一致 \\
UC-05 & 用户点击三维楼层 & 系统跳转统计分析并锁定建筑楼层 & 点击健康楼层时不展示空图表 & 页面联动准确 \\
UC-06 & 用户点击异常解释 & 系统返回触发规则、指标证据和建议动作 & 记录不存在时返回空对象 & 解释内容可支持运维判断 \\
UC-07 & 用户创建工单 & 系统选择异常、负责人并生成处理中工单 & 重复创建时由用户确认是否继续 & 工单刷新后仍存在 \\
UC-08 & 用户完成工单 & 系统更新状态、排序和颜色 & 工单不存在时返回 404 & 已完成工单置后且绿色显示 \\
UC-09 & 用户发起问答 & 系统检索知识库并可选调用外部模型 & 外部模型失败时回退本地回答 & 回答包含项目数据或知识库依据 \\
UC-10 & AI 客户端调用 MCP & MCP Server 调用同一服务层返回数据或报告 & transport 配置错误时启动失败并提示 & MCP 工具可列出并调用 \\
\bottomrule
\end{longtable}

\section{功能需求}
\subsection{需求优先级定义}
本项目采用 Must、Should、Could 三档优先级。Must 表示最终演示和验收必须具备；Should 表示对系统完整性有明显帮助，当前版本已实现或基本实现；Could 表示可作为后续扩展。

\begin{longtable}{p{2cm}p{3.5cm}p{1.7cm}p{5.3cm}p{2.2cm}}
\caption{功能需求列表}\\
\toprule
编号 & 功能名称 & 优先级 & 需求描述 & 实现证据 \\
\midrule
\endfirsthead
\toprule
编号 & 功能名称 & 优先级 & 需求描述 & 实现证据 \\
\midrule
\endhead
FR-01 & 数据集与数据字典 & Must & 系统应提供 4,864 条建筑能耗样例数据，字段含义、类型、单位和用途应可追溯。 & \code{data/} \\
FR-02 & 数据元信息 & Must & 系统应返回字段列表、建筑清单、记录数量、建筑数量和时间范围。 & \code{/dataset-meta} \\
FR-03 & 数据总览 & Must & 系统应展示总记录数、建筑数、平均 COP、异常记录数、时间范围和能耗合计。 & \code{/overview} \\
FR-04 & 数据浏览 & Must & 系统应支持按建筑、楼层、开始时间、结束时间和数量上限筛选能耗记录。 & \code{/records} \\
FR-05 & CSV 导出 & Should & 系统应支持按当前筛选条件导出 CSV 文件。 & \code{/export/csv} \\
FR-06 & 时间序列统计 & Must & 系统应支持小时、日、周、月粒度汇总电耗、水耗、空调电耗、制冷量和 COP。 & \code{/analytics/time-summary} \\
FR-07 & 建筑对比 & Must & 系统应比较各建筑总电耗、水耗、空调电耗、制冷量和平均 COP。 & \code{/analytics/building-comparison} \\
FR-08 & COP 排名 & Must & 系统应按建筑平均 COP 排名，识别制冷效率差异。 & \code{/analytics/cop-ranking} \\
FR-09 & 异常识别 & Must & 系统应依据设备状态、建筑基线、COP 阈值和夜间负荷规则识别异常。 & \code{analysis_service.py} \\
FR-10 & 异常明细 & Must & 系统应在选定建筑/楼层/时间范围内优先展示异常记录。 & \code{/analytics/anomalies} \\
FR-11 & 异常原因统计 & Should & 系统应按异常原因统计数量，用于图表展示和诊断。 & \code{/analytics/anomaly-reasons} \\
FR-12 & 异常解释 & Must & 系统应对单条异常输出触发规则、指标证据、严重程度和建议动作。 & \code{/anomaly-explanations} \\
FR-13 & 楼层分析 & Must & 系统应派生楼层标签并统计楼层能耗、COP、异常数量和健康状态。 & \code{/floor-summary} \\
FR-14 & 设备分析 & Should & 系统应统计设备点位、设备类型、状态、最近出现时间和维护提示。 & \code{/equipment-summary} \\
FR-15 & 三维风险视图 & Must & 系统应以可拖拽三维楼宇展示楼层健康状态，并支持点击联动统计分析。 & 前端总览页 \\
FR-16 & 工单闭环 & Must & 系统应支持从异常创建工单、分配负责人、完成工单和持久化状态。 & \code{/work-orders} \\
FR-17 & 决策报告 & Should & 系统应生成运营日报，汇总风险、工单、优化建议和收益模拟。 & \code{/operation-report} \\
FR-18 & 智能问答 & Should & 系统应基于本地知识库回答问题，并在配置外部模型时增强回答。 & \code{/assistant/query} \\
FR-19 & 外部模型选择 & Should & 页面应展示可用模型选项，允许选择不同 OpenAI-compatible 提供商。 & \code{/assistant/providers} \\
FR-20 & MCP Server & Must & 系统应通过 MCP Tools/Resources 暴露数据、分析、异常解释、知识检索和问答能力。 & \code{mcp_server.py} \\
\bottomrule
\end{longtable}

\section{数据需求}
\subsection{数据规模与时间范围}
最终数据集位于 \code{data/samples/energy_records.csv}，包含 4,864 条原始记录、16 个原始字段、4 栋建筑，时间范围为 2026-01-01 00:00:00 至 2026-06-01 21:00:00。分析服务会在运行时派生楼层、区域、设备类型、COP、动态阈值、异常标记和异常原因等字段，分析层共形成 30 个字段。

\begin{table}[H]
\centering
\caption{数据集关键指标}
\begin{tabularx}{\textwidth}{p{4cm}Y}
\toprule
指标 & 当前取值 \\
\midrule
原始记录数 & 4,864 条 \\
建筑数量 & 4 栋：综合教学楼A、行政办公楼B、图书信息楼C、科研实验楼D \\
原始字段数 & 16 个 \\
分析层字段数 & 30 个 \\
楼层标签 & 1F、2F、3F、4F、5F、B1 机房、RF 屋顶 \\
建筑-楼层组合 & 14 个 \\
设备点位 & 28 个派生运维设备点位 \\
异常记录 & 351 条分析异常 \\
\bottomrule
\end{tabularx}
\end{table}

\subsection{核心字段}
\begin{longtable}{p{3.7cm}p{2.2cm}p{7.6cm}}
\caption{核心数据字段}\\
\toprule
字段 & 类型 & 说明 \\
\midrule
\endfirsthead
\toprule
字段 & 类型 & 说明 \\
\midrule
\endhead
\code{record_id} & string & 能耗记录唯一编号 \\
\code{building_id} & string & 建筑唯一编号，例如 BLD-A \\
\code{building_name} & string & 建筑展示名称 \\
\code{building_type} & string & 建筑类型，用于不同业务场景解释 \\
\code{timestamp} & datetime & 采集时间戳，当前粒度为 3 小时 \\
\code{electricity_kwh} & float & 当前时间粒度下总电耗 \\
\code{water_m3} & float & 当前时间粒度下用水量 \\
\code{hvac_kwh} & float & 空调系统电耗 \\
\code{cooling_load_kwh} & float & 制冷负荷折算值 \\
\code{environment_temp_c} & float & 室外环境温度 \\
\code{humidity_rh} & float & 相对湿度 \\
\code{occupancy_density_per_100m2} & float & 每百平方米人员密度 \\
\code{equipment_id} & string & 原始或派生设备编号 \\
\code{equipment_status} & string & 设备状态，normal 或 abnormal \\
\code{floor_label} & derived & 运行时派生楼层标签 \\
\code{average_cop} & derived & 制冷量与空调电耗比值，用于能效判断 \\
\code{is_anomaly} & derived & 是否触发异常规则 \\
\code{anomaly_reason} & derived & 异常原因说明 \\
\bottomrule
\end{longtable}

\section{外部接口需求}
\subsection{REST API}
REST API 前缀为 \code{/api/v1}，前端通过 \code{frontend/src/lib/api.js} 统一调用。接口应返回 JSON，并对无数据、参数错误或文件异常给出明确错误信息。

\begin{longtable}{p{4.2cm}p{2.2cm}p{7.5cm}}
\caption{REST API 需求}\\
\toprule
路径 & 方法 & 功能 \\
\midrule
\endfirsthead
\toprule
路径 & 方法 & 功能 \\
\midrule
\endhead
\code{/health} & GET & 健康检查 \\
\code{/overview} & GET & 系统总览指标 \\
\code{/dataset-meta} & GET & 数据集元信息 \\
\code{/buildings} & GET & 建筑下拉选项 \\
\code{/records} & GET & 能耗记录查询 \\
\code{/analytics/time-summary} & GET & 时间序列汇总 \\
\code{/analytics/building-comparison} & GET & 建筑对比 \\
\code{/analytics/cop-ranking} & GET & COP 排名 \\
\code{/analytics/anomalies} & GET & 异常明细 \\
\code{/analytics/anomaly-explanations/\{record_id\}} & GET & 单条异常解释 \\
\code{/analytics/floor-summary} & GET & 楼层汇总 \\
\code{/analytics/equipment-summary} & GET & 设备汇总 \\
\code{/analytics/operation-report} & GET & 运营日报 \\
\code{/work-orders} & GET/POST & 查询和创建持久化工单 \\
\code{/work-orders/\{id\}} & PATCH & 更新工单状态和备注 \\
\code{/assistant/query} & POST & 智能问答 \\
\code{/assistant/providers} & GET & 可用外部模型选项 \\
\bottomrule
\end{longtable}

\subsection{MCP 接口}
MCP Server 应支持 stdio 和 streamable-http 两种启动模式。MCP Tools 应覆盖数据元信息、建筑清单、能耗记录查询、总览、时间汇总、建筑对比、COP 排名、异常、异常解释、楼层汇总、设备汇总、工单建议、优化建议、运营报告、知识库检索和问答。MCP Resources 应至少包括数据集元信息、建筑清单、运营报告和知识库入口。

\subsection{环境变量接口}
真实 API Key 只能存放在仓库根目录 \code{.env}。提交仓库和最终压缩包时不得包含真实 \code{.env}。系统应提供 \code{.env.example} 作为配置模板，说明 \code{LLM_ENABLED}、\code{LLM_PROVIDER}、\code{LLM_BASE_URL}、\code{LLM_MODEL}、\code{LLM_API_KEY} 等变量。

\section{非功能需求}
\begin{longtable}{p{2cm}p{3.4cm}p{6.5cm}p{2.6cm}}
\caption{非功能需求}\\
\toprule
编号 & 类别 & 要求 & 验收方式 \\
\midrule
\endfirsthead
\toprule
编号 & 类别 & 要求 & 验收方式 \\
\midrule
\endhead
NFR-01 & 可运行性 & 同学拉取仓库后，应能根据 README 安装依赖、放置 \code{.env}、启动前后端并访问页面。 & README 演示 \\
NFR-02 & 可测试性 & 后端应提供 pytest 测试，前端应可构建，项目应提供一键验证脚本。 & \code{check-project.ps1} \\
NFR-03 & 可解释性 & 异常判断应说明触发规则和指标证据，避免黑箱结论。 & 异常解释页 \\
NFR-04 & 安全性 & 真实 API Key 不得提交；运行期工单数据不污染仓库。 & Git 配置 \\
NFR-05 & 可维护性 & REST API 和 MCP Server 应复用同一服务层，减少口径不一致。 & 代码结构 \\
NFR-06 & 性能 & 课程数据规模下，查询和图表刷新应在本地普通电脑上可交互完成。 & 人工测试 \\
NFR-07 & 可演示性 & 5 至 8 分钟内应能展示总览、查询、分析、3D、工单、报告、问答和文档。 & 演示脚本 \\
NFR-08 & 可扩展性 & 后续应可替换 CSV 为数据库、增加权限、接入真实设备和扩展模型。 & 设计说明 \\
\bottomrule
\end{longtable}

\section{需求追踪矩阵}
\begin{longtable}{p{2.2cm}p{4.2cm}p{4.2cm}p{3.5cm}}
\caption{需求追踪矩阵}\\
\toprule
需求编号 & 设计/实现位置 & 测试或验收证据 & 用户价值 \\
\midrule
\endfirsthead
\toprule
需求编号 & 设计/实现位置 & 测试或验收证据 & 用户价值 \\
\midrule
\endhead
FR-01 至 FR-04 & \code{data_loader.py}、\code{data.py}、数据浏览页 & 数据接口测试、页面查询 & 数据可查、可追溯 \\
FR-05 至 FR-08 & \code{export.py}、\code{analysis_service.py}、图表组件 & 导出测试、统计接口测试 & 管理者掌握能耗结构 \\
FR-09 至 FR-14 & 异常规则、楼层和设备分析服务 & 异常接口测试、人工验收 & 异常可解释、可定位 \\
FR-15 & \code{BuildingRiskScene.vue}、总览页联动逻辑 & 浏览器操作验证 & 风险态势直观展示 \\
FR-16 & \code{work_orders.py}、\code{work_order_store.py} & 工单接口测试、刷新验证 & 运维形成闭环 \\
FR-17 & \code{build_operation_report}、决策报告页 & 报告接口测试 & 汇报和决策支持 \\
FR-18 至 FR-19 & \code{assistant_service.py}、\code{llm_client.py} & 问答接口测试、模型配置测试 & 智能问答与模型扩展 \\
FR-20 & \code{mcp_server.py}、MCP 测试 & MCP 集成测试 & 支持 AI 客户端接入 \\
\bottomrule
\end{longtable}

\section{验收标准}
系统最终验收应满足以下条件：
\begin{enumerate}
    \item 后端自动化测试全部通过，当前基线为 75 passed。
    \item 前端生产构建成功，页面能够访问并完成核心演示路径。
    \item \code{scripts/check-project.ps1} 能正确执行并在失败时返回失败。
    \item README 能指导运行人员完成从拉取、配置、启动到访问的完整流程。
    \item SRS、SDD、SEE、SEM、测试验收、用户部署、数据接口和提交说明均已形成 PDF。
    \item 最终提交材料不包含真实 \code{.env}、API Key、\code{node_modules}、前端构建缓存和运行期工单状态。
    \item 系统演示能够覆盖总览、数据浏览、统计分析、三维楼层、工单中心、决策报告、智能问答和 MCP 说明。
\end{enumerate}
"""


SDD_ABSTRACT = r"""
本文档为《\projectname》的软件设计说明书（SDD/SDS），说明系统的总体架构、模块划分、数据设计、接口设计、异常算法、工单状态机、三维交互设计、大模型接入设计、MCP Server 设计、部署方案和关键设计取舍。文档以最终可运行代码为依据，重点说明系统如何从需求落地到可维护、可测试、可演示的工程结构。
"""


SDD_BODY = r"""
\section{文档控制}
\begin{longtable}{p{4cm}p{10.5cm}}
\toprule
项目 & 内容 \\
\midrule
文档名称 & SDD/SDS 软件设计说明书 \\
文档版本 & \docversion \\
设计对象 & 建筑能源智能管理 Web 系统、REST API、MCP Server、数据与知识库 \\
主要代码范围 & \code{backend/}、\code{frontend/}、\code{data/}、\code{knowledge_base/}、\code{scripts/} \\
设计原则 & 前后端分离、服务层复用、可解释分析、本地可运行、密钥不入库、演示优先且保留扩展性 \\
\bottomrule
\end{longtable}

\section{总体设计}
\subsection{架构风格}
系统采用前后端分离架构，并在后端旁路提供 MCP Server。前端负责交互、图表、三维楼层和用户操作；后端负责数据读取、统计分析、异常解释、工单持久化、知识库检索和大模型调用编排；MCP Server 复用后端服务层，使 AI 客户端可以调用同一套项目能力。

\subsection{总体架构图}
\begin{figure}[H]
\centering
\resizebox{0.96\textwidth}{!}{%
\begin{tikzpicture}[node distance=10mm and 12mm]
\node[box, minimum width=31mm] (browser) {浏览器用户\\Vue 工作台};
\node[process, right=of browser, minimum width=34mm] (vite) {Vite Dev Server\\代理 /api/v1};
\node[process, right=of vite, minimum width=34mm] (fastapi) {FastAPI\\REST API};
\node[process, below=of fastapi, minimum width=40mm] (services) {服务层\\分析/工单/问答/导出};
\node[data, right=of services, minimum width=30mm] (csv) {CSV\\能耗数据};
\node[data, below=of csv, minimum width=30mm] (json) {JSON\\工单状态};
\node[data, above=of csv, minimum width=30mm] (kb) {Markdown\\知识库};
\node[box, below=of browser, minimum width=31mm] (mcpclient) {MCP 客户端\\AI Agent};
\node[process, right=of mcpclient, minimum width=34mm] (mcp) {MCP Server\\Tools/Resources};
\node[box, below=of services, minimum width=34mm] (llm) {外部 LLM\\可选接入};
\draw[arrow] (browser) -- (vite);
\draw[arrow] (vite) -- (fastapi);
\draw[arrow] (fastapi) -- (services);
\draw[arrow] (services) -- (csv);
\draw[arrow] (services) -- (json);
\draw[arrow] (services) -- (kb);
\draw[arrow] (mcpclient) -- (mcp);
\draw[arrow] (mcp) -- (services);
\draw[arrow] (services) -- (llm);
\end{tikzpicture}
}
\caption{系统总体架构}
\end{figure}

\subsection{逻辑组件图}
\begin{figure}[H]
\centering
\resizebox{0.98\textwidth}{!}{%
\begin{tikzpicture}[x=1cm,y=1cm,every node/.style={font=\scriptsize}]
\node[process, minimum width=2.7cm, minimum height=0.8cm] (view) at (0,0) {DashboardView\\页面编排};
\node[process, minimum width=2.5cm, minimum height=0.8cm] (api) at (3.2,0) {api.js\\接口封装};
\node[process, minimum width=2.8cm, minimum height=0.8cm] (routes) at (6.4,0) {FastAPI Routes\\HTTP 边界};
\node[process, minimum width=2.8cm, minimum height=0.8cm] (schemas) at (9.7,0) {Schemas\\参数与响应};

\node[process, minimum width=2.9cm, minimum height=0.8cm] (analysis) at (1.6,-1.7) {Analysis Service\\统计与异常};
\node[process, minimum width=2.9cm, minimum height=0.8cm] (work) at (5.0,-1.7) {Work Order Store\\工单持久化};
\node[process, minimum width=2.9cm, minimum height=0.8cm] (assistant) at (8.4,-1.7) {Assistant Service\\知识库与模型};
\node[process, minimum width=2.9cm, minimum height=0.8cm] (mcp) at (8.4,-3.1) {MCP Server\\Tools/Resources};

\node[data, minimum width=2.4cm, minimum height=0.8cm] (csv) at (1.6,-4.7) {CSV\\能耗数据};
\node[data, minimum width=2.4cm, minimum height=0.8cm] (json) at (5.0,-4.7) {JSON\\工单状态};
\node[data, minimum width=2.4cm, minimum height=0.8cm] (kb) at (8.4,-4.7) {Markdown\\知识库};
\node[box, minimum width=2.4cm, minimum height=0.8cm] (llm) at (11.3,-1.7) {LLM Provider};

\draw[arrow] (view) -- (api);
\draw[arrow] (api) -- (routes);
\draw[arrow] (routes) -- (schemas);
\draw[arrow] (routes.south) -- ++(0,-0.45) -| (analysis.north);
\draw[arrow] (routes.south) -- ++(0,-0.45) -| (work.north);
\draw[arrow] (routes.south) -- ++(0,-0.45) -| (assistant.north);
\draw[arrow] (mcp.north) -- (assistant.south);
\draw[arrow] (analysis) -- (csv);
\draw[arrow] (work) -- (json);
\draw[arrow] (assistant) -- (kb);
\draw[arrow] (assistant) -- (llm);
\end{tikzpicture}
}
\caption{系统逻辑组件图}
\end{figure}

\subsection{分层职责}
\begin{longtable}{L{2.8cm}L{4.5cm}L{6.7cm}}
\caption{分层职责说明}\\
\toprule
层次 & 组成 & 职责说明 \\
\midrule
\endfirsthead
\toprule
层次 & 组成 & 职责说明 \\
\midrule
\endhead
表现层 & Vue 页面、组件、图表、3D 楼层 & 接收用户操作，展示 KPI、表格、图表、三维楼层、工单和问答结果。 \\
接口层 & FastAPI Routes、Pydantic Schema & 负责参数接收、校验、HTTP 响应、异常转换和前后端契约稳定。 \\
业务服务层 & 分析服务、问答服务、工单服务、导出服务 & 承载统计分析、异常解释、工单状态、报告生成和知识库检索等核心业务。 \\
协议扩展层 & MCP Server & 将同一套业务服务暴露给支持 MCP 的 AI 客户端，避免重复实现。 \\
数据层 & CSV、JSON、Markdown、环境变量 & 保存样例能耗数据、运行期工单、知识库和本地模型配置。 \\
\bottomrule
\end{longtable}

\section{模块分解}
\subsection{后端模块}
\begin{longtable}{p{4.4cm}p{4cm}p{5.8cm}}
\caption{后端模块设计}\\
\toprule
模块 & 主要文件 & 设计职责 \\
\midrule
\endfirsthead
\toprule
模块 & 主要文件 & 设计职责 \\
\midrule
\endhead
应用入口 & \code{backend/app/main.py} & 创建 FastAPI 应用、配置中间件和挂载路由 \\
路由聚合 & \code{backend/app/api/router.py} & 将 health、data、analytics、assistant、export、work-orders 路由统一挂载 \\
数据路由 & \code{routes/data.py} & 提供概览、元信息、建筑清单和记录查询接口 \\
分析路由 & \code{routes/analytics.py} & 提供时间汇总、建筑对比、COP、异常、楼层、设备和报告接口 \\
工单路由 & \code{routes/work_orders.py} & 提供持久化工单查询、创建和状态更新 \\
问答路由 & \code{routes/assistant.py} & 提供智能问答和模型选项接口 \\
数据加载服务 & \code{data_loader.py} & 校验 CSV 字段、缓存数据、按建筑和时间筛选 \\
分析服务 & \code{analysis_service.py} & 派生楼层、设备、COP、异常、解释、建议和运营报告 \\
工单存储服务 & \code{work_order_store.py} & 使用 JSON 文件保存工单，避免刷新丢失 \\
LLM 客户端 & \code{llm_client.py} & 封装 OpenAI-compatible 外部模型调用 \\
MCP Server & \code{mcp_server.py} & 暴露项目 Tools、Resources 和 Prompt \\
\bottomrule
\end{longtable}

\subsection{前端模块}
\begin{longtable}{p{4.4cm}p{4cm}p{5.8cm}}
\caption{前端模块设计}\\
\toprule
模块 & 主要文件 & 设计职责 \\
\midrule
\endfirsthead
\toprule
模块 & 主要文件 & 设计职责 \\
\midrule
\endhead
应用入口 & \code{frontend/src/main.js} & 挂载 Vue 应用 \\
主工作台 & \code{DashboardView.vue} & 管理导航、筛选、数据加载、状态和页面编排 \\
API 封装 & \code{frontend/src/lib/api.js} & 统一封装 REST API 调用和错误处理 \\
三维视图 & \code{BuildingRiskScene.vue} & 构建立体楼宇、拖拽旋转、楼层点击联动 \\
图表组件 & \code{TrendChart.vue} 等 & 展示趋势、建筑对比和异常原因 \\
通用组件 & \code{KpiCard.vue}、\code{SectionCard.vue} 等 & 统一页面布局和状态展示 \\
样式系统 & \code{frontend/src/styles.css} & 定义整体视觉、响应式布局和交互状态 \\
\bottomrule
\end{longtable}

\section{数据设计}
\subsection{数据流设计}
\begin{figure}[H]
\centering
\begin{tikzpicture}[node distance=9mm and 8mm]
\node[data] (raw) {原始 CSV\\16 字段};
\node[process, right=of raw] (validate) {字段校验\\时间转换};
\node[process, right=of validate] (derive) {派生维度\\楼层/区域/设备};
\node[process, below=of derive] (metric) {指标计算\\COP/基线/阈值};
\node[process, left=of metric] (anom) {异常识别\\原因分类};
\node[process, left=of anom] (api) {REST/MCP\\序列化输出};
\node[data, below=of api] (wo) {工单 JSON\\状态持久化};
\draw[arrow] (raw) -- (validate);
\draw[arrow] (validate) -- (derive);
\draw[arrow] (derive) -- (metric);
\draw[arrow] (metric) -- (anom);
\draw[arrow] (anom) -- (api);
\draw[arrow] (api) -- (wo);
\end{tikzpicture}
\caption{数据处理与分析流}
\end{figure}

\subsection{数据实体关系}
\begin{figure}[H]
\centering
\begin{tikzpicture}[node distance=10mm and 12mm, every node/.style={font=\scriptsize}]
\node[data, minimum width=27mm] (building) {Building\\建筑};
\node[data, right=of building, minimum width=30mm] (record) {EnergyRecord\\能耗记录};
\node[data, right=of record, minimum width=27mm] (equipment) {Equipment\\设备点位};
\node[data, below=of record, minimum width=30mm] (anomaly) {Anomaly\\异常解释};
\node[data, below=of equipment, minimum width=28mm] (order) {WorkOrder\\工单};
\node[data, below=of building, minimum width=28mm] (kb) {KnowledgeCard\\知识卡片};
\draw[arrow] (building) -- node[above]{1..n} (record);
\draw[arrow] (equipment) -- node[above]{1..n} (record);
\draw[arrow] (record) -- node[right]{触发} (anomaly);
\draw[arrow] (anomaly) -- node[above]{生成} (order);
\draw[arrow] (kb) -- node[below, sloped]{支撑解释} (anomaly);
\end{tikzpicture}
\caption{核心数据实体关系}
\end{figure}

\subsection{运行时派生字段}
原始 CSV 不直接存放楼层和异常标记，系统在服务层根据建筑、设备、时段和指标动态派生。这种设计保持原始数据轻量，同时允许在不重写数据文件的情况下扩展分析维度。关键派生逻辑包括：
\begin{enumerate}
    \item 根据建筑类型和设备代码推断设备所处楼层，例如冷水机组映射到 B1 机房，冷却塔映射到 RF 屋顶。
    \item 根据建筑业务场景推断区域名称，例如教学楼映射为教室区、公共走廊、教师办公区等。
    \item 根据制冷量与空调电耗计算平均 COP，用于能效分析。
    \item 按建筑计算电耗均值和标准差，形成动态上界。
    \item 根据设备状态、动态上界、COP 阈值和夜间负荷规则判断异常。
\end{enumerate}

\section{异常分析算法设计}
\subsection{规则组合}
系统采用可解释规则而非黑箱模型。当前规则如下：
\begin{longtable}{p{3.2cm}p{5.2cm}p{5.5cm}}
\caption{异常识别规则}\\
\toprule
规则 & 判定条件 & 输出说明 \\
\midrule
\endfirsthead
\toprule
规则 & 判定条件 & 输出说明 \\
\midrule
\endhead
设备状态异常 & \code{equipment_status} 非 normal & 优先输出“设备状态异常”，说明设备需要现场确认 \\
高于建筑动态阈值 & 当前电耗高于同建筑均值加一倍标准差 & 输出“电耗高于同建筑基线”，说明负荷显著偏高 \\
COP 低于阈值 & 平均 COP 小于 2.20 & 输出“COP低于告警阈值”，说明制冷效率偏低 \\
夜间负荷偏高 & 0 点至 6 点或 22 点后负荷高于建筑基线 1.1 倍 & 输出“夜间负荷偏高”，提示关停策略或值班负荷异常 \\
\bottomrule
\end{longtable}

\subsection{异常解释生成}
异常解释并不只返回“异常”两个字，而是返回可被运维人员理解的结构化对象：记录编号、建筑、楼层、区域、设备、设备类型、时间、严重程度、异常原因、结论、关键指标、触发规则和建议动作。这样前端可以在弹窗或详情区域展示证据链，MCP 客户端也可以直接把解释作为回答依据。

\subsection{异常分析时序图}
\begin{figure}[H]
\centering
\resizebox{0.98\textwidth}{!}{%
\begin{tikzpicture}[x=1cm,y=1cm,every node/.style={font=\scriptsize}]
\node[box, minimum width=2.1cm, minimum height=0.85cm] (s1) at (0,0) {1 用户\\选择范围};
\node[process, minimum width=2.5cm, minimum height=0.85cm] (s2) at (2.9,0) {2 前端\\组织参数};
\node[process, minimum width=2.8cm, minimum height=0.85cm] (s3) at (6.0,0) {3 Analytics Route\\接收请求};
\node[process, minimum width=2.8cm, minimum height=0.85cm] (s4) at (9.2,0) {4 Analysis Service\\计算异常};
\node[data, minimum width=2.2cm, minimum height=0.85cm] (s5) at (12.2,0) {5 CSV\\筛选记录};
\node[process, minimum width=3.0cm, minimum height=0.85cm] (s6) at (9.2,-1.7) {6 汇总返回\\明细/原因/建议};
\node[box, minimum width=2.6cm, minimum height=0.85cm] (s7) at (2.9,-1.7) {7 前端展示\\表格与图表};
\draw[arrow] (s1) -- (s2);
\draw[arrow] (s2) -- (s3);
\draw[arrow] (s3) -- (s4);
\draw[arrow] (s4) -- (s5);
\draw[arrow] (s5.south) |- (s6.east);
\draw[arrow] (s6) -- (s7);
\draw[arrow] (s7.west) -- ++(-2.0,0) |- (s1.south);
\end{tikzpicture}
}
\caption{异常分析请求时序}
\end{figure}

\subsection{工单处理时序图}
\begin{figure}[H]
\centering
\resizebox{0.98\textwidth}{!}{%
\begin{tikzpicture}[x=1cm,y=1cm,every node/.style={font=\scriptsize}]
\node[box, minimum width=2.1cm, minimum height=0.85cm] (w1) at (0,0) {1 运维人员\\选择异常};
\node[process, minimum width=2.6cm, minimum height=0.85cm] (w2) at (3.0,0) {2 工单中心\\负责人/备注};
\node[process, minimum width=2.7cm, minimum height=0.85cm] (w3) at (6.2,0) {3 Work Order API\\创建请求};
\node[process, minimum width=2.8cm, minimum height=0.85cm] (w4) at (9.5,0) {4 Store\\编号与状态};
\node[data, minimum width=2.4cm, minimum height=0.85cm] (w5) at (12.7,0) {5 JSON\\持久化};
\node[process, minimum width=2.9cm, minimum height=0.85cm] (w6) at (9.5,-1.7) {6 返回处理中\\置顶黄色};
\node[box, minimum width=2.6cm, minimum height=0.85cm] (w7) at (3.0,-1.7) {7 页面刷新\\状态保留};
\draw[arrow] (w1) -- (w2);
\draw[arrow] (w2) -- (w3);
\draw[arrow] (w3) -- (w4);
\draw[arrow] (w4) -- (w5);
\draw[arrow] (w5.south) |- (w6.east);
\draw[arrow] (w6) -- (w7);
\draw[arrow] (w7.west) -- ++(-2.0,0) |- (w1.south);
\end{tikzpicture}
}
\caption{工单创建与持久化时序}
\end{figure}

\section{工单状态机设计}
\begin{figure}[H]
\centering
\resizebox{0.9\textwidth}{!}{%
\begin{tikzpicture}[x=1cm,y=1cm,every node/.style={font=\small}]
\node[process, minimum width=2.7cm, minimum height=0.9cm] (create) at (0,0) {选择异常\\创建工单};
\node[process, minimum width=2.7cm, minimum height=0.9cm] (doing) at (3.8,0) {处理中\\置顶黄色};
\node[process, minimum width=2.7cm, minimum height=0.9cm] (done) at (7.6,0) {已完成\\绿色靠后};
\draw[arrow] (create) -- node[above, fill=white, inner sep=1pt]{生成} (doing);
\draw[arrow] (doing) -- node[above, fill=white, inner sep=1pt]{完成} (done);
\node[font=\footnotesize, text=gray!70] at (3.8,-1.15)
{说明：课程演示中不保留“待处理”中间态，创建成功即进入处理中。};
\end{tikzpicture}
}
\caption{异常工单状态机}
\end{figure}

工单中心将“待处理”简化为“创建后即处理中”，避免课程演示中出现无实际操作意义的状态。状态排序规则为：处理中工单优先显示，已完成工单显示在后部。工单写入 \code{data/runtime/work_orders.json}，该目录被 Git 忽略，保证演示刷新后状态保留，但不会污染代码仓库。

\section{三维楼层交互设计}
三维楼层视图位于总览页，用颜色表达建筑楼层健康状态。绿色代表健康，红色代表异常风险，点击楼层后跳转到统计分析页并自动填入建筑和楼层筛选。三维视图使用前端 CSS 3D 和交互逻辑完成，不依赖大型 3D 引擎，从而降低安装成本并保持课程演示稳定。

\begin{table}[H]
\centering
\caption{三维楼层交互规则}
\begin{tabularx}{\textwidth}{p{4cm}Y}
\toprule
交互 & 系统行为 \\
\midrule
拖拽视图 & 改变整体旋转角度，支持 360 度观察建筑群 \\
点击异常楼层 & 切换到统计分析页，锁定对应建筑和楼层，展示异常明细 \\
点击健康楼层 & 切换到统计分析页，仅展示健康提示块，不展示无意义的空图表 \\
切换筛选范围 & 统计分析按建筑、楼层、时间重新加载，数据浏览不被联动污染 \\
\bottomrule
\end{tabularx}
\end{table}

\section{智能问答与外部模型设计}
\subsection{本地知识库优先}
系统的问答设计以本地知识库为基础，确保在没有外部 API Key 或网络不可用的情况下仍能回答典型问题。本地知识库包括异常诊断、设备维护、指标解释、演示问题、RAG 检索卡片等内容。

\subsection{外部模型可选增强}
外部模型通过 OpenAI-compatible 接口统一接入，支持 NVIDIA、Groq、OpenRouter、SiliconFlow 等提供商。前端展示模型选项，用户可以选择模型；后端在模型不可用时自动回退本地回答。真实密钥只能来自根目录 \code{.env}，不得写入代码或文档。

\section{MCP Server 设计}
MCP Server 与 REST API 共享服务层，其设计目的不是另写一套后端，而是让支持 MCP 的 AI 客户端可以直接调用项目能力。MCP 工具划分如下：
\begin{longtable}{p{4.5cm}p{9.2cm}}
\caption{MCP Tools 设计}\\
\toprule
工具类别 & 工具名称 \\
\midrule
\endfirsthead
\toprule
工具类别 & 工具名称 \\
\midrule
\endhead
数据访问 & \code{get_dataset_meta}、\code{list_buildings}、\code{query_energy_records} \\
总体统计 & \code{get_energy_overview}、\code{get_time_summary}、\code{get_building_comparison}、\code{get_cop_ranking} \\
异常诊断 & \code{get_anomalies}、\code{get_anomaly_reasons}、\code{explain_anomaly} \\
楼层设备 & \code{get_floor_summary}、\code{get_equipment_summary} \\
运维报告 & \code{suggest_anomaly_work_orders}、\code{get_optimization_recommendations}、\code{get_operation_report} \\
知识与问答 & \code{search_energy_knowledge}、\code{ask_energy_assistant} \\
\bottomrule
\end{longtable}

\section{部署设计}
\subsection{本地开发部署}
系统部署采用轻量本地方式，适合课程验收：
\begin{enumerate}
    \item 根目录创建 Python 虚拟环境并安装 \code{backend/requirements.txt}。
    \item 使用 \code{scripts/start-backend.ps1} 启动 FastAPI，默认端口 8000。
    \item 进入 \code{frontend/} 安装 npm 依赖，使用 \code{npm run dev} 或脚本启动 Vite。
    \item 浏览器访问 \code{http://127.0.0.1:5173}。
    \item 如需 MCP，运行 \code{scripts/start-mcp.ps1}。
\end{enumerate}

\subsection{部署图}
\begin{figure}[H]
\centering
\begin{tikzpicture}[node distance=10mm and 12mm]
\node[box, minimum width=35mm] (pc) {演示电脑\\Windows + PowerShell};
\node[process, below left=of pc, minimum width=35mm] (py) {Python 3.11\\FastAPI 8000};
\node[process, below right=of pc, minimum width=35mm] (node) {Node.js\\Vite 5173};
\node[process, below=of py, minimum width=35mm] (mcp) {MCP Server\\stdio/8765};
\node[data, below=of node, minimum width=35mm] (files) {CSV/JSON/Markdown\\本地文件};
\draw[arrow] (pc) -- (py);
\draw[arrow] (pc) -- (node);
\draw[arrow] (py) -- (files);
\draw[arrow] (node) -- (py);
\draw[arrow] (mcp) -- (py);
\draw[arrow] (mcp) -- (files);
\end{tikzpicture}
\caption{本地演示部署结构}
\end{figure}

\section{关键设计取舍}
\begin{longtable}{p{3.4cm}p{3.4cm}p{7cm}}
\caption{设计取舍}\\
\toprule
问题 & 当前选择 & 原因 \\
\midrule
\endfirsthead
\toprule
问题 & 当前选择 & 原因 \\
\midrule
\endhead
数据库还是 CSV & CSV + JSON & 课程演示部署轻量，数据规模可控，便于提交和复现 \\
机器学习还是规则 & 可解释规则 & 无需训练数据，结果稳定，可清晰向评审说明 \\
单一 Web 还是 Web + MCP & Web + MCP & 同时满足人工演示和 AI 客户端接入要求 \\
外部模型强依赖还是可选 & 可选增强 & 防止 Key、网络或额度影响系统基本演示 \\
工单状态是否复杂 & 简化状态机 & 课程项目突出闭环，不引入复杂审批流 \\
3D 引擎还是轻量 CSS 3D & 轻量 3D & 减少依赖，保证同学拉取后容易运行 \\
\bottomrule
\end{longtable}
"""


SEE_ABSTRACT = r"""
本文档为《\projectname》的软件经济分析与评价（SEE），覆盖开发成本、维护成本、部署成本、定价策略、资金来源、收益测算、ROI、敏感性和综合经济评价。由于本项目为课程项目，文档同时采用课程实际投入口径和小规模校园试点口径，说明系统在课程交付和后续推广中的经济合理性。
"""


SEE_BODY = r"""
\section{文档控制}
\begin{longtable}{p{4cm}p{10.5cm}}
\toprule
项目 & 内容 \\
\midrule
文档名称 & SEE 软件经济分析与评价 \\
文档版本 & \docversion \\
评价范围 & 软件开发、部署运行、维护、定价、资金、收益、财务指标和风险敏感性 \\
评价对象 & 建筑能源智能管理与运维优化系统最终演示版本 \\
估算口径 & 课程项目影子成本 + 小规模校园试点假设 \\
\bottomrule
\end{longtable}

\section{经济评价范围}
\subsection{纳入范围}
本次经济评价纳入以下内容：
\begin{enumerate}
    \item 建筑能耗数据管理、查询、统计和导出能力。
    \item 后端 REST API、MCP Server、外部模型配置和知识库问答能力。
    \item 前端 Web 工作台，包括总览、数据浏览、统计分析、工单中心、决策报告和智能问答。
    \item 样例数据构造、数据字典、知识库、测试脚本、部署脚本和最终交付文档。
    \item 项目管理、测试、整合、系统展示和最终材料整理工作。
\end{enumerate}

\subsection{不纳入范围}
以下费用不纳入本次估算：真实传感器采购、楼宇自控系统接口费、生产级账号权限系统、正式商业合同税费、销售费用、法务费用和长期运维人员值班费用。

\section{开发成本估算}
\subsection{WBS 成本分解}
\begin{longtable}{p{4cm}p{5.8cm}p{2cm}p{2cm}}
\caption{工作分解结构与工时估算}\\
\toprule
工作包 & 主要内容 & 工时 & 占比 \\
\midrule
\endfirsthead
\toprule
工作包 & 主要内容 & 工时 & 占比 \\
\midrule
\endhead
需求与计划 & 作业要求分析、项目范围、任务拆解、接口契约 & 30 & 12.5\% \\
数据与知识库 & 数据源调研、样例数据生成、数据字典、知识库素材 & 42 & 17.5\% \\
后端开发 & FastAPI、分析服务、导出、工单、问答、MCP & 55 & 22.9\% \\
前端开发 & Vue 工作台、图表、三维视图、工单和交互 & 52 & 21.7\% \\
测试与联调 & pytest、前端构建、浏览器验收、修复问题 & 28 & 11.7\% \\
文档与提交 & SRS、SDD、SEE、SEM、验收、用户手册、PDF & 33 & 13.7\% \\
\midrule
合计 & 完成最终课程项目交付 & 240 & 100\% \\
\bottomrule
\end{longtable}

\subsection{成本构成图}
\begin{figure}[H]
\centering
\begin{tikzpicture}[x=0.055cm,y=0.42cm, every node/.style={font=\scriptsize}]
\draw[fill=cyan!25, draw=cyan!60!black] (0,0) rectangle (30,1);
\draw[fill=teal!25, draw=teal!60!black] (30,0) rectangle (72,1);
\draw[fill=orange!25, draw=orange!70!black] (72,0) rectangle (127,1);
\draw[fill=red!20, draw=red!60!black] (127,0) rectangle (179,1);
\draw[fill=purple!20, draw=purple!60!black] (179,0) rectangle (207,1);
\draw[fill=gray!20, draw=gray!60!black] (207,0) rectangle (240,1);
\node at (15,1.45) {需求 30h};
\node at (51,1.45) {数据 42h};
\node at (99.5,1.45) {后端 55h};
\node at (153,1.45) {前端 52h};
\node at (193,1.45) {测试 28h};
\node at (223.5,1.45) {文档 33h};
\node[align=center] at (120,-0.8) {总工时 240h，其中开发实现约占 44.6\%，测试和文档约占 25.4\%};
\end{tikzpicture}
\caption{课程项目工时构成}
\end{figure}

\subsection{人员成本}
按课程项目影子成本估算，人工单价取 80 元/小时。该单价不是实际工资，而是用于把学生投入转化为软件经济分析口径。

\begin{table}[H]
\centering
\caption{人员投入成本}
\begin{tabularx}{\textwidth}{p{2.5cm}Yp{2cm}p{2.4cm}}
\toprule
成员 & 主要职责 & 工时 & 成本 \\
\midrule
许奕 & 项目规划、整合、测试、文档、最终封版 & 80 & 6,400 元 \\
王天一 & 后端接口、架构、分析服务、MCP、测试 & 55 & 4,400 元 \\
马源胜 & 数据集、知识库、数据源调研、AI 配置 & 50 & 4,000 元 \\
周由 & 前端页面、图表、三维风险、交互联调 & 55 & 4,400 元 \\
\midrule
合计 & 需求、设计、开发、测试、文档、演示 & 240 & 19,200 元 \\
\bottomrule
\end{tabularx}
\end{table}

\subsection{工具与环境成本}
开发工具主要采用开源或免费方案。Python、FastAPI、Pandas、Vue、Vite、ECharts、GitHub 免费仓库均不产生直接软件授权费。考虑电脑折旧、网络和少量外部模型调试额度，课程阶段工具环境成本估算为 1,200 元。因此课程阶段一次性开发成本为：
\[
19,200 + 1,200 = 20,400 \text{ 元}
\]

\section{运行维护成本}
\subsection{本地演示成本}
课程验收以本地部署为主，不需要云服务器和公网域名。只要演示电脑安装 Python、Node.js 和项目依赖，即可完成完整演示。本地演示的直接现金成本近似为 0，但需要计入配置、测试和排错时间成本。

\subsection{校园试点运行成本}
\begin{longtable}{p{4cm}p{2.8cm}p{2.8cm}p{4.4cm}}
\caption{校园试点年运行成本}\\
\toprule
项目 & 月费用 & 年费用 & 说明 \\
\midrule
\endfirsthead
\toprule
项目 & 月费用 & 年费用 & 说明 \\
\midrule
\endhead
云服务器 & 100 元 & 1,200 元 & 2 核 4G 可支撑小规模试点 \\
存储与备份 & 30 元 & 360 元 & 保存数据、日志和工单 \\
外部大模型 API & 100--500 元 & 1,200--6,000 元 & 可配置关闭，本地知识库兜底 \\
域名与 HTTPS & 50 元 & 600 元 & 校园内网部署可省略 \\
运维人力 & 2,160 元 & 25,920 元 & 数据检查、规则维护、故障处理和文档维护 \\
\midrule
合计 & 2,440--2,840 元 & 29,280--34,080 元 & 不含真实传感器与接口费 \\
\bottomrule
\end{longtable}

\section{收益分析}
\subsection{直接节能收益}
假设校园 4 栋建筑年电耗为 300,000 kWh，电价按 0.8 元/kWh 计算。系统通过异常识别、COP 监控、设备状态提醒和工单闭环，保守节能率取 5\%：
\[
\text{年节电量}=300,000 \times 5\% = 15,000 \text{ kWh}
\]
\[
\text{年节能收益}=15,000 \times 0.8 = 12,000 \text{ 元}
\]

\subsection{人工节约}
系统减少人工查表、人工定位异常和重复沟通。假设每个工作日节约 1 小时，全年 250 个工作日，人工机会成本 80 元/小时：
\[
1 \times 250 \times 80 = 20,000 \text{ 元/年}
\]

\subsection{异常损失减少}
异常设备长时间运行可能带来额外电费、设备磨损和服务投诉。保守假设每年避免 5 次中等异常，每次减少损失 2,000 元：
\[
5 \times 2,000 = 10,000 \text{ 元/年}
\]

\subsection{管理收益}
管理收益难以完全货币化，但对学校后勤管理和课程项目评审有重要价值：数据口径统一、异常定位更快、处理过程可追踪、报告自动生成、AI 客户端可调用系统能力、后续可扩展到真实部署。

\section{财务评价}
\subsection{课程项目口径}
课程项目一次性开发成本约 20,400 元。项目不产生直接收入，但形成完整软件资产、工程文档、演示系统、团队协作经验和后续复用能力。从课程评价角度，投入与成果匹配。

\subsection{四栋建筑试点口径}
四栋建筑试点情况下，年直接收益为：
\[
12,000 + 20,000 + 10,000 = 42,000 \text{ 元}
\]
若一次性实施成本取 25,000 元，年运行维护成本取 30,000 元，则第一年净收益为：
\[
42,000 - 25,000 - 30,000 = -13,000 \text{ 元}
\]
第一年 ROI 为：
\[
\frac{-13,000}{25,000 + 30,000} = -23.6\%
\]
第二年起不再承担一次性实施成本，年度净收益为：
\[
42,000 - 30,000 = 12,000 \text{ 元}
\]
第二年起 ROI 为：
\[
\frac{12,000}{30,000}=40\%
\]

\subsection{二十栋建筑扩展口径}
若扩展到 20 栋建筑，平台维护成本不会随建筑数量线性增长，而节能收益和异常减少收益会显著提升。假设年总收益 120,000 元，年运行维护成本 45,000 元，一次性实施成本 60,000 元，则：
\[
\text{年净收益}=120,000-45,000=75,000 \text{ 元}
\]
\[
\text{投资回收期}=\frac{60,000}{75,000}=0.8 \text{ 年}
\]
该结果说明系统在小范围试点时主要体现管理价值，在多建筑场景下具备更明确的经济收益。

\subsection{方案对比}
\begin{longtable}{L{3cm}L{3.2cm}L{3.2cm}L{3.2cm}L{2cm}}
\caption{不同部署规模的经济性对比}\\
\toprule
方案 & 一次性投入 & 年运行成本 & 年直接收益 & 评价 \\
\midrule
\endfirsthead
\toprule
方案 & 一次性投入 & 年运行成本 & 年直接收益 & 评价 \\
\midrule
\endhead
课程演示 & 20,400 元影子成本 & 近似 0 元 & 不产生直接收入 & 适合课程验收和能力展示 \\
4 栋试点 & 25,000 元 & 约 30,000 元 & 约 42,000 元 & 第二年起具备正向收益 \\
20 栋推广 & 60,000 元 & 约 45,000 元 & 约 120,000 元 & 回收期约 0.8 年 \\
生产级产品 & 视接口和权限复杂度确定 & 需加入安全、审计、运维成本 & 取决于客户数和节能率 & 适合后续产品化，不属于本期范围 \\
\bottomrule
\end{longtable}

\section{定价策略}
\subsection{项目制私有化部署}
适合学校、园区或企业内部使用。建议基础部署费 50,000 至 120,000 元，定制接口费按真实系统对接复杂度另计，年维护费按部署费 15\% 至 20\% 计取。优点是一次性收入明确，缺点是交付定制化压力较大。

\subsection{订阅制 SaaS}
适合后续产品化和多客户标准化使用。基础版可定价 1,000 至 3,000 元/月，专业版可定价 3,000 至 8,000 元/月，企业版按建筑数量、数据量、接口数量和模型调用量报价。该模式现金流稳定，但需要补充多租户、安全、权限和运维能力。

\subsection{咨询加平台混合模式}
当前项目成熟度更适合“能源诊断咨询 + 平台部署 + 后续维护”的混合模式。前期以数据整理和节能诊断服务进入，中期提供平台部署和培训，后期收取维护费、模型调用费和扩展开发费。

\section{资金与融资}
\begin{table}[H]
\centering
\caption{资金来源分析}
\begin{tabularx}{\textwidth}{p{3cm}YY}
\toprule
阶段 & 资金来源 & 说明 \\
\midrule
课程阶段 & 自有设备、免费开源工具、少量模型测试额度 & 不需要外部融资 \\
校内试点 & 学院实验教学经费、后勤节能管理经费、创新项目经费 & 适合验证系统价值 \\
推广阶段 & 节能减排专项、企业合作、节能服务公司分成 & 以真实节能收益支撑扩展 \\
商业化阶段 & 种子资金、产品化投入、渠道合作 & 用于多租户、安全和运维体系建设 \\
\bottomrule
\end{tabularx}
\end{table}

\section{敏感性分析}
\begin{figure}[H]
\centering
\begin{tikzpicture}[node distance=9mm and 10mm]
\node[box] (benefit) {经济收益};
\node[risk, above left=of benefit] (buildings) {建筑数量};
\node[risk, above right=of benefit] (saving) {节能率};
\node[risk, below left=of benefit] (maint) {维护成本};
\node[risk, below right=of benefit] (llm) {模型费用};
\draw[arrow] (buildings) -- node[above, sloped]{正相关} (benefit);
\draw[arrow] (saving) -- node[above, sloped]{正相关} (benefit);
\draw[arrow] (maint) -- node[below, sloped]{负相关} (benefit);
\draw[arrow] (llm) -- node[below, sloped]{负相关} (benefit);
\end{tikzpicture}
\caption{经济性敏感因素}
\end{figure}

敏感性结论如下：建筑数量和节能率是收益端最关键因素；维护成本和外部模型费用是成本端关键因素。若仅管理少数建筑，系统更偏管理工具；若扩展到多楼宇并形成统一运维流程，经济性明显提升。外部模型必须保持可关闭和可替换，以避免 API 费用成为不可控成本。

\section{综合评价}
从课程项目角度，本项目以较低现金成本形成完整软件系统和交付文档，体现了良好的学习与展示价值。从校园试点角度，系统能够改善数据管理、异常定位和运维闭环，短期经济收益不一定立刻覆盖全部投入，但管理价值明确。从多建筑推广角度，系统具备正向 ROI 和较短回收期。综合判断，本项目成本可控、收益路径清晰、推广潜力合理，符合课程中软件经济分析与评价要求。
"""


SEM_ABSTRACT = r"""
本文档为《\projectname》的软件工程管理说明（SEM），覆盖项目范围、计划、组织分工、软件过程监控与控制、质量保证、配置管理、风险管理、沟通管理、变更管理和最终交付管理。文档从工程管理角度说明项目如何由初始骨架、两轮分工、两次整合发展为最终可运行、可测试、可提交的系统。
"""


SEM_BODY = r"""
\section{文档控制}
\begin{longtable}{p{4cm}p{10.5cm}}
\toprule
项目 & 内容 \\
\midrule
文档名称 & SEM 软件工程管理说明 \\
文档版本 & \docversion \\
管理范围 & 范围、计划、组织、过程控制、质量、风险、配置、沟通、交付 \\
项目组织 & 四人课程项目小组 \\
管理模式 & 文档先行、目录分工、两轮任务、集中整合、最终封版 \\
\bottomrule
\end{longtable}

\section{项目范围管理}
\subsection{本期范围}
本期范围包括：建筑能耗样例数据、数据字典、FastAPI 后端、Vue 前端、三维楼层态势、统计分析、异常解释、工单闭环、决策报告、智能问答、外部模型配置、MCP Server、自动化测试、运行脚本和最终文档。

\subsection{范围排除}
不纳入本期范围的内容包括：真实传感器接入、企业级登录权限、生产数据库、高可用部署、移动端 App、长期真实节能审计和商业合同实施。范围排除的目的不是降低质量，而是在课程周期内保证核心系统闭环可以稳定完成。

\section{组织与职责}
\begin{longtable}{p{2.5cm}p{4.2cm}p{4.2cm}p{3.4cm}}
\caption{团队分工与交付物}\\
\toprule
成员 & 主要职责 & 核心交付物 & 集成边界 \\
\midrule
\endfirsthead
\toprule
成员 & 主要职责 & 核心交付物 & 集成边界 \\
\midrule
\endhead
许奕 & 项目规划、整合、测试、文档、最终封版 & README、任务说明、整合总结、最终文档、测试验证 & 统一接口、统一文档、最终质量控制 \\
王天一 & 后端与架构 & REST API、分析服务、MCP Server、后端测试 & 保持 API 契约稳定 \\
马源胜 & 数据与 AI & 样例数据、数据源调研、知识库、模型配置 & 数据字段与知识库口径稳定 \\
周由 & 前端与集成 & Vue 页面、图表、3D 风险、前后端联调 & 通过 \code{api.js} 调用接口 \\
\bottomrule
\end{longtable}

\subsection{RACI 职责矩阵}
\begin{longtable}{L{3.4cm}C{1.7cm}C{1.7cm}C{1.7cm}C{1.7cm}L{3.2cm}}
\caption{RACI 职责矩阵}\\
\toprule
活动 & 许奕 & 王天一 & 马源胜 & 周由 & 说明 \\
\midrule
\endfirsthead
\toprule
活动 & 许奕 & 王天一 & 马源胜 & 周由 & 说明 \\
\midrule
\endhead
需求与范围 & A/R & C & C & C & 负责人统一范围和验收口径 \\
后端接口 & C & A/R & C & C & 后端负责实现与测试 \\
数据与知识库 & C & C & A/R & C & 数据负责人保证字段和知识库质量 \\
前端页面 & C & C & C & A/R & 前端负责页面和交互 \\
系统整合 & A/R & C & C & C & 集中整合减少冲突 \\
测试验收 & A/R & R & C & R & 自动化与人工验收结合 \\
最终文档 & A/R & C & C & C & 正式文档由负责人统一封版 \\
\bottomrule
\end{longtable}

其中 A 表示最终负责，R 表示执行负责，C 表示参与咨询。该矩阵的作用是把“谁最终负责”和“谁具体执行”分开，避免多人协作中出现职责空白。

\section{项目计划}
\subsection{阶段划分}
\begin{figure}[H]
\centering
\resizebox{0.96\textwidth}{!}{%
\begin{tikzpicture}[node distance=7mm and 6mm]
\node[process] (init) {初始化\\骨架与 README};
\node[process, right=of init] (r1) {第一次任务\\三方独立开发};
\node[process, right=of r1] (i1) {第一次整合\\补齐基础闭环};
\node[process, right=of i1] (r2) {第二次任务\\强化演示能力};
\node[process, below=of r2] (i2) {第二次整合\\系统主线完成};
\node[process, left=of i2] (polish) {封版优化\\3D/工单/LLM/MCP};
\node[process, left=of polish] (docs) {最终文档\\SRS/SDD/SEE/SEM};
\node[process, left=of docs] (submit) {提交准备\\PDF/源码/演示};
\draw[arrow] (init) -- (r1);
\draw[arrow] (r1) -- (i1);
\draw[arrow] (i1) -- (r2);
\draw[arrow] (r2) -- (i2);
\draw[arrow] (i2) -- (polish);
\draw[arrow] (polish) -- (docs);
\draw[arrow] (docs) -- (submit);
\end{tikzpicture}
}
\caption{项目阶段路径}
\end{figure}

\subsection{里程碑}
\begin{longtable}{p{3cm}p{5.4cm}p{5.5cm}}
\caption{主要里程碑}\\
\toprule
里程碑 & 完成标准 & 证据 \\
\midrule
\endfirsthead
\toprule
里程碑 & 完成标准 & 证据 \\
\midrule
\endhead
M1 仓库初始化 & 目录结构、README、环境模板、基础文档完成 & 根目录、\code{docs/}、\code{.env.example} \\
M2 第一次整合 & 后端、前端、数据 AI 初步连通 & \code{docs/11-first-integration-summary.md} \\
M3 第二次整合 & 主要页面和接口可运行，功能闭环形成 & \code{docs/12-second-integration-summary.md} \\
M4 封版优化 & 数据扩展、3D 联动、工单持久化、统计分析优化 & 前端页面和后端测试 \\
M5 文档封版 & SRS、SDD、SEE、SEM 等正式文档生成 PDF & \code{docs/final-latex/pdf/} \\
M6 最终提交 & 源码、文档、演示材料按要求整理 & \code{期末提交材料/} \\
\bottomrule
\end{longtable}

\section{软件过程监控与控制}
\subsection{Git 控制}
项目使用 GitHub 作为统一仓库。关键控制规则如下：真实 \code{.env} 不提交；每次整合前先拉取远程；整合后运行检查脚本；功能稳定后再提交；提交信息应能表达变化内容；最终提交材料排除缓存、依赖目录和个人无关作业文件。

\subsection{接口控制}
REST API 契约以 \code{docs/06-api-contract.md} 为基础，前端只通过 \code{frontend/src/lib/api.js} 调用接口，MCP Server 复用后端服务层。这样可以降低多人协作中“前端字段名”和“后端字段名”不一致的风险。

\subsection{自动化质量控制}
项目提供 \code{scripts/check-project.ps1} 作为质量验证入口，覆盖 Python 语法、后端 pytest 和前端构建。脚本失败即退出，避免出现测试失败但仍显示成功的误判。

\subsection{过程监控闭环}
\begin{figure}[H]
\centering
\resizebox{0.86\textwidth}{!}{%
\begin{tikzpicture}[x=1cm,y=1cm,every node/.style={font=\small}]
\node[process, minimum width=2.7cm, minimum height=0.9cm] (plan) at (0,1.6) {1 计划\\任务边界};
\node[process, minimum width=2.7cm, minimum height=0.9cm] (do) at (3.8,1.6) {2 执行\\分模块开发};
\node[process, minimum width=2.7cm, minimum height=0.9cm] (check) at (7.6,1.6) {3 检查\\测试与评审};
\node[process, minimum width=2.7cm, minimum height=0.9cm] (act) at (7.6,-0.4) {4 纠偏\\修复与整合};
\node[process, minimum width=2.7cm, minimum height=0.9cm] (base) at (3.8,-0.4) {5 基线\\提交与文档};
\draw[arrow] (plan) -- (do);
\draw[arrow] (do) -- (check);
\draw[arrow] (check) -- (act);
\draw[arrow] (act) -- (base);
\draw[arrow] (base.west) -- ++(-3.8,0) -- (plan.south);
\end{tikzpicture}
}
\caption{软件过程监控与控制闭环}
\end{figure}
每轮整合均以测试通过、文档同步和安全检查作为进入下一轮的条件。该闭环强调先冻结任务边界，再执行开发、测试评审、修复整合和基线归档，避免后期反复增加范围导致提交质量失控。

\section{质量管理}
\subsection{质量目标}
\begin{enumerate}
    \item 系统能够按 README 在普通 Windows 环境复现运行。
    \item 后端接口测试、服务测试、MCP 测试和 LLM 封装测试通过。
    \item 前端生产构建通过，核心页面无阻断错误。
    \item 系统展示路径覆盖项目亮点，并能应对刷新、筛选、点击、导出和问答。
    \item 最终文档使用正式口吻，面向教师评审，不包含对话式说明。
    \item 最终材料不泄露真实 API Key。
\end{enumerate}

\subsection{质量保证矩阵}
\begin{longtable}{p{3.2cm}p{4.8cm}p{5.5cm}}
\caption{质量保证矩阵}\\
\toprule
质量活动 & 控制内容 & 输出证据 \\
\midrule
\endfirsthead
\toprule
质量活动 & 控制内容 & 输出证据 \\
\midrule
\endhead
需求确认 & 功能是否覆盖课程要求和系统展示路径 & SRS、验收报告 \\
设计确认 & 架构是否清晰、接口是否一致、数据是否可追溯 & SDD、API 文档 \\
代码验证 & 路由、服务、前端页面、脚本是否能运行 & 源码目录、构建结果 \\
自动化测试 & 后端接口、服务、MCP、LLM 封装 & pytest 结果 \\
人工验收 & 浏览器操作、3D 联动、工单持久化、报告生成 & 测试与验收报告 \\
安全控制 & \code{.env}、API Key、运行期数据是否被排除 & \code{.gitignore}、交付材料 \\
\bottomrule
\end{longtable}

\section{风险管理}
\begin{longtable}{p{3.2cm}p{1.6cm}p{1.6cm}p{5.2cm}p{2.3cm}}
\caption{风险登记表}\\
\toprule
风险 & 概率 & 影响 & 应对措施 & 当前状态 \\
\midrule
\endfirsthead
\toprule
风险 & 概率 & 影响 & 应对措施 & 当前状态 \\
\midrule
\endhead
成员提交质量不一致 & 中 & 高 & 分工文件写清边界，整合阶段统一补齐 & 已控制 \\
多人合并冲突 & 中 & 中 & 按目录和模块分工，减少同时改同一文件 & 已控制 \\
数据量不足导致演示单薄 & 中 & 高 & 扩展至 4,864 条、1 月至 6 月、派生楼层设备维度 & 已控制 \\
系统像写死数据 & 中 & 高 & 增加筛选、楼层分析、工单持久化、报告和 MCP 调用 & 已控制 \\
外部模型 Key 泄露 & 中 & 高 & 真实 Key 仅放本地 \code{.env}，发布前进行模式扫描 & 已控制 \\
外部模型不可用 & 中 & 中 & 本地知识库兜底，LLM 可配置关闭 & 已控制 \\
MCP 依赖影响运行 & 低 & 中 & requirements 声明依赖，提供单独启动脚本和测试 & 已控制 \\
PPT/视频材料衔接不足 & 中 & 中 & 软件侧交付内容完整，展示材料按最终系统截图和文档组织 & 可控制 \\
\bottomrule
\end{longtable}

\section{配置管理}
\subsection{配置项}
\begin{longtable}{p{3.5cm}p{5cm}p{5.2cm}}
\caption{配置项说明}\\
\toprule
类别 & 配置项 & 管理规则 \\
\midrule
\endfirsthead
\toprule
类别 & 配置项 & 管理规则 \\
\midrule
\endhead
源码 & \code{backend/}、\code{frontend/}、\code{scripts/} & 纳入 Git 管理，版本发布前运行验证脚本 \\
数据 & \code{data/samples/}、\code{data/dictionaries/} & 样例数据与字典纳入仓库，运行期数据排除 \\
知识库 & \code{knowledge_base/} & 作为问答和 RAG 素材纳入仓库 \\
环境模板 & \code{.env.example} & 只存占位变量，不含真实密钥 \\
真实环境 & \code{.env} & 本地私有文件，不提交、不打包 \\
运行状态 & \code{data/runtime/} & 本地生成，不提交 \\
最终材料 & \code{期末提交材料/} & 统一整理源码、PDF、说明和展示材料 \\
\bottomrule
\end{longtable}

\section{变更管理}
项目后期采用集中优化方式。原因是系统主链路已经形成，继续分散开发会增加冲突和回归风险。后期变更原则为：只接受能明显提升系统展示质量、文档质量或验收通过率的变更；每次变更后确认是否影响 README、API、测试和交付材料；涉及密钥、数据和依赖的变更必须额外确认安全性。

\section{交付管理}
\subsection{最终交付物}
最终交付应包含：源码、SRS、SDD/SDS、SEE、SEM、测试与验收报告、用户手册与部署说明、数据与接口说明、最终提交说明、PPT、演示视频或视频链接。

\subsection{排除项}
最终压缩包必须排除：\code{.env}、\code{frontend/node_modules/}、\code{frontend/dist/}、\code{data/runtime/}、\code{.pytest_cache/}、个人无关实验文件、临时日志和真实 API Key。

\section{管理结论}
从软件工程管理角度看，本项目已经完成范围定义、计划执行、多人分工、过程控制、质量验证、风险收敛和最终文档化。系统实现、正式文档和交付材料已经形成闭环，项目具备课程期末提交条件。
"""


TEST_ABSTRACT = r"""
本文档为《\projectname》的测试与验收报告，说明测试目标、测试环境、测试范围、自动化测试、人工验收场景、缺陷处理、验收矩阵和最终结论。报告用于证明系统不仅完成代码实现，而且具备可运行、可测试、可演示和可提交的质量状态。
"""


TEST_BODY = r"""
\section{测试目标}
测试目标包括：验证后端接口正确性，验证分析服务和异常规则稳定性，验证前端构建可通过，验证三维楼层、工单持久化、智能问答和 MCP 接入能够完成演示，验证最终提交材料不包含敏感文件。

\section{测试环境}
\begin{table}[H]
\centering
\caption{测试环境}
\begin{tabularx}{\textwidth}{p{4cm}Y}
\toprule
项目 & 环境 \\
\midrule
操作系统 & Windows 10/11，PowerShell \\
后端 & Python 3.11，FastAPI，Pandas，pytest \\
前端 & Node.js，Vue 3，Vite，ECharts \\
浏览器 & Microsoft Edge 或 Chrome \\
数据 & \code{data/samples/energy_records.csv}，4,864 条记录 \\
检查脚本 & \code{scripts/check-project.ps1} \\
\bottomrule
\end{tabularx}
\end{table}

\section{测试范围}
\begin{longtable}{p{3.2cm}p{6cm}p{4.6cm}}
\caption{测试范围}\\
\toprule
测试类别 & 覆盖内容 & 证据位置 \\
\midrule
\endfirsthead
\toprule
测试类别 & 覆盖内容 & 证据位置 \\
\midrule
\endhead
后端接口测试 & health、data、analytics、export、assistant、work-orders & \code{backend/tests/} \\
服务层测试 & 数据加载、知识库检索、LLM 客户端、分析逻辑 & \code{backend/tests/} \\
MCP 测试 & MCP Server 工具注册、stdio 集成、工具调用 & \code{test_mcp_server.py} \\
前端构建测试 & Vue 生产构建和资源打包 & \code{npm run build} \\
人工功能验收 & 浏览器页面、筛选、3D、工单、报告、问答 & 本报告验收场景 \\
安全控制 & \code{.env} 排除、密钥不进入交付材料 & 最终交付说明 \\
\bottomrule
\end{longtable}

\section{自动化测试}
\subsection{后端测试}
后端测试覆盖接口返回、参数筛选、异常解释、导出、问答、工单持久化、MCP Server 和 LLM 客户端封装。当前基线为 75 passed。后端测试的价值在于防止后期页面和文档优化过程中破坏已有接口。

\subsection{前端构建}
前端构建使用 \code{npm run build}。构建通过说明 Vue 文件、组件导入、Vite 配置和生产打包流程无明显错误。由于课程演示使用开发服务器，构建测试同时提供提交质量证据。

\subsection{一键验证}
\begin{figure}[H]
\centering
\begin{tikzpicture}[node distance=9mm and 12mm]
\node[process] (start) {运行\\check-project.ps1};
\node[process, right=of start] (py) {Python\\语法验证};
\node[process, right=of py] (pytest) {pytest\\后端测试};
\node[process, below=of pytest] (npm) {npm run build\\前端构建};
\node[process, left=of npm] (result) {输出结果\\失败即退出};
\draw[arrow] (start) -- (py);
\draw[arrow] (py) -- (pytest);
\draw[arrow] (pytest) -- (npm);
\draw[arrow] (npm) -- (result);
\end{tikzpicture}
\caption{一键验证流程}
\end{figure}

\section{人工验收场景}
\begin{longtable}{p{2cm}p{4.2cm}p{5.2cm}p{2.4cm}}
\caption{人工验收用例}\\
\toprule
编号 & 场景 & 操作步骤 & 预期结果 \\
\midrule
\endfirsthead
\toprule
编号 & 场景 & 操作步骤 & 预期结果 \\
\midrule
\endhead
AT-01 & 启动系统 & 启动后端、启动前端、访问首页 & 页面加载，健康状态正常 \\
AT-02 & 查看总览 & 进入总览页 & KPI、趋势和 3D 楼宇显示 \\
AT-03 & 拖拽三维视图 & 鼠标拖动建筑群 & 视图旋转，楼层颜色保持 \\
AT-04 & 点击异常楼层 & 点击红色楼层 & 跳转统计分析并锁定建筑楼层 \\
AT-05 & 点击健康楼层 & 点击绿色楼层 & 展示健康提示，不展示空分析模块 \\
AT-06 & 数据浏览查询 & 设置建筑、楼层、时间和数量 & 表格记录与筛选条件一致 \\
AT-07 & 导出数据 & 点击导出 CSV & 下载文件可打开 \\
AT-08 & 统计分析 & 选择建筑/楼层刷新分析 & 异常明细、图表、楼层设备数据更新 \\
AT-09 & 异常解释 & 点击某条异常解释 & 显示触发规则、指标和建议 \\
AT-10 & 创建工单 & 选择异常和负责人后创建 & 生成处理中工单并置顶 \\
AT-11 & 完成工单 & 点击完成并刷新页面 & 工单保持已完成状态 \\
AT-12 & 决策报告 & 进入报告页生成报告 & 展示摘要、风险、建议和收益模拟 \\
AT-13 & 智能问答 & 提问当前异常风险 & 返回知识库引用和项目数据相关回答 \\
AT-14 & MCP 启动 & 运行 MCP 启动脚本 & MCP Server 可被客户端接入 \\
\bottomrule
\end{longtable}

\section{验收矩阵}
\begin{longtable}{p{4cm}p{3.5cm}p{3.5cm}p{2.2cm}}
\caption{需求验收矩阵}\\
\toprule
验收项 & 对应需求 & 验收方式 & 状态 \\
\midrule
\endfirsthead
\toprule
验收项 & 对应需求 & 验收方式 & 状态 \\
\midrule
\endhead
数据集与字典 & FR-01 & 文件验证、接口验证 & 通过 \\
查询与导出 & FR-02 至 FR-05 & 页面操作、接口测试 & 通过 \\
统计分析 & FR-06 至 FR-14 & 页面操作、接口测试 & 通过 \\
三维楼层联动 & FR-15 & 浏览器人工验收 & 通过 \\
工单闭环 & FR-16 & 创建、完成、刷新验证 & 通过 \\
决策报告 & FR-17 & 页面生成、接口返回 & 通过 \\
智能问答 & FR-18 至 FR-19 & 本地知识库与可选 LLM 测试 & 通过 \\
MCP 接入 & FR-20 & MCP 测试与启动脚本 & 通过 \\
最终交付材料 & 课程要求 & 文件结构验证 & 通过 \\
\bottomrule
\end{longtable}

\section{缺陷处理记录}
最终封版前已处理的关键问题包括：数据量过少、统计筛选数量不一致、健康楼层显示空模块、工单刷新后状态丢失、工单创建控件拥挤、3D 楼层点击无反应、外部模型不可用时演示中断风险、文档口吻不正式、Markdown PDF 不够规范等。上述问题均已通过系统优化或正式文档重写处理。

\section{验收结论}
系统已满足课程项目的软件实现、测试验证和文档交付要求。后端测试、前端构建、人工演示路径和最终材料整理均具备验收条件。剩余工作主要是 PPT 与演示视频制作，不影响软件系统本身的验收结论。
"""


USER_ABSTRACT = r"""
本文档为《\projectname》的用户手册与部署说明，面向系统使用者、评审人员和后续维护人员，说明如何获取代码、放置环境变量、安装依赖、启动后端、启动前端、启动 MCP Server、使用主要功能、处理常见问题和完成系统展示。
"""


USER_BODY = r"""
\section{运行前准备}
\subsection{环境要求}
\begin{table}[H]
\centering
\caption{运行环境要求}
\begin{tabularx}{\textwidth}{p{4cm}Y}
\toprule
类别 & 要求 \\
\midrule
操作系统 & Windows 10/11，建议使用 PowerShell \\
Python & Python 3.11 或兼容版本 \\
Node.js & 支持 Vite 的 Node.js 版本 \\
浏览器 & Edge、Chrome 或其他现代浏览器 \\
网络 & 基础系统不强依赖外网；外部大模型需要网络和有效 API Key \\
\bottomrule
\end{tabularx}
\end{table}

\subsection{代码获取}
运行人员可从 GitHub 拉取代码：
\begin{verbatim}
git clone <GitHub 仓库地址>
cd building-energy-intelligence-platform
\end{verbatim}

\subsection{环境变量}
如果只演示基础系统，可复制模板：
\begin{verbatim}
Copy-Item .env.example .env
\end{verbatim}
如果需要启用外部大模型，应由项目负责人单独提供真实 \code{.env} 文件，并放在仓库根目录。真实 \code{.env} 不应放入 \code{backend/} 或 \code{frontend/}，不得提交到 GitHub，也不得放进最终 zip。

\section{启动后端}
\begin{verbatim}
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 `
  --app-dir backend
\end{verbatim}
也可以直接运行脚本：
\begin{verbatim}
.\scripts\start-backend.ps1
\end{verbatim}
启动后可访问 \code{http://127.0.0.1:8000/docs} 查看接口文档，访问 \code{http://127.0.0.1:8000/api/v1/health} 检查健康状态。

\section{启动前端}
\begin{verbatim}
cd frontend
npm install
npm run dev
\end{verbatim}
也可以在项目根目录运行：
\begin{verbatim}
.\scripts\start-frontend.ps1
\end{verbatim}
前端默认访问地址为 \code{http://127.0.0.1:5173}。后端和前端通常需要两个 PowerShell 窗口分别运行。

\section{启动 MCP Server}
默认 stdio 模式：
\begin{verbatim}
.\scripts\start-mcp.ps1
\end{verbatim}
HTTP 模式：
\begin{verbatim}
.\scripts\start-mcp.ps1 -Transport streamable-http `
  -HostAddress 127.0.0.1 -Port 8765
\end{verbatim}
HTTP 模式地址为 \code{http://127.0.0.1:8765/mcp}。

\section{页面功能说明}
\subsection{总览}
总览页展示系统 KPI、时间范围、总体指标和三维楼层风险态势。用户可以拖拽三维视图观察不同角度，点击红色楼层进入统计分析。

\subsection{数据浏览}
数据浏览页用于查询原始和派生后的能耗记录。用户可选择建筑、楼层、开始时间、结束时间和显示数量。该页面用于全量查询，不受三维楼层点击联动影响。

\subsection{统计分析}
统计分析页是异常诊断工作台。用户可按建筑、楼层和时间范围锁定分析对象。若选中异常楼层，页面优先展示异常明细、异常原因、楼层设备、趋势和建议；若选中健康楼层，页面只展示健康提示。

\subsection{工单中心}
工单中心支持从异常记录创建工单。用户选择建筑、楼层、异常记录和负责人后，系统生成“处理中”工单。处理中工单显示在顶部，完成后变为绿色并靠后显示。工单状态保存到本地 JSON 文件，刷新页面不会丢失。

\subsection{决策报告}
决策报告页汇总当前范围内的能耗、异常、工单和优化建议，并提供简单收益模拟。该页面用于体现系统从异常发现到管理建议的综合价值。

\subsection{智能问答}
智能问答页支持本地知识库问答和可选外部模型增强。若外部模型不可用，系统会回退到本地知识库，保证演示不中断。

\section{推荐系统展示路径}
\begin{enumerate}
    \item 打开总览页，说明数据规模、建筑数量、时间范围和平均 COP。
    \item 拖拽三维楼宇，点击红色异常楼层，展示页面自动跳转统计分析。
    \item 在统计分析页查看异常明细，点击异常解释，说明触发规则和指标证据。
    \item 进入工单中心，从异常创建工单，分配负责人，完成工单并刷新验证持久化。
    \item 进入决策报告页，展示风险摘要、优化建议和收益模拟。
    \item 进入智能问答页，提问“当前有哪些异常风险”或“哪些设备优先维护”。
    \item 简要说明 MCP Server 可让 AI 客户端直接调用项目数据与分析工具。
\end{enumerate}

\section{常见问题}
\begin{longtable}{p{4cm}p{9.8cm}}
\caption{常见问题与处理}\\
\toprule
问题 & 处理方式 \\
\midrule
\endfirsthead
\toprule
问题 & 处理方式 \\
\midrule
\endhead
前端无法连接后端 & 确认后端运行在 8000 端口，Vite 代理配置未改动 \\
提示找不到数据文件 & 确认根目录存在 \code{data/samples/energy_records.csv}，不要从子目录启动错误脚本 \\
外部模型无回答 & 检查 \code{.env} 中 API Key、base URL、model 是否有效；也可关闭 LLM 使用本地回答 \\
工单刷新后丢失 & 检查 \code{data/runtime/work_orders.json} 是否可写 \\
npm install 慢 & 可更换 npm 镜像，但不要提交 \code{node_modules} \\
pytest 找不到模块 & 确认使用项目根目录运行检查脚本或正确设置 \code{PYTHONPATH} \\
\bottomrule
\end{longtable}
"""


DATA_ABSTRACT = r"""
本文档为《\projectname》的数据、接口与 MCP 说明，集中描述样例数据来源思路、数据字段、派生指标、异常规则、REST API、MCP Tools/Resources、知识库和外部模型配置。该文档用于支撑系统开发、联调、验收和后续扩展。
"""


DATA_BODY = r"""
\section{数据来源与构造原则}
本项目数据用于课程演示，不直接声称来自真实校园传感器。数据构造参考建筑能耗管理常见字段和公开资料中的指标口径，重点模拟多建筑、多时段、多设备、多环境变量和异常状态。这样既能满足课程演示，又避免使用未经授权的真实运行数据。

\section{数据文件}
\begin{longtable}{p{4cm}p{5.5cm}p{4.5cm}}
\caption{数据文件说明}\\
\toprule
文件 & 内容 & 用途 \\
\midrule
\endfirsthead
\toprule
文件 & 内容 & 用途 \\
\midrule
\endhead
\code{data/samples/energy_records.csv} & 4,864 条能耗样例记录 & 查询、统计、异常分析、图表展示 \\
\code{data/dictionaries/energy_records_dictionary.csv} & 字段名、类型、是否必填、说明和示例 & 数据解释与文档引用 \\
\code{data/processed/data_quality_report_round1.md} & 数据质量检查说明 & 数据质量追溯 \\
\code{data/processed/external_source_shortlist_round1.md} & 外部数据资料调研简表 & 说明数据设计参考来源 \\
\code{data/runtime/work_orders.json} & 运行期工单状态 & 本地生成，不提交 \\
\bottomrule
\end{longtable}

\section{字段与派生指标}
原始字段包括建筑、时间、电耗、水耗、空调电耗、制冷量、冷冻水温度、环境温湿度、人员密度、设备编号和设备状态。派生字段包括楼层、区域、设备类型、小时、建筑均值、动态阈值、COP、低 COP 标记、夜间高负荷标记、异常标记和异常原因。

\section{REST API 汇总}
\begin{longtable}{p{5cm}p{2cm}p{6.8cm}}
\caption{REST API 汇总}\\
\toprule
接口 & 方法 & 说明 \\
\midrule
\endfirsthead
\toprule
接口 & 方法 & 说明 \\
\midrule
\endhead
\code{/api/v1/health} & GET & 健康检查 \\
\code{/api/v1/overview} & GET & 总览指标 \\
\code{/api/v1/dataset-meta} & GET & 数据集元信息 \\
\code{/api/v1/buildings} & GET & 建筑选项 \\
\code{/api/v1/records} & GET & 能耗记录查询 \\
\code{/api/v1/export/csv} & GET & CSV 导出 \\
\code{/api/v1/analytics/time-summary} & GET & 时间序列汇总 \\
\code{/api/v1/analytics/building-comparison} & GET & 建筑对比 \\
\code{/api/v1/analytics/cop-ranking} & GET & COP 排名 \\
\code{/api/v1/analytics/anomalies} & GET & 异常明细 \\
\code{/api/v1/analytics/anomaly-explanations/\{record_id\}} & GET & 异常解释 \\
\code{/api/v1/analytics/anomaly-reasons} & GET & 异常原因统计 \\
\code{/api/v1/analytics/floor-summary} & GET & 楼层汇总 \\
\code{/api/v1/analytics/floor-registry} & GET & 楼层注册表 \\
\code{/api/v1/analytics/equipment-summary} & GET & 设备汇总 \\
\code{/api/v1/analytics/work-orders} & GET & 异常工单建议 \\
\code{/api/v1/analytics/optimization-recommendations} & GET & 优化建议 \\
\code{/api/v1/analytics/operation-report} & GET & 运营报告 \\
\code{/api/v1/work-orders} & \shortstack{GET\\POST} & 持久化工单查询和创建 \\
\code{/api/v1/work-orders/\{id\}} & PATCH & 工单状态更新 \\
\code{/api/v1/assistant/providers} & GET & 模型供应商选项 \\
\code{/api/v1/assistant/query} & POST & 智能问答 \\
\bottomrule
\end{longtable}

\section{MCP 设计}
\subsection{MCP Tools}
\begin{longtable}{p{4cm}p{9.8cm}}
\caption{MCP Tools}\\
\toprule
类别 & 工具 \\
\midrule
\endfirsthead
\toprule
类别 & 工具 \\
\midrule
\endhead
数据查询 & \code{get_dataset_meta}、\code{list_buildings}、\code{query_energy_records} \\
统计分析 & \code{get_energy_overview}、\code{get_time_summary}、\code{get_building_comparison}、\code{get_cop_ranking} \\
异常诊断 & \code{get_anomalies}、\code{get_anomaly_reasons}、\code{explain_anomaly} \\
楼层设备 & \code{get_floor_summary}、\code{get_equipment_summary} \\
运维决策 & \code{suggest_anomaly_work_orders}、\code{get_optimization_recommendations}、\code{get_operation_report} \\
知识问答 & \code{search_energy_knowledge}、\code{ask_energy_assistant} \\
\bottomrule
\end{longtable}

\subsection{MCP Resources 与 Prompt}
MCP Resources 包括 \code{energy://dataset/meta}、\code{energy://buildings}、\code{energy://operation/report} 和 \code{energy://knowledge/readme}。系统还提供 \code{energy_operation_prompt}，用于引导 AI 客户端先使用 MCP 工具检查数据、异常、报告和知识库引用，再回答用户问题。

\section{接口一致性原则}
REST API、MCP Tools 和前端页面必须复用同一分析服务层。任何新指标应优先添加到 \code{analysis_service.py}，再由 REST 和 MCP 暴露，最后由前端展示。这样可以避免不同入口出现不同统计口径。

\section{密钥与模型配置}
外部模型配置只允许存在于本地 \code{.env}。文档、源码和提交材料中不得出现真实 API Key。\code{.env.example} 只保留变量名和占位值。模型不可用时，系统必须回退到本地知识库回答，保证课程演示不受外部服务影响。
"""


SUBMIT_ABSTRACT = r"""
本文档为《\projectname》的最终提交说明，按照课程期末要求列出应提交的源码、SRS\&SDS、SEE\&SEM、测试与验收材料、演示材料和打包排除项。本文档用于最终检查，确保提交给教师的材料完整、正式、可运行且不泄露敏感信息。
"""


SUBMIT_BODY = r"""
\section{教师要求对照}
\begin{longtable}{p{5cm}p{5.2cm}p{3.2cm}}
\caption{教师要求与项目材料对应关系}\\
\toprule
教师要求 & 对应材料 & 状态 \\
\midrule
\endfirsthead
\toprule
教师要求 & 对应材料 & 状态 \\
\midrule
\endhead
Complete financial analysis for course project & SEE 软件经济分析与评价 & 已完成 \\
Design, implement and deploy course project & 源码、README、用户手册与部署说明 & 已完成 \\
Project scope and planning & SEM 软件工程管理说明 & 已完成 \\
Software process monitor and control & SEM 软件工程管理说明 & 已完成 \\
Risk management & SEM 风险管理章节 & 已完成 \\
Cost of development and maintenance & SEE 成本估算与维护成本章节 & 已完成 \\
Pricing strategy & SEE 定价策略章节 & 已完成 \\
Funding and financing & SEE 资金与融资章节 & 已完成 \\
Financial analysis and evaluation & SEE 财务评价、ROI、敏感性分析 & 已完成 \\
SRS\&SDS & SRS 软件需求规格说明书、SDD/SDS 软件设计说明书 & 已完成 \\
SEE\&SEM & SEE 软件经济分析与评价、SEM 软件工程管理说明 & 已完成 \\
Source code developed and deployed & \code{source-code/}、README、启动脚本 & 已完成 \\
\bottomrule
\end{longtable}

\section{推荐提交目录}
\begin{verbatim}
期末提交材料/
|-- source-code/
|-- documents/
|   |-- latex/
|   |-- pdf-latex/
|   `-- markdown/
|-- demo/
`-- submission-readme.md
\end{verbatim}

\section{正式 PDF 文件}
正式 PDF 以 LaTeX 编译版为准：
\begin{enumerate}
    \item SRS 软件需求规格说明书。
    \item SDD/SDS 软件设计说明书。
    \item SEE 软件经济分析与评价。
    \item SEM 软件工程管理说明。
    \item 测试与验收报告。
    \item 用户手册与部署说明。
    \item 数据、接口与 MCP 说明。
    \item 最终提交说明。
\end{enumerate}

\section{源码提交要求}
源码应包含 \code{backend/}、\code{frontend/}、\code{data/}、\code{knowledge_base/}、\code{scripts/}、\code{README.md}、\code{.env.example} 和 \code{.gitignore}。源码应能够按 README 启动并运行完整演示。

\section{必须排除的内容}
\begin{longtable}{p{4cm}p{9.8cm}}
\caption{提交排除项}\\
\toprule
排除项 & 原因 \\
\midrule
\endfirsthead
\toprule
排除项 & 原因 \\
\midrule
\endhead
\code{.env} & 可能包含真实 API Key，严禁提交 \\
\code{frontend/node_modules/} & 依赖体积大，可通过 npm install 还原 \\
\code{frontend/dist/} & 构建产物可重新生成 \\
\code{data/runtime/} & 本地演示工单状态，不属于基线数据 \\
\code{.pytest_cache/} & 测试缓存，无提交价值 \\
个人无关实验文件 & 与期末项目无关，避免干扰评审 \\
真实 API Key 或截图 & 存在安全风险 \\
\bottomrule
\end{longtable}

\section{交付确认}
\begin{enumerate}
    \item 运行 \code{scripts/check-project.ps1}，确认后端测试和前端构建通过。
    \item 确认最终目录中不存在 \code{.env} 和真实 API Key。
    \item 打开 LaTeX PDF，确认封面、目录、图表、页码和中文显示正常。
    \item 按用户手册启动系统，完成系统展示路径。
    \item 确认 PPT 和演示视频与当前系统一致。
    \item 将材料打包为一个 zip 文件并提交到 Canvas。
\end{enumerate}

\section{最终结论}
项目已经形成可运行源码、正式需求与设计文档、经济分析与工程管理文档、测试验收材料、用户部署说明和最终交付说明。软件系统、正式文档和交付材料已经具备课程期末提交条件。
"""


def make_longtable(caption: str, spec: str, headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    header_line = " & ".join(headers) + r" \\"
    row_lines = "\n".join(" & ".join(row) + r" \\" for row in rows)
    return (
        f"\\begin{{longtable}}{{{spec}}}\n"
        f"\\caption{{{caption}}}\\\\\n"
        "\\toprule\n"
        f"{header_line}\n"
        "\\midrule\n"
        "\\endfirsthead\n"
        "\\toprule\n"
        f"{header_line}\n"
        "\\midrule\n"
        "\\endhead\n"
        f"{row_lines}\n"
        "\\bottomrule\n"
        "\\end{longtable}\n"
    )


SRS_FUNCTION_ROWS = [
    ("FR-01", "数据集与字典", "系统启动时读取样例 CSV，校验字段、时间、数值和建筑标识，数据字典应解释每个字段的含义、单位、来源和用途。", "打开数据浏览页，字段显示完整，元信息接口返回记录数、建筑数和时间范围。"),
    ("FR-02", "数据元信息", "系统应提供建筑清单、字段清单、时间范围和数据规模，便于前端初始化筛选器并向教师说明数据来源。", "接口返回值与 CSV 内容一致，空数据或路径错误时给出明确提示。"),
    ("FR-03", "系统总览", "总览应展示记录数、建筑数、平均 COP、异常数、总能耗、三维楼宇状态和全局趋势摘要。", "刷新页面后总览指标与后端计算口径一致。"),
    ("FR-04", "数据浏览", "用户可按建筑、楼层、开始时间、结束时间和数量限制查询能耗记录，数据浏览只承担全量查询职责，不被 3D 点击联动污染。", "筛选后的记录数量、建筑、楼层和时间范围均正确。"),
    ("FR-05", "CSV 导出", "系统应按照当前筛选条件导出 CSV，导出字段保持与数据浏览一致，便于后续报告或表格软件分析。", "导出文件可打开，表头和筛选结果一致。"),
    ("FR-06", "时间序列统计", "系统支持小时、日、周、月粒度汇总电耗、水耗、空调电耗、制冷量和 COP，用于趋势分析和报告。", "切换粒度后图表刷新，空范围返回空数组而非前端错误。"),
    ("FR-07", "建筑对比", "系统按建筑汇总能耗、水耗、空调电耗、制冷量、平均 COP 和异常数量，用于横向比较。", "不同建筑的排名和总览指标可交叉验证。"),
    ("FR-08", "COP 排名", "系统按建筑平均 COP 排名，识别制冷效率差异并提示低效建筑。", "COP 数值由制冷量和空调电耗计算，排序稳定。"),
    ("FR-09", "异常识别", "系统基于设备状态、建筑动态阈值、COP 阈值和夜间负荷规则识别异常，结论应可解释。", "异常明细中的原因能追溯到具体规则。"),
    ("FR-10", "异常明细", "统计分析页在选定建筑、楼层和时间范围后优先展示异常记录，健康楼层只显示健康结论。", "异常条数与筛选器显示一致，健康楼层不出现无意义空图。"),
    ("FR-11", "异常原因统计", "系统按原因聚合异常数量，用于图表和报告中的风险结构说明。", "原因统计合计数等于异常明细数。"),
    ("FR-12", "异常解释", "每条异常应给出触发规则、关键证据、严重程度、原因、结论和建议动作。", "点击异常解释后内容足够支持运维判断。"),
    ("FR-13", "楼层分析", "系统派生楼层标签，统计楼层能耗、COP、异常数量、风险状态和设备信息。", "3D 楼层点击可跳转到相同建筑楼层的统计分析。"),
    ("FR-14", "设备分析", "系统统计设备点位、设备类型、设备状态、最近出现时间和维护提示。", "设备明细与异常记录可相互验证。"),
    ("FR-15", "三维风险视图", "总览页展示可旋转拖动的三维楼宇，异常楼层红色，健康楼层绿色，点击后进入统计分析。", "拖拽、旋转和点击联动可演示。"),
    ("FR-16", "工单闭环", "用户可从异常创建工单，分配负责人，工单进入处理中，完成后变为已完成并持久化。", "刷新后工单状态不丢失，处理中置顶，已完成置后。"),
    ("FR-17", "决策报告", "系统生成运营日报，汇总风险、工单状态、节能建议、收益模拟和优先级。", "报告内容可用于系统展示和管理说明。"),
    ("FR-18", "智能问答", "系统基于本地知识库回答项目问题，可选调用外部模型增强，外部失败时回退本地回答。", "无 API Key 时仍能回答基础问题。"),
    ("FR-19", "模型选择", "页面展示可用模型选项，用户选择后后端按统一 OpenAI-compatible 契约调用。", "提供商不可用时前端显示回退结果或错误提示。"),
    ("FR-20", "MCP Server", "MCP Server 暴露数据、统计、异常解释、报告和知识库检索能力，供 AI 客户端调用。", "MCP 工具可列出并返回与 REST API 一致的数据。"),
]

SRS_SCENARIO_ROWS = [
    ("SC-01", "首次进入总览", "用户打开前端后系统应自动加载总览、建筑清单、三维楼宇和关键 KPI，若后端未启动则显示接口错误提示。", "页面不白屏，错误信息可读。"),
    ("SC-02", "查询单栋建筑", "用户选择综合教学楼 A 后，数据浏览、统计分析和楼层筛选应只使用该建筑范围。", "表格中不出现其他建筑。"),
    ("SC-03", "锁定楼层异常", "用户在统计分析中选择 RF 屋顶，应优先显示该楼层异常明细和解释入口。", "异常条数与楼层下拉展示一致。"),
    ("SC-04", "点击健康楼层", "用户从 3D 图点击绿色楼层，统计分析只展示健康提示，不展示趋势、异常和推荐模块。", "页面说明该楼层健康且无空图表。"),
    ("SC-05", "点击异常楼层", "用户从 3D 图点击红色楼层，系统跳转统计分析并自动填入建筑和楼层。", "筛选标签显示目标建筑和楼层。"),
    ("SC-06", "创建工单", "用户选择某条异常并分配给管理员，系统生成处理中工单并置顶展示。", "工单编号、负责人、异常引用均存在。"),
    ("SC-07", "完成工单", "用户点击完成按钮后，工单状态变为已完成，颜色变绿并移动到列表后部。", "刷新页面后状态仍为已完成。"),
    ("SC-08", "导出数据", "用户在数据浏览页完成筛选后导出 CSV，系统按当前条件生成文件。", "文件可打开，记录范围正确。"),
    ("SC-09", "生成日报", "管理人员进入决策报告页，系统按当前数据生成运营日报和节能建议。", "报告包含风险摘要和优先事项。"),
    ("SC-10", "本地问答", "无外部模型密钥时，用户询问异常规则或演示路径，系统使用本地知识库回答。", "回答不依赖网络且包含项目内容。"),
    ("SC-11", "外部模型问答", "配置外部模型后，用户选择模型并提问，系统把项目上下文作为提示输入。", "回答更自然，失败时有回退。"),
    ("SC-12", "MCP 调用", "支持 MCP 的客户端调用工具获取建筑清单或异常解释。", "工具返回 JSON 或文本资源。"),
    ("SC-13", "时间范围为空", "用户选择没有记录的时间范围，系统显示空状态而不是前端错误。", "空状态文字明确。"),
    ("SC-14", "异常不存在", "用户请求不存在的异常解释，后端返回空对象或 404，前端显示提示。", "系统不崩溃。"),
    ("SC-15", "模型密钥缺失", "模型提供商被启用但 API Key 未配置，系统提示配置问题并回退。", "真实密钥不出现在页面或日志。"),
    ("SC-16", "数据文件缺失", "后端启动时无法找到 CSV，系统应给出明确错误，便于定位部署问题。", "启动日志或接口错误可追踪。"),
    ("SC-17", "工单文件缺失", "运行目录没有工单 JSON 时，系统自动创建或返回空列表。", "不会影响正常演示。"),
    ("SC-18", "重复创建工单", "用户对同一异常重复创建工单时，系统允许创建但保留异常引用，便于演示多负责人场景。", "工单编号不冲突。"),
    ("SC-19", "接口响应慢", "前端应显示加载状态，避免用户误以为页面无反应。", "加载状态覆盖核心卡片。"),
    ("SC-20", "最终验收", "评审人员按演示脚本走完整路径，系统应覆盖总览、查询、分析、3D、工单、报告、问答和文档。", "演示路径闭环完整。"),
]

SRS_EXPANSION = (
    r"""
\clearpage
\section{补充需求规格}
\subsection{功能需求细化}
本节对前述功能需求进一步展开，强调每项需求的输入、处理、输出和验收口径。这样做的目的不是重复列功能，而是把课堂演示中的“能看到页面”转化为可检查、可追踪、可测试的软件需求。
"""
    + make_longtable("功能需求细化与验收口径", "L{1.7cm}L{2.8cm}L{6.2cm}L{4.5cm}", ("编号", "功能", "详细要求", "验收口径"), SRS_FUNCTION_ROWS)
    + r"""
\subsection{典型业务场景}
系统的主要价值体现在跨页面业务闭环，而不是单个接口返回数据。以下场景覆盖最终演示和验收时最容易被教师询问的路径。
"""
    + make_longtable("典型业务场景与边界条件", "L{1.6cm}L{3.0cm}L{6.2cm}L{4.4cm}", ("编号", "场景", "业务说明", "预期结果"), SRS_SCENARIO_ROWS)
    + r"""
\subsection{数据质量与安全约束}
数据质量约束用于保证分析结果可信，安全约束用于保证仓库提交和课堂演示不会泄露真实密钥。
"""
    + make_longtable(
        "数据质量、安全与合规约束",
        "L{1.7cm}L{3.0cm}L{6.0cm}L{4.5cm}",
        ("编号", "约束项", "约束说明", "处理方式"),
        [
            ("DQ-01", "字段完整", "CSV 必须包含建筑、时间、能耗、水耗、空调电耗、制冷量、环境温湿度、人员密度和设备状态等核心字段。", "启动或加载时校验字段，不满足时拒绝继续分析。"),
            ("DQ-02", "时间可解析", "时间字段必须可解析为统一时间戳，前端筛选必须使用相同时间口径。", "数据加载层统一转换。"),
            ("DQ-03", "数值非空", "电耗、水耗、空调电耗、制冷量等指标不能为空，否则会影响 COP 和异常计算。", "异常值在加载阶段标记或排除。"),
            ("DQ-04", "建筑标识一致", "同一建筑的编号和名称需要稳定，避免总览、统计和 3D 展示口径不一致。", "建筑清单由后端统一生成。"),
            ("DQ-05", "楼层派生可解释", "楼层来自设备和建筑场景推断，必须能说明为什么冷水机组映射到 B1 或屋顶设备映射到 RF。", "SDD 中记录派生规则。"),
            ("DQ-06", "异常原因唯一主因", "一条记录可触发多条规则，但页面优先展示一个主因并保留证据说明。", "分析服务按优先级排序。"),
            ("DQ-07", "工单持久化", "工单状态必须写入运行目录，刷新后不丢失，但不进入 Git 仓库。", "\code{data/runtime/} 加入忽略。"),
            ("DQ-08", "密钥不入库", "真实 API Key 只能放在本地 \code{.env}，不得写入源码、文档、PDF 或提交材料。", "发布前执行模式搜索。"),
            ("DQ-09", "外部模型可关闭", "没有外部模型时系统仍应使用本地知识库回答，避免演示依赖网络。", "通过 \code{LLM_ENABLED} 控制。"),
            ("DQ-10", "文档正式口吻", "最终文档应面向课程评审，不应出现对话式说明或个人任务口吻。", "生成正式 PDF 前统一确认。"),
        ],
    )
)


SDD_EXPANSION = (
    r"""
\clearpage
\section{补充详细设计}
\subsection{模块内部职责细化}
为避免设计说明停留在架构图层面，本节进一步说明主要模块的输入、输出、状态和失败处理，使各模块职责能够从设计说明追踪到代码结构。
"""
    + make_longtable(
        "模块内部职责与设计边界",
        "L{3.4cm}L{3.8cm}L{4.8cm}L{3.1cm}",
        ("模块", "输入", "处理职责", "输出"),
        [
            ("数据加载服务", "CSV 路径、筛选条件", "校验字段、解析时间、缓存 DataFrame、派生基础字段。", "标准化记录集"),
            ("概览服务", "标准化记录集", "计算总记录数、建筑数、时间范围、平均 COP、异常总数和总能耗。", "总览 JSON"),
            ("时间汇总服务", "记录集、粒度", "按小时、日、周、月分组，聚合能耗、水耗、空调电耗和 COP。", "趋势数组"),
            ("建筑对比服务", "记录集", "按建筑聚合总能耗、平均 COP、异常数和排序指标。", "建筑对比表"),
            ("楼层派生服务", "建筑、设备、场景字段", "根据设备和建筑场景推断楼层、区域和设备类型。", "楼层化记录"),
            ("异常识别服务", "楼层化记录", "执行设备状态、动态阈值、COP 和夜间负荷规则。", "异常标记与原因"),
            ("异常解释服务", "异常记录编号", "构造触发规则、指标证据、严重程度和建议动作。", "解释对象"),
            ("设备汇总服务", "楼层化记录", "统计设备点位、状态、类型、最近出现时间和维护提示。", "设备表"),
            ("工单存储服务", "创建或更新请求", "生成编号、写入 JSON、排序状态、处理缺失文件。", "工单列表"),
            ("日报服务", "概览、异常、工单、建议", "生成风险摘要、优先级、节能动作和收益模拟。", "运营报告"),
            ("知识库检索服务", "用户问题", "从 Markdown 知识卡片中匹配项目背景、指标和演示问题。", "本地回答素材"),
            ("LLM 客户端", "模型配置、提示词", "按 OpenAI-compatible 协议调用外部模型并处理失败。", "模型回答或回退"),
            ("MCP Server", "AI 客户端工具调用", "复用分析服务，暴露 Tools、Resources 和 Prompt。", "MCP 响应"),
            ("前端 API 封装", "页面参数", "拼接查询参数、捕获错误、统一响应结构。", "页面数据"),
            ("三维楼层组件", "楼层健康状态", "构建立体楼宇、处理拖拽旋转、点击楼层联动。", "交互事件"),
            ("图表组件", "趋势或聚合数据", "渲染折线、柱状、排名和原因统计图。", "可视化视图"),
            ("工单中心组件", "异常和工单数据", "创建工单、完成工单、排序和颜色状态。", "工单交互界面"),
            ("AI 助手组件", "问题、模型选择", "显示模型列表、提交问题、展示回答和回退状态。", "问答结果"),
        ],
    )
    + r"""
\subsection{关键设计决策}
以下决策体现了项目从课程原型到可演示系统之间的工程取舍，重点考虑可运行性、可维护性和评审可解释性。
"""
    + make_longtable(
        "关键设计决策与取舍",
        "L{3.2cm}L{4.3cm}L{4.8cm}L{3.0cm}",
        ("决策点", "采用方案", "理由", "备选方案"),
        [
            ("数据存储", "CSV 加运行期 JSON", "课程项目部署简单，便于查看原始数据，同时工单状态可持久化。", "SQLite 或 MySQL"),
            ("异常算法", "规则组合", "规则可解释，便于验证和维护，避免黑箱模型难以说明。", "机器学习模型"),
            ("前端框架", "Vue 加 Vite", "启动快、结构轻、适合课程演示和组件化页面。", "React 或纯 HTML"),
            ("3D 实现", "CSS 3D", "不增加大型依赖，浏览器兼容性较好。", "Three.js"),
            ("问答能力", "本地知识库优先", "无密钥时仍能演示，外部模型作为增强。", "完全依赖外部 LLM"),
            ("MCP 设计", "复用后端服务层", "REST API 与 MCP 口径一致，减少重复实现。", "MCP 单独实现"),
            ("文档生成", "LaTeX 统一模板", "版面正式，适合提交 PDF，图表可控。", "Markdown 直接转 PDF"),
            ("测试策略", "pytest 加前端构建", "覆盖接口和服务层，前端至少保证生产构建可通过。", "纯人工测试"),
            ("工单状态", "创建即处理中", "课程演示中减少无意义待处理状态，更贴合用户要求。", "待处理到处理中"),
            ("密钥管理", ".env 本地配置", "避免真实 API Key 入库，符合安全要求。", "写在配置文件中"),
            ("时间范围", "样例覆盖 2026-01-01 至 2026-06-01", "数据量足够支撑趋势和筛选演示。", "单日样例"),
            ("提交材料", "源码与正式 PDF 分离", "评审可快速找到正式文档，同时保留源码可运行。", "只提交仓库链接"),
        ],
    )
    + r"""
\subsection{异常与降级设计}
系统需要在演示环境中保持稳定，因此必须明确各类异常的处理方式。
"""
    + make_longtable(
        "异常处理与降级策略",
        "L{3.0cm}L{4.4cm}L{5.0cm}L{2.9cm}",
        ("异常类型", "触发条件", "处理策略", "用户感知"),
        [
            ("数据文件缺失", "CSV 路径不存在或文件为空", "后端启动或接口调用时返回明确错误。", "显示数据错误"),
            ("字段缺失", "CSV 不包含必要字段", "数据加载层阻断并说明缺失字段。", "接口错误提示"),
            ("时间解析失败", "时间格式无法转换", "记录被拒绝或整体加载失败，避免错误统计。", "日志可定位"),
            ("筛选无数据", "建筑、楼层、时间组合没有记录", "返回空数组和空状态说明。", "页面空状态"),
            ("异常记录不存在", "解释接口找不到编号", "返回 404 或空解释对象。", "提示记录不存在"),
            ("工单文件不存在", "首次启动没有运行期 JSON", "自动创建空状态或返回空列表。", "无感知"),
            ("工单写入失败", "目录权限不足", "返回错误并保留前端输入。", "提示保存失败"),
            ("模型未配置", "LLM 启用但缺少 Key", "自动回退本地知识库回答。", "显示回退说明"),
            ("模型接口失败", "网络、额度或提供商错误", "捕获异常，返回本地回答和失败原因。", "不阻断问答"),
            ("MCP 启动失败", "transport 或依赖配置错误", "命令行输出错误，README 提供排查步骤。", "运维可排查"),
            ("前端请求失败", "后端未启动或端口错误", "API 封装捕获错误并显示提示。", "页面错误提示"),
            ("图表数据为空", "健康楼层或空筛选", "隐藏无意义图表，仅展示健康或空状态。", "页面简洁"),
        ],
    )
)


SEE_EXPANSION = (
    r"""
\clearpage
\section{补充经济分析}
\subsection{工作包成本明细}
本节将 240 小时课程项目投入进一步分解到更细工作包，说明成本估算与需求、设计、开发、测试、文档和系统展示工作直接相关。
"""
    + make_longtable(
        "工作包成本分解明细",
        "L{1.5cm}L{3.2cm}L{5.8cm}L{1.6cm}L{2.4cm}",
        ("编号", "工作包", "主要活动", "工时", "成本"),
        [
            ("W01", "作业要求分析", "阅读教师 PPT、整理最终交付范围、识别 SRS、SDS、SEE、SEM 和源码提交要求。", "8", "640 元"),
            ("W02", "需求边界确定", "确定建筑能源管理、异常分析、工单闭环、AI 问答和 MCP 的范围。", "10", "800 元"),
            ("W03", "数据源调研", "调研真实建筑能耗数据来源，形成模拟依据和字段口径。", "8", "640 元"),
            ("W04", "样例数据生成", "扩充多建筑、多楼层、多时段数据至 2026-06-01。", "12", "960 元"),
            ("W05", "数据字典", "整理字段、单位、派生字段和分析口径。", "6", "480 元"),
            ("W06", "后端骨架", "建立 FastAPI 应用、路由、配置和基础服务结构。", "10", "800 元"),
            ("W07", "数据接口", "实现概览、元信息、建筑、记录查询和导出接口。", "10", "800 元"),
            ("W08", "统计服务", "实现时间汇总、建筑对比、COP 排名和原因统计。", "12", "960 元"),
            ("W09", "异常服务", "实现规则识别、异常解释、楼层和设备分析。", "14", "1120 元"),
            ("W10", "工单服务", "实现创建、更新、排序和 JSON 持久化。", "8", "640 元"),
            ("W11", "问答服务", "实现知识库检索、外部模型配置和回退逻辑。", "8", "640 元"),
            ("W12", "MCP Server", "暴露 Tools、Resources 和 Prompt，复用服务层。", "8", "640 元"),
            ("W13", "前端工作台", "构建导航、状态管理、数据加载和页面布局。", "10", "800 元"),
            ("W14", "数据浏览页", "实现筛选、表格、导出和空状态。", "6", "480 元"),
            ("W15", "统计分析页", "实现范围筛选、异常优先、健康楼层和全局板块。", "10", "800 元"),
            ("W16", "三维总览", "实现 3D 楼宇、楼层颜色、拖拽旋转和点击联动。", "10", "800 元"),
            ("W17", "工单中心", "实现创建工单、完成工单、排序和持久化交互。", "8", "640 元"),
            ("W18", "决策报告", "实现运营日报、建议和收益模拟展示。", "6", "480 元"),
            ("W19", "AI 助手", "实现模型选择、问答提交、回退和结果展示。", "6", "480 元"),
            ("W20", "后端测试", "编写接口、服务、工单、MCP 和 LLM 封装测试。", "14", "1120 元"),
            ("W21", "前端构建验证", "运行生产构建并修复构建错误。", "6", "480 元"),
            ("W22", "浏览器验收", "按演示路径检查页面、联动和刷新。", "8", "640 元"),
            ("W23", "SRS 文档", "撰写需求、用例、功能表和追踪矩阵。", "8", "640 元"),
            ("W24", "SDD 文档", "撰写架构、模块、数据、算法、状态机和接口设计。", "8", "640 元"),
            ("W25", "SEE 文档", "完成成本、收益、定价、融资和经济评价。", "6", "480 元"),
            ("W26", "SEM 文档", "完成范围、过程、质量、风险、配置和沟通管理。", "6", "480 元"),
            ("W27", "用户手册", "整理安装、启动、页面使用和故障排查。", "4", "320 元"),
            ("W28", "提交材料", "整理最终目录、PDF、源码副本和安全检查。", "6", "480 元"),
        ],
    )
    + r"""
\subsection{收益与敏感性分析}
课程项目没有真实商业收费，因此经济分析采用“节能收益、人工节约、风险避免和管理价值”四类收益口径，并通过敏感性分析说明结果变化。
"""
    + make_longtable(
        "收益与敏感性分析",
        "L{2.4cm}L{3.0cm}L{5.6cm}L{3.8cm}",
        ("情景", "关键假设", "测算说明", "评价"),
        [
            ("保守节能", "节电 2\\%", "系统仅帮助发现明显夜间负荷和设备状态异常，收益较低但更可信。", "适合作为最低收益边界。"),
            ("基准节能", "节电 5\\%", "结合异常定位、COP 优化和工单闭环，形成持续改进。", "作为课程主估算口径。"),
            ("积极节能", "节电 8\\%", "运维团队及时执行建议并扩展到更多楼栋。", "适合推广情景。"),
            ("人工节约", "每周减少 4 小时巡检分析", "系统自动汇总异常和报告，减少人工查表。", "管理收益明显。"),
            ("风险避免", "减少设备异常延迟发现", "早发现低 COP、夜间负荷和设备状态异常，降低维修和投诉风险。", "难完全量化但价值高。"),
            ("模型成本", "外部模型可选", "无 Key 时使用本地知识库，接入模型时按调用量产生边际成本。", "成本可控。"),
            ("部署成本", "本地运行", "课程演示不需要云服务器，后续推广可再估算服务器和运维费用。", "当前成本低。"),
            ("数据成本", "样例数据", "当前使用模拟数据，真实部署需接入设备或能源平台。", "推广时需新增预算。"),
            ("维护成本", "每月少量维护", "主要维护数据口径、异常规则、依赖升级和模型配置。", "可由小团队承担。"),
            ("规模扩展", "从 4 栋到 20 栋", "服务层复用，主要增加数据接入和性能优化工作。", "扩展性较好。"),
            ("失败情景", "系统不被使用", "若运维人员不按工单闭环处理，节能收益下降。", "需管理制度配合。"),
            ("最佳情景", "纳入月度运维流程", "日报和工单成为固定流程，异常闭环形成管理证据。", "经济价值最高。"),
        ],
    )
)


SEM_EXPANSION = (
    r"""
\clearpage
\section{补充工程管理说明}
\subsection{阶段计划与控制点}
项目采用两轮任务分配加最终整合的方式推进。管理重点不是追求形式上的每日进度，而是保证每个阶段都有明确输入、输出、检查项和纠偏动作。
"""
    + make_longtable(
        "阶段计划、产出与控制点",
        "L{2.0cm}L{3.2cm}L{5.2cm}L{4.2cm}",
        ("阶段", "目标", "主要产出", "控制点"),
        [
            ("S1", "项目骨架", "README、目录结构、环境示例、基础文档和样例数据。", "能够说明项目要做什么。"),
            ("S2", "第一次分工", "后端、数据 AI、前端三个方向的独立任务说明。", "边界清楚，减少合并冲突。"),
            ("S3", "第一次整合", "统一接口、补齐测试、修复质量不足、形成第一版系统。", "运行脚本通过。"),
            ("S4", "第二次分工", "围绕系统完善、AI、3D、工单、报告和文档继续细化。", "不再大规模改架构。"),
            ("S5", "第二次整合", "合并成员提交，统一代码风格，补充缺失逻辑。", "后端测试和前端构建通过。"),
            ("S6", "最终优化", "扩充数据、优化 3D、工单持久化、统计分析和文档。", "演示路径完整。"),
            ("S7", "正式文档", "SRS、SDD、SEE、SEM、测试、用户手册、数据接口和提交说明。", "PDF 可读且无密钥。"),
            ("S8", "最终交付", "提交材料目录、源码副本、PDF、PPT 和视频。", "按教师要求打包。"),
        ],
    )
    + r"""
\subsection{风险登记册}
风险管理关注对最终提交影响最大的事项，包括运行风险、文档风险、密钥风险和协作风险。
"""
    + make_longtable(
        "风险登记册",
        "L{1.6cm}L{3.0cm}L{4.8cm}L{4.8cm}",
        ("编号", "风险", "影响", "应对措施"),
        [
            ("R-01", "成员提交质量不均", "接口、数据和页面可能无法直接整合。", "整合者补齐缺口并用测试脚本作为质量闸门。"),
            ("R-02", "合并冲突", "多人同时改同一文件导致返工。", "任务边界按文件划分，尽量减少交叉修改。"),
            ("R-03", "数据量过少", "演示显得像写死数据。", "扩展到多建筑、多楼层、多时段。"),
            ("R-04", "业务逻辑单薄", "系统容易退化为单纯查询页面。", "增加楼层分析、设备分析、异常解释、工单闭环和报告。"),
            ("R-05", "外部模型不可用", "问答功能演示失败。", "本地知识库优先，外部模型可选。"),
            ("R-06", "真实密钥泄露", "GitHub 公开后造成安全和费用风险。", ".env 不入库，发布前模式搜索。"),
            ("R-07", "文档版面错误", "PDF 图表重叠或表格出页影响评分。", "使用 LaTeX 重写并检查 Overfull 日志和页面预览。"),
            ("R-08", "演示刷新丢工单", "交互逻辑显得不完整。", "工单写入运行期 JSON。"),
            ("R-09", "前端构建失败", "最终源码不可复现。", "发布前运行 Vite build。"),
            ("R-10", "后端测试失败", "接口口径不可信。", "pytest 作为发布前必须验证项。"),
            ("R-11", "PPT 与系统不一致", "系统展示和实际功能脱节。", "PPT 以最终系统截图和文档为准。"),
            ("R-12", "压缩包结构混乱", "评审人员难以找到正式文档和源码。", "使用统一提交材料目录。"),
            ("R-13", "运行说明不足", "拉取代码后无法启动。", "README 和用户手册写明完整步骤。"),
            ("R-14", "系统过度依赖单机状态", "换机器运行时工单数据缺失。", "说明运行期数据可自动生成。"),
            ("R-15", "图表含义不清", "评审无法理解业务价值。", "文档为每张图补充文字解释。"),
            ("R-16", "时间线不真实", "课程过程材料可能与实际开发不完全一致。", "最终文档聚焦工程成果和可验收内容。"),
        ],
    )
    + r"""
\subsection{质量检查矩阵}
"""
    + make_longtable(
        "质量检查矩阵",
        "L{2.4cm}L{4.0cm}L{4.5cm}L{3.5cm}",
        ("检查对象", "检查内容", "通过标准", "证据"),
        [
            ("README", "环境、启动、测试、密钥说明", "同学按说明可运行系统。", "人工复现"),
            ("后端", "语法、接口、服务测试", "pytest 全部通过。", "75 passed"),
            ("前端", "构建、页面加载、交互", "Vite build 成功，页面可演示。", "构建日志"),
            ("数据", "规模、字段、时间范围", "覆盖 2026-01-01 至 2026-06-01。", "数据字典"),
            ("3D", "旋转、颜色、点击联动", "异常楼层跳转统计分析。", "浏览器验收"),
            ("工单", "创建、完成、排序、持久化", "刷新后状态保留。", "接口和人工测试"),
            ("AI 问答", "本地回答、模型选择、回退", "无 Key 时不阻断演示。", "问答测试"),
            ("MCP", "工具、资源、提示词", "可通过 MCP 调用项目能力。", "MCP 测试"),
            ("SRS", "需求、用例、追踪矩阵", "可说明系统范围。", "PDF"),
            ("SDD", "架构、模块、数据、状态机", "可说明实现方案。", "PDF"),
            ("SEE", "成本、收益、定价、评价", "覆盖教师经济分析要求。", "PDF"),
            ("SEM", "范围、过程、风险、质量", "覆盖工程管理要求。", "PDF"),
            ("安全", ".env 和 Key", "最终材料不包含真实密钥。", "模式搜索"),
            ("交付包", "源码、文档、PPT、视频", "结构清晰，可直接上传。", "目录说明"),
        ],
    )
)


TEST_EXPANSION = (
    r"""
\clearpage
\section{补充测试用例}
\subsection{功能测试用例}
以下测试用例覆盖最终系统的主要页面、接口和业务闭环。它们既可作为自动化测试的补充，也可作为人工验收时逐项执行的依据。
"""
    + make_longtable(
        "功能测试用例",
        "L{1.6cm}L{3.0cm}L{5.6cm}L{4.8cm}",
        ("编号", "测试点", "测试步骤", "预期结果"),
        [
            ("TC-01", "健康检查", "启动后端并访问 \code{/api/v1/health}。", "返回正常状态。"),
            ("TC-02", "元信息", "访问数据元信息接口。", "返回记录数、字段、建筑和时间范围。"),
            ("TC-03", "建筑清单", "请求建筑列表。", "返回 4 栋建筑及其标识。"),
            ("TC-04", "记录查询", "按建筑和数量限制查询。", "记录建筑一致且数量不超过限制。"),
            ("TC-05", "楼层查询", "按建筑和楼层查询。", "记录只包含目标楼层。"),
            ("TC-06", "时间筛选", "设置开始和结束时间。", "记录时间均在范围内。"),
            ("TC-07", "CSV 导出", "按当前筛选导出 CSV。", "文件表头完整并可打开。"),
            ("TC-08", "总览指标", "访问总览接口。", "KPI 与数据集计算口径一致。"),
            ("TC-09", "时间汇总", "分别按日和月请求趋势。", "粒度不同但指标字段一致。"),
            ("TC-10", "建筑对比", "访问建筑对比接口。", "每栋建筑有总能耗和平均 COP。"),
            ("TC-11", "COP 排名", "访问 COP 排名接口。", "按 COP 排序且数值合理。"),
            ("TC-12", "异常列表", "访问异常接口。", "返回异常编号、原因、严重度和楼层。"),
            ("TC-13", "异常原因统计", "请求原因统计。", "原因数量合计等于异常明细数。"),
            ("TC-14", "异常解释", "选择一条异常请求解释。", "返回触发规则、证据和建议。"),
            ("TC-15", "楼层汇总", "请求楼层汇总。", "每个楼层有健康状态和异常数。"),
            ("TC-16", "设备汇总", "请求设备汇总。", "返回设备类型、状态和维护提示。"),
            ("TC-17", "运营报告", "访问运营报告接口。", "返回风险摘要、工单状态和建议。"),
            ("TC-18", "工单创建", "选择异常并提交负责人。", "创建处理中工单。"),
            ("TC-19", "工单完成", "对处理中工单执行完成。", "状态变为已完成。"),
            ("TC-20", "工单刷新", "刷新页面或重新请求列表。", "之前工单仍存在。"),
            ("TC-21", "3D 旋转", "拖拽三维楼宇。", "视图角度变化。"),
            ("TC-22", "3D 异常楼层", "点击红色楼层。", "跳转统计分析并锁定楼层。"),
            ("TC-23", "3D 健康楼层", "点击绿色楼层。", "只显示健康提示。"),
            ("TC-24", "AI 本地问答", "关闭外部模型后提问异常规则。", "返回本地知识库答案。"),
            ("TC-25", "模型列表", "访问模型选项接口。", "返回可选提供商和模型名称。"),
            ("TC-26", "模型回退", "配置错误 Key 后提问。", "返回回退答案和错误提示。"),
            ("TC-27", "MCP 工具列表", "启动 MCP Server 并列出工具。", "工具可被发现。"),
            ("TC-28", "MCP 资源", "读取项目数据资源。", "返回元信息或报告资源。"),
            ("TC-29", "空筛选", "选择无数据时间范围。", "页面显示空状态。"),
            ("TC-30", "错误提示", "停止后端后刷新前端。", "页面显示接口错误而非白屏。"),
        ],
    )
    + r"""
\subsection{验收测试场景}
"""
    + make_longtable(
        "验收测试场景",
        "L{1.6cm}L{3.2cm}L{6.0cm}L{4.2cm}",
        ("编号", "场景", "验收步骤", "通过标准"),
        [
            ("AT-01", "完整启动", "按 README 配置环境、启动后端和前端。", "浏览器可访问首页。"),
            ("AT-02", "总览演示", "展示 KPI、三维楼宇和异常楼层颜色。", "教师能理解系统状态。"),
            ("AT-03", "数据查询", "筛选建筑、楼层和时间。", "表格结果准确。"),
            ("AT-04", "异常分析", "查看异常明细并打开解释。", "解释具有证据链。"),
            ("AT-05", "工单闭环", "创建工单并完成。", "状态变化可见且持久化。"),
            ("AT-06", "决策报告", "展示运营日报。", "包含经济和管理建议。"),
            ("AT-07", "智能问答", "询问当前系统如何判断异常。", "回答结合项目数据或知识库。"),
            ("AT-08", "MCP 说明", "展示 MCP 工具和资源文档。", "说明 AI 客户端可调用能力。"),
            ("AT-09", "测试结果", "展示检查脚本输出。", "后端测试和前端构建通过。"),
            ("AT-10", "提交材料", "打开正式 PDF 和源码目录。", "材料结构符合教师要求。"),
        ],
    )
)


USER_EXPANSION = (
    r"""
\clearpage
\section{补充用户操作手册}
\subsection{页面任务说明}
本节按用户实际操作任务组织，而不是按代码模块组织，便于第一次接触系统的同学或评审人员快速完成演示。
"""
    + make_longtable(
        "用户任务、入口与操作结果",
        "L{2.4cm}L{3.2cm}L{5.8cm}L{3.8cm}",
        ("任务", "入口", "操作步骤", "结果"),
        [
            ("查看系统状态", "总览页", "打开首页，等待 KPI 和三维楼宇加载。", "掌握整体能耗和风险。"),
            ("查看建筑风险", "总览页", "观察楼宇颜色和风险卡片。", "发现异常楼层。"),
            ("旋转 3D 视图", "总览页", "按住鼠标拖拽楼宇区域。", "从不同角度观察楼群。"),
            ("进入楼层分析", "总览页", "点击某个红色楼层。", "跳转统计分析并锁定范围。"),
            ("查询原始记录", "数据浏览", "选择建筑、楼层、时间和数量后刷新。", "查看符合条件的记录。"),
            ("导出记录", "数据浏览", "在筛选后点击导出。", "下载 CSV 文件。"),
            ("查看异常明细", "统计分析", "选择建筑、楼层和时间范围。", "优先看到异常记录。"),
            ("查看健康楼层", "统计分析", "选择无异常楼层。", "只显示健康结论。"),
            ("查看趋势", "统计分析", "选择有异常的范围并查看趋势模块。", "了解能耗变化。"),
            ("查看设备", "统计分析", "打开设备分析区域。", "定位异常相关设备。"),
            ("解释异常", "统计分析", "点击异常解释或详情。", "看到规则、证据和建议。"),
            ("创建工单", "工单中心", "选择建筑、楼层、异常和负责人。", "生成处理中工单。"),
            ("完成工单", "工单中心", "点击完成按钮。", "工单变绿并移动到后部。"),
            ("刷新验证", "工单中心", "刷新浏览器或重新进入页面。", "工单状态仍保留。"),
            ("查看日报", "决策报告", "进入页面并查看风险摘要。", "获得管理建议和收益模拟。"),
            ("使用问答", "AI 助手", "选择模型或本地回答后输入问题。", "获得能源运维回答。"),
            ("查看模型", "AI 助手", "打开模型选择下拉框。", "看到可用模型选项。"),
            ("查看 API", "后端 docs", "访问 \code{http://127.0.0.1:8000/docs}。", "检查接口契约。"),
            ("启动 MCP", "命令行", "执行 MCP 启动脚本。", "为 AI 客户端提供工具。"),
            ("运行验证", "项目根目录", "执行 \code{scripts/check-project.ps1}。", "确认测试和构建通过。"),
        ],
    )
    + r"""
\subsection{常见问题排查}
"""
    + make_longtable(
        "常见问题与处理方式",
        "L{2.8cm}L{4.0cm}L{5.0cm}L{2.0cm}",
        ("问题", "可能原因", "处理方式", "优先级"),
        [
            ("前端打不开", "Vite 服务未启动或端口不是 5173。", "重新执行前端启动脚本并查看终端输出。", "高"),
            ("接口报错", "后端未启动或端口不是 8000。", "启动后端并访问健康检查接口。", "高"),
            ("数据为空", "筛选条件过窄或时间范围无记录。", "重置筛选或选择有数据的时间段。", "中"),
            ("图表不显示", "当前范围为健康楼层或无数据。", "查看健康提示或扩大范围。", "中"),
            ("工单不保存", "运行目录无法写入。", "检查 \code{data/runtime/} 权限。", "高"),
            ("AI 没有外部回答", "未配置真实 API Key。", "使用本地知识库回答或补充 \code{.env}。", "低"),
            ("模型请求失败", "网络、额度或 Key 错误。", "检查提供商配置并允许系统回退。", "中"),
            ("MCP 启动失败", "依赖或 transport 参数错误。", "按数据接口文档检查命令。", "中"),
            ("PDF 乱码", "未使用 XeLaTeX 或字体环境异常。", "使用脚本重新编译并确认 MiKTeX 可用。", "中"),
            ("交付包太大", "包含 \\code{node_modules} 或 \\code{dist}。", "按交付说明删除依赖和构建产物。", "高"),
        ],
    )
)


DATA_EXPANSION = (
    r"""
\clearpage
\section{补充数据与接口说明}
\subsection{REST API 详细契约}
以下表格补充每个接口的参数、返回和使用场景，便于前端、MCP 和文档保持一致。
"""
    + make_longtable(
        "REST API 详细契约",
        "L{4.0cm}L{1.8cm}L{4.5cm}L{4.8cm}",
        ("路径", "方法", "参数", "返回内容"),
        [
            ("\code{/health}", "GET", "无", "系统健康状态。"),
            ("\code{/dataset-meta}", "GET", "无", "字段、记录数、建筑数、时间范围。"),
            ("\code{/buildings}", "GET", "无", "建筑编号、名称和类型。"),
            ("\code{/records}", "GET", "building、floor、start、end、limit", "能耗记录列表。"),
            ("\code{/export/csv}", "GET", "同记录查询", "CSV 文件下载。"),
            ("\code{/overview}", "GET", "无", "总览 KPI 和核心摘要。"),
            ("\code{/analytics/time-summary}", "GET", "building、floor、grain、start、end", "时间序列统计。"),
            ("\code{/analytics/building-comparison}", "GET", "start、end", "建筑对比结果。"),
            ("\code{/analytics/cop-ranking}", "GET", "start、end", "COP 排名。"),
            ("\code{/analytics/anomalies}", "GET", "building、floor、start、end", "异常明细。"),
            ("\code{/analytics/anomaly-reasons}", "GET", "building、floor、start、end", "异常原因统计。"),
            ("\code{/analytics/anomaly-explanations/\{id\}}", "GET", "record id", "单条异常解释。"),
            ("\code{/analytics/floor-summary}", "GET", "building、start、end", "楼层健康汇总。"),
            ("\code{/analytics/equipment-summary}", "GET", "building、floor", "设备点位汇总。"),
            ("\code{/analytics/operation-report}", "GET", "building、floor、start、end", "运营日报。"),
            ("\code{/assistant/providers}", "GET", "无", "可用模型提供商。"),
            ("\code{/assistant/query}", "POST", "question、provider、model", "问答结果。"),
            ("\code{/work-orders}", "GET", "status 可选", "工单列表。"),
            ("\code{/work-orders}", "POST", "record id、assignee、note", "新建工单。"),
            ("\code{/work-orders/\{id\}}", "PATCH", "status、note", "更新后工单。"),
        ],
    )
    + r"""
\subsection{MCP Tools 详细说明}
"""
    + make_longtable(
        "MCP Tools 详细说明",
        "L{4.0cm}L{5.4cm}L{5.0cm}",
        ("工具", "用途", "与 REST API 的关系"),
        [
            ("\code{get_dataset_meta}", "获取数据集规模、字段和时间范围。", "对应数据元信息接口。"),
            ("\code{list_buildings}", "列出建筑选项。", "对应建筑清单接口。"),
            ("\code{query_records}", "按条件查询记录。", "对应记录查询接口。"),
            ("\code{get_overview}", "获取总览指标。", "对应总览接口。"),
            ("\code{get_time_summary}", "获取时间序列统计。", "对应时间汇总接口。"),
            ("\code{get_building_comparison}", "获取建筑对比。", "对应建筑对比接口。"),
            ("\code{get_cop_ranking}", "获取 COP 排名。", "对应 COP 接口。"),
            ("\code{get_anomalies}", "查询异常明细。", "对应异常接口。"),
            ("\code{explain_anomaly}", "解释单条异常。", "对应异常解释接口。"),
            ("\code{get_floor_summary}", "获取楼层健康状态。", "对应楼层接口。"),
            ("\code{get_equipment_summary}", "获取设备状态。", "对应设备接口。"),
            ("\code{suggest_work_orders}", "根据异常建议工单。", "复用工单和异常服务。"),
            ("\code{get_operation_report}", "生成运营报告。", "对应日报接口。"),
            ("\code{search_knowledge}", "检索本地知识库。", "复用知识库检索服务。"),
            ("\code{ask_energy_assistant}", "面向 AI 客户端的问答入口。", "复用问答服务。"),
        ],
    )
)


SRS_REVIEW_TOPICS = [
    "项目目标", "用户角色", "业务边界", "数据来源", "字段含义", "建筑范围", "楼层范围", "时间范围", "查询条件", "导出功能",
    "总览指标", "趋势统计", "建筑对比", "COP 排名", "异常规则", "异常明细", "异常解释", "健康楼层", "设备分析", "三维视图",
    "楼层联动", "工单创建", "工单完成", "工单持久化", "运营日报", "节能建议", "收益模拟", "智能问答", "模型选择", "本地回退",
    "MCP 工具", "MCP 资源", "接口错误", "空数据状态", "权限边界", "密钥安全", "部署说明", "测试口径", "验收口径", "系统展示路径",
    "性能边界", "扩展方向", "维护责任", "交付材料", "文档一致性", "风险说明", "配置项", "日志提示", "最终结论", "课程验收点",
]

SRS_EXPANSION += (
    r"""
\subsection{需求可追踪性说明}
需求可追踪性用于说明需求文档是否能够支撑设计、开发、测试和最终验收。每一项都要求能在系统、代码或文档中找到证据。
"""
    + make_longtable(
        "需求可追踪性说明",
        "L{1.7cm}L{3.0cm}L{6.2cm}L{4.4cm}",
        ("编号", "需求项", "追踪说明", "验收依据"),
        [
            (
                f"SR-{index:02d}",
                topic,
                f"“{topic}”已经在需求、界面、接口或验收说明中被明确描述，避免只停留在口头说明。",
                f"能够在正式文档或系统页面中找到“{topic}”对应证据。",
            )
            for index, topic in enumerate(SRS_REVIEW_TOPICS, start=1)
        ],
    )
)


SDD_CHECK_TOPICS = [
    "前后端职责", "路由聚合", "服务层复用", "数据加载", "字段校验", "楼层派生", "设备派生", "COP 计算", "动态阈值", "异常优先级",
    "异常解释结构", "楼层健康状态", "设备维护提示", "工单编号", "工单排序", "工单持久化", "日报生成", "知识库检索", "模型回退", "提供商配置",
    "MCP 工具复用", "MCP 资源输出", "前端状态管理", "三维拖拽", "三维点击联动", "图表空状态", "错误提示", "CSV 导出", "测试隔离", "运行期目录",
    "环境变量读取", "日志定位", "响应模型", "接口兼容", "性能边界", "未来数据库替换", "权限扩展", "真实设备接入", "部署扩展", "文档生成",
]

SDD_EXPANSION += (
    r"""
\subsection{设计要素说明}
本节从工程角度说明系统结构、模块边界和维护方式，使设计方案能够支撑后续理解、复现和扩展。
"""
    + make_longtable(
        "设计要素说明",
        "L{1.7cm}L{3.2cm}L{6.4cm}L{4.0cm}",
        ("编号", "设计项", "设计说明", "设计依据"),
        [
            (
                f"SD-{index:02d}",
                topic,
                f"“{topic}”在设计中具有明确位置、输入输出和失败处理，避免模块之间职责模糊。",
                "可在 SDD、代码结构或接口契约中追踪。",
            )
            for index, topic in enumerate(SDD_CHECK_TOPICS, start=1)
        ],
    )
)


SEE_DETAIL_TOPICS = [
    "需求分析投入", "数据调研投入", "后端接口投入", "分析算法投入", "前端页面投入", "三维交互投入", "工单功能投入", "AI 问答投入",
    "MCP 集成投入", "测试投入", "文档投入", "系统展示投入", "人员单价", "工具成本", "部署成本", "模型调用成本", "维护成本", "数据接入成本",
    "节能收益", "人工节约", "风险避免", "管理价值", "课程评分价值", "推广试点价值", "保守情景", "基准情景", "积极情景", "成本敏感性",
    "收益敏感性", "盈亏平衡", "定价策略", "融资假设", "维护预算", "风险成本", "经济结论",
]

SEE_EXPANSION += (
    r"""
\subsection{经济评价要素}
该表用于把课程要求的成本、收益、定价、融资和评价内容逐项落到项目本身，避免经济分析与系统功能脱节。
"""
    + make_longtable(
        "经济评价要素",
        "L{1.8cm}L{3.3cm}L{6.2cm}L{4.0cm}",
        ("编号", "评价项", "分析说明", "文档体现"),
        [
            (
                f"EC-{index:02d}",
                topic,
                f"围绕“{topic}”说明其与建筑能源管理系统的关系，并给出成本、收益或管理价值判断。",
                "SEE 正文或补充表格中体现。",
            )
            for index, topic in enumerate(SEE_DETAIL_TOPICS, start=1)
        ],
    )
)


SEM_CONTROL_TOPICS = [
    "任务分解", "成员边界", "第一次整合", "第二次整合", "最终优化", "接口控制", "数据控制", "代码验证", "测试闸门", "文档闸门",
    "安全闸门", "交付闸门", "风险跟踪", "变更记录", "沟通机制", "质量目标", "配置管理", "版本管理", "依赖管理", "运行环境",
    "系统展示", "PPT 协同", "视频协同", "最终打包", "密钥排查", "PDF 版式", "图表版式", "表格版式", "README 说明", "部署说明",
    "验收路径", "问题记录", "纠偏动作", "经验总结", "后续维护",
]

SEM_EXPANSION += (
    r"""
\subsection{管理控制项}
以下控制项覆盖项目过程监控和最终交付管理，是从“能做出来”到“能稳定交付”的管理保证。
"""
    + make_longtable(
        "管理控制项",
        "L{1.8cm}L{3.2cm}L{6.4cm}L{4.0cm}",
        ("编号", "控制项", "控制说明", "责任输出"),
        [
            (
                f"MC-{index:02d}",
                topic,
                f"对“{topic}”设置明确控制方式，发现问题后由项目整合人员修复或协调相关成员补齐。",
                "过程记录、提交记录或最终文档。",
            )
            for index, topic in enumerate(SEM_CONTROL_TOPICS, start=1)
        ],
    )
)


TEST_REGRESSION_TOPICS = [
    "后端启动", "前端启动", "健康检查", "数据元信息", "建筑清单", "记录查询", "楼层筛选", "时间筛选", "CSV 导出", "总览 KPI",
    "趋势图", "建筑对比", "COP 排名", "异常明细", "异常原因", "异常解释", "楼层汇总", "设备汇总", "三维旋转", "三维点击",
    "健康楼层", "工单创建", "工单完成", "工单刷新", "运营日报", "知识库问答", "模型列表", "模型回退", "MCP 工具", "MCP 资源",
    "空数据", "接口错误", "密钥缺失", "构建测试", "最终打包",
]

TEST_EXPANSION += (
    r"""
\subsection{回归测试范围}
回归测试用于每次最终文档或系统调整后快速确认核心能力未被破坏。
"""
    + make_longtable(
        "回归测试范围",
        "L{1.8cm}L{3.2cm}L{6.4cm}L{4.0cm}",
        ("编号", "回归项", "验证动作", "通过标准"),
        [
            (
                f"RT-{index:02d}",
                topic,
                f"执行与“{topic}”相关的页面操作、接口请求或脚本验证，记录是否出现错误。",
                "结果与正式文档说明一致。",
            )
            for index, topic in enumerate(TEST_REGRESSION_TOPICS, start=1)
        ],
    )
)


USER_TRAINING_TOPICS = [
    "环境准备", "复制环境变量", "安装后端依赖", "安装前端依赖", "启动后端", "启动前端", "打开总览", "理解 KPI", "旋转楼宇", "点击楼层",
    "查询记录", "筛选楼层", "导出 CSV", "查看趋势", "查看异常", "查看解释", "查看设备", "创建工单", "完成工单", "刷新验证",
    "查看日报", "提出问题", "选择模型", "理解回退", "启动 MCP", "查看 API 文档", "运行测试", "编译文档", "密钥安全", "整理交付包",
    "打开正式 PDF", "准备 PPT", "录制视频", "系统展示", "故障排查",
]

USER_EXPANSION += (
    r"""
\subsection{系统使用任务说明}
本节说明使用者完成安装、运行、主要功能操作和基础排查时需要覆盖的任务范围。
"""
    + make_longtable(
        "系统使用任务说明",
        "L{1.8cm}L{3.2cm}L{6.4cm}L{4.0cm}",
        ("编号", "任务", "操作说明", "完成结果"),
        [
            (
                f"UT-{index:02d}",
                topic,
                f"按照用户手册完成“{topic}”相关操作，遇到失败时先检查终端输出和常见问题表。",
                "能够完成对应操作并获得预期页面或终端结果。",
            )
            for index, topic in enumerate(USER_TRAINING_TOPICS, start=1)
        ],
    )
)


DATA_FIELD_TOPICS = [
    ("\\code{record_id}", "记录编号", "唯一标识一条能耗记录。"),
    ("\\code{building_id}", "建筑编号", "用于接口筛选和建筑对比。"),
    ("\\code{building_name}", "建筑名称", "用于页面展示。"),
    ("\\code{building_type}", "建筑类型", "用于解释不同建筑业务场景。"),
    ("\\code{timestamp}", "采集时间", "用于时间筛选和趋势汇总。"),
    ("\\code{electricity_kwh}", "电耗", "用于总览、趋势和异常判断。"),
    ("\\code{water_m3}", "水耗", "用于建筑综合对比。"),
    ("\\code{hvac_kwh}", "空调电耗", "用于 COP 和空调效率分析。"),
    ("\\code{cooling_load_kwh}", "制冷量", "用于计算平均 COP。"),
    ("\\code{environment_temp_c}", "环境温度", "用于解释负荷变化。"),
    ("\\code{humidity_rh}", "相对湿度", "用于辅助解释空调负荷。"),
    ("\\code{occupancy_density_per_100m2}", "人员密度", "用于解释建筑使用强度。"),
    ("\\code{equipment_id}", "设备编号", "用于设备维度分析。"),
    ("\\code{equipment_status}", "设备状态", "用于异常规则。"),
    ("\\code{floor_label}", "楼层标签", "运行时派生，用于楼层分析和 3D 联动。"),
    ("\\code{area_name}", "区域名称", "运行时派生，用于业务解释。"),
    ("\\code{equipment_type}", "设备类型", "运行时派生，用于维护建议。"),
    ("\\code{average_cop}", "平均 COP", "运行时计算，用于能效评价。"),
    ("\\code{is_anomaly}", "异常标记", "运行时计算，用于统计分析。"),
    ("\\code{anomaly_reason}", "异常原因", "运行时生成，用于解释和工单。"),
]

DATA_EXPANSION += (
    r"""
\subsection{字段契约与派生口径}
字段契约用于保证数据浏览、统计分析、MCP 和文档说明使用同一套口径。
"""
    + make_longtable(
        "字段契约与派生口径",
        "L{4.2cm}L{3.0cm}L{7.4cm}",
        ("字段", "含义", "使用说明"),
        DATA_FIELD_TOPICS,
    )
    + make_longtable(
        "接口错误处理约定",
        "L{2.0cm}L{4.2cm}L{5.0cm}L{3.4cm}",
        ("编号", "错误场景", "后端处理", "前端表现"),
        [
            ("E-01", "参数类型错误", "返回参数校验错误。", "提示筛选条件错误。"),
            ("E-02", "建筑不存在", "返回空结果或错误提示。", "显示空状态。"),
            ("E-03", "楼层不存在", "返回空结果。", "显示健康或无数据提示。"),
            ("E-04", "时间范围无效", "拒绝请求或返回空结果。", "提示时间范围错误。"),
            ("E-05", "记录编号不存在", "返回 404。", "提示记录不存在。"),
            ("E-06", "工单编号不存在", "返回 404。", "提示工单不存在。"),
            ("E-07", "工单写入失败", "返回保存失败信息。", "提示稍后重试。"),
            ("E-08", "模型配置缺失", "回退本地知识库。", "显示回退答案。"),
            ("E-09", "MCP 工具异常", "返回工具调用错误。", "AI 客户端可读取错误。"),
            ("E-10", "数据文件缺失", "返回服务错误并记录日志。", "页面显示数据加载失败。"),
        ],
    )
)


SRS_RATIONALE_TOPICS = [
    "建筑能源管理场景", "楼层维度分析", "异常优先展示", "健康楼层简化展示", "工单创建后直接处理中",
    "工单状态持久化", "数据浏览独立查询", "统计分析承担异常诊断", "COP 指标", "设备状态规则",
    "夜间负荷规则", "可解释规则算法", "CSV 导出", "运营日报", "本地知识库",
    "外部模型可选", "MCP 与 REST 共用服务层", "真实密钥不入库", "多月样例数据", "自动检测定位",
    "数据与页面解耦", "异常条数一致性", "楼层联动有效性", "刷新后状态保留", "模型失败回退",
    "接口契约稳定性", "系统可复现运行", "核心功能测试覆盖", "文档与系统一致性", "经济分析关联性",
    "README 运行说明", "SRS 需求基线", "SDD 设计基线", "SEE 经济评价", "SEM 工程管理",
    "系统启动路径", "页面刷新行为", "源码结构", "API 契约", "交付材料结构",
    "真实楼宇数据扩展", "用户权限扩展", "数据库替换扩展", "预测模型扩展", "真实工单系统扩展",
]

SRS_EXPANSION += (
    r"""
\subsection{需求合理性说明}
本节说明关键需求的来源、业务价值、验收方式和与系统功能的对应关系，使需求文档不仅描述“系统有什么功能”，也说明这些功能为什么纳入本期范围。
"""
    + make_longtable(
        "需求合理性说明",
        "L{1.7cm}L{4.4cm}L{6.0cm}L{3.4cm}",
        ("编号", "需求主题", "合理性说明", "关联证据"),
        [
            (
                f"RA-{index:02d}",
                topic,
                f"“{topic}”与建筑能源管理、异常处置、系统运行或后续扩展有关，能够支撑本项目的业务闭环和工程完整性。",
                "SRS、页面展示或接口返回。",
            )
            for index, topic in enumerate(SRS_RATIONALE_TOPICS, start=1)
        ],
    )
)

SRS_CHANGE_TOPICS = [
    ("C-01", "从单日数据扩展为多月数据", "解决数据量太少、趋势不足的问题，使系统能展示 2026-01-01 至 2026-06-01 的连续记录。"),
    ("C-02", "增加楼层筛选", "把建筑级分析细化到楼层级，支撑 3D 楼层点击和异常定位。"),
    ("C-03", "统计分析承接异常查询", "将异常相关内容集中在统计分析页，数据浏览保持全量查询职责。"),
    ("C-04", "健康楼层简化展示", "健康楼层只显示健康提示，避免空图表降低页面表达质量。"),
    ("C-05", "增加三维楼宇视图", "通过立体楼宇展示楼层风险，使总览页更直观。"),
    ("C-06", "增加工单持久化", "避免刷新后工单消失，提高业务闭环可信度。"),
    ("C-07", "调整工单状态", "去掉无意义的待处理状态，创建后直接进入处理中。"),
    ("C-08", "增加决策报告", "把异常、工单和收益建议汇总为管理视角输出。"),
    ("C-09", "增加外部模型选择", "支持多个 OpenAI-compatible 模型提供商，但保留本地回退。"),
    ("C-10", "增加 MCP Server", "让 AI 客户端可直接调用项目数据和分析能力。"),
    ("C-11", "增加正式 LaTeX 文档", "把 Markdown 过程资料升级为可提交的正式 PDF。"),
    ("C-12", "重画关键流程图", "解决图形重叠和箭头混乱问题，提高文档可读性。"),
    ("C-13", "收紧表格版式", "避免长表超出页面宽度。"),
    ("C-14", "增加交付材料目录", "将源码、正式 PDF、LaTeX 源和展示材料分区整理。"),
    ("C-15", "增加安全控制", "确保交付材料不包含真实 .env 和 API Key。"),
]

SRS_EXPANSION += (
    r"""
\subsection{需求变更与版本控制说明}
项目在最终打磨阶段根据系统展示效果、课程要求和系统完整性进行了多轮需求修正。以下记录说明主要变更的原因和需求层影响。
"""
    + make_longtable(
        "需求变更与版本控制说明",
        "L{1.7cm}L{4.2cm}L{6.6cm}L{3.0cm}",
        ("编号", "变更项", "变更原因与影响", "状态"),
        [(code, title, detail, "已纳入最终版") for code, title, detail in SRS_CHANGE_TOPICS],
    )
)


SDD_AUDIT_TOPICS = [
    "总览页数据链路", "数据浏览链路", "统计分析链路", "异常解释链路", "三维点击链路", "工单创建链路", "工单完成链路", "运营日报链路",
    "AI 问答链路", "MCP 调用链路", "CSV 导出链路", "环境变量链路", "模型回退链路", "错误处理链路", "空状态链路",
    "数据缓存策略", "服务复用策略", "字段命名策略", "Schema 校验策略", "接口前缀策略", "运行期文件策略", "测试数据隔离策略",
    "前端导航策略", "组件拆分策略", "图表加载策略", "3D 状态同步策略", "工单排序策略", "报告生成策略", "文档生成策略", "交付包同步策略",
]

SDD_EXPANSION += (
    r"""
\subsection{端到端设计说明}
端到端设计说明用于展示系统设计是否形成闭环。每条记录都能够从前端操作追踪到后端服务和数据输出。
"""
    + make_longtable(
        "端到端设计说明",
        "L{1.7cm}L{4.0cm}L{6.2cm}L{3.6cm}",
        ("编号", "设计主题", "链路说明", "设计证据"),
        [
            (
                f"DA-{index:02d}",
                topic,
                f"“{topic}”从界面入口、接口调用、服务处理到返回展示均具有明确设计，避免只实现单点功能。",
                "SDD 图、模块表或源码路径。",
            )
            for index, topic in enumerate(SDD_AUDIT_TOPICS, start=1)
        ],
    )
)


SEE_FINANCE_TOPICS = [
    "开发投入折算", "测试投入折算", "文档投入折算", "维护投入折算", "人员机会成本", "本地部署节省", "云部署备选成本", "模型调用边际成本",
    "数据接入追加成本", "真实设备集成成本", "权限系统追加成本", "数据库替换成本", "多校区推广成本", "运维培训成本", "使用阻力成本",
    "低效设备发现收益", "夜间负荷治理收益", "COP 优化收益", "人工报表节约", "异常闭环管理价值", "数据口径统一价值", "管理可视化价值",
    "系统展示价值", "课程学习价值", "试点推广价值", "保守 ROI", "基准 ROI", "乐观 ROI", "回收期", "盈亏平衡点",
]

SEE_EXPANSION += (
    r"""
\subsection{财务分析展开项}
财务分析展开项用于说明本项目的经济分析并非脱离系统泛泛而谈，而是与每个功能模块、成本来源和收益来源直接关联。
"""
    + make_longtable(
        "财务分析展开项",
        "L{1.7cm}L{4.0cm}L{6.4cm}L{3.4cm}",
        ("编号", "分析项", "说明", "经济意义"),
        [
            (
                f"FA-{index:02d}",
                topic,
                f"对“{topic}”进行成本或收益解释，并说明它如何影响项目投入、维护费用、节能收益或管理价值。",
                "用于支撑 SEE 结论。",
            )
            for index, topic in enumerate(SEE_FINANCE_TOPICS, start=1)
        ],
    )
)


SEM_EVIDENCE_TOPICS = [
    "第一次任务说明", "第二次任务说明", "整合说明", "接口契约", "数据字典", "测试计划", "验收报告", "运行脚本", "环境示例", "Git 忽略规则",
    "安全控制", "构建日志", "测试日志", "正式 PDF", "LaTeX 源文件", "最终交付说明", "系统展示脚本", "PPT 材料", "视频材料", "交付目录",
    "源码副本", "Markdown 过程资料", "外部数据调研", "大模型接入说明", "MCP 说明", "最终 README", "风险登记册", "质量矩阵", "变更控制", "维护建议",
]

SEM_EXPANSION += (
    r"""
\subsection{过程证据说明}
过程证据说明用于体现项目具备需求、设计、开发、测试、经济分析、管理控制和交付整理的完整过程。
"""
    + make_longtable(
        "过程证据说明",
        "L{1.7cm}L{4.0cm}L{6.2cm}L{3.6cm}",
        ("编号", "证据项", "说明", "存放位置"),
        [
            (
                f"PE-{index:02d}",
                topic,
                f"“{topic}”用于支撑软件工程管理过程，能够说明项目从任务分解到最终交付的演进路径。",
                "仓库文档或交付材料目录。",
            )
            for index, topic in enumerate(SEM_EVIDENCE_TOPICS, start=1)
        ],
    )
)


DOCUMENTS = [
    (
        "01-SRS-软件需求规格说明书.tex",
        "SRS 软件需求规格说明书",
        SRS_ABSTRACT,
        SRS_BODY + SRS_EXPANSION,
    ),
    (
        "02-SDD-SDS-软件设计说明书.tex",
        "SDD/SDS 软件设计说明书",
        SDD_ABSTRACT,
        SDD_BODY + SDD_EXPANSION,
    ),
    (
        "03-SEE-软件经济分析与评价.tex",
        "SEE 软件经济分析与评价",
        SEE_ABSTRACT,
        SEE_BODY + SEE_EXPANSION,
    ),
    (
        "04-SEM-软件工程管理说明.tex",
        "SEM 软件工程管理说明",
        SEM_ABSTRACT,
        SEM_BODY + SEM_EXPANSION,
    ),
    (
        "05-测试与验收报告.tex",
        "测试与验收报告",
        TEST_ABSTRACT,
        TEST_BODY + TEST_EXPANSION,
    ),
    (
        "06-用户手册与部署说明.tex",
        "用户手册与部署说明",
        USER_ABSTRACT,
        USER_BODY + USER_EXPANSION,
    ),
    (
        "07-数据接口与MCP说明.tex",
        "数据、接口与 MCP 说明",
        DATA_ABSTRACT,
        DATA_BODY + DATA_EXPANSION,
    ),
    (
        "08-最终提交说明.tex",
        "最终提交说明",
        SUBMIT_ABSTRACT,
        SUBMIT_BODY,
    ),
]


README = """# LaTeX 正式交付文档

本目录保存课程期末项目正式交付文档的 LaTeX 源文件和编译后的 PDF。文档样式基于实验三 `main.tex` 的 `ctexart` 模板扩展，使用 XeLaTeX 编译。

正式提交时以 `pdf-latex/` 或 `docs/final-latex/pdf/` 中的 PDF 为准。真实 `.env` 和 API Key 不得进入本目录或最终压缩包。

生成命令：

```powershell
python .\\scripts\\build_final_latex_documents.py --compile
```
"""


def write_documents() -> list[Path]:
    for path in (TEX_DIR, BUILD_DIR, PDF_DIR, SUBMISSION_LATEX_DIR, SUBMISSION_PDF_DIR):
        path.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for filename, title, abstract, body in DOCUMENTS:
        content = wrap_document(title, abstract, body)
        tex_path = TEX_DIR / filename
        tex_path.write_text(content, encoding="utf-8")
        shutil.copy2(tex_path, SUBMISSION_LATEX_DIR / filename)
        written.append(tex_path)

    (DOCS_DIR / "README.md").write_text(README, encoding="utf-8")
    (SUBMISSION_LATEX_DIR / "README.md").write_text(README, encoding="utf-8")
    return written


def compile_documents(tex_files: list[Path]) -> None:
    xelatex = shutil.which("xelatex")
    if not xelatex:
        raise RuntimeError("xelatex was not found in PATH")

    for tex_path in tex_files:
        for _ in range(2):
            subprocess.run(
                [
                    xelatex,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-output-directory",
                    str(BUILD_DIR),
                    str(tex_path),
                ],
                cwd=ROOT,
                check=True,
            )
        pdf_path = BUILD_DIR / tex_path.with_suffix(".pdf").name
        if not pdf_path.exists():
            raise RuntimeError(f"PDF was not generated: {pdf_path}")
        shutil.copy2(pdf_path, PDF_DIR / pdf_path.name)
        shutil.copy2(pdf_path, SUBMISSION_PDF_DIR / pdf_path.name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile", action="store_true", help="Compile PDFs with XeLaTeX")
    args = parser.parse_args()

    tex_files = write_documents()
    if args.compile:
        compile_documents(tex_files)

    print(f"Generated {len(tex_files)} LaTeX documents in {TEX_DIR}")
    if args.compile:
        print(f"PDFs written to {PDF_DIR}")
        print(f"Submission PDFs written to {SUBMISSION_PDF_DIR}")


if __name__ == "__main__":
    main()
