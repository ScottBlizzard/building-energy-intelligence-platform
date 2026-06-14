@startuml
class AssistantService {
  + build_assistant_reply(question)
}

class GroundingService {
  + classify_assistant_question(question)
  + extract_entities(question)
}

class KnowledgeSearchService {
  + search_and_format_citations(query)
}

class LLMClient {
  + build_external_assistant_answer()
}

class MCPServer {
  + ask_energy_assistant()
  + search_energy_knowledge()
}

AssistantService --> GroundingService
AssistantService --> KnowledgeSearchService
AssistantService --> LLMClient
MCPServer --> AssistantService

@enduml