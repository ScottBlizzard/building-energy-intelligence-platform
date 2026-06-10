# 可信问答、经济决策、对照仿真与角色权限迭代计划

## 1. 文档定位

本文档面向后续开发者、验收人员和可接力执行的 AI agent，用于规划下一轮业务增强迭代。

当前系统已经具备建筑能耗监测、异常分析、角色登录、工单派发、工人处理、管理员复核、时间机器、预算管理、ROI 改造分析、决策报告、MCP 与外部 LLM 问答能力。真实浏览器验收表明，核心链路已经可以跑通：

```text
异常发现 -> 管理员派单 -> 工人处置 -> 管理员复核 -> 能耗改善估算 -> 时间机器干预未来 -> 决策报告归档 -> 智能问答辅助说明
```

本轮迭代不再追求新增更多松散页面，而是把现有功能进一步串成可信、可解释、可演示的管理系统。重点解决四个问题：

1. 外部 LLM 能回答，但可能编造工单号或设备号。
2. 工单已有风险和经济字段，但尚未充分驱动资源调度、预算和改造决策。
3. 时间机器能体现修复后未来恢复，但缺少“不处理 / 立即处理 / 延迟处理”的对照冲击力。
4. 管理员和工人角色已有区分，但权限边界、工作台信息和可操作动作还可以继续收紧。

## 2. 总体目标

本轮目标是把系统从“可演示闭环”升级为“可信决策闭环”：

```text
异常发现
  -> 经济损失评估
  -> 优先级排序与资源约束派单
  -> 工人标准化处置
  -> 管理员复核关闭
  -> 预算预测修正
  -> ROI 改造候选沉淀
  -> 时间机器对照实验
  -> 决策报告与可信问答解释
```

验收时应能讲清楚三句话：

- 系统不是只展示异常，而是能判断哪个异常更值得先处理。
- 系统不是只调用大模型，而是能约束大模型必须基于真实工单和设备回答。
- 系统不是只走流程，而是能展示不同处置时机对未来能耗、费用和碳排的影响。

## 3. 迭代范围与优先级

| 优先级 | 主题 | 建议阶段 | 价值 |
| --- | --- | --- | --- |
| P0 | LLM 问答强接地 | 第 1 阶段 | 修复最明显的不可信点，避免答辩时外部模型编造工单 |
| P0 | 角色权限继续深化 | 第 1 阶段 | 保证管理员和工人看到的内容、能做的动作符合业务身份 |
| P1 | 异常处置经济决策闭环 | 第 2 阶段 | 让工单字段真正驱动派单排序、资源分配、预算和 ROI |
| P1 | 时间机器对照实验 | 第 3 阶段 | 提升演示冲击力，说明“早处理为什么有价值” |

建议按 P0 -> P1 顺序实现。若时间紧，至少完成 P0 两项，因为它们直接影响演示可信度和角色业务感。

## 4. 主题一：LLM 问答强接地

### 4.1 背景问题

当前 `/api/v1/assistant/query` 会先生成本地规则回答和知识库引用，再尝试调用外部模型增强回答。真实验收中，外部模型链路可用，但在询问刚关闭工单时出现了事实错误：

- 真实工单：`WO-MANUAL-1781097639887`
- 真实设备：`AHU-A-5F-06`
- 外部模型回答中却出现了其他工单编号和设备编号。

这说明模型虽然能生成自然语言，但缺少对运行时工单数据的强约束。

### 4.2 目标行为

当用户问题涉及工单、派单、复核、关闭、处理结果、节能闭环、设备维护、最近案例时，系统应：

1. 自动识别问题属于“工单相关问题”。
2. 从后端实时读取最新工单列表和必要详情。
3. 构造结构化上下文，包含真实 `work_order_id`、`equipment_id`、状态、时间线、能耗前后对比、经济影响。
4. 将该上下文传给外部 LLM。
5. 模型返回后执行事实校验。
6. 如果回答中出现不存在的工单号、设备号、建筑名或明显状态错误，自动降级为本地规则回答。
7. 前端明确显示回答依据标签：
   - `基于实时工单数据`
   - `基于知识库`
   - `外部模型增强`
   - `已触发事实校验回退`

