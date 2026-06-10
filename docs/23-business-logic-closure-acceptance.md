# 业务逻辑闭环实现与验收记录

## 1. 实现目标

本次迭代将系统从“建筑能源监测看板”扩展为“建筑能源异常运维闭环系统”。核心链路为：

```text
异常发现 -> 管理员派单 -> 工人接单处理 -> 工人提交复核 -> 管理员复核关闭 -> 运营日报归档
```

系统保留两个登录角色：

| 角色 | 演示账号 | 职责 |
| --- | --- | --- |
| 管理员 | `admin / admin123` | 查看全局看板、生成工单、派单、复核、关闭或忽略 |
| 工人 | `worker_ahu / worker123`、`worker_chiller / worker123` | 查看本人任务、接单、填写现场原因和处理结果、提交复核 |

## 2. 后端实现

### 2.1 认证与角色

- 新增 `auth_service.py`，内置演示用户、口令校验、演示 token 生成和 token 解析。
- 新增 `/api/v1/auth/login`、`/api/v1/auth/me`、`/api/v1/auth/users`。
- 管理员和工人拥有不同页面入口和接口过滤范围。

### 2.2 工单状态机

工单状态从旧版三态升级为：

| 状态 | 中文 | 触发方 |
| --- | --- | --- |
| `pending_confirm` | 待确认 | 系统或管理员 |
| `assigned` | 已派单 | 管理员 |
| `in_progress` | 处理中 | 工人 |
| `pending_review` | 待复核 | 工人 |
| `rejected` | 已驳回 | 管理员 |
| `closed` | 已关闭 | 管理员 |
| `ignored` | 已忽略 | 管理员 |

每个工单保留 `timeline`，记录创建、派单、接单、提交、复核、驳回或忽略等动作。

### 2.3 新增业务接口

- `GET /api/v1/admin/dashboard`
- `GET /api/v1/admin/worker-dashboard/{user_id}`
- `GET /api/v1/anomaly-events/{record_id}`
- `PATCH /api/v1/work-orders/{work_order_id}/assign`
- `PATCH /api/v1/work-orders/{work_order_id}/accept`
- `PATCH /api/v1/work-orders/{work_order_id}/submit`
- `PATCH /api/v1/work-orders/{work_order_id}/review`
- `PATCH /api/v1/work-orders/{work_order_id}/ignore`

## 3. 前端实现

### 3.1 登录与角色入口

- 未登录时显示登录工作台。
- 管理员登录后显示总览、数据浏览、统计分析、工单中心、决策报告和智能问答。
- 工人登录后显示“我的工单”和智能问答。

### 3.2 管理员闭环工作台

- 总览页新增管理员业务闭环看板。
- 工单中心支持从异常记录生成并派单。
- 管理员可以调整工人、忽略告警、复核通过关闭、复核驳回。
- 工单卡片展示状态、优先级、现场原因、处理结果和生命周期时间线。

### 3.3 工人工作台

- 工人只看到分配给自己的工单。
- 支持接单并进入处理中。
- 支持填写现场实际原因、处理结果、更换部件、安全备注和恢复确认。
- 提交后进入管理员待复核队列。

## 4. MCP 补充

MCP Server 已补充只读业务闭环工具：

- `get_admin_business_dashboard`
- `list_persistent_work_orders`
- `get_worker_business_dashboard`
- `get_work_order_detail`
- `get_anomaly_event_context`

这些工具用于在 MCP 客户端中验证：管理员队列、工人工单过滤、工单状态机、异常事件上下文和运营日报之间的关系。

## 5. 演示建议

1. 使用 `admin / admin123` 登录，展示管理员业务闭环看板。
2. 在“工单中心”选择一条异常，分配给 `worker_ahu` 或 `worker_chiller`。
3. 退出后使用对应工人账号登录，在“我的工单”接单。
4. 填写现场实际原因和处理结果，提交管理员复核。
5. 切回管理员账号，在工单中心复核通过并关闭。
6. 打开“决策报告”，展示已关闭工单被纳入运营日报。
7. 通过 MCP 工具查询管理员看板、工人工单和工单详情，说明系统同时具备 REST 与 MCP 双接口能力。

