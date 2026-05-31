# 基于大模型的建筑能源智能管理与运维优化系统

这是课程项目的统一代码仓库。当前版本已经完成第一次整合，不再只是原型骨架，而是一个前后端、数据、知识素材和演示流程都已接回同一仓库的可继续开发版本。

## 项目目标

- 构建不少于 1000 条记录的建筑能耗数据集，并附数据字典。
- 提供按建筑、时间、参数的多条件查询能力。
- 完成时段汇总、COP 计算、异常分析等核心统计分析。
- 提供趋势、对比类可视化展示。
- 集成知识库与大模型问答，支持典型运维场景答复。
- 最终形成可演示系统和完整交付材料。

## 当前仓库包含什么

- `backend/`：FastAPI 后端和 MCP Server，已包含总览、元数据、查询、分析、导出和知识引用型问答接口。
- `frontend/`：Vue 3 + Vite 前端，已形成“总览 / 数据浏览 / 统计分析 / 智能问答”四区工作台。
- `data/`：样例能耗数据、数据字典、原始/处理后数据目录和数据检查说明。
- `knowledge_base/`：异常诊断、设备维护、建筑类型、术语规则和结构化问答素材。
- `docs/`：课程交付文档、接口契约、MCP 集成说明、协作规则、集成清单和测试计划。
- `scripts/`：启动脚本、MCP 启动脚本、检查脚本和样例数据生成脚本。

## 仓库结构

```text
.
|-- backend/
|   |-- app/
|   |   |-- api/routes/
|   |   |-- core/
|   |   |-- schemas/
|   |   `-- services/
|   `-- tests/
|-- frontend/
|   |-- src/components/
|   |-- src/lib/
|   `-- src/views/
|-- data/
|   |-- raw/
|   |-- processed/
|   |-- samples/
|   `-- dictionaries/
|-- knowledge_base/
|   |-- manuals/
|   |-- glossary/
|   `-- faq/
|-- docs/
`-- scripts/
```

## 技术选型

- 后端：FastAPI + Pandas
- 前端：Vue 3 + Vite
- 可视化：ECharts + 自定义三维楼层风险视图
- 智能问答：知识库规则回答 + 可选外部大模型增强
- 数据格式：CSV 为主，后续可扩展数据库

## 快速启动

### 0. 拉取代码与放置环境变量

同学第一次运行时，先拉取仓库并进入项目根目录：

```powershell
git clone https://github.com/ScottBlizzard/building-energy-intelligence-platform.git
cd building-energy-intelligence-platform
```

如果只演示基础系统，可以直接复制模板：

```powershell
Copy-Item .env.example .env
```

如果需要启用页面里的外部大模型选项，由项目负责人单独提供真实 `.env` 文件。同学只需要把这份文件放在仓库根目录，路径应为：

```text
building-energy-intelligence-platform/.env
```

不要把真实 `.env` 放到 `backend/` 或 `frontend/`，也不要提交到 GitHub。后端会自动读取根目录 `.env`；前端默认使用 `/api/v1`，开发环境下由 Vite 代理到 `http://127.0.0.1:8000`，通常不需要单独配置 `frontend/.env`。