### 4.3 后端设计

建议新增服务：

```text
backend/app/services/grounding_service.py
```

职责：

- 识别问题意图。
- 提取问题中可能出现的工单号、设备号、建筑名、状态词。
- 从 `work_order_store` 读取实时工单数据。
- 构造 LLM grounding context。
- 校验外部模型回答是否引用了不存在的业务实体。

建议核心函数：

| 函数 | 说明 |
| --- | --- |
| `classify_assistant_question(question: str) -> dict` | 判断问题是否涉及工单、预算、ROI、时间机器、知识库 |
| `build_work_order_grounding_context(question: str) -> dict` | 返回相关工单摘要、最近关闭工单、待处理工单、实体白名单 |
| `format_grounding_context_for_llm(context: dict) -> str` | 将结构化上下文压缩成可传给 LLM 的文本 |
| `validate_grounded_answer(answer: str, context: dict) -> dict` | 检查模型回答中的工单号、设备号、建筑名是否合法 |
| `build_grounded_fallback_reply(question: str, context: dict, local_reply: dict) -> dict` | 当模型不可信时，生成基于真实数据的本地回答 |

建议在 `backend/app/services/llm_client.py` 中扩展 `_build_grounded_messages`：

- system prompt 明确禁止编造工单号、设备号和不存在的金额。
- user prompt 附加 `REAL_TIME_WORK_ORDER_CONTEXT`。
- 要求模型如果上下文没有某项信息，就说“当前数据未提供”，不要猜测。

建议在 `backend/app/api/routes/assistant.py` 中扩展返回字段。

### 4.4 数据结构建议

`AssistantReply` 建议新增字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `grounding_used` | bool | 是否使用实时业务数据接地 |
| `grounding_sources` | list[string] | 例如 `work_orders`、`knowledge_base`、`budget` |
| `grounding_status` | string | `none`、`grounded`、`validated`、`fallback_after_validation` |
| `validation_warnings` | list[string] | 模型回答中被发现的问题 |
| `referenced_entities` | object | 回答涉及的工单号、设备号、建筑名 |

示例：

```json
{
  "grounding_used": true,
  "grounding_sources": ["work_orders", "knowledge_base"],
  "grounding_status": "fallback_after_validation",
  "validation_warnings": [
    "外部模型回答引用了不存在的工单号 WO-2026043009-R01924，已回退本地可信回答。"
  ],
  "referenced_entities": {
    "work_order_ids": ["WO-MANUAL-1781097639887"],
    "equipment_ids": ["AHU-A-5F-06"]
  }
}
```

### 4.5 前端设计

修改 `frontend/src/components/AssistantPanel.vue`：

- 在回答标题旁显示来源标签。
- 当 `grounding_status === "validated"` 时显示 `基于实时工单数据`。
- 当 `grounding_status === "fallback_after_validation"` 时显示醒目的但不吓人的提示：
  - `外部模型回答未通过事实校验，已切换为本地可信回答。`
- 回答下方展示“本次引用的实时实体”：
  - 工单号
  - 设备号
  - 建筑
  - 状态
- 如果回答是纯知识库问题，仍显示知识库引用，不强行展示工单信息。

### 4.6 推荐实现任务

| 编号 | 任务 | 文件 |
| --- | --- | --- |
| LLM-01 | 新增问题意图识别和实体抽取 | `backend/app/services/grounding_service.py` |
| LLM-02 | 接入实时工单上下文 | `backend/app/services/grounding_service.py`、`work_order_store.py` |
| LLM-03 | 扩展 LLM prompt，强制基于真实上下文回答 | `backend/app/services/llm_client.py` |
| LLM-04 | 增加外部回答事实校验 | `backend/app/services/grounding_service.py` |
| LLM-05 | 扩展 Assistant schema 和 API 返回 | `backend/app/schemas/assistant.py`、`backend/app/api/routes/assistant.py` |
| LLM-06 | 前端显示接地来源和校验状态 | `frontend/src/components/AssistantPanel.vue` |
| LLM-07 | 增加后端测试 | `backend/tests/test_grounded_assistant.py` |

### 4.7 验收标准

