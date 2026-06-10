# 业务逻辑升级 TODO

## 目标

把系统从“后端数据采集 + 前端展示看板”升级为“建筑能源异常发现、经济影响评估、工单处置、验证关闭、管理报告”的业务闭环系统，支撑 8 分钟系统演示。

## Demo 主线

1. 系统发现某栋楼/某楼层能耗异常。
2. 系统给出异常类型、严重等级、触发规则和可能原因。
3. 系统估算浪费电量、浪费费用、碳排影响和可节约金额。
4. 管理员一键生成工单，分派给对应角色。
5. 工单进入“待分派 -> 处理中 -> 待验证 -> 已关闭”的状态流。
6. 系统根据异常改善情况给出验证结论。
7. 运营报告汇总异常、未闭环工单、节能收益和后续建议。

## P0：本轮必须完成

- [x] 异常分析增加业务字段：
  - 严重等级：高 / 中 / 低。
  - 风险评分：0-100。
  - 触发规则数量。
  - 浪费电量估算。
  - 浪费费用估算。
  - 碳排影响估算。
  - 预计节能收益。
- [x] 异常解释接口增加经济影响与处置建议。
- [x] 工单候选列表带入业务影响字段。
- [x] 持久化工单支持完整状态流：
  - 待分派
  - 处理中
  - 待验证
  - 已关闭
  - 已忽略
- [x] 工单更新时支持处置动作、验证结果、关闭时间。
- [x] 新增或增强运营报告，使其展示：
  - 估算浪费费用总额。
  - 可节约金额。
  - 未闭环高风险工单数。
  - 需要优先处理的异常。
- [x] 前端工单页展示状态流、经济影响和验证结论。

## P1：适合演示增强

- [x] 增加“处理后验证”按钮或状态切换，模拟复核异常是否下降。
- [x] 增加“节能策略模拟”轻量模块：
  - 夜间空调关闭。
  - 设定温度上调 1 度。
  - 高风险设备优先巡检。
- [x] 把运营报告中的 action items 改成更业务化的待办清单。
- [ ] AI 助手回答时能够引用浪费费用、工单状态和验证结果。

## P2：后续可扩展

- [x] 按建筑配置月度能耗预算。
- [x] 增加预算超支预测。
- [ ] 增加工单 SLA 逾期提醒。
- [x] 增加多角色权限：管理员、运维人员、审计人员。
- [x] 增加节能改造项目 ROI 分析。
- [x] 增加设备改造方案对比与投资回收期、NPV、IRR 指标。
- [ ] 接入真实传感器或数据库后替换样例数据源。

## 实施顺序

1. 后端业务评估函数：先统一计算异常等级、成本、碳排和建议。
2. 分析接口改造：让 anomalies、anomaly-explanations、work-orders、operation-report 都复用同一套评估结果。
3. 工单状态机改造：扩展 schema 和持久化 store。
4. 前端展示改造：优先改工单与异常详情区域，保证 Demo 可讲。
5. 测试与文档：补充后端测试，更新本 TODO 状态。

## 验收标准

- [x] 后端测试通过。
- [x] 前端构建通过。
- [x] 演示中能清楚讲出“发现异常 -> 估算损失 -> 生成工单 -> 处理验证 -> 报告复盘”。
- [x] 不夸大为真实传感器生产系统，仍明确当前是课程样例数据原型。

## 本轮完成记录（2026-06-10）

- 后端新增统一异常业务影响模型：风险分、严重等级、浪费 kWh、浪费费用、碳排影响、预计可回收金额、SLA 和验证口径。
- `/analytics/anomalies`、`/analytics/anomaly-explanations/{record_id}`、`/analytics/work-orders`、`/analytics/operation-report` 已带出业务影响字段。
- 持久化工单状态流升级为“待分派 -> 处理中 -> 待验证 -> 已关闭”，兼容旧的“已完成”，并支持“已忽略”。
- 工单 PATCH 支持记录分派动作、处置动作、验证状态、验证结果、验证时间和关闭时间。
- 前端工单中心新增异常预览、业务损失汇总、状态链、快速推进按钮、验证口径和复测结果展示。
- 决策报告新增异常浪费、经济损失、预计回收和碳排影响指标卡。
- 验证命令：
  - `python -m pytest backend/tests/test_analytics_endpoints.py backend/tests/test_work_orders_endpoint.py`
  - `npm run build`

## DeepSeek 扩展集成记录（2026-06-10）

