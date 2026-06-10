# 演示脚本草案

## 开场

说明项目定位：本项目是面向建筑能源管理与运维场景的智能管理系统原型，目标是把数据、分析、可视化和智能问答整合到同一个平台中。

## 第一部分：系统首页

- 使用 `admin / admin123` 登录系统
- 展示管理员业务闭环看板，说明开放工单、待复核、高优先级未闭环和闭环率
- 介绍四个核心模块：数据管理、统计分析、可视化、智能问答
- 指出当前样例数据和知识库都已经接入到仓库结构中

## 第二部分：接口展示

- 打开 `/docs`
- 调用 `/api/v1/overview`
- 调用 `/api/v1/records`
- 调用 `/api/v1/analytics/anomalies`
- 调用 `/api/v1/analytics/floor-summary`，说明系统可以按楼层和区域定位异常
- 调用 `/api/v1/analytics/work-orders`，说明异常会转换成可执行工单
- 调用 `/api/v1/analytics/optimization-recommendations`，说明系统能给出节能优化建议
- 展示 `docs/16-mcp-integration.md`，说明系统除 REST API 外，还通过 MCP Server 暴露数据接入、查询统计、异常诊断、运营报告和智能问答工具
- 如果需要现场演示 MCP，可运行 `.\scripts\start-mcp.ps1 -Transport streamable-http -HostAddress 127.0.0.1 -Port 8765`，说明 `/mcp` 是 MCP HTTP 协议入口

## 第三部分：前端分析页展示

- 总览页：展示三维楼宇风险态势，拖拽旋转视图，点击风险楼层后跳转到统计分析并自动带入建筑与楼层筛选
- 数据浏览页：展示更完整的原始字段，包括水耗、制冷量、环境温湿度、占用密度和设备编号
- 统计分析页：展示趋势、异常原因和异常明细
- 楼层与区域分析：说明查询建筑后可以下钻到楼层/区域维度
- 设备运行监测：展示设备类型、楼层位置、最新状态、异常数和维护建议
- 运营优化建议：展示高优先级节能方向、依据和预期效果
- 最后展示建筑对比和 COP 排名，作为全局稳定基准

## 第四部分：工单与决策展示

- 工单中心：从异常记录中选择一个问题，分配给 `worker_ahu` 或 `worker_chiller`，生成“已派单”工单
- 退出管理员，使用工人账号登录，进入“我的工单”
- 工人点击“接单并开始处理”，填写现场实际原因、处理结果、部件和安全备注
- 工人提交管理员复核，工单进入“待复核”
- 切回管理员账号，在工单中心复核通过并关闭；说明时间线记录了 create、accept、submit、review_approve
- 决策报告：展示未来 7 天能耗预测
- 调整节能模拟器参数，展示预计节电量和预计节约费用
- 展示自动运营报告，说明已关闭工单会进入日报归档口径，可以作为汇报材料的核心内容

## 第五部分：智能问答展示

推荐提问：

- 当前样例数据的平均 COP 是多少？
- 当前有哪些异常记录？
- 科研实验楼D哪一层异常最多？
- 哪些设备需要优先维护？
- 生成当前异常处置建议
- 有什么节能优化建议？
- 系统后续如何接入知识库？

## 第六部分：MCP 能力说明

- 说明默认 `.\scripts\start-mcp.ps1` 使用 stdio transport，适合 Cursor、Claude Desktop 或其他支持 MCP 的客户端接入
- 强调 MCP Tools 不是给 PowerShell 人工输入菜单用的，而是给 AI 客户端调用项目真实数据和分析函数
- 对照原项目要求说明：`query_energy_records` 对应数据接入与查询，`get_time_summary` 对应时段汇总，`get_cop_ranking` 和 `get_energy_overview` 对应 COP 计算，`get_anomalies` 与 `explain_anomaly` 对应异常分析和运维诊断
- 补充说明：`get_admin_business_dashboard`、`list_persistent_work_orders`、`get_worker_business_dashboard`、`get_work_order_detail` 和 `get_anomaly_event_context` 用于让 MCP 客户端查询业务闭环状态

## 收尾

强调当前已经完成从项目结构、数据样例、角色登录、REST/MCP 双接口、分析图表、异常派单、工人处理、管理员复核、运营日报归档到外部大模型可选调用的演示闭环。后续如果有时间，再继续升级真实传感器接入、RAG 和更完整的权限体系。