| 编号 | 验收项 | 步骤 | 通过标准 |
| --- | --- | --- | --- |
| GQA-01 | 实时工单接地 | 提问“刚关闭的综合教学楼A工单是什么？” | 回答中的工单号、设备号与真实数据一致 |
| GQA-02 | 模型编造回退 | mock 外部模型返回不存在工单号 | API 返回 `grounding_status=fallback_after_validation` |
| GQA-03 | UI 来源标签 | 前端提问工单问题 | 页面显示 `基于实时工单数据` 和 `外部模型增强` 或回退提示 |
| GQA-04 | 知识库问题不误判 | 提问“COP 是什么？” | 可走知识库回答，不强制引用工单 |
| GQA-05 | 外部模型不可用 | 关闭或移除外部模型配置 | 本地规则回答正常，页面不崩溃 |

## 5. 主题二：异常处置的经济决策闭环

### 5.1 背景问题

当前工单已经有：

- `risk_score`
- `wasted_kwh`
- `wasted_cost_yuan`
- `carbon_kg`
- `estimated_saving_yuan`
- `sla_hours`

但这些字段主要用于展示，还没有充分参与“应该先处理谁”“资源不足时怎么派单”“关闭后如何影响预算和 ROI”的决策。

### 5.2 目标行为

系统应能回答并展示：

- 当前最应该优先处理的 3 个工单是什么？
- 如果今天只有 3 个工人，应该派给哪些异常？
- 某个工单延迟处理会多损失多少电费和碳排？
- 某设备多次异常后是否应进入改造候选？
- 关闭工单后，预算执行预测是否得到改善？

### 5.3 后端设计

建议新增服务：

```text
backend/app/services/decision_service.py
```

核心输出：

| 函数 | 说明 |
| --- | --- |
| `score_work_order_decision(order) -> dict` | 计算综合调度分 |
| `rank_open_work_orders(limit: int = 10) -> list` | 返回未闭环工单优先级队列 |
| `recommend_dispatch_plan(worker_capacity: int = 3) -> dict` | 在工人数量约束下给出派单建议 |
| `summarize_budget_impact_from_closures() -> dict` | 根据已关闭工单估算预算改善 |
| `find_roi_candidates_from_repeated_anomalies() -> list` | 找出多次异常设备，推入 ROI 候选 |

建议综合调度分公式：

```text
decision_score =
  risk_score * 0.35
  + normalized(wasted_cost_yuan) * 0.25
  + normalized(carbon_kg) * 0.15
  + sla_urgency_score * 0.15
  + repeated_equipment_bonus * 0.10
```

其中：

- `sla_urgency_score`：SLA 越短、创建时间越久，分越高。
- `repeated_equipment_bonus`：同一设备近期异常越多，分越高。
- 所有分数保持可解释，接口返回每个分项，便于前端展示“为什么排第一”。

### 5.4 API 建议

新增路由：

```text
GET /api/v1/decision/work-order-priorities
GET /api/v1/decision/dispatch-plan?worker_capacity=3
GET /api/v1/decision/budget-impact
GET /api/v1/decision/roi-candidates
```

返回示例：

```json
{
  "worker_capacity": 3,
  "summary": "建议优先处理 3 个高经济损失或 SLA 紧急工单，预计可回收 286.4 元，减少碳排 173.2 kg。",
  "items": [
    {
      "rank": 1,
      "work_order_id": "WO-MANUAL-...",
      "equipment_id": "AHU-A-5F-06",
      "decision_score": 82.4,
      "reason": "风险分较高、预计损失较大、SLA 剩余时间较短。",
      "estimated_saving_yuan": 64.4,
      "carbon_kg": 68.9,
      "recommended_worker_id": "worker_ahu"
    }
  ]
}
```

### 5.5 前端设计

建议在管理员“总览”或“工单中心”增加一个紧凑决策面板：

```text
今日派单建议
工人容量：[-] 3 [+]
预计可回收：xxx 元
预计减少碳排：xxx kg
推荐优先处理：
1. 综合教学楼A 5F AHU-A-5F-06
2. ...
```

在工单卡片上新增：

