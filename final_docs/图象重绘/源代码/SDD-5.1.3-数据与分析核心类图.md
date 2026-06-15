@startuml
title 数据与分析子系统核心类图

class DataLoader {
  - dataset_cache
  + read_dataset()
  + get_filtered_dataset()
  + get_dataset_meta()
}

class AnalysisService {
  - baseline_rules
  - risk_formula
  + build_analysis_frame()
  + build_overview()
  + build_anomaly_summary()
  + build_operation_report()
}

class ExportService {
  + build_csv_content()
  + build_export_filename()
}

class SimulationService {
  + apply_window()
  + apply_interventions()
}

class AnalysisFrame {
  + floor_label
  + equipment_type
  + risk_score
  + business_impact
}

class OperationReport {
  + energy_summary
  + anomaly_summary
  + work_order_summary
  + decision_summary
}

DataLoader --> SimulationService
AnalysisService --> DataLoader
AnalysisService --> AnalysisFrame
AnalysisService --> OperationReport
ExportService --> AnalysisService
@enduml
