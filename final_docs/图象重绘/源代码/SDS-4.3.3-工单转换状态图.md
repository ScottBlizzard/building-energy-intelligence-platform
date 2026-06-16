@startuml

hide empty description

[*] --> pending_confirm : 自动队列/创建草稿

pending_confirm --> assigned : 管理员派单
pending_confirm --> ignored : 管理员忽略

assigned --> in_progress : 工人接单
assigned --> assigned : 管理员改派

in_progress --> pending_review : 工人提交处理结果

pending_review --> closed : 管理员复核通过
pending_review --> rejected : 管理员驳回

rejected --> assigned : 管理员重新派单

closed --> [*]
ignored --> [*]

@enduml