- `调度分`
- `排序原因`
- `SLA 剩余`
- `经济损失`
- `碳排影响`

在 ROI 页面新增“来自工单闭环的改造候选”区域：

- 设备 ID
- 异常次数
- 已处理次数
- 累计损失
- 推荐改造类型
- 一键带入 ROI 计算器

在预算页面新增“闭环改善口径”：

- 已关闭工单预计节省电量
- 已关闭工单预计节省费用
- 当前月末预测执行率修正值

### 5.6 推荐实现任务

| 编号 | 任务 | 文件 |
| --- | --- | --- |
| DEC-01 | 新增调度评分服务 | `backend/app/services/decision_service.py` |
| DEC-02 | 新增决策 API | `backend/app/api/routes/decision.py`、`backend/app/api/router.py` |
| DEC-03 | 工单列表按综合调度分排序或提供排序选项 | `work_order_store.py`、`DashboardView.vue` |
| DEC-04 | 总览页新增今日派单建议面板 | `frontend/src/views/DashboardView.vue` |
| DEC-05 | 预算页展示已关闭工单预计改善 | `budget_service.py`、`BudgetPanel.vue` |
| DEC-06 | ROI 页展示多次异常设备候选池 | `roi_service.py`、`ROIPanel.vue` |
| DEC-07 | 决策报告纳入派单建议和经济影响摘要 | `analysis_service.py` |
| DEC-08 | 增加后端测试 | `backend/tests/test_decision_service.py` |

### 5.7 验收标准

| 编号 | 验收项 | 步骤 | 通过标准 |
| --- | --- | --- | --- |
| EDC-01 | 工单优先级排序 | 创建多个不同风险/损失/SLA 工单 | 接口按 `decision_score` 降序返回 |
| EDC-02 | 资源约束派单 | 请求 `worker_capacity=3` | 返回 3 个推荐工单和预计收益 |
| EDC-03 | 前端调度解释 | 管理员进入工单中心 | 工单卡显示排序原因，不只是分数 |
| EDC-04 | 预算改善 | 关闭带 `estimated_saving_yuan` 的工单 | 预算页或决策接口体现预计改善 |
| EDC-05 | ROI 候选 | 同设备多次异常 | ROI 页面出现该设备候选项 |

## 6. 主题三：时间机器对照实验

### 6.1 背景问题

当前时间机器已经支持：

- 启动仿真日期。
- 隐藏未来数据。
- 推进日期。
- 工单关闭后把设备从关闭日期起登记为修复干预。
- 修复设备在未来数据中恢复正常。

但演示时还缺少对照组。老师可能看到“修好了”，但未必直观看到“早修和晚修差多少钱”。

### 6.2 目标行为

系统应能展示同一异常在三种场景下的未来 7 天结果：

1. 不处理：异常持续，损失继续累积。
2. 立即处理：从当前日期开始恢复正常。
3. 延迟 3 天处理：前三天继续损失，之后恢复。

对比指标：

- 总电耗 kWh
- 估算浪费电量 kWh
- 经济损失 yuan
- 碳排 kg
- 异常记录数

输出结论：

```text
如果今天处理 AHU-A-5F-06，相比延迟 3 天，未来 7 天预计少浪费 128.4 kWh，节约 105.3 元，减少碳排 73.2 kg。
```

### 6.3 后端设计

建议扩展 `backend/app/services/simulation_service.py`，或新增：

```text
backend/app/services/scenario_service.py
```

核心函数：

| 函数 | 说明 |
| --- | --- |
| `simulate_counterfactual(equipment_id, start_date, horizon_days=7)` | 返回三种策略的指标 |
| `build_no_action_scenario(...)` | 不登记干预，保持异常持续 |
| `build_immediate_action_scenario(...)` | 从当前日期登记干预 |
| `build_delayed_action_scenario(delay_days=3)` | 从当前日期 + 3 天登记干预 |
| `compare_scenarios(...)` | 计算立即处理相对其他策略的节省 |

注意：对照实验应尽量纯函数化，不直接改写 `sim_state.json`。只有真实工单复核关闭才应登记正式 intervention。

### 6.4 API 建议

新增接口：