## 6. 验收结果

已执行验证：

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
npm run build
```

当前结果：

- 后端测试：`86 passed, 1 warning`
- 前端构建：通过

剩余建议：

- 录制演示前清理或保留一组合适的样例工单，使演示链路更流畅。
- 如需展示外部 LLM，可在 `.env` 中配置真实 API Key 后使用智能问答页或 MCP 的 `ask_energy_assistant(use_external_llm=True)`。

## 7. 完整验收清单

本节面向二次验收人员或其他 AI agent。建议按顺序执行，每一项均应记录“通过 / 不通过 / 备注”。若需要保持仓库干净，验收前可备份或清空 `data/runtime/work_orders.json`；该目录已在 `.gitignore` 中，不会提交。

### 7.1 环境与启动验收

| 编号 | 检查项 | 操作 | 期望结果 |
| --- | --- | --- | --- |
| ENV-01 | Python 环境可用 | `.\.venv\Scripts\python.exe --version` | 输出当前虚拟环境 Python 版本 |
| ENV-02 | 后端依赖可导入 | `.\.venv\Scripts\python.exe -m pytest backend\tests -q` | 测试通过，当前基线为 `86 passed, 1 warning` |
| ENV-03 | 前端依赖可构建 | `cd frontend; npm run build` | Vite build 成功 |
| ENV-04 | 后端可启动 | `.\scripts\start-backend.ps1` | `http://127.0.0.1:8000/api/v1/health` 返回 `status=ok` |
| ENV-05 | 前端可启动 | `.\scripts\start-frontend.ps1` | `http://127.0.0.1:5173` 可打开登录页 |
| ENV-06 | MCP 可启动 | `.\scripts\start-mcp.ps1` | stdio 模式下终端保持等待；`Ctrl+C` 停止时不视为异常 |

### 7.2 后端认证与角色验收

| 编号 | 检查项 | 操作 | 期望结果 |
| --- | --- | --- | --- |
| AUTH-01 | 管理员登录 | `POST /api/v1/auth/login`，body 为 `{"username":"admin","password":"admin123"}` | 返回 `access_token`，`user.role=admin` |
| AUTH-02 | 工人登录 | 使用 `worker_ahu / worker123` 登录 | 返回 `user.role=worker`，`specialty=AHU` |
| AUTH-03 | 制冷工人登录 | 使用 `worker_chiller / worker123` 登录 | 返回 `user.role=worker`，`specialty=CH` |
| AUTH-04 | 密码错误 | 使用错误密码登录 | 返回 HTTP `401` |
| AUTH-05 | 当前用户解析 | `GET /api/v1/auth/me`，Header 带 `Authorization: Bearer <token>` | 返回 token 对应用户 |
| AUTH-06 | 用户列表 | `GET /api/v1/auth/users` | 返回管理员和两个工人账号，不返回密码 |

PowerShell 示例：

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/auth/login `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"admin123"}'
$login.user
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/auth/me `
  -Headers @{ Authorization = "Bearer $($login.access_token)" }
