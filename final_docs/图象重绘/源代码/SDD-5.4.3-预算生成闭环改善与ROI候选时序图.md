@startuml
title 预算生成、闭环改善与 ROI 候选

actor "管理员" as Admin
participant "budget_service" as Budget
participant "decision_service" as Decision
participant "roi_service" as ROI
participant "analysis_service" as Analysis
database "work_order_store" as Store

Admin -> Budget : POST /budget/budgets/generate
Budget -> Analysis : 读取沙盘可见数据
Budget --> Admin : 月度预算列表
Admin -> Decision : GET /decisions/budget-impact
Decision -> Store : list_work_orders(status=closed)
Decision --> Admin : 节省与预测改善
Admin -> Decision : GET /decisions/roi-candidates
Decision -> Analysis : 识别重复异常设备
Decision --> Admin : 改造候选池
Admin -> ROI : POST /roi/analyze
ROI --> Admin : NPV / IRR / EAA / 回收期 / 敏感性
@enduml