```text
GET /api/v1/sim/counterfactual?equipment_id=AHU-A-5F-06&horizon_days=7&delay_days=3
```

返回示例：

```json
{
  "equipment_id": "AHU-A-5F-06",
  "start_date": "2026-05-02",
  "horizon_days": 7,
  "scenarios": [
    {
      "key": "no_action",
      "label": "不处理",
      "total_kwh": 2190.4,
      "wasted_kwh": 212.7,
      "wasted_cost_yuan": 174.4,
      "carbon_kg": 121.2,
      "anomaly_count": 7
    },
    {
      "key": "immediate_action",
      "label": "立即处理",
      "total_kwh": 1970.2,
      "wasted_kwh": 0,
      "wasted_cost_yuan": 0,
      "carbon_kg": 0,
      "anomaly_count": 0
    },
    {
      "key": "delayed_3_days",
      "label": "延迟 3 天处理",
      "total_kwh": 2072.6,
      "wasted_kwh": 102.4,
      "wasted_cost_yuan": 84.0,
      "carbon_kg": 58.3,
      "anomaly_count": 3
    }
  ],
  "decision_sentence": "立即处理相比延迟 3 天，未来 7 天预计少浪费 102.4 kWh，节约 84.0 元，减少碳排 58.3 kg。"
}
```

### 6.5 前端设计

建议在工单中心新增“处置时机对照”模块：

- 当选中异常或打开工单卡片时显示。
- 使用三列或折线图比较“不处理 / 立即处理 / 延迟 3 天”。
- 显示一句自动生成的管理结论。
- 对已关闭工单，也可显示“本次提前处理的估算价值”。

如果不想引入图表库，可以用简单表格和横向条形进度条实现，降低开发风险。

### 6.6 推荐实现任务

| 编号 | 任务 | 文件 |
| --- | --- | --- |
| SIM-01 | 新增纯函数化对照仿真服务 | `backend/app/services/scenario_service.py` |
| SIM-02 | 新增 `/sim/counterfactual` API | `backend/app/api/routes/simulation.py` |
| SIM-03 | 工单中心对接对照实验接口 | `frontend/src/lib/api.js`、`DashboardView.vue` |
| SIM-04 | 决策报告加入处置时机结论 | `analysis_service.py` |
| SIM-05 | MCP 暴露对照实验工具 | `backend/app/mcp_server.py` |
| SIM-06 | 增加后端测试 | `backend/tests/test_counterfactual_simulation.py` |

### 6.7 验收标准

| 编号 | 验收项 | 步骤 | 通过标准 |
| --- | --- | --- | --- |
| CFS-01 | 不改写真实状态 | 调用对照接口前后查询 `/sim/state` | `interventions` 不因对照实验变化 |
| CFS-02 | 三场景完整 | 请求指定设备对照 | 返回不处理、立即处理、延迟处理三组结果 |
| CFS-03 | 立即处理收益更优 | 对有异常设备请求对照 | 立即处理的损失不高于延迟处理和不处理 |
| CFS-04 | 前端展示结论 | 选中异常工单 | 页面显示未来 7 天节省 kWh、元、kg |
| CFS-05 | 报告归档 | 生成决策报告 | 报告包含处置时机价值句 |

## 7. 主题四：角色权限继续深化

### 7.1 背景问题

当前系统已经有管理员和工人账号：

- `admin / admin123`
- `worker_ahu / worker123`
- `worker_chiller / worker123`

前端也已经根据角色隐藏部分菜单。但为了让系统更像真实业务系统，还需要继续强化“看什么、能做什么、不能做什么”。

### 7.2 权限目标

管理员：

- 能看全局异常、预算、ROI、报告、时间机器、所有工单。
- 能创建工单、派单、调整分配、忽略告警。
- 能复核、驳回、关闭。
- 能查看派单建议、预算影响、ROI 候选。
- 不能直接填写工人现场处理表单。

工人：

- 只能看分配给自己的工单。
- 只能接单、提交处理、补充材料。
- 能查看与自己工种相关的标准作业建议和相似历史案例。
- 不能看预算、ROI、决策报告、全局异常列表。
- 不能复核关闭工单，不能调整派单。

### 7.3 后端权限设计

