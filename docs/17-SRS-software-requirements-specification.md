# SRS 软件需求规格说明书

> 正式提交版已经按课程 LaTeX 模板重写并编译为 PDF。评审和最终提交请优先使用 `docs/final-latex/pdf/01-SRS-软件需求规格说明书.pdf`，LaTeX 源文件见 `docs/final-latex/tex/01-SRS-软件需求规格说明书.tex`。本文档保留为过程版本和快速查阅入口。

项目名称：基于大模型的建筑能源智能管理与运维优化系统

文档版本：V1.0

编写日期：2026-05-31

适用范围：课程期末项目最终提交、项目展示演示、系统验收与后续维护。

## 1. 文档信息

| 项目 | 内容 |
| --- | --- |
| 文档类型 | Software Requirements Specification, SRS |
| 面向对象 | 任课教师、项目组成员、项目展示评审、后续维护人员 |
| 关联文档 | `docs/01-requirements.md`、`docs/03-user-manual.md`、`docs/06-api-contract.md`、`docs/14-final-submission-checklist.md` |
| 代码范围 | `backend/`、`frontend/`、`data/`、`knowledge_base/`、`scripts/` |
| 当前状态 | 最终演示版需求基线 |

## 2. 引言

### 2.1 编写目的

本文档用于明确本系统在期末项目中的需求边界、功能范围、非功能要求、接口要求、数据要求和验收标准。它是后续软件设计说明书、测试报告、经济分析和工程管理说明的基础。

### 2.2 项目背景

建筑能源管理场景中，能耗数据通常分散在电表、空调系统、设备台账和人工巡检记录中，管理者难以及时发现异常楼层、异常设备和高能耗时段。本项目以校园建筑能耗管理为背景，构建一个可演示的智能运维平台，将数据浏览、统计分析、三维风险态势、异常工单、运营报告、知识库问答、外部大模型增强和 MCP 数据接入整合到一个系统中。

### 2.3 项目目标

- 构建不少于 1000 条记录的建筑能耗样例数据集，并提供数据字典。
- 支持按建筑、楼层、时间范围查询和导出能耗记录。
- 支持总览、趋势、建筑对比、COP、异常原因、楼层和设备分析。
- 支持三维楼宇风险态势展示，并能联动异常分析。
- 支持异常工单创建、分派、处理、完成和持久化。
- 支持知识库问答和可选外部大模型问答。
- 支持基于 MCP 协议的数据接入、查询统计、异常解释和智能问答工具。
- 形成可运行、可测试、可演示、可打包提交的完整课程项目。

## 3. 综合描述

### 3.1 产品定位

本系统是面向课程项目的建筑能源智能管理原型系统，不直接接入真实传感器，而是使用经过真实数据源调研和领域规则参考后构造的样例数据，模拟建筑能耗监测、异常诊断和运维处置流程。

### 3.2 用户角色

| 角色 | 主要诉求 | 典型操作 |
| --- | --- | --- |
| 能源管理人员 | 快速掌握建筑能耗和异常情况 | 查看总览、统计分析、运营日报 |
| 运维人员 | 定位异常楼层和设备并处理工单 | 查看异常解释、创建工单、更新状态 |
| 管理者 | 了解节能收益和管理成效 | 查看决策报告、导出数据、查看风险排序 |
| 项目评审/教师 | 验收系统功能和工程完整性 | 运行系统、查看文档、检查测试结果 |
| AI 客户端/智能体 | 通过协议调用项目能力 | 使用 MCP Tools 查询数据和生成分析 |

### 3.3 运行环境

- 操作系统：Windows 10/11，PowerShell。
- 后端：Python 3.11，FastAPI，Pandas，MCP Python SDK。
- 前端：Node.js，Vue 3，Vite，ECharts。
- 数据：CSV 样例数据、JSON 工单持久化文件、Markdown 知识库。
- 浏览器：Chrome、Edge 或其他现代浏览器。

### 3.4 约束与假设