- 已新增“预算管理”方向：
  - 后端路由：`/api/v1/budget/budgets`、`/api/v1/budget/budgets/analysis`、`/api/v1/budget/budgets/kpi/{building_id}`。
  - 前端入口：`预算管理` Tab，组件为 `frontend/src/components/BudgetPanel.vue`。
  - 功能：自动生成楼栋月度预算、手动调整预算、当前执行率、月末预测执行率、预算状态预警、楼栋 KPI 考核卡。
  - KPI 字段：预算控制率、COP 达标率、异常响应及时率、月度评分和年度等级。
- 已新增“节能改造 ROI”方向：
  - 后端路由：`/api/v1/roi/audit/{building_id}`、`/api/v1/roi/analyze`、`/api/v1/roi/compare`。
  - 兼容旧路径：`/api/v1/roi/roi/...` 暂时保留但不在文档中主推。
  - 前端入口：`改造分析` Tab，组件为 `frontend/src/components/ROIPanel.vue`。
  - 功能：按楼栋诊断设备能效、推荐变频改造/高效设备更换/智能控制升级/综合节能方案，计算投资额、年节电、静态回收期、5 年 ROI、NPV、IRR、年减排。
- 集成修正：
  - ROI 项目寿命从 `expected_cop_improvement` 拆出为 `project_lifespan_years`，避免字段语义混乱。
  - ROI 年度收益按样例期数据年化，避免因为样例数据只有 2026-03-01 到 2026-06-01 而低估投资收益。
  - 预算分析同时展示“当前实际执行率”和“按已观测天数推算的月末执行率”，更适合做提前预警演示。
  - 预算持久化支持 `BUDGET_FILE` 环境变量，方便测试隔离。
- 验证命令：
  - `python -m pytest backend/tests/test_budget_roi_endpoints.py backend/tests/test_analytics_endpoints.py backend/tests/test_work_orders_endpoint.py`
  - `npm run build`
- 演示提醒：
  - 当前样例数据覆盖 2026-03-01 至 2026-06-01，6 月只有少量样例记录。
  - 汇报时应表述为“基于样例采样周期的月末推算/原型演示”，不要说成真实生产系统已经采集到 6 月 18 日。

## Codex 业务闭环优化记录（2026-06-10）

- 已将预算与 ROI 服务的数据入口切换为仿真可见数据：
  - `budget_service` 与 `roi_service` 使用 `get_visible_dataset()`，时间机器推进和工单修复干预会影响预算执行率、KPI 和 ROI 审计结果。
  - 自动预算生成增加 `basis` 与 `seasonal_coefficient`，避免没有同月数据时直接依赖固定兜底值。
- 已增强 KPI 计算口径：
  - `anomaly_response_timely_rate` 优先基于持久化工单 `timeline` 计算 SLA 达标率。
  - 没有关联工单样本时保留异常数量近似口径，保证原型数据可稳定演示。
- 已增强 ROI 业务逻辑：
  - ROI 结果新增 `payback_label`、`payback_within_lifespan`、`observed_days`、`annualization_factor` 和三情景 `sensitivity`。
  - 多方案比较返回可行方案数量、最快回收期标签和推荐文本。
  - 前端 `ROIPanel.vue` 新增多方案经济性对比表、最佳 NPV 高亮和敏感性分析卡片。
- 已增强管理层决策输出：
  - `operation-report` 返回 `management_decision`、`budget_summary`、`roi_recommendation`，将预算风险、KPI 和 ROI 推荐汇总到同一份运营报告。
  - AI 助手新增预算/KPI 与 ROI 问答分支，可回答“本月预算是否超支”“哪个改造方案回本最快”等演示问题。
- 新增/更新测试：
  - 预算 KPI 测试覆盖月度响应及时率字段。
  - ROI 测试覆盖回本标签、寿命期可行性、敏感性分析和多方案比较。
  - AI 助手测试覆盖预算/KPI 与 ROI 问答。
- 验证命令：
  - `python -m pytest backend/tests/test_budget_roi_endpoints.py backend/tests/test_assistant_endpoint.py backend/tests/test_analytics_endpoints.py backend/tests/test_work_orders_endpoint.py backend/tests/test_simulation.py`
  - `python -m pytest backend/tests/test_analytics_endpoints.py backend/tests/test_work_orders_endpoint.py backend/tests/test_auth_endpoint.py backend/tests/test_business_closure_endpoints.py backend/tests/test_business_upgrade.py backend/tests/test_building_detail_endpoint.py backend/tests/test_data_endpoints.py backend/tests/test_export_endpoint.py backend/tests/test_health.py backend/tests/test_simulation.py backend/tests/test_budget_roi_endpoints.py backend/tests/test_assistant_endpoint.py`
  - `npm run build`
