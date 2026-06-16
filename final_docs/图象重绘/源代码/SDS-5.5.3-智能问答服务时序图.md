@startuml
title 智能问答服务交互

actor "用户/MCP客户端" as User
participant "Assistant API / MCP Tool" as API
participant "assistant_service" as Local
participant "knowledge_search_service" as KB
participant "grounding_service" as Ground
participant "llm_client" as LLM

User -> API : question + provider/model
API -> Local : build_assistant_reply(question)
API -> KB : search_and_format_citations(question)
API -> Ground : build_work_order_grounding_context(question)
API -> LLM : build_external_assistant_answer(...)
LLM --> API : external_answer 或失败
API -> Ground : validate_grounded_answer() / fallback
API --> User : AssistantResponse
@enduml
