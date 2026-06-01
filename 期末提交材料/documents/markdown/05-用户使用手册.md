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

## 4. 启动 MCP Server

默认 stdio transport，适合支持 MCP 的本地客户端：

```powershell
.\scripts\start-mcp.ps1
```

如果希望看到类似后端服务的启动日志，可使用 HTTP transport：

```powershell
.\scripts\start-mcp.ps1 -Transport streamable-http -HostAddress 127.0.0.1 -Port 8765
```

stdio 模式下 PowerShell 终端保持等待是正常现象，表示 MCP Server 正在等待客户端发送协议消息。手动停止可按 `Ctrl+C`。

## 5. 推荐演示路径

1. 打开首页，说明系统面向建筑能源管理与运维支持场景。
2. 展示 KPI 卡片、模块分区和数据元信息，说明当前样例数据范围。
3. 进入“数据浏览”页，按建筑和时间范围筛选记录，并演示 CSV 导出。
4. 在“总览”页展示三维楼宇风险态势图，拖拽旋转视图，并点击风险楼层跳转到统计分析页。
5. 进入“数据浏览”页，演示建筑、楼层、时间和记录数筛选，并演示 CSV 导出。
6. 进入“统计分析”页，展示异常明细并点击“解释”，说明异常触发规则、基线对比、可能原因和处置建议。
7. 继续展示楼层 / 设备台账、趋势、异常原因、设备监测、优化建议、建筑对比和 COP 排名。
8. 进入“工单中心”页，从异常记录中选择一个问题，分配管理员，生成“处理中”工单，再点击完成工单；工单状态和备注会保存到后端 JSON 文件，刷新后仍可保留。
9. 进入“决策报告”页，演示未来 7 天能耗预测、节能策略模拟和“一键生成今日运营日报”。
10. 进入“智能问答”页，演示楼层异常、设备优先维护、异常处置建议、节能优化建议和建筑类型差异相关问题。
11. 如需展示 MCP 能力，说明 MCP Server 已把数据查询、统计分析、异常诊断、运营报告和智能问答封装为可被 AI 客户端调用的 Tools 与 Resources。

## 6. 常见问题

### 页面显示为静态骨架

说明前端未连上后端。请确认后端是否启动，并检查前端环境变量 `VITE_API_BASE_URL` 是否指向 `http://127.0.0.1:8000/api/v1` 或代理路径 `/api/v1`。

### 接口提示找不到数据文件

确认样例数据是否存在于 `data/samples/energy_records.csv`，并检查 `.env` 中的 `DATA_FILE` 配置。

### 数据导出失败

请确认后端已启动，并确认 `GET /api/v1/export/csv` 接口可访问。若当前筛选条件没有命中任何记录，导出接口会返回空结果或 404。

### 问答回答较简单或没有使用外部大模型

请确认后端 `.env` 中 `LLM_ENABLED=true`，并且至少配置了一个供应商 API Key。若外部模型调用失败，系统会自动回退到本地规则问答，保证演示流程不中断。

### 启动 MCP 后 PowerShell 没有菜单或明显输出

这是 stdio transport 的正常表现。MCP Server 不是人工命令菜单，而是给 MCP 客户端调用的协议服务。若要验证它是否可用，可运行后端测试中的 MCP 测试，或使用 `-Transport streamable-http` 查看 HTTP 服务启动日志。