- 样例数据用于课程演示，不作为真实能耗审计凭证。
- 外部大模型 API Key 只能放在本地 `.env`，不得提交到 GitHub。
- Web 前端调用 REST API；AI 客户端可通过 MCP Server 调用同一套服务能力。
- 课程验收优先关注功能闭环、工程组织、经济分析和演示可复现性。

## 4. 功能需求

### FR-01 数据集与数据字典

系统应提供标准化建筑能耗数据集，当前样例数据共 `4,864` 条，覆盖 `2026-01-01 00:00` 至 `2026-06-01 21:00`，包含 4 栋建筑。系统应提供数据字典说明字段含义、单位、类型和用途。

验收方式：检查 `data/samples/energy_records.csv`、`data/dictionaries/energy_records_dictionary.csv` 和 `docs/10-data-source-research.md`。

### FR-02 数据总览

系统应展示总记录数、建筑数、总电耗、平均 COP、异常数量、最近数据时间等关键指标，并为后续分析提供入口。

验收方式：打开前端总览页，检查 KPI 卡片与后端 `/api/v1/overview` 返回一致。

### FR-03 数据浏览与查询

系统应支持按建筑、楼层、时间范围和记录数量查询能耗记录。查询结果应展示记录 ID、建筑、楼层、区域、时间、电耗、空调电耗、COP、设备状态等信息。

验收方式：在“数据浏览”页切换筛选条件，并检查 `/api/v1/records`。

### FR-04 数据导出

系统应支持将当前筛选条件下的数据导出为 CSV 文件，便于报告和二次分析。

验收方式：调用 `/api/v1/export/csv` 或在页面触发导出。

### FR-05 统计分析

系统应支持按建筑、楼层、时间范围进行统计分析，至少包括时间序列汇总、建筑对比、COP 排名、异常明细、异常原因、楼层汇总、设备汇总和优化建议。

验收方式：打开“统计分析”页，选择不同建筑和楼层，检查图表、异常表格和健康楼层提示。

### FR-06 三维楼层风险态势

系统应在总览页提供可拖拽旋转的三维楼宇风险视图，以颜色区分异常风险状态。点击风险楼层后，应跳转到统计分析页并自动带入建筑与楼层筛选。

验收方式：在总览页拖拽旋转视图，点击异常楼层，检查页面联动。

### FR-07 异常解释

系统应对异常记录生成解释，包括触发规则、关键指标、可能原因和建议动作。

验收方式：在统计分析页点击异常明细中的“解释”操作，或调用 `/api/v1/analytics/anomaly-explanations/{record_id}`。

### FR-08 异常工单

系统应支持从异常记录创建工单，选择建筑、楼层、异常记录和管理员，生成“处理中”状态工单。工单应支持完成和忽略，状态变化应持久化保存。

验收方式：打开“工单中心”，创建工单、完成工单、刷新页面后检查状态是否保留。

### FR-09 决策报告

系统应生成运营日报，汇总能源总览、重点风险、最近异常、工单状态、未来能耗估算和建议动作。

验收方式：打开“决策报告”页，点击生成运营日报，或调用 `/api/v1/analytics/operation-report`。

### FR-10 智能问答

系统应支持基于本地知识库的问答，并在配置外部大模型时支持增强回答。回答应尽量引用当前项目数据、知识库条目或分析结果。

验收方式：打开“AI 助手”，提问“当前项目的主要异常风险是什么”等问题，检查回答来源。

### FR-11 外部大模型配置

系统应支持通过 `.env` 配置 NVIDIA、Groq、OpenRouter、SiliconFlow 等 OpenAI-compatible 模型入口。真实 API Key 不得出现在代码仓库。

验收方式：检查 `.env.example`、`docs/13-llm-provider-integration.md` 和 `scripts/test_llm_providers.py`。

### FR-12 MCP 数据接入与查询

系统应提供独立 MCP Server，将数据元信息、建筑清单、能耗查询、统计分析、异常解释、运营报告、知识库检索和智能问答暴露为 MCP Tools 或 Resources。

