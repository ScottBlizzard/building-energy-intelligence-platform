@startuml
title 数据分析处理流程图
start
:CSV / MySQL energy_readings;
:data_loader.read_dataset();
:get_filtered_dataset(building, start, end, limit);
:simulation_service.apply_window/apply_interventions;
:analysis_service.build_analysis_frame();
fork
  :KPI / 趋势 / 对比 / COP;
fork again
  :异常列表 / 异常解释 / 工单草稿;
fork again
  :运营报告 / MCP / AI 接地上下文;
end fork
stop
@enduml
