@startuml
title 前端展示子系统核心组件类图

class DashboardView {
  - currentUser
  - activeTab
  - simClock
  - analytics
  - workOrderState
  + bootstrapAuthenticatedApp()
  + refreshBusinessState()
  + handleAsk()
  + handleExport()
}

class ApiClient {
  + request()
  + setApiOperator()
  + buildApiUrl()
}

class StateStores {
  + loading
  + errors
  + decisionState
  + assistantReply
}

class BusinessPanels {
  + BudgetPanel
  + ROIPanel
  + AssistantPanel
}

class VisualizationComponents {
  + TrendChart
  + BuildingComparisonChart
  + BuildingRiskScene
}

class TableAndFeedback {
  + DataTable
  + StatusBanner
  + EmptyState
  + LoadingSpinner
}

DashboardView --> ApiClient
DashboardView --> StateStores
DashboardView --> BusinessPanels
DashboardView --> VisualizationComponents
DashboardView --> TableAndFeedback
@enduml
