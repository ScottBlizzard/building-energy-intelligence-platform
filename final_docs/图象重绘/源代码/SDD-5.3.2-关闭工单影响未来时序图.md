@startuml
title 管理员关闭工单并影响未来

actor "管理员" as Admin
participant "WorkOrder API" as API
database "work_order_store" as Store
participant "simulation_service" as Sim
participant "data_loader/analysis" as Data
participant "前端报告" as UI

Admin -> API : PATCH /work-orders/{id}/review\napproved=true
activate API

API -> Store : review_work_order()
activate Store

Store -> Store : 状态置为 closed\n写入 timeline
activate Store

Store -> Sim : register_intervention(equipment_id)
activate Sim

Sim -> Sim : 保存维修干预
deactivate Sim



Admin -> API : POST /sim/advance
activate API

API -> Sim : advance_day()
activate Sim

UI -> Data : 查询未来可见数据
activate Data

Data -> Sim : apply_interventions()
activate Sim


Data --> UI : 已修复设备异常减少
deactivate Data

@enduml