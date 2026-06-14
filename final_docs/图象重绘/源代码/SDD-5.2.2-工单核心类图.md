@startuml
class WorkOrder {
  - work_order_id
  - source_record_id
  - equipment_id
  - status
  - priority
  - assignee_id
  - risk_score
  - wasted_cost_yuan
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

class SimulationService {
  + register_intervention()
}

WorkOrderStore --> WorkOrder
WorkOrderStore --> PermissionService
WorkOrderStore --> SimulationService

@enduml