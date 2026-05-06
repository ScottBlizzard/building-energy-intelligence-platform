# 用户使用手册

## 1. 环境准备

- Python 3.8 及以上
- Node.js 18 及以上
- npm 或 pnpm

## 2. 启动后端

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --app-dir backend
```

## 3. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

## 4. 推荐演示路径

1. 打开首页，说明系统面向建筑能源管理与运维支持场景。
2. 展示 KPI 卡片、模块分区和数据元信息，说明当前样例数据范围。
3. 进入“数据浏览”页，按建筑和时间范围筛选记录，并演示 CSV 导出。
4. 进入“统计分析”页，展示日度趋势、建筑对比、COP 排名和异常原因分布。
5. 进入“智能问答”页，演示数据来源、异常诊断、设备维护和建筑类型差异相关问题。
6. 最后说明当前问答已接入第一轮知识素材，后续可继续升级为 RAG + 大模型链路。

## 5. 常见问题

### 页面显示为静态骨架

说明前端未连上后端。先确认后端是否启动，并检查前端环境变量 `VITE_API_BASE_URL` 是否指向 `http://127.0.0.1:8000/api/v1` 或代理路径 `/api/v1`。

### 接口提示找不到数据文件

确认样例数据是否存在于 `data/samples/energy_records.csv`，并检查 `.env` 中的 `DATA_FILE` 配置。

### 数据导出失败

先确认后端已启动，并确认 `GET /api/v1/export/csv` 接口可访问。若当前筛选条件没有命中任何记录，导出接口会返回空结果或 404。

### 问答回答较简单或不够像大模型

这是当前第一轮整合阶段的正常表现。现在问答已经能引用知识库与数据说明，但仍属于规则化回答；完整版本需继续补充知识切分、向量检索和 LLM 接入。
