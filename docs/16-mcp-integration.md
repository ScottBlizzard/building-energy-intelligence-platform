# MCP 集成说明

## 1. 目标

本项目已经补充独立的 Model Context Protocol Server，用于把建筑能耗数据接入、查询统计、异常诊断、运营报告和智能问答能力暴露给支持 MCP 的客户端。

MCP 入口文件：

```text
backend/app/mcp_server.py
```

启动脚本：

```text
scripts/start-mcp.ps1
```

## 2. 启动方式

默认使用 stdio transport，适合 Cursor、Claude Desktop、支持 MCP 的本地 Agent 或课程验收时的工具调用演示：

```powershell
.\scripts\start-mcp.ps1
```

也可以启动 Streamable HTTP transport，便于用网络方式接入：

```powershell
.\scripts\start-mcp.ps1 -Transport streamable-http -HostAddress 127.0.0.1 -Port 8765
```

对应 MCP HTTP 路径为：

```text
http://127.0.0.1:8765/mcp
```

## 3. 已暴露的 MCP Tools

| Tool | 说明 |
| --- | --- |
| `get_dataset_meta` | 获取字段、建筑选项、记录数和时间范围。 |
| `list_buildings` | 获取当前数据集覆盖的建筑清单。 |
| `query_energy_records` | 按建筑、楼层、时间范围和条数查询能耗记录。 |
| `get_energy_overview` | 获取总记录数、建筑数、平均 COP、异常数量和能耗汇总。 |
| `get_time_summary` | 按小时、日、周、月汇总电耗、水耗、暖通能耗、冷量和 COP。 |
| `get_building_comparison` | 按建筑对比能耗、水耗、暖通能耗、冷量和 COP。 |
| `get_cop_ranking` | 输出建筑 COP 排名。 |
| `get_anomalies` | 查询异常记录。 |
| `get_anomaly_reasons` | 按异常原因统计异常数量。 |
| `explain_anomaly` | 对单条异常记录生成规则解释、可能原因和处置建议。 |
| `get_floor_summary` | 输出楼层/区域维度能耗、COP、异常率和关注建议。 |
| `get_equipment_summary` | 输出设备状态、维护优先级和维护建议。 |
| `suggest_anomaly_work_orders` | 根据异常记录生成建议工单，不写入持久化文件。 |
| `get_optimization_recommendations` | 输出节能优化建议。 |
| `get_operation_report` | 生成当前范围的运营日报摘要。 |
| `search_energy_knowledge` | 检索本地知识库并返回引用。 |
| `ask_energy_assistant` | 使用本地规则、知识库引用和可选外部 LLM 回答运维问题。 |

## 4. 已暴露的 MCP Resources

| Resource URI | 说明 |
| --- | --- |
| `energy://dataset/meta` | 数据集元信息。 |
| `energy://buildings` | 建筑清单。 |
| `energy://operation/report` | 当前全量运营报告。 |
| `energy://knowledge/readme` | 知识库入口文档。 |

## 5. 验收示例

典型验收问题可以通过 MCP 客户端调用以下工具完成：

1. 调用 `get_dataset_meta`，确认数据规模、字段和时间范围。
2. 调用 `query_energy_records`，按 `building_id=BLD-C` 查询图书信息楼记录。
3. 调用 `get_time_summary`，生成日维度能耗趋势。
4. 调用 `get_cop_ranking`，确认 COP 统计能力。
5. 调用 `get_anomalies` 和 `explain_anomaly`，验证异常诊断。
6. 调用 `get_operation_report`，生成运营日报。
7. 调用 `ask_energy_assistant`，验证智慧运维问答。

## 6. 与原项目描述的对应关系

原描述要求“基于 MCP 协议开发数据接入与查询接口”。当前实现已经将原 FastAPI 服务层封装为独立 MCP Server，MCP Tools 覆盖数据接入、统一查询、统计分析、异常诊断、知识库检索和智能问答，MCP Resources 提供数据集和运营报告上下文。因此，该项已经从“REST 等价实现”补充为“REST + MCP 双接口实现”。
