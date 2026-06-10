# API 契约文档

本文档用于定义前后端 REST API 与 MCP 协议接口契约，减少集成阶段返工，并作为最终提交材料中的接口说明。

## 基础约定

- API 前缀：`/api/v1`
- 返回格式：优先使用对象包裹，列表类接口统一放在 `items`
- 时间格式：`YYYY-MM-DD HH:mm:ss`
- 数值单位：电耗 `kWh`，水耗 `m3`，温度 `℃`

## 已冻结接口

本项目对外提供两类接口：

- REST API：服务 Web 前端、浏览器演示和常规 HTTP 调试。
- MCP Server：服务支持 MCP 的 AI 客户端或智能体，满足原项目“基于 MCP 协议开发数据接入与查询接口”的要求。

### `GET /api/v1/health`

用途：检查后端是否正常运行

### `GET /api/v1/overview`

用途：获取首页总览指标

返回核心字段：

- `total_records`
- `building_count`
- `average_cop`
- `abnormal_record_count`
- `time_range`
- `totals`

### `GET /api/v1/dataset-meta`

用途：获取字段列表、建筑选项和数据时间范围

### `GET /api/v1/buildings`

用途：返回可筛选的建筑列表

返回字段：

- `building_id`
- `building_name`
- `building_type`

### `GET /api/v1/records`

用途：查询原始记录

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`
- `limit`

返回核心字段：

- `count`
- `total_filtered_count`
- `items`

`items` 中除原始能耗字段外，会额外返回用于前端展示和演示下钻的派生字段：

- `floor_label`
- `zone_name`
- `equipment_type`
- `source_equipment_id`

### `GET /api/v1/analytics/time-summary`

用途：返回时段汇总统计

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`
- `freq`

### `GET /api/v1/analytics/building-comparison`

用途：返回建筑间对比结果

查询参数：

- `start_time`
- `end_time`

### `GET /api/v1/analytics/cop-ranking`

用途：返回建筑 COP 排名

查询参数：

- `start_time`
- `end_time`

### `GET /api/v1/analytics/anomalies`

用途：返回异常明细

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

### `GET /api/v1/analytics/anomaly-explanations/{record_id}`

用途：返回单条异常的解释信息，包括触发规则、同建筑基线、同楼层均值、动态阈值、可能原因和处置建议。

返回核心字段：

- `record_id`
- `building_name`
- `floor_label`
- `equipment_id`
- `severity`
- `anomaly_reason`
- `conclusion`
- `metrics`
- `triggered_rules`
- `possible_cause`
- `recommended_action`

### `GET /api/v1/analytics/anomaly-reasons`

用途：返回异常原因计数

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

### `GET /api/v1/analytics/floor-summary`

用途：返回建筑楼层与区域维度的能耗、COP、异常数量和运维判断。

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

返回核心字段：

- `building_id`
- `building_name`
- `floor_label`
- `zone_name`
- `record_count`
- `equipment_count`
- `electricity_kwh`
- `water_m3`
- `average_cop`
- `anomaly_count`
- `anomaly_rate`
- `operation_focus`

说明：当前样例数据没有真实 BIM 楼层字段，楼层、区域和设备类型由设备编号、建筑类型和运行规则派生，适合作为课程演示级的逐层分析。

### `GET /api/v1/analytics/floor-registry`

用途：返回楼层 / 设备台账，用于展示楼层用途、面积、负责人、设备构成、健康评分和风险等级。

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

返回核心字段：

- `building_id`
- `building_name`
- `floor_label`
- `floor_area_m2`
- `usage`
- `owner`
- `main_equipment_types`
- `health_score`
- `risk_level`
- `operation_policy`

### `GET /api/v1/analytics/equipment-summary`

用途：返回设备级运行监测结果，用于判断维护优先级。

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

返回核心字段：

- `building_name`
- `equipment_id`
- `equipment_type`
- `floor_label`
- `zone_name`
- `latest_status`
- `latest_seen_at`
- `average_cop`
- `anomaly_count`
- `priority`
- `maintenance_hint`

### `GET /api/v1/analytics/work-orders`

用途：把异常记录转换为可执行的巡检工单和处置建议。

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

返回核心字段：

- `work_order_id`
- `priority`
- `status`
- `building_name`
- `floor_label`
- `zone_name`
- `equipment_id`
- `equipment_type`
- `timestamp`
- `anomaly_reason`
- `possible_cause`
- `recommended_action`
- `owner_role`