验收方式：运行 MCP 测试，或通过 `scripts/start-mcp.ps1` 启动 MCP Server。

## 5. 外部接口需求

### 5.1 REST API

REST API 前缀为 `/api/v1`，完整契约见 `docs/06-api-contract.md`。主要接口包括：

- 健康检查：`GET /api/v1/health`
- 数据概览：`GET /api/v1/overview`
- 数据查询：`GET /api/v1/records`
- 统计分析：`GET /api/v1/analytics/*`
- 工单管理：`GET/POST/PATCH /api/v1/work-orders`
- CSV 导出：`GET /api/v1/export/csv`
- 智能问答：`POST /api/v1/assistant/query`

### 5.2 MCP 接口

MCP Server 入口为 `backend/app/mcp_server.py`，启动脚本为 `scripts/start-mcp.ps1`。默认使用 stdio transport，也支持 streamable-http。MCP 详细说明见 `docs/16-mcp-integration.md`。

### 5.3 环境变量接口

系统通过根目录 `.env` 读取本地配置。`.env.example` 只提供变量名和占位值，不包含真实密钥。

## 6. 数据需求

| 数据对象 | 文件或存储位置 | 用途 |
| --- | --- | --- |
| 能耗记录 | `data/samples/energy_records.csv` | 查询、统计、异常检测、图表展示 |
| 数据字典 | `data/dictionaries/energy_records_dictionary.csv` | 字段说明和报告引用 |
| 知识库 | `knowledge_base/` | 本地问答、RAG 素材、运维解释 |
| 工单记录 | `data/runtime/work_orders.json` | 保存用户创建的异常工单 |

## 7. 非功能需求

### 7.1 可运行性

运行人员拉取仓库后，应能根据 README 完成依赖安装、放置 `.env`、启动后端、启动前端并访问系统。

### 7.2 可测试性

系统应提供一键验证脚本 `scripts/check-project.ps1`，覆盖 Python 语法检查、后端测试和前端构建。任何关键步骤失败时，脚本应返回失败。

### 7.3 可演示性

系统应支持 5-8 分钟课程演示路径，覆盖总览、数据浏览、统计分析、三维风险、工单、决策报告、AI 助手和 MCP 说明。

### 7.4 安全性

真实 API Key 只能存放在本地 `.env`。`.gitignore` 应排除 `.env` 和运行期数据。交付确认阶段应检查仓库中不存在真实密钥。

### 7.5 可维护性

REST API、MCP Tools 和前端页面应复用同一套后端服务层，避免业务口径不一致。新增功能时应优先补充测试和 API 契约。

## 8. 需求追踪矩阵

| 需求来源 | 系统实现 | 证据 |
| --- | --- | --- |
| 建筑能耗数据集 | 4,864 条样例数据和数据字典 | `data/samples/energy_records.csv` |
| 查询统计 | REST 数据与分析接口 | `docs/06-api-contract.md` |
| 可视化图表 | 前端趋势、对比、异常原因、3D 风险 | `frontend/src/views/DashboardView.vue` |
| 异常分析 | 异常明细、异常解释、风险楼层 | `backend/app/services/analysis_service.py` |
| 运维闭环 | 工单创建、完成、持久化 | `backend/app/services/work_order_store.py` |
| 大模型问答 | 本地知识库 + 可选外部 LLM | `docs/13-llm-provider-integration.md` |
| MCP 协议接口 | MCP Tools 与 Resources | `backend/app/mcp_server.py` |
| 最终提交材料 | SRS、SDS、SEE、SEM、验收报告 | `docs/17-*.md` 至 `docs/21-*.md` |

## 9. 验收标准

- 后端测试通过，当前基线为 `75 passed`。
- 前端 `npm run build` 成功。
- `scripts/check-project.ps1` 失败时能正确退出，成功时说明系统可演示。
- README 能指导运行人员从空环境拉取、配置、启动系统。
- 最终文档覆盖 SRS、SDS、SEE、SEM。
- 压缩包中不得包含真实 `.env` 和 API Key。
