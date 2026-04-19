# 技术方案文档

## 1. 总体架构

系统采用前后端分离结构：

- 前端：Vue 3 + Vite，负责页面展示、交互、后端接口调用。
- 后端：FastAPI，负责数据读取、查询、分析和问答接口封装。
- 数据层：先使用 CSV 样例数据，后续可扩展到数据库。
- 知识层：先以 Markdown 文档为知识库载体，后续接入向量检索和大模型。

## 2. 模块划分

### 2.1 后端模块

- `api/routes/health.py`：运行状态检查。
- `api/routes/data.py`：数据概览和记录查询。
- `api/routes/analytics.py`：时间汇总、建筑对比、异常分析。
- `api/routes/assistant.py`：问答接口。
- `services/data_loader.py`：读取和过滤数据集。
- `services/analysis_service.py`：统计分析逻辑。
- `services/assistant_service.py`：问答占位逻辑。

### 2.2 前端模块

- 项目首页：展示系统定位、KPI、模块状态。
- 数据模块：后续展示查询表格和筛选器。
- 分析模块：后续接入趋势图、对比图和异常列表。
- 问答模块：后续接入聊天式交互和答案引用来源。

## 3. 数据设计

当前样例数据字段包含：

- 建筑标识：`building_id`、`building_name`、`building_type`
- 时间信息：`timestamp`
- 能耗信息：`electricity_kwh`、`water_m3`、`hvac_kwh`、`cooling_load_kwh`
- 环境和运行信息：温度、湿度、人员密度、设备编号、设备状态

这些字段已经足够支撑第一阶段的查询、汇总、COP 和异常分析。

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
- `GET /api/v1/analytics/anomalies`

### 4.4 问答接口

- `POST /api/v1/assistant/query`
- 当前使用规则化占位逻辑
- 后续升级为“检索 -> 重排 -> 大模型生成”的链路

## 5. 智能问答演进路径

### 当前阶段

- 使用规则化逻辑快速给出演示答案
- 可以引用样例数据与知识库文件路径

### 下一阶段

- 将 Markdown 文档切分为知识片段
- 建立向量索引
- 接入 LLM 服务
- 返回来源引用和结构化建议

## 6. 后续重点扩展

- 补充数据导入和清洗脚本
- 增加 ECharts 图表接口与导出能力
- 增加认证、日志和异常处理
- 增加测试覆盖率
