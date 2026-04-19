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

1. 打开首页，说明系统面向建筑能源管理场景。
2. 展示 KPI 卡片和模块分区，介绍当前骨架。
3. 打开后端接口文档，演示概览、记录和分析接口。
4. 演示问答接口的占位回答。
5. 说明后续如何接入完整数据集和大模型。

## 5. 常见问题

### 页面显示为静态骨架

说明前端未连上后端。先确认后端是否启动，接口地址是否为 `http://127.0.0.1:8000/api/v1`。

### 接口提示找不到数据文件

确认样例数据是否存在于 `data/samples/energy_records.csv`，并检查 `.env` 中的 `DATA_FILE` 配置。

### 问答回答较简单

这是当前骨架阶段的正常表现。完整版本需补充知识切分、检索和 LLM 接入。

