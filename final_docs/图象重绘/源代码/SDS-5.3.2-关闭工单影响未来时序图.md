@startuml
title 管理员关闭工单并影响未来

actor "管理员" as Admin
participant "WorkOrder API" as API
database "work_order_store" as Store
participant "simulation_service" as Sim
participant "data_loader/analysis" as Data
participant "前端报告" as UI

Admin -> API : PATCH /work-orders/{id}/review\napproved=true
API -> Store : review_work_order()
Store -> Store : 状态置为 closed\n写入 timeline
Store -> Sim : register_intervention(equipment_id)
Sim -> Sim : 保存维修干预
Admin -> API : POST /sim/advance
API -> Sim : advance_day()
UI -> Data : 查询未来可见数据
Data -> Sim : apply_interventions()
Data --> UI : 已修复设备异常减少
@enduml
