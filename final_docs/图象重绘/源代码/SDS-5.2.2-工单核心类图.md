@startuml
title 工单与权限子系统核心类图

class WorkOrder {
  - work_order_id
  - source_record_id
  - equipment_id
  - status
  - assignee_id
  - timeline
}

class WorkOrderStore {
  + list_work_orders()
  + create_work_order()
  + assign_work_order()
  + accept_work_order()
  + submit_work_order()
  + review_work_order()
  + ignore_work_order()
}

class PermissionService {
  + require_admin_operator()
  + require_worker_operator()
  + build_worker_support()
}

class TimelineEvent {
  + action
  + operator_id
  + at
  + note
}

class WorkerSupport {
  + active_orders
  + standard_guidance
  + similar_cases
}

class SimulationService {
  + register_intervention()
}

WorkOrderStore --> WorkOrder
WorkOrder --> TimelineEvent
WorkOrderStore --> PermissionService
PermissionService --> WorkerSupport
WorkOrderStore --> SimulationService
@enduml
