@startuml
title 工单派发

actor "管理员" as Admin
participant "Web前端" as UI
participant "工单API" as API
participant "工单状态机引擎" as Engine
database "持久化存储" as Store

Admin -> UI : 选择异常并提交派单
activate UI

UI -> API : POST /work-orders
activate API

API -> Engine : 校验设备去重和工人忙闲
activate Engine

Engine --> API : 校验通过
deactivate Engine

API -> Store : 保存工单和时间线
activate Store

Store --> API : 返回工单ID
deactivate Store

API --> UI : 返回已派单工单
deactivate API

UI --> Admin : 展示派单成功
deactivate UI

@enduml