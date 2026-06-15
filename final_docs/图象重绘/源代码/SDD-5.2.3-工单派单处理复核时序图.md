@startuml
title 管理员派单、工人提交、管理员复核

actor "管理员" as Admin
actor "工人" as Worker
participant "WorkOrder API" as API
participant "permission_service" as Perm
database "work_order_store" as Store
participant "simulation_service" as Sim

Admin -> API : POST /work-orders 或 PATCH /assign
API -> Perm : require_admin_operator()
API -> Store : create/assign_work_order()
Store -> Store : 校验同设备工单与工人忙闲锁
Store --> Admin : assigned 工单
Worker -> API : PATCH /accept
API -> Store : accept_work_order()
Worker -> API : PATCH /submit
API -> Store : submit_work_order(...)
Store --> Admin : pending_review 工单
Admin -> API : PATCH /review approved=true
API -> Store : review_work_order()
Store -> Sim : register_intervention(equipment_id)
Store --> Admin : closed 工单和 timeline
@enduml
