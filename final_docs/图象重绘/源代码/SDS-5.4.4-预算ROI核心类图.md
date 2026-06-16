@startuml
title 预算与 ROI 子系统核心类图

class BudgetService {
  + auto_generate_budgets()
  + set_budget()
  + build_budget_analysis()
  + build_budget_kpi()
}

class DecisionService {
  + summarize_budget_impact_from_closures()
  + find_roi_candidates_from_repeated_anomalies()
}

class ROIService {
  + build_equipment_audit()
  + analyze_roi_project()
  + compare_scenarios()
}

class Budget {
  + building_id
  + year
  + month
  + budget_kwh
}

class BudgetAnalysis {
  + execution_rate
  + forecast_rate
  + risk_level
}

class EquipmentAudit {
  + equipment_type
  + sample_count
  + current_cop
}

class ROIProject {
  + investment
  + npv
  + irr
  + eaa
  + payback
}

BudgetService --> Budget
BudgetService --> BudgetAnalysis
DecisionService --> BudgetAnalysis
DecisionService --> EquipmentAudit
ROIService --> EquipmentAudit
ROIService --> ROIProject
@enduml
