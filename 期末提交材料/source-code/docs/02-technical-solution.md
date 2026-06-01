# 技术方案文档

## 1. 总体架构

系统采用前后端分离结构：

- 前端：Vue 3 + Vite，负责页面展示、交互、后端接口调用。
- 后端：FastAPI，负责数据读取、查询、分析和问答接口封装。
- MCP 接入层：基于官方 `mcp` Python SDK，将数据查询、统计分析、异常诊断、运营报告和智能问答封装为 MCP Tools 与 Resources。
- 数据层：先使用 CSV 样例数据，后续可扩展到数据库。
- 知识层：先以 Markdown 文档为知识库载体，后续接入向量检索和大模型。

## 2. 模块划分

### 2.1 后端模块

- `api/routes/health.py`：运行状态检查。
- `api/routes/data.py`：数据概览和记录查询。
- `api/routes/analytics.py`：时间汇总、建筑对比、异常分析、楼层区域分析、设备监测、异常工单和优化建议。
- `api/routes/export.py`：原始记录 CSV 导出。
- `api/routes/assistant.py`：问答接口。
- `app/mcp_server.py`：MCP Server 入口，支持 stdio、SSE 和 streamable-http transport。
- `services/data_loader.py`：读取和过滤数据集。
- `services/analysis_service.py`：统计分析、派生楼层区域、设备优先级、异常工单和优化建议逻辑。
- `services/export_service.py`：CSV 导出逻辑。
- `services/assistant_service.py`：规则问答、知识文件引用和追问建议逻辑。
- `services/llm_client.py`：可选外部大模型调用逻辑，默认关闭，失败时回退本地问答。

### 2.2 前端模块

- 项目首页：展示系统定位、KPI、模块状态。
- 数据模块：展示查询表格、建筑/时间筛选器和导出入口。
- 分析模块：展示趋势图、异常原因、楼层区域分析、设备运行监测、异常工单、优化建议、建筑对比和 COP 排名。
- 问答模块：提供推荐问题、结构化回答、引用来源和继续追问。

## 3. 数据设计

当前样例数据字段包含：

- 建筑标识：`building_id`、`building_name`、`building_type`
- 时间信息：`timestamp`
- 能耗信息：`electricity_kwh`、`water_m3`、`hvac_kwh`、`cooling_load_kwh`
- 环境和运行信息：温度、湿度、人员密度、设备编号、设备状态

这些字段已经足够支撑查询、汇总、COP、异常分析，并可在分析阶段派生 `floor_label`、`zone_name`、`equipment_type` 等业务字段，用于演示逐层定位和设备级运维。

当前主数据集仍以自建模拟数据为主，但其字段设计与后续模拟规则应参考公开建筑能耗数据和官方资料。可优先参考 [`docs/10-data-source-research.md`](./10-data-source-research.md) 中整理的 BDG2、SHIFDR、NYC LL84、AlphaBuilding 与 NREL 相关资料。

## 4. 接口设计

### 4.1 概览接口

- `GET /api/v1/overview`
- 返回记录总数、建筑数、时间范围、总能耗和平均 COP

### 4.2 数据查询接口

- `GET /api/v1/records`
- 支持按建筑和时间区间筛选

### 4.3 分析接口

- `GET /api/v1/analytics/time-summary`
- `GET /api/v1/analytics/building-comparison`
- `GET /api/v1/analytics/cop-ranking`
- `GET /api/v1/analytics/anomalies`
- `GET /api/v1/analytics/anomaly-reasons`
- `GET /api/v1/analytics/floor-summary`
- `GET /api/v1/analytics/equipment-summary`
- `GET /api/v1/analytics/work-orders`
- `GET /api/v1/analytics/optimization-recommendations`

### 4.4 导出接口

- `GET /api/v1/export/csv`
- 支持按建筑和时间范围导出当前筛选结果
- 适合作为第一次整合后的独立后端增量能力

### 4.5 问答接口

- `POST /api/v1/assistant/query`
- 默认使用规则逻辑 + 知识素材引用
- 若本地 `.env` 开启 `LLM_ENABLED=true`，可调用外部 OpenAI-compatible 模型增强回答
- 外部模型不可用时保持本地规则问答结果，避免演示被网络和限流影响

### 4.6 MCP 协议接口

- 启动脚本：`scripts/start-mcp.ps1`
- 默认 transport：`stdio`，适合 Cursor、Claude Desktop 等支持 MCP 的本地客户端
- HTTP transport：`.\scripts\start-mcp.ps1 -Transport streamable-http -HostAddress 127.0.0.1 -Port 8765`
- HTTP MCP 路径：`http://127.0.0.1:8765/mcp`

MCP Tools 覆盖：

- 数据接入：`get_dataset_meta`、`list_buildings`
- 数据查询：`query_energy_records`
- 统计分析：`get_energy_overview`、`get_time_summary`、`get_building_comparison`、`get_cop_ranking`
- 异常诊断：`get_anomalies`、`get_anomaly_reasons`、`explain_anomaly`
- 运维决策：`get_floor_summary`、`get_equipment_summary`、`suggest_anomaly_work_orders`、`get_optimization_recommendations`、`get_operation_report`
- 智能问答：`search_energy_knowledge`、`ask_energy_assistant`

MCP Resources 覆盖数据集元信息、建筑清单、运营报告和知识库入口。该层与 REST API 复用同一服务层，避免两套业务逻辑不一致。

## 5. 智能问答演进路径

### 已实现阶段

- 使用规则化逻辑快速给出演示答案
- 可以引用样例数据、数据质量报告、术语规则、异常诊断和设备维护知识文件
- 已支持推荐追问，适合课堂连续演示
- 已预留外部大模型供应商选择配置，详见 [`docs/13-llm-provider-integration.md`](13-llm-provider-integration.md)

### 下一阶段

- 将 Markdown 文档切分为知识片段并建立向量索引
- 在当前 MCP Tools 之上接入更完整的 LLM/RAG 服务链路
- 返回来源引用和结构化建议

## 6. 后续重点扩展

- 补充更多数据导入和清洗脚本
- 将知识库切分为知识片段并建立向量索引
- 视课程展示需要，为 MCP HTTP 模式增加更完整的客户端配置示例
- 增加认证、日志、真实传感器接入和更细粒度异常闭环
- 持续增加测试覆盖率
