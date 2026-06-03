# AI Module

Unified LLM client with memory management and RAG. All components are auto-injected into builtins.

## ChatModel

```python
# Basic chat
response = await chat_model.chat([{"role": "user", "content": "Hello"}])

# Specify model
response = await chat_model.chat([...], model="gemini")

# Stream output
async for chunk in chat_model.chat_stream([...]):
    print(chunk, end="")

# Generate embeddings
vector = await chat_model.embed("Some text")
```

### Supported Providers

| Provider | Type | Base URL |
|----------|------|----------|
| DeepSeek | `openai` | `https://api.deepseek.com` |
| OpenAI | `openai` | `https://api.openai.com/v1` |
| Gemini | `google` | — |
| Ollama | `ollama` | `http://localhost:11434` |
| GLM / Moonshot / Qwen / vLLM | `openai` | Custom |

### Custom Provider

```python
class MyProvider(BaseProvider):
    async def chat(self, messages, **kwargs) -> str:
        ...

register_provider("my_provider", MyProvider)
```

## Short-Term Memory

Session-based conversation context.

```python
await short_term_memory.add("session_001", "user", "My name is Alice")
await short_term_memory.add("session_001", "assistant", "Hello Alice!")
messages = await short_term_memory.get_messages("session_001")
```

## Long-Term Memory

Persistent key-value memory.

```python
await long_term_memory.remember("user_name", "Alice")
name = await long_term_memory.recall("user_name")
await long_term_memory.forget("user_name")
```

## RAG (Retrieval-Augmented Generation)

```python
await rag.add_document("Pancake is a Python framework...")
await rag.add_documents(["doc1 content", "doc2 content"])
answer = await rag.ask("What is Pancake?")
results = await rag.search("framework", top_k=5)
```

## Configuration

```yaml
ai:
  default_model: deepseek
  providers:
    deepseek:
      type: openai
      base_url: https://api.deepseek.com
      api_key: ${DEEPSEEK_API_KEY}
      model: deepseek-chat
      max_tokens: 4096
      temperature: 0.7
      timeout: 60
      retry: 3
    gemini:
      type: google
      api_key: ${GOOGLE_API_KEY}
      model: gemini-2.0-flash
  memory:
    short_term:
      backend: memory          # memory | redis | mybatis
      ttl: 86400
      max_messages: 20
    long_term:
      backend: memory
      table_name: ai_long_term
  rag:
    backend: pgvector          # pgvector | redis | mongodb
    embedding_model: text-embedding-3-small
    chunk_size: 500
    top_k: 5
    dimension: 1536
```

Use `${ENV_VAR}` to reference environment variables.

## Memory Backends

| Backend | Description |
|---------|-------------|
| `memory` | In-memory (default, non-persistent) |
| `redis` | Redis storage |
| `mybatis` | Database via MyBatis mapper |

## Optional Dependency

```bash
pip install pancake_framework[ai]
```
