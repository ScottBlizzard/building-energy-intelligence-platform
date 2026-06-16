@startuml
title 智能服务子系统核心类图

class MCPServer {
  + ask_energy_assistant()
  + search_energy_knowledge()
}

class AssistantService {
  + build_assistant_reply(question)
}

class GroundingService {
  + classify_assistant_question()
  + build_work_order_grounding_context()
  + validate_grounded_answer()
}

class KnowledgeSearchService {
  + search_knowledge()
  + search_and_format_citations()
}

class LLMClient {
  + list_llm_model_options()
  + build_external_assistant_answer()
}

MCPServer --> AssistantService
AssistantService --> GroundingService
AssistantService --> KnowledgeSearchService
AssistantService --> LLMClient
@enduml
