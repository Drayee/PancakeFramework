# AI 模块

统一 LLM 客户端，集成记忆管理和 RAG。所有组件自动注入 builtins。

## ChatModel

```python
# 基本对话
response = await chat_model.chat([{"role": "user", "content": "你好"}])

# 指定模型
response = await chat_model.chat([...], model="gemini")

# 流式输出
async for chunk in chat_model.chat_stream([...]):
    print(chunk, end="")

# 生成嵌入向量
vector = await chat_model.embed("一些文本")
```

### 支持的提供商

| 提供商 | 类型 | Base URL |
|--------|------|----------|
| DeepSeek | `openai` | `https://api.deepseek.com` |
| OpenAI | `openai` | `https://api.openai.com/v1` |
| Gemini | `google` | — |
| Ollama | `ollama` | `http://localhost:11434` |
| 智谱 GLM / Moonshot / Qwen / vLLM | `openai` | 自定义 |

### 自定义提供商

```python
class MyProvider(BaseProvider):
    async def chat(self, messages, **kwargs) -> str:
        ...

register_provider("my_provider", MyProvider)
```

## 短期记忆

基于会话的对话上下文。

```python
await short_term_memory.add("session_001", "user", "我叫小明")
await short_term_memory.add("session_001", "assistant", "你好小明！")
messages = await short_term_memory.get_messages("session_001")
```

## 长期记忆

持久化键值记忆。

```python
await long_term_memory.remember("user_name", "小明")
name = await long_term_memory.recall("user_name")
await long_term_memory.forget("user_name")
```

## RAG（检索增强生成）

```python
await rag.add_document("Pancake 是一个 Python 框架...")
await rag.add_documents(["文档1内容", "文档2内容"])
answer = await rag.ask("什么是 Pancake？")
results = await rag.search("框架", top_k=5)
```

## 配置

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

使用 `${ENV_VAR}` 引用环境变量。

## 记忆后端

| 后端 | 说明 |
|------|------|
| `memory` | 内存（默认，非持久化） |
| `redis` | Redis 存储 |
| `mybatis` | 通过 MyBatis Mapper 存储到数据库 |

## 可选依赖

```bash
pip install pancake_framework[ai]
```