### 1. 启动后端

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --app-dir backend
```

或者：

```powershell
.\scripts\start-backend.ps1
```

### 2. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

或者：

```powershell
.\scripts\start-frontend.ps1
```

注意：如果使用脚本启动，后端和前端需要分别开两个 PowerShell 窗口运行。

### 3. 常用访问地址

- 前端开发页：`http://127.0.0.1:5173`
- 后端文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/api/v1/health`

### 4. 启动 MCP Server

默认 stdio transport，适合支持 MCP 的本地客户端：

```powershell
.\scripts\start-mcp.ps1
```

如需 HTTP 方式接入：

```powershell
.\scripts\start-mcp.ps1 -Transport streamable-http -HostAddress 127.0.0.1 -Port 8765
```

### 5. 一键自检

安装完依赖后，可以运行完整检查：

```powershell
.\scripts\check-project.ps1
```

该脚本会执行后端测试和前端构建。通过后说明当前环境基本可以完整运行和演示。

## 已提供接口

- `GET /api/v1/health`
- `GET /api/v1/overview`
- `GET /api/v1/dataset-meta`
- `GET /api/v1/buildings`
- `GET /api/v1/records`
- `GET /api/v1/analytics/time-summary`
- `GET /api/v1/analytics/building-comparison`
- `GET /api/v1/analytics/cop-ranking`
- `GET /api/v1/analytics/anomalies`
- `GET /api/v1/analytics/anomaly-explanations/{record_id}`
- `GET /api/v1/analytics/anomaly-reasons`
- `GET /api/v1/analytics/floor-summary`
- `GET /api/v1/analytics/floor-registry`
- `GET /api/v1/analytics/equipment-summary`
- `GET /api/v1/analytics/work-orders`
- `GET /api/v1/analytics/optimization-recommendations`
- `GET /api/v1/analytics/operation-report`
- `GET /api/v1/work-orders`
- `POST /api/v1/work-orders`
- `PATCH /api/v1/work-orders/{work_order_id}`
- `GET /api/v1/export/csv`
- `GET /api/v1/assistant/providers`
- `POST /api/v1/assistant/query`

MCP 接入说明见 [`docs/16-mcp-integration.md`](docs/16-mcp-integration.md)。MCP Server 入口为 `backend/app/mcp_server.py`，覆盖数据元信息、建筑清单、能耗记录查询、统计分析、异常解释、运营报告、知识库检索和智能问答。

## 数据与知识库说明

- 样例数据文件：[`data/samples/energy_records.csv`](data/samples/energy_records.csv)
- 数据字典：[`data/dictionaries/energy_records_dictionary.csv`](data/dictionaries/energy_records_dictionary.csv)
- 知识库入口：[`knowledge_base/README.md`](knowledge_base/README.md)

当前样例数据已经扩展为 `2,976` 条记录，覆盖 `2026-03-01 00:00` 至 `2026-06-01 21:00`，可以用于联调、演示和最终答辩。数据检查说明和外部来源简表已经放在 `data/processed/`。若要重新生成同规模数据，可运行：

```powershell
python .\scripts\generate_sample_dataset.py
```

## 文档入口

- 需求分析：[`docs/01-requirements.md`](docs/01-requirements.md)
- 技术方案：[`docs/02-technical-solution.md`](docs/02-technical-solution.md)
- 用户手册：[`docs/03-user-manual.md`](docs/03-user-manual.md)
- 数据字典模板：[`docs/04-data-dictionary-template.md`](docs/04-data-dictionary-template.md)
- 演示脚本：[`docs/05-demo-script.md`](docs/05-demo-script.md)
- API 契约：[`docs/06-api-contract.md`](docs/06-api-contract.md)
- 协作规则：[`docs/07-collaboration-rules.md`](docs/07-collaboration-rules.md)
- 集成清单：[`docs/08-integration-checklist.md`](docs/08-integration-checklist.md)
- 测试计划：[`docs/09-testing-plan.md`](docs/09-testing-plan.md)
- 数据源调研：[`docs/10-data-source-research.md`](docs/10-data-source-research.md)
- 第一次整合总结：[`docs/11-first-integration-summary.md`](docs/11-first-integration-summary.md)
- 第二次整合总结：[`docs/12-second-integration-summary.md`](docs/12-second-integration-summary.md)
- 外部大模型接入说明：[`docs/13-llm-provider-integration.md`](docs/13-llm-provider-integration.md)
- 期末项目最终提交清单：[`docs/14-final-submission-checklist.md`](docs/14-final-submission-checklist.md)
- 项目验收报告：[`docs/15-project-acceptance-report.md`](docs/15-project-acceptance-report.md)
- MCP 集成说明：[`docs/16-mcp-integration.md`](docs/16-mcp-integration.md)
- SRS 软件需求规格说明书：[`docs/17-SRS-software-requirements-specification.md`](docs/17-SRS-software-requirements-specification.md)
- SDS 软件设计说明书：[`docs/18-SDS-software-design-description.md`](docs/18-SDS-software-design-description.md)
- SEE 软件经济分析与评价：[`docs/19-SEE-software-economic-evaluation.md`](docs/19-SEE-software-economic-evaluation.md)
- SEM 软件工程管理说明：[`docs/20-SEM-software-engineering-management.md`](docs/20-SEM-software-engineering-management.md)
- 最终提交与打包说明：[`docs/21-final-submission-guide.md`](docs/21-final-submission-guide.md)

## 开发说明

当前项目已经完成主要多人协作阶段，后续修改应优先保持以下内容稳定：

- 数据字段与数据字典
- `docs/06-api-contract.md` 中的接口路径和主要字段
- 前端主导航、筛选条件和页面分区
- `.env.example` 只保留占位配置，真实 API Key 只放本地 `.env`

## 常用脚本

- 启动后端：[`scripts/start-backend.ps1`](scripts/start-backend.ps1)
- 启动前端：[`scripts/start-frontend.ps1`](scripts/start-frontend.ps1)
- 启动 MCP Server：[`scripts/start-mcp.ps1`](scripts/start-mcp.ps1)
- 自检项目：[`scripts/check-project.ps1`](scripts/check-project.ps1)
- 生成样例数据：[`scripts/generate_sample_dataset.py`](scripts/generate_sample_dataset.py)

## 当前阶段

1. 已完成两轮任务整合后的核心系统打磨，前后端、数据、知识库、外部大模型配置和演示文档已进入可演示状态。
2. 统计分析不再只停留在建筑级查询，已补充异常解释、楼层设备台账、设备运行监测、异常工单和运营优化建议。
3. 总览页已加入可拖拽旋转的三维楼宇风险态势图，点击楼层可联动统计分析筛选。
4. 已新增“工单中心”和“决策报告”导航，用于展示后端持久化工单闭环、能耗预测、节能模拟和一键运营日报。
5. 已补齐 SRS、SDS、SEE、SEM、验收报告和最终提交说明。系统侧进入封版状态，剩余主要是 PPT、演示视频和 Canvas 打包提交。