```

### 7.3 后端工单状态机验收

| 编号 | 检查项 | 操作 | 期望结果 |
| --- | --- | --- | --- |
| WO-01 | 查询工单列表 | `GET /api/v1/work-orders` | 返回 `items` 数组 |
| WO-02 | 从异常创建派单工单 | `POST /api/v1/work-orders`，body 中包含 `source_record_id`、异常字段、`assignee_id=worker_ahu` | 返回 `status=assigned`，`status_label=已派单` |
| WO-03 | 时间线创建事件 | 检查 WO-02 返回值 | `timeline` 至少包含 `action=create` |
| WO-04 | 工人接单 | `PATCH /api/v1/work-orders/{id}/accept`，`operator_id=worker_ahu` | 返回 `status=in_progress`，时间线新增 `accept` |
| WO-05 | 非本人不能接单 | 用 `operator_id=worker_chiller` 接 `worker_ahu` 工单 | 返回 HTTP `400` 或状态不变 |
| WO-06 | 工人提交处理结果 | `PATCH /submit`，填写 `actual_cause`、`resolution_note`、`recovery_confirmed=true` | 返回 `status=pending_review`，时间线新增 `submit` |
| WO-07 | 管理员复核通过 | `PATCH /review`，`approved=true` | 返回 `status=closed`，包含 `closed_at`，时间线新增 `review_approve` |
| WO-08 | 管理员复核驳回 | 对另一条待复核工单执行 `approved=false` | 返回 `status=rejected`，工人可再次接单处理 |
| WO-09 | 管理员忽略 | 对待确认或已派单工单执行 `/ignore` | 返回 `status=ignored` |
| WO-10 | 按工人过滤 | `GET /api/v1/work-orders?assignee_id=worker_ahu&role=worker` | 只返回 `assignee_id=worker_ahu` 的工单 |
| WO-11 | 按状态过滤 | `GET /api/v1/work-orders?status=closed` | 只返回关闭工单 |
| WO-12 | 兼容旧状态 | 若存在旧状态 `处理中/已完成/已忽略` | 服务层能归一为 `in_progress/closed/ignored` |

建议创建工单 body 可参考前端实际字段或先调用：

```powershell
$anomaly = (Invoke-RestMethod http://127.0.0.1:8000/api/v1/analytics/anomalies).items[0]
```

再将异常字段映射为工单字段。

### 7.4 后端业务聚合接口验收

| 编号 | 检查项 | 操作 | 期望结果 |
| --- | --- | --- | --- |
| BIZ-01 | 管理员看板 | `GET /api/v1/admin/dashboard` | 返回 `item.kpis`、`work_order_metrics`、`next_actions` |
| BIZ-02 | 工人看板 | `GET /api/v1/admin/worker-dashboard/worker_ahu` | 返回 `kpis`、`items`、`next_actions`，items 均属于该工人 |
| BIZ-03 | 异常事件上下文 | `GET /api/v1/anomaly-events/{record_id}` | 返回 `anomaly`、`explanation`、`equipment`、`linked_work_orders`、`next_action` |
| BIZ-04 | 运营日报闭环口径 | `GET /api/v1/analytics/operation-report` | 返回 `work_order` 和 `work_order_closure` |
| BIZ-05 | 关闭工单计入归档 | 完成一条工单关闭后重新请求 operation-report | `work_order_closure` 中已关闭数量增加或与当前关闭工单数一致 |

### 7.5 前端登录与角色界面验收

| 编号 | 检查项 | 操作 | 期望结果 |
| --- | --- | --- | --- |
| UI-01 | 未登录页面 | 打开 `http://127.0.0.1:5173` | 显示“建筑能源业务闭环工作台”和三个演示账号按钮 |
| UI-02 | 管理员登录 | 使用 `admin / admin123` | 进入系统，用户条显示“管理员 / 能源运营管理员” |
| UI-03 | 管理员导航 | 观察导航栏 | 显示“总览、数据浏览、统计分析、工单中心、决策报告、智能问答” |
| UI-04 | 工人登录 | 使用 `worker_ahu / worker123` | 用户条显示“工人 / 空调机组巡检员” |
| UI-05 | 工人导航隔离 | 观察导航栏 | 只显示“我的工单、智能问答”，不显示数据浏览、统计分析、决策报告 |
| UI-06 | 退出登录 | 点击“退出登录” | 回到登录页 |
| UI-07 | 错误登录提示 | 输入错误密码 | 页面显示账号或密码错误提示 |

### 7.6 前端管理员业务闭环验收

| 编号 | 检查项 | 操作 | 期望结果 |
| --- | --- | --- | --- |
| ADM-01 | 管理员业务看板 | 管理员进入“总览” | 显示开放工单、待复核、高优先级未闭环、闭环率 |
| ADM-02 | 下一步动作 | 查看管理员业务看板 | 显示复核、派单、归档相关动作 |
| ADM-03 | 工单中心加载 | 点击“工单中心” | 显示异常选择、工人选择和状态统计 |
| ADM-04 | 异常选项 | 打开“选择异常”下拉框 | 可看到建筑、楼层、设备、异常原因、时间 |
| ADM-05 | 工人选项 | 打开“分配工人”下拉框 | 包含“空调机组巡检员 · AHU”和“制冷机房值班员 · CH” |
| ADM-06 | 生成并派单 | 选择异常和工人后点击“生成并派单” | 新工单卡片出现，状态为“已派单” |
| ADM-07 | 工单卡片信息 | 查看新工单卡片 | 显示工单号、建筑、楼层、设备、优先级、状态、工人、异常原因、建议 |
| ADM-08 | 派单时间线 | 查看时间线 | 包含 `create` 和管理员名称 |
| ADM-09 | 调整分配 | 修改卡片中的工人并点“确认派单” | 工单仍为已派单，工人字段更新 |
| ADM-10 | 忽略告警 | 对待确认或已派单工单点“忽略告警” | 状态变为“已忽略” |
| ADM-11 | 待复核显示 | 工人提交复核后管理员回到工单中心 | 卡片状态为“待复核”，显示现场原因和处理结果 |
| ADM-12 | 复核通过 | 填复核意见并点“复核通过并关闭” | 状态变为“已关闭”，时间线出现 `review_approve` |
| ADM-13 | 复核驳回 | 对待复核工单点“驳回重办” | 状态变为“已驳回”，工人可再次接单 |

### 7.7 前端工人工作台验收

| 编号 | 检查项 | 操作 | 期望结果 |
| --- | --- | --- | --- |
| WRK-01 | 工人只看本人任务 | 使用 `worker_ahu` 登录“我的工单” | 只显示分配给 `worker_ahu` 的工单 |
| WRK-02 | 工人 KPI | 查看工作台顶部 | 显示待接单、处理中、待复核、已关闭 |
| WRK-03 | 接单 | 对“已派单”工单点“接单并开始处理” | 状态变为“处理中”，出现处理表单 |
| WRK-04 | 处理表单字段 | 查看处理中工单 | 有现场实际原因、处理结果、更换部件、安全备注、恢复确认 |
| WRK-05 | 必填校验 | 不填原因或结果直接提交 | 页面提示需要填写实际原因和处理结果 |
| WRK-06 | 提交复核 | 填写原因和结果后提交 | 状态变为“待复核”，显示等待管理员复核提示 |
| WRK-07 | 工人时间线 | 查看时间线 | 包含 `accept` 和 `submit` |
| WRK-08 | 关闭后只读提示 | 管理员关闭后工人刷新页面 | 工单显示“已关闭”，不再出现提交按钮 |

### 7.8 决策报告与归档验收

| 编号 | 检查项 | 操作 | 期望结果 |
| --- | --- | --- | --- |
| RPT-01 | 决策报告页面 | 管理员进入“决策报告” | 显示能耗预测、节能模拟器、自动运营报告 |
| RPT-02 | 一键生成日报 | 点击“一键生成今日运营日报” | 生成时间刷新 |
| RPT-03 | 未完成工单口径 | 有未关闭工单时查看日报 | `work_order` 描述未完成工单数量 |
| RPT-04 | 关闭工单归档 | 完成一条工单关闭后查看日报 | 显示“当前已关闭 X 个工单，可作为日报归档案例” |
| RPT-05 | 节能模拟器 | 调整温度、夜间关闭小时、电价 | 节电量、节约金额和降幅联动变化 |

### 7.9 原有能力回归验收

| 编号 | 检查项 | 操作 | 期望结果 |
| --- | --- | --- | --- |
| REG-01 | 总览 KPI | 管理员总览页 | 数据记录、建筑数量、平均 COP、异常记录显示正常 |
| REG-02 | 三维楼宇态势 | 总览页拖拽 3D 场景 | 场景非空、楼层可见，点击楼层可联动到统计分析 |
| REG-03 | 数据浏览 | 进入“数据浏览”，筛选建筑/楼层/时间 | 表格随筛选刷新 |
| REG-04 | CSV 导出 | 在数据浏览点击导出 | 下载 CSV 文件 |
| REG-05 | 统计分析 | 进入“统计分析” | 趋势、异常明细、楼层台账、设备监测等模块显示 |
| REG-06 | 异常解释 | 在异常明细点击解释 | 显示触发规则、可能原因、处置建议 |
| REG-07 | 优化建议 | 查看统计分析和决策报告建议 | 有高优先级节能或异常治理建议 |
| REG-08 | 智能问答 | 进入“智能问答”提问“当前有哪些异常记录？” | 返回本地规则或外部 LLM 增强回答，并带引用/追问 |
| REG-09 | 外部 LLM 降级 | 未配置外部模型时提问 | 页面不崩溃，回退本地回答 |

### 7.10 MCP 验收清单

默认 stdio 模式可通过 MCP 客户端验收；若使用 HTTP transport：

```powershell
.\scripts\start-mcp.ps1 -Transport streamable-http -HostAddress 127.0.0.1 -Port 8765
```

| 编号 | Tool | 参数示例 | 期望结果 |
| --- | --- | --- | --- |
| MCP-01 | `get_dataset_meta` | 无 | 返回字段、建筑、记录数和时间范围 |
| MCP-02 | `list_buildings` | 无 | 返回建筑清单 |
| MCP-03 | `query_energy_records` | `building_id=BLD-C, limit=5` | 返回图书信息楼记录 |
| MCP-04 | `get_time_summary` | `freq=D` | 返回日维度能耗趋势 |
| MCP-05 | `get_cop_ranking` | 无 | 返回建筑 COP 排名 |
| MCP-06 | `get_anomalies` | `limit=5` | 返回异常记录 |
| MCP-07 | `explain_anomaly` | 使用 MCP-06 中的 `record_id` | 返回异常解释 |
| MCP-08 | `get_admin_business_dashboard` | 无 | 返回管理员 KPI、待复核队列和下一步动作 |
| MCP-09 | `list_persistent_work_orders` | `limit=10` | 返回持久化工单和状态统计 |
| MCP-10 | `get_worker_business_dashboard` | `user_id=worker_ahu` | 返回该工人的工单 |
| MCP-11 | `get_work_order_detail` | 使用现有 `work_order_id` | 返回单个工单和时间线 |
| MCP-12 | `get_anomaly_event_context` | 使用现有 `record_id` | 返回异常、解释、设备、关联工单 |
| MCP-13 | `get_operation_report` | 无 | 返回运营日报，含工单闭环口径 |
| MCP-14 | `search_energy_knowledge` | `query=AHU 异常怎么处理` | 返回知识库引用 |
| MCP-15 | `ask_energy_assistant` | `question=哪些设备需要优先维护` | 返回回答、引用和追问 |

### 7.11 文档与提交物验收

| 编号 | 检查项 | 文件 | 期望结果 |
| --- | --- | --- | --- |
| DOC-01 | README 更新 | `README.md` | 包含演示账号、新 REST 接口和 MCP 说明 |
| DOC-02 | 用户手册更新 | `docs/03-user-manual.md` | 推荐演示路径为角色闭环路径 |
| DOC-03 | 演示脚本更新 | `docs/05-demo-script.md` | 第四部分包含管理员、工人、复核、日报归档 |
| DOC-04 | API 契约更新 | `docs/06-api-contract.md` | 包含 auth/admin/anomaly-events/work-order action 接口 |
| DOC-05 | MCP 文档更新 | `docs/16-mcp-integration.md` | 包含业务闭环 MCP Tools |
| DOC-06 | 迭代计划存在 | `docs/22-business-logic-iteration-plan.md` | 描述完整开发计划 |
| DOC-07 | 验收记录存在 | `docs/23-business-logic-closure-acceptance.md` | 包含实现记录和本完整验收清单 |

### 7.12 自动化测试与构建验收

| 编号 | 检查项 | 命令 | 期望结果 |
| --- | --- | --- | --- |
| TST-01 | 后端全量测试 | `.\.venv\Scripts\python.exe -m pytest backend\tests -q` | `86 passed, 1 warning` 或更多测试通过 |
| TST-02 | 认证测试 | pytest 中 `test_auth_endpoint.py` | 登录、me、用户列表、错误密码通过 |
| TST-03 | 工单状态机测试 | pytest 中 `test_work_orders_endpoint.py` | 派单、接单、提交、复核关闭、非本人接单拦截通过 |
| TST-04 | 业务聚合测试 | pytest 中 `test_business_closure_endpoints.py` | admin dashboard、worker dashboard、anomaly event 通过 |
| TST-05 | MCP 业务工具测试 | pytest 中 `test_mcp_business_tools.py` | MCP 业务工具返回结构通过 |
| TST-06 | 前端构建 | `cd frontend; npm run build` | Vite build 成功 |

### 7.13 数据与 Git 清洁验收

| 编号 | 检查项 | 操作 | 期望结果 |
| --- | --- | --- | --- |
| GIT-01 | 运行时工单不提交 | `git status --short --untracked-files=all` | 不出现 `data/runtime/work_orders.json` |
| GIT-02 | 私人实验目录不提交 | 检查 `.gitignore` | `实验二` 私人差异文件和 `实验三/` 已忽略 |
| GIT-03 | 环境变量不提交 | `git status --short` | 不出现 `.env` |
| GIT-04 | 前端构建产物不提交 | `git status --short` | 不出现 `frontend/dist` |
| GIT-05 | 只包含预期源码与文档 | 查看 `git diff --name-only` | 变更集中在 backend、frontend、docs、README |

### 7.14 负向与边界验收

| 编号 | 检查项 | 操作 | 期望结果 |
| --- | --- | --- | --- |
| NEG-01 | 未登录访问前端 | 清空浏览器 localStorage 后刷新 | 回到登录页 |
| NEG-02 | 工人无法看到管理员导航 | 工人登录 | 不显示“数据浏览、统计分析、工单中心、决策报告” |
| NEG-03 | 空工单列表 | 清空 `data/runtime/work_orders.json` 后刷新 | 页面显示空状态，不报错 |
| NEG-04 | 重复异常派单 | 对同一 `source_record_id` 重复创建开放工单 | 服务层更新开放工单或避免重复开放工单 |
| NEG-05 | 已关闭工单不可重复接单 | 对 closed 工单调用 `/accept` | 返回错误或状态不变 |
| NEG-06 | 待复核前不可关闭 | 对非 pending_review 工单调用 `/review approved=true` | 返回错误或状态不变 |
| NEG-07 | 后端不可用 | 停止后端后刷新前端 | 页面显示接口不可用提示，不白屏 |
| NEG-08 | MCP Ctrl+C | stdio 模式按 `Ctrl+C` 停止 | 可出现 KeyboardInterrupt/停止提示，不视为启动失败 |

## 8. 推荐验收顺序

若时间有限，建议按以下最短路径验收：

1. 执行 `TST-01` 和 `TST-06`，确认自动化基线。
2. 执行 `AUTH-01` 至 `AUTH-04`，确认登录角色。
3. 执行 `UI-01` 至 `UI-06`，确认前端角色隔离。
4. 执行 `ADM-03` 至 `ADM-12` 与 `WRK-01` 至 `WRK-07`，跑通完整业务闭环。
5. 执行 `RPT-04`，确认关闭工单进入日报归档。
6. 执行 `MCP-08` 至 `MCP-13`，确认 MCP 已覆盖新增业务链路。
7. 执行 `GIT-01` 至 `GIT-05`，确认不会提交运行时或私人文件。
