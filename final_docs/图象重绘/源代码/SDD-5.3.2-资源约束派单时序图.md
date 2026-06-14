@startuml
actor 管理员 as Admin
participant decision_service as Decision
participant work_order_store as Store
participant auth_service as Auth

Admin -> Decision: GET /decisions/dispatch-plan
Decision -> Store: list_work_orders()
Decision -> Auth: list_demo_users()
Decision -> Decision: 计算工人忙闲、风险分、损失、SLA、碳排、重复异常
Decision --> Admin: selected + deferred + summary
@enduml