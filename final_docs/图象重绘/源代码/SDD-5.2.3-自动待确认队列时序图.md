@startuml
title 自动待确认队列

actor "管理员" as Admin
participant "/work-orders/auto-confirm" as API
participant "analysis_service" as Analysis
database "work_order_store" as Store

Admin -> API : POST /work-orders/auto-confirm
API -> Analysis : build_anomaly_work_order_drafts()
API -> Store : create_pending_confirm_drafts()
Store -> Store : 跳过同设备未关闭工单和已修复设备
Store --> Admin : created / skipped / total
@enduml