建议不要只依赖前端隐藏按钮。后端接口也应检查角色：

| 操作 | 管理员 | 工人 |
| --- | --- | --- |
| 查看全部工单 | 允许 | 禁止 |
| 查看本人工单 | 允许 | 允许，仅本人 |
| 创建工单 | 允许 | 禁止 |
| 分派工单 | 允许 | 禁止 |
| 接单 | 禁止或仅测试允许 | 允许，仅本人 |
| 提交处置 | 禁止或仅测试允许 | 允许，仅本人 |
| 复核关闭 | 允许 | 禁止 |
| 查看预算/ROI/决策报告 | 允许 | 禁止 |
| 智能问答 | 允许 | 允许，但上下文范围不同 |

建议新增一个轻量权限服务：

```text
backend/app/services/permission_service.py
```

核心函数：

| 函数 | 说明 |
| --- | --- |
| `require_admin(user)` | 非管理员抛出权限异常 |
| `require_worker_owner(user, order)` | 工人只能操作自己的工单 |
| `filter_orders_for_user(user, orders)` | 根据身份过滤工单列表 |
| `get_allowed_tabs(user)` | 返回前端可展示菜单 |

如果当前系统没有完整 token 体系，可以先基于现有请求中的 `user_id` / `operator_id` 做轻量校验，保持课程项目复杂度可控。

### 7.4 工人工作台增强

工人端不应只是少几个菜单，而应更像工作台：

- 今日待接单
- 处理中
- 被驳回需补充
- 已提交待复核
- 本工种标准作业建议
- 相似历史案例

相似案例可以基于：

- 相同 `equipment_type`
- 相同 `anomaly_reason`
- 已关闭工单

返回内容：

- 曾经的现场原因
- 处理结果
- 预计改善
- 附件说明

### 7.5 推荐实现任务

| 编号 | 任务 | 文件 |
| --- | --- | --- |
| ROL-01 | 新增权限服务 | `backend/app/services/permission_service.py` |
| ROL-02 | 工单接口增加角色校验 | `backend/app/api/routes/work_orders.py` |
| ROL-03 | 预算、ROI、报告接口增加管理员限制 | 对应 API routes |
| ROL-04 | 工人工作台增加标准作业建议 | `DashboardView.vue`、`assistant_service.py` 或新服务 |
| ROL-05 | 工人工作台增加相似历史案例 | `work_order_store.py`、`DashboardView.vue` |
| ROL-06 | 前端菜单由后端权限返回驱动 | `auth_service.py`、`DashboardView.vue` |
| ROL-07 | 增加权限测试 | `backend/tests/test_role_permissions.py` |

### 7.6 验收标准

| 编号 | 验收项 | 步骤 | 通过标准 |
| --- | --- | --- | --- |
| RBA-01 | 工人看不到管理菜单 | `worker_ahu` 登录 | 不显示预算、ROI、决策报告、工单中心全局派单入口 |
| RBA-02 | 工人不能操作他人工单 | 用 `worker_ahu` 请求 `worker_chiller` 工单提交 | 返回 403 或业务错误 |
| RBA-03 | 工人不能复核 | 工人请求复核关闭接口 | 返回 403 或业务错误 |
| RBA-04 | 管理员不能误填工人处理 | 管理员页面不展示现场处理提交表单 |
| RBA-05 | 工人有作业指导 | 工人打开待处理 AHU 工单 | 显示 AHU 标准检查项和相似案例 |

## 8. 推荐开发阶段

### 第 1 阶段：可信问答与权限收紧

目标：先把最影响演示可信度的问题修掉。

任务：

- LLM-01 至 LLM-07。
- ROL-01 至 ROL-03。
- ROL-07。

验收：

- 外部模型不能再编造工单号或设备号。
- 工人无法访问预算、ROI 和全局报告。
- 工人无法复核或处理非本人任务。

### 第 2 阶段：经济决策闭环

目标：让工单风险、费用、碳排、SLA 变成调度和管理决策依据。

任务：

- DEC-01 至 DEC-08。
- ROL-04 至 ROL-05。

验收：

