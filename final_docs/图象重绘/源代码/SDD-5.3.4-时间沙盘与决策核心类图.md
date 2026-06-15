@startuml
title 时间沙盘与决策子系统核心类图

class SimulationService {
  + get_state()
  + start_simulation()
  + advance_day()
  + register_intervention()
  + apply_window()
  + apply_interventions()
}

class SimulationState {
  + active
  + current_date
  + start_date
  + interventions
}

class ScenarioService {
  + build_counterfactual_scenarios()
}

class DecisionService {
  + rank_open_work_orders()
  + recommend_dispatch_plan()
  + worker_status_overview()
}

class WorkOrderStore {
  + list_work_orders()
  + review_work_order()
}

class DispatchPlan {
  + selected
  + deferred
  + worker_status
  + summary
}

SimulationService --> SimulationState
ScenarioService --> SimulationService
DecisionService --> WorkOrderStore
DecisionService --> DispatchPlan
WorkOrderStore --> SimulationService
@enduml
