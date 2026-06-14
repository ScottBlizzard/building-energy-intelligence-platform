@startuml
!theme plain

entity ENERGY_READING {
  *record_id : string <<PK>>
  *building_id : string <<FK>>
  *equipment_id : string <<FK>>
  --
  timestamp : datetime
  electricity_kwh : float
  hvac_kwh : float
  cooling_load_kwh : float
  equipment_status : string
}

entity WORK_ORDER {
  *work_order_id : string <<PK>>
  *source_record_id : string <<FK>>
  *equipment_id : string <<FK>>
  --
  status : string
  assignee_id : string
  data : json
}

entity BUILDING {
  *building_id : string <<PK>>
}

entity BUDGET {
  *id : int <<PK>>
  *building_id : string <<FK>>
  --
  year : int
  month : int
  budget_kwh : float
  data : json
}

entity ROI_PROJECT {
  *building_id : string <<PK>>
}

entity WORK_ORDER_TIMELINE {
  *embedded timeline : string <<PK>>
}

entity SIM_INTERVENTION {
  *closed order registers repair : string <<PK>>
}

entity SIM_STATE {
  *id : int <<PK>>
  --
  sim_current_date : string
  sim_start_date : string
  data : json
}

ENERGY_READING ||--o{ WORK_ORDER : "source_record_id / equipment_id"
ENERGY_READING ||--o{ BUDGET : "building_id"
WORK_ORDER ||--o{ WORK_ORDER_TIMELINE : "embedded timeline"
WORK_ORDER ||--o{ SIM_INTERVENTION : "closed order registers repair"
BUILDING ||--o{ ENERGY_READING : "building_id"
BUILDING ||--o{ BUDGET : "building_id"
BUILDING ||--o{ ROI_PROJECT : "building_id"

@enduml