- 管理员能看到今日派单建议。
- 工单卡能解释为什么某个任务排在前面。
- ROI 页面能看到多次异常设备候选。
- 决策报告能汇总预计节省和预算改善。

### 第 3 阶段：时间机器对照实验

目标：让演示时可以直观看到早处理、晚处理、不处理的差异。

任务：

- SIM-01 至 SIM-06。

验收：

- 选中异常后显示三场景对比。
- 对照实验不污染真实仿真状态。
- 决策报告能生成“提前处理节省多少”的管理结论。

### 第 4 阶段：综合演示打磨

目标：把上述能力串成 8 分钟答辩脚本。

任务：

- 更新 `docs/05-demo-script.md`。
- 更新 `docs/03-user-manual.md`。
- 更新 `docs/06-api-contract.md`。
- 更新 `docs/23-business-logic-closure-acceptance.md` 或新增验收清单。
- 增加 Playwright E2E 脚本，固定跑通管理员与工人闭环。

验收：

- 8 分钟内可完成完整演示。
- 不依赖临场解释弥补页面缺口。
- 所有关键数字能在页面、接口或测试中追溯。

## 9. 测试计划

### 9.1 后端测试

建议新增测试文件：

| 文件 | 覆盖 |
| --- | --- |
| `backend/tests/test_grounded_assistant.py` | 接地上下文、模型回答校验、回退 |
| `backend/tests/test_decision_service.py` | 调度分、容量约束、预算影响、ROI 候选 |
| `backend/tests/test_counterfactual_simulation.py` | 三场景对照、不污染真实状态 |
| `backend/tests/test_role_permissions.py` | 管理员/工人权限边界 |

### 9.2 前端构建

每阶段至少执行：

```powershell
cd frontend
npm run build
```

### 9.3 真实浏览器验收

建议保留以下人工 E2E 路径：

1. 管理员登录。
2. 启动时间机器。
3. 选中异常并查看对照实验。
4. 查看今日派单建议。
5. 生成并派单。
6. 工人登录并只看到本人任务。
7. 工人查看标准作业建议和相似案例。
8. 工人提交处理。
9. 管理员复核关闭。
10. 决策报告出现关闭案例、经济改善、对照实验结论。
11. 智能问答提问“刚关闭的工单是什么”，返回真实工单号和设备号。

## 10. 风险与控制

| 风险 | 影响 | 控制 |
| --- | --- | --- |
| 外部 LLM 仍可能胡编 | 演示可信度下降 | 强制实体白名单校验，失败回退 |
| 接地上下文过长 | 外部模型慢或超 token | 只传最近关闭、未闭环和问题相关工单 |
| 权限改动破坏演示 | 操作流程中断 | 先后端测试，再真实浏览器走完整链路 |
| 经济评分被质疑主观 | 解释困难 | 返回分项得分和排序原因，不只返回总分 |
| 对照仿真污染真实状态 | 时间机器行为混乱 | 对照服务纯函数化，不写 `sim_state.json` |
| 前端堆叠过多信息 | 演示页面杂乱 | 管理员看决策摘要，详情折叠展开 |

## 11. 完成定义

本轮迭代完成时，应满足：

- 工单相关问答必须基于实时工单数据，不能输出不存在的工单号和设备号。
- 外部模型回答不可信时，系统自动回退，并在 UI 明确说明。
- 管理员可以看到基于风险、损失、SLA、碳排的派单优先级建议。
- 资源约束问题“今天只有 3 个工人先派谁”能由接口和页面回答。
- 已关闭工单能影响预算改善摘要和 ROI 候选沉淀。
- 时间机器能展示不处理、立即处理、延迟处理三种对照结果。
- 管理员和工人的可见页面、可操作动作、后端权限均符合角色职责。
- 后端测试、前端构建、真实浏览器主流程验收均通过。

## 12. 建议提交顺序

为了降低合并风险，建议拆成 4 次提交：

1. `docs: add grounded decision iteration plan`
2. `feat: ground assistant answers with realtime work orders`
3. `feat: add economic dispatch decision workflow`
4. `feat: add counterfactual simulation and role permission hardening`

如果开发周期较短，也可先只提交第 1 和第 2 项，优先修复外部 LLM 可信度问题。