### `GET /api/v1/analytics/optimization-recommendations`

用途：根据 COP、夜间负荷、异常数量和空调电耗占比生成运营优化建议。

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

返回核心字段：

- `recommendation_id`
- `building_id`
- `building_name`
- `category`
- `priority`
- `finding`
- `action`
- `expected_impact`

### `GET /api/v1/analytics/operation-report`

用途：生成运营日报，汇总总览、重点风险、最近异常、工单状态、未来 7 天电耗估算和建议动作。

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

返回核心字段：

- `title`
- `generated_at`
- `overview`
- `risk`
- `latest_anomaly`
- `work_order`
- `work_order_closure`
- `forecast`
- `recommendation`
- `action_items`

### `POST /api/v1/auth/login`

用途：演示账号登录，返回用户信息和演示 token。

请求体核心字段：

- `username`
- `password`

演示账号：

- `admin / admin123`
- `worker_ahu / worker123`
- `worker_chiller / worker123`

### `GET /api/v1/auth/me`

用途：根据 `Authorization: Bearer <token>` 返回当前用户。

### `GET /api/v1/auth/users`

用途：返回可分配工单的演示用户列表。

### `GET /api/v1/admin/dashboard`

用途：返回管理员业务闭环看板，包括开放工单、待复核、高优先级未闭环、已关闭工单、待复核队列和下一步动作。

### `GET /api/v1/admin/worker-dashboard/{user_id}`

用途：返回某个工人的个人工单看板，包括待接单、处理中、待复核和已关闭数量。

### `GET /api/v1/anomaly-events/{record_id}`

用途：返回异常事件上下文，聚合异常解释、设备画像、关联工单和下一步动作。

### `GET /api/v1/work-orders`

用途：读取后端持久化保存的人工工单列表。

查询参数：

- `assignee_id`
- `status`
- `role`

### `POST /api/v1/work-orders`

用途：把前端选择的异常记录创建为持久化工单，并写入 `data/runtime/work_orders.json`。若带有 `assignee_id`，默认进入 `assigned` 已派单状态。

### `PATCH /api/v1/work-orders/{work_order_id}`

用途：兼容旧版页面，更新工单状态、负责人或处理备注。

### `PATCH /api/v1/work-orders/{work_order_id}/assign`

用途：管理员派单或重新派单。

请求体核心字段：

- `assignee_id`
- `operator_id`
- `note`

### `PATCH /api/v1/work-orders/{work_order_id}/accept`

用途：工人接单，状态进入 `in_progress`。

### `PATCH /api/v1/work-orders/{work_order_id}/submit`

用途：工人提交处理结果，状态进入 `pending_review`。

请求体核心字段：

- `operator_id`
- `actual_cause`
- `resolution_note`
- `recovery_confirmed`
- `parts_used`
- `safety_note`

### `PATCH /api/v1/work-orders/{work_order_id}/review`

用途：管理员复核。`approved=true` 时关闭工单，`approved=false` 时驳回重办。

### `PATCH /api/v1/work-orders/{work_order_id}/ignore`

用途：管理员判断异常无需现场处理，将工单置为 `ignored`。

### `GET /api/v1/export/csv`

用途：导出当前筛选范围内的原始记录 CSV

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

返回形式：

- `text/csv` 文件流
- 文件名会根据建筑和时间筛选条件自动生成

### `POST /api/v1/assistant/query`

用途：智能问答入口

说明：

- 默认使用本地规则问答和知识库引用
- 若本地 `.env` 中开启 `LLM_ENABLED=true`，后端会尝试调用外部大模型增强回答
- 外部模型调用失败时自动回退本地问答，响应结构不变

请求体：

```json
{
  "question": "当前有哪些异常记录？",
  "provider": "nvidia",
  "model": "meta/llama-3.3-70b-instruct"
}
```

其中 `provider` 和 `model` 为可选字段。若不传，则使用 `.env` 中的默认模型；若外部模型未启用或调用失败，则回退本地规则问答。

响应体：

```json
{
  "answer": "字符串回答",
  "citations": [
    {
      "title": "来源标题",
      "path": "来源路径"
    }
  ],
  "follow_up": ["可继续提问的问题"],
  "llm_used": true,
  "llm_provider": "nvidia",
  "llm_model": "meta/llama-3.3-70b-instruct"
}
```

