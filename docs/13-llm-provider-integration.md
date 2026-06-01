# 外部大模型接入说明

## 1. 安全原则

真实 API Key 只能放在本地 `.env` 文件中，不得写入：

- `.env.example`
- README
- 代码文件
- 文档文件
- GitHub issue / commit message
- 截图和演示视频

如果真实 Key 曾经出现在即时通信记录、群聊或公开仓库，应立即到对应平台撤销或重置。

## 2. 当前接入方式

后端问答接口仍然是：

```text
POST /api/v1/assistant/query
```

默认情况下，系统使用本地规则问答和知识库引用，不依赖外部大模型。只有本地 `.env` 中显式设置：

```env
LLM_ENABLED=true
```

系统才会尝试调用外部模型。外部模型调用失败时，会自动退回本地规则问答，不影响演示流程。

## 3. 支持的供应商入口

当前后端按 OpenAI-compatible `/chat/completions` 协议接入，已内置这些供应商入口：

| LLM_PROVIDER | 默认 Base URL | 说明 |
| --- | --- | --- |
| `nvidia` | `https://integrate.api.nvidia.com/v1` | NVIDIA NIM / Integrate |
| `groq` | `https://api.groq.com/openai/v1` | Groq OpenAI-compatible API |
| `openrouter` | `https://openrouter.ai/api/v1` | OpenRouter |
| `together` | `https://api.together.xyz/v1` | Together AI |
| `siliconflow` | `https://api.siliconflow.cn/v1` | 硅基流动 |
| `alibaba` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 阿里百炼 OpenAI 兼容模式 |
| `gemini` | `https://generativelanguage.googleapis.com/v1beta/openai` | Gemini OpenAI 兼容入口 |
| `openai` | `https://api.openai.com/v1` | OpenAI |
| `local` | `http://127.0.0.1:10531/v1` | 本地 OpenAI-compatible 服务 |

如果某个平台的入口发生变化，可以直接用 `LLM_BASE_URL` 覆盖默认值。

## 4. 本地 `.env` 示例

### 使用 NVIDIA

```env
LLM_ENABLED=true
LLM_PROVIDER=nvidia
LLM_MODEL=meta/llama-3.3-70b-instruct
NVIDIA_API_KEY=your_real_key_here
```

### 使用 OpenRouter

```env
LLM_ENABLED=true
LLM_PROVIDER=openrouter
LLM_MODEL=meta-llama/llama-3.3-70b-instruct
OPENROUTER_API_KEY=your_real_key_here
```

### 使用本地 OpenAI-compatible 服务

```env
LLM_ENABLED=true
LLM_PROVIDER=local
LLM_BASE_URL=http://127.0.0.1:10531/v1
LLM_MODEL=gpt-5.4
LLM_API_KEY=not-needed
```

## 5. 演示建议

正式项目展示演示时，建议准备两种模式：

1. `LLM_ENABLED=false`：稳定本地规则问答，确保无网络时也能演示。
2. `LLM_ENABLED=true`：展示外部模型增强后的自然语言回答。

不应将外部模型作为唯一演示路径。外部 API 可能受余额、限流、网络和平台状态影响。

前端智能问答区已经提供模型选择器。页面会从：

```text
GET /api/v1/assistant/providers
```

读取可选模型，只展示供应商和模型名，不展示 API Key。发送问题时，前端会把选中的 `provider` 和 `model` 一起传给：

```text
POST /api/v1/assistant/query
```

如果外部模型调用失败或回答质量不达标，后端会自动保留本地规则问答结果。

## 6. 测试供应商可用性

本地 `.env` 配好后，可以运行：

```powershell
python scripts/test_llm_providers.py
```

脚本会读取 `.env` 中的 key，用极短 prompt 测试各供应商和模型，并只输出 `OK / FAIL / SKIP`，不会打印真实 API Key。

如果只想测试部分供应商，可以在 `.env` 中增加：

```env
LLM_TEST_PROVIDERS=nvidia,groq,siliconflow
```
