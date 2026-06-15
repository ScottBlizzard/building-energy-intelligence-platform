@startuml
title 资源约束派单

actor "管理员" as Admin
participant "decision_service" as Decision
database "work_order_store" as Store
participant "auth_service" as Auth
participant "管理员界面" as UI

Admin -> Decision : GET /decisions/dispatch-plan
Decision -> Store : list_work_orders()
Decision -> Auth : list_demo_users()
Decision -> Decision : 计算忙闲、风险、损失、SLA、碳排
Decision --> UI : selected + deferred + summary
@enduml
