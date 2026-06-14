@startuml
title 可信智能问答

actor "用户" as User
participant "AI助手面板" as UI
participant "可信问答引擎" as Assistant
participant "业务服务层" as Services
participant "外部大模型" as LLM

User -> UI : 输入问题
activate UI

UI -> Assistant : POST /assistant/query
activate Assistant

Assistant -> Services : 获取数据/异常/工单/报告上下文
activate Services

Services --> Assistant : 返回事实上下文
deactivate Services

alt 外部模型启用
    Assistant -> LLM : 携带事实上下文请求增强
    activate LLM
    LLM --> Assistant : 返回候选回答
    deactivate LLM
    Assistant -> Assistant : 实体和事实校验
    activate Assistant
    Assistant --> Assistant : 
    deactivate Assistant
else 外部模型未启用或校验失败
    Assistant -> Assistant : 生成本地可信回答
    activate Assistant
    Assistant --> Assistant : 
    deactivate Assistant
end

Assistant --> UI : 返回回答 + 引用 + 来源标签
deactivate Assistant

UI --> User : 展示结果
deactivate UI

@enduml