### `GET /api/v1/assistant/providers`

用途：返回前端可展示的外部模型选项

安全说明：

- 只返回供应商、模型名、展示标签和是否已配置
- 不返回任何 API Key 或敏感配置

响应体：

```json
{
  "enabled": true,
  "default_provider": "nvidia",
  "default_model": "meta/llama-3.3-70b-instruct",
  "options": [
    {
      "provider": "nvidia",
      "model": "meta/llama-3.3-70b-instruct",
      "label": "NVIDIA · meta/llama-3.3-70b-instruct",
      "configured": true
    }
  ]
}
```

## MCP 协议契约

### 启动方式

默认 stdio transport：

```powershell
.\scripts\start-mcp.ps1
```

Streamable HTTP transport：

```powershell
.\scripts\start-mcp.ps1 -Transport streamable-http -HostAddress 127.0.0.1 -Port 8765
```

HTTP MCP 路径：

```text
http://127.0.0.1:8765/mcp
```

### MCP Tools

| Tool | 用途 | 主要参数 |
| --- | --- | --- |
| `get_dataset_meta` | 获取字段、建筑、记录数和时间范围 | 无 |
| `list_buildings` | 获取建筑清单 | 无 |
| `query_energy_records` | 查询能耗记录 | `building_id`、`floor_label`、`start_time`、`end_time`、`limit` |
| `get_energy_overview` | 获取总览 KPI、平均 COP 和异常数 | `building_id`、`start_time`、`end_time` |
| `get_time_summary` | 获取时段汇总 | `building_id`、`floor_label`、`start_time`、`end_time`、`freq`、`limit` |
| `get_building_comparison` | 获取建筑对比 | `start_time`、`end_time` |
| `get_cop_ranking` | 获取 COP 排名 | `start_time`、`end_time` |
| `get_anomalies` | 获取异常记录 | `building_id`、`floor_label`、`start_time`、`end_time`、`limit` |
| `get_anomaly_reasons` | 获取异常原因统计 | `building_id`、`floor_label`、`start_time`、`end_time` |
| `explain_anomaly` | 解释单条异常 | `record_id` |
| `get_floor_summary` | 获取楼层/区域汇总 | `building_id`、`floor_label`、`start_time`、`end_time` |
| `get_equipment_summary` | 获取设备运行摘要 | `building_id`、`floor_label`、`start_time`、`end_time`、`limit` |
| `suggest_anomaly_work_orders` | 生成建议工单，不写入持久化文件 | `building_id`、`floor_label`、`start_time`、`end_time`、`limit` |
| `get_optimization_recommendations` | 获取节能优化建议 | `building_id`、`floor_label`、`start_time`、`end_time` |
| `get_operation_report` | 生成运营日报摘要 | `building_id`、`floor_label`、`start_time`、`end_time` |
| `get_admin_business_dashboard` | 获取管理员业务闭环看板 | 无 |
| `list_persistent_work_orders` | 查询持久化工单和状态统计 | `assignee_id`、`status`、`role`、`limit` |
| `get_worker_business_dashboard` | 获取工人个人工单看板 | `user_id` |
| `get_work_order_detail` | 获取单个工单详情和时间线 | `work_order_id` |
| `get_anomaly_event_context` | 获取异常事件、设备上下文和关联工单 | `record_id` |
| `search_energy_knowledge` | 检索本地知识库 | `query`、`top_k` |
| `ask_energy_assistant` | 智能运维问答 | `question`、`use_external_llm` |

### MCP Resources

| Resource URI | 用途 |
| --- | --- |
| `energy://dataset/meta` | 数据集元信息 |
| `energy://buildings` | 建筑清单 |
| `energy://operation/report` | 当前全量运营报告 |
| `energy://knowledge/readme` | 知识库入口文档 |

说明：MCP Tools 与 REST API 复用后端服务层，返回口径与 Web 页面一致。`stdio` 模式下 PowerShell 终端保持等待是正常现象，stdout 用于 MCP JSON-RPC 协议消息；手动停止可按 `Ctrl+C`。

## 协作规则

- 前端开发人员不得自行修改返回字段名。
- 后端开发人员不得在未同步的情况下修改接口路径。
- 若必须修改 REST 或 MCP 契约，应先更新本文档，再统一通知项目组。
