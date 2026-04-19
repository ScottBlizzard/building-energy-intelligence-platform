# 基于大模型的建筑能源智能管理与运维优化系统

这是课程项目的统一代码仓库。当前版本已经不仅是空骨架，而是一个适合 4 人并行协作的原型起点：包含前后端基础实现、可联调页面、样例数据、知识库占位、接口契约、协作规则和测试占位。

## 项目目标

- 构建不少于 1000 条记录的建筑能耗数据集，并附数据字典。
- 提供按建筑、时间、参数的多条件查询能力。
- 完成时段汇总、COP 计算、异常分析等核心统计分析。
- 提供趋势、对比类可视化展示。
- 集成知识库与大模型问答，支持典型运维场景答复。
- 最终形成可演示系统和完整交付材料。

## 当前仓库包含什么

- `backend/`：FastAPI 后端，已包含总览、元数据、查询、分析和问答占位接口。
- `frontend/`：Vue 3 + Vite 前端，已升级为多模块演示工作台。
- `data/`：样例能耗数据、数据字典、原始/处理后数据目录和生成脚本。
- `knowledge_base/`：运维手册、术语表、常见问题占位内容。
- `docs/`：课程交付文档、接口契约、协作规则、集成清单和测试计划。
- `scripts/`：启动脚本、检查脚本和样例数据生成脚本。

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
- 可视化：后续接入 ECharts
- 智能问答：先提供规则化占位接口，后续接入 LLM / RAG
- 数据格式：CSV 为主，后续可扩展数据库

## 快速启动

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

### 3. 常用访问地址

- 前端开发页：`http://127.0.0.1:5173`
- 后端文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/api/v1/health`

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
- `GET /api/v1/analytics/anomaly-reasons`
- `POST /api/v1/assistant/query`

## 数据与知识库说明

- 样例数据文件：[`data/samples/energy_records.csv`](data/samples/energy_records.csv)
- 数据字典：[`data/dictionaries/energy_records_dictionary.csv`](data/dictionaries/energy_records_dictionary.csv)
- 知识库入口：[`knowledge_base/README.md`](knowledge_base/README.md)

当前样例数据已经可以用于联调和演示。若要重新生成更大规模的数据，可运行：

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

## 协作建议

在第一次任务分发前，先默认以下内容已经冻结：

- 数据字段与数据字典
- `docs/06-api-contract.md` 中的接口路径和主要字段
- 前端主导航和页面分区
- 目录归属和两轮集成流程

这样做的目的不是“官僚”，而是把多人开发的冲突留在最前面解决。

## 常用脚本

- 启动后端：[`scripts/start-backend.ps1`](scripts/start-backend.ps1)
- 启动前端：[`scripts/start-frontend.ps1`](scripts/start-frontend.ps1)
- 自检项目：[`scripts/check-project.ps1`](scripts/check-project.ps1)
- 生成样例数据：[`scripts/generate_sample_dataset.py`](scripts/generate_sample_dataset.py)

## 建议下一步

1. 用当前仓库直接开始第一次任务分发，保证每个人只改自己负责区域。
2. 先完成数据、后端、前端、AI 四部分的基础版功能。
3. 做第一次整合，统一字段、接口和页面流程。
4. 再进入第二轮功能补齐和联调。
5. 最后统一测试、演示脚本和提交材料。
