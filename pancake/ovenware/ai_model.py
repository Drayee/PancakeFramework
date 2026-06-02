"""
AI 模块 — 统一 LLM 调用、记忆管理、RAG

提供可直接 inject 的 AI 组件：
  chat_model           — ChatModel 实例（全局单例）
  short_term_memory    — ShortTermMemory 实例
  long_term_memory     — LongTermMemory 实例
  rag                  — RAG 实例

配置项（YAML）：
  ai.default_model: deepseek
  ai.providers.<name>.type: openai | google | ollama
  ai.providers.<name>.base_url: ...
  ai.providers.<name>.api_key: ...
  ai.providers.<name>.model: ...
  ai.memory.short_term.strategy: sliding_window | token_limit
  ai.memory.long_term.backend: sqlite | redis
  ai.rag.collection: pancake_docs

可选依赖：pip install pancake[ai]
"""

import asyncio
import json
import logging
import os
from typing import Any, AsyncIterator, Callable, Optional

from pancake import oven

logger = logging.getLogger(__name__)


# ============================================================
#  默认配置
# ============================================================

_DEFAULT_CONFIG = {
    "default_model": "deepseek",
    "providers": {
        "deepseek": {
            "type": "openai",
            "base_url": "https://api.deepseek.com",
            "api_key": "",
            "model": "deepseek-chat",
            "max_tokens": 4096,
            "temperature": 0.7,
            "timeout": 60,
            "retry": 3,
        }
    },
    "memory": {
        "short_term": {
            "strategy": "sliding_window",
            "max_messages": 20,
            "max_tokens": 4000,
            "summary_on_overflow": False,
            "summary_model": None,
        },
        "long_term": {
            "backend": "sqlite",
            "ttl": 0,
            "namespace": "default",
            "redis_url": "redis://localhost:6379",
            "redis_db": 0,
            "sqlite_path": "resource/db/memory.db",
        },
    },
    "rag": {
        "collection": "pancake_docs",
        "embedding_provider": None,
        "embedding_model": "text-embedding-3-small",
        "chunk_size": 500,
        "chunk_overlap": 50,
        "top_k": 5,
        "persist_dir": "resource/db/chroma",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """深度合并字典，override 覆盖 base"""
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _resolve_env(value: str) -> str:
    """解析 ${ENV_VAR} 占位符（与 yml.py 的占位符解析保持一致）"""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_key = value[2:-1]
        return os.environ.get(env_key, "")
    return value


def _resolve_env_recursive(obj):
    """递归解析配置中的 ${ENV_VAR} 占位符"""
    if isinstance(obj, dict):
        return {k: _resolve_env_recursive(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env_recursive(i) for i in obj]
    if isinstance(obj, str):
        return _resolve_env(obj)
    return obj


# ============================================================
#  Provider 基类和实现
# ============================================================

class BaseProvider:
    """
    LLM Provider 基类

    用户可继承此类并重写方法来自定义行为：
        class MyProvider(OpenAIProvider):
            async def chat(self, messages, **kwargs):
                # 自定义逻辑
                return await super().chat(messages, **kwargs)
    """

    def __init__(self, config: dict):
        self.config = config
        self.model = config.get("model", "")
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.7)
        self.timeout = config.get("timeout", 60)

    async def chat(self, messages: list[dict], **kwargs) -> str:
        """调用模型，返回完整响应"""
        raise NotImplementedError

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        """流式调用"""
        raise NotImplementedError

    async def embed(self, text: str, **kwargs) -> list[float]:
        """文本向量化"""
        raise NotImplementedError


class OpenAIProvider(BaseProvider):
    """
    OpenAI 兼容 API Provider

    支持：OpenAI、DeepSeek、智谱 GLM、Moonshot、Qwen、vLLM、Ollama（OpenAI 兼容模式）
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = _resolve_env(config.get("base_url", "https://api.openai.com/v1"))
        self.api_key = _resolve_env(config.get("api_key", ""))
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key or "none",
                timeout=self.timeout,
            )
        return self._client

    async def chat(self, messages: list[dict], **kwargs) -> str:
        client = await self._get_client()
        model = kwargs.get("model", self.model)
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        for attempt in range(self.config.get("retry", 3)):
            try:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message.content
            except Exception as e:
                if attempt == self.config.get("retry", 3) - 1:
                    raise
                logger.warning(f"LLM 调用失败，重试 {attempt + 1}: {e}")
                await asyncio.sleep(1)

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        client = await self._get_client()
        model = kwargs.get("model", self.model)
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, text: str, **kwargs) -> list[float]:
        client = await self._get_client()
        model = kwargs.get("model", self.config.get("embedding_model", "text-embedding-3-small"))
        resp = await client.embeddings.create(model=model, input=text)
        return resp.data[0].embedding


class GoogleProvider(BaseProvider):
    """Google Gemini Provider"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = _resolve_env(config.get("api_key", ""))
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def chat(self, messages: list[dict], **kwargs) -> str:
        client = await self._get_client()
        model = kwargs.get("model", self.model)

        # 转换消息格式
        contents = self._convert_messages(messages)

        resp = await asyncio.to_thread(
            client.models.generate_content,
            model=model,
            contents=contents,
        )
        return resp.text

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        client = await self._get_client()
        model = kwargs.get("model", self.model)

        contents = self._convert_messages(messages)

        stream = await asyncio.to_thread(
            client.models.generate_content_stream,
            model=model,
            contents=contents,
        )
        for chunk in stream:
            if chunk.text:
                yield chunk.text

    async def embed(self, text: str, **kwargs) -> list[float]:
        client = await self._get_client()
        model = kwargs.get("model", "text-embedding-004")
        resp = await asyncio.to_thread(
            client.models.embed_content,
            model=model,
            contents=text,
        )
        return resp.embeddings[0].values

    def _convert_messages(self, messages: list[dict]) -> list:
        """将 OpenAI 格式转换为 Gemini 格式"""
        contents = []
        for msg in messages:
            role = msg["role"]
            if role == "system":
                contents.append({"role": "user", "parts": [msg["content"]]})
                contents.append({"role": "model", "parts": ["好的，我理解了。"]})
            elif role == "user":
                contents.append({"role": "user", "parts": [msg["content"]]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [msg["content"]]})
        return contents


class OllamaProvider(BaseProvider):
    """Ollama 本地模型 Provider"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")

    async def chat(self, messages: list[dict], **kwargs) -> str:
        import aiohttp
        model = kwargs.get("model", self.model)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json={"model": model, "messages": messages, "stream": False},
            ) as resp:
                data = await resp.json()
                return data["message"]["content"]

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        import aiohttp
        model = kwargs.get("model", self.model)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json={"model": model, "messages": messages, "stream": True},
            ) as resp:
                async for line in resp.content:
                    if line:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]

    async def embed(self, text: str, **kwargs) -> list[float]:
        import aiohttp
        model = kwargs.get("model", self.model)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/embed",
                json={"model": model, "input": text},
            ) as resp:
                data = await resp.json()
                return data["embeddings"][0]


# Provider 注册表
_PROVIDER_REGISTRY: dict[str, type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "google": GoogleProvider,
    "ollama": OllamaProvider,
}


def register_provider(name: str, provider_class: type[BaseProvider]):
    """注册自定义 Provider 类型"""
    _PROVIDER_REGISTRY[name] = provider_class


# ============================================================
#  ChatModel — 统一 LLM 客户端
# ============================================================

class ChatModel:
    """
    统一 LLM 调用接口

    使用方法：
        response = await chat_model.chat([{"role": "user", "content": "你好"}])
        response = await chat_model.chat([...], model="gemini")

        async for chunk in chat_model.chat_stream([...]):
            print(chunk, end="")

        vector = await chat_model.embed("一些文本")
    """

    def __init__(self, config: dict):
        self._config = config
        self._default = config.get("default_model", "deepseek")
        self._providers: dict[str, BaseProvider] = {}

    def _get_or_create_provider(self, name: str) -> BaseProvider:
        if name not in self._providers:
            provider_config = self._config.get("providers", {}).get(name)
            if not provider_config:
                raise ValueError(f"未配置的模型提供商: {name}")

            provider_type = provider_config.get("type", "openai")
            provider_class = _PROVIDER_REGISTRY.get(provider_type)
            if not provider_class:
                raise ValueError(f"不支持的 provider 类型: {provider_type}")

            self._providers[name] = provider_class(provider_config)
            logger.info(f"创建 LLM Provider: {name} ({provider_type})")

        return self._providers[name]

    def get_provider(self, name: str = None) -> BaseProvider:
        """获取指定 provider 实例"""
        return self._get_or_create_provider(name or self._default)

    async def chat(self, messages: list[dict], model: str = None,
                   temperature: float = None, max_tokens: int = None) -> str:
        """调用模型，返回完整响应"""
        provider = self._get_or_create_provider(model or self._default)
        return await provider.chat(
            messages, temperature=temperature, max_tokens=max_tokens
        )

    async def chat_stream(self, messages: list[dict], model: str = None,
                          temperature: float = None, max_tokens: int = None) -> AsyncIterator[str]:
        """流式调用"""
        provider = self._get_or_create_provider(model or self._default)
        async for chunk in provider.chat_stream(
            messages, temperature=temperature, max_tokens=max_tokens
        ):
            yield chunk

    async def embed(self, text: str, model: str = None) -> list[float]:
        """文本向量化"""
        provider = self._get_or_create_provider(model or self._default)
        return await provider.embed(text)


# ============================================================
#  ShortTermMemory — 短期记忆
# ============================================================

class ShortTermMemory:
    """
    对话上下文管理

    支持两种策略：
      sliding_window — 保留最近 N 条消息
      token_limit    — 按 token 数限制

    使用方法：
        short_term_memory.add("user", "你好")
        short_term_memory.add("assistant", "你好！")
        messages = short_term_memory.get_messages()
    """

    def __init__(self, config: dict):
        self._strategy = config.get("strategy", "sliding_window")
        self._max_messages = config.get("max_messages", 20)
        self._max_tokens = config.get("max_tokens", 4000)
        self._summary_on_overflow = config.get("summary_on_overflow", False)
        self._summary_model = config.get("summary_model")
        self._messages: list[dict] = []

    def add(self, role: str, content: str) -> None:
        """添加消息，自动应用策略"""
        self._messages.append({"role": role, "content": content})
        self._apply_strategy()

    def get_messages(self) -> list[dict]:
        """获取当前上下文"""
        return list(self._messages)

    def clear(self) -> None:
        """清空记忆"""
        self._messages.clear()

    def _apply_strategy(self):
        """应用溢出策略"""
        if self._strategy == "sliding_window":
            if len(self._messages) > self._max_messages:
                self._messages = self.on_overflow(self._messages)
        elif self._strategy == "token_limit":
            total = self._estimate_tokens()
            if total > self._max_tokens:
                self._messages = self.on_overflow(self._messages)

    def _estimate_tokens(self) -> int:
        """粗略估算 token 数（中文约 1.5 字/token，英文约 4 字符/token）"""
        total = 0
        for msg in self._messages:
            content = msg.get("content", "")
            # 简单估算
            cjk = sum(1 for c in content if '一' <= c <= '鿿')
            other = len(content) - cjk
            total += cjk * 1.5 + other * 0.25
        return int(total)

    def on_overflow(self, messages: list[dict]) -> list[dict]:
        """
        溢出处理 — 用户可重写自定义策略

        默认行为：
          sliding_window: 保留最近 max_messages 条
          token_limit: 保留最近一半
        """
        if self._strategy == "sliding_window":
            return messages[-self._max_messages:]
        elif self._strategy == "token_limit":
            # 保留一半
            half = len(messages) // 2
            return messages[-half:] if half > 0 else messages[-1:]
        return messages

    async def summarize(self) -> str:
        """摘要当前上下文（需要配置 chat_model）"""
        global _chat_model
        if _chat_model is None:
            raise RuntimeError("chat_model 未初始化，无法摘要")

        model = self._summary_model
        summary_prompt = [
            {"role": "system", "content": "请将以下对话历史压缩为简洁的摘要，保留关键信息。"},
            {"role": "user", "content": json.dumps(self._messages, ensure_ascii=False)},
        ]
        summary = await _chat_model.chat(summary_prompt, model=model)

        # 用摘要替换历史
        self._messages = [
            {"role": "system", "content": f"之前的对话摘要：{summary}"}
        ]
        return summary


# ============================================================
#  LongTermMemory — 长期记忆
# ============================================================

class LongTermMemory:
    """
    持久化记忆基类

    使用方法：
        await long_term_memory.remember("user_name", "小明")
        name = await long_term_memory.recall("user_name")
        await long_term_memory.forget("user_name")
    """

    def __init__(self, config: dict):
        self._namespace = config.get("namespace", "default")
        self._ttl = config.get("ttl", 0)

    def _ns_key(self, key: str) -> str:
        """添加命名空间前缀"""
        return f"memory:{self._namespace}:{key}"

    async def remember(self, key: str, value: Any, ttl: int = None) -> None:
        """存储记忆"""
        raise NotImplementedError

    async def recall(self, key: str) -> Any:
        """召回记忆"""
        raise NotImplementedError

    async def forget(self, key: str) -> None:
        """删除记忆"""
        raise NotImplementedError

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        """搜索相关记忆"""
        raise NotImplementedError

    async def list_keys(self, pattern: str = "*") -> list[str]:
        """列出所有记忆 key"""
        raise NotImplementedError


class RedisLongTermMemory(LongTermMemory):
    """Redis 后端长期记忆"""

    def __init__(self, config: dict):
        super().__init__(config)
        from .redis_cache import RedisClient
        self._client = RedisClient(
            url=config.get("redis_url", "redis://localhost:6379"),
            db=config.get("redis_db", 0),
            key_prefix=f"memory:{self._namespace}:",
        )

    async def remember(self, key: str, value: Any, ttl: int = None) -> None:
        actual_ttl = ttl if ttl is not None else (self._ttl if self._ttl > 0 else None)
        await self._client.set_json(key, value, ttl=actual_ttl)

    async def recall(self, key: str) -> Any:
        return await self._client.get_json(key)

    async def forget(self, key: str) -> None:
        await self._client.delete(key)

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        # Redis 不支持全文搜索，返回所有匹配 key 的值
        keys = await self._client.keys("*")
        results = []
        for k in keys[:limit]:
            value = await self._client.get_json(k)
            if value is not None:
                results.append({"key": k, "value": value})
        return results

    async def list_keys(self, pattern: str = "*") -> list[str]:
        return await self._client.keys(pattern)


class SQLiteLongTermMemory(LongTermMemory):
    """SQLite 后端长期记忆

    优先复用 mybatis 的数据库连接（如果已初始化），
    否则使用独立的 aiosqlite 连接。
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self._db_path = config.get("sqlite_path", "resource/db/memory.db")
        self._conn = None
        self._use_mybatis = False

    async def _get_conn(self):
        if self._conn is None:
            # 尝试复用 mybatis 的数据库连接
            try:
                from .mybatis.connection import get_database
                db = get_database()
                # databases 库的 execute 返回的是 Row，需要不同处理
                # 先检查 memory 表是否存在
                self._use_mybatis = True
                self._db = db
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS memory (
                        namespace TEXT,
                        key TEXT,
                        value TEXT,
                        created_at REAL DEFAULT (strftime('%s', 'now')),
                        PRIMARY KEY (namespace, key)
                    )
                """)
                return db
            except (RuntimeError, ImportError):
                # mybatis 未初始化，使用独立连接
                import aiosqlite
                os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
                self._conn = await aiosqlite.connect(self._db_path)
                await self._conn.execute("""
                    CREATE TABLE IF NOT EXISTS memory (
                        namespace TEXT,
                        key TEXT,
                        value TEXT,
                        created_at REAL DEFAULT (strftime('%s', 'now')),
                        PRIMARY KEY (namespace, key)
                    )
                """)
                await self._conn.commit()
        return self._db if self._use_mybatis else self._conn

    async def remember(self, key: str, value: Any, ttl: int = None) -> None:
        conn = await self._get_conn()
        data = json.dumps(value, ensure_ascii=False)
        if self._use_mybatis:
            await conn.execute(
                "INSERT OR REPLACE INTO memory (namespace, key, value) VALUES (:ns, :key, :val)",
                {"ns": self._namespace, "key": key, "val": data},
            )
        else:
            await conn.execute(
                "INSERT OR REPLACE INTO memory (namespace, key, value) VALUES (?, ?, ?)",
                (self._namespace, key, data),
            )
            await conn.commit()

    async def recall(self, key: str) -> Any:
        conn = await self._get_conn()
        if self._use_mybatis:
            row = await conn.fetch_one(
                "SELECT value FROM memory WHERE namespace = :ns AND key = :key",
                {"ns": self._namespace, "key": key},
            )
            return json.loads(row[0]) if row else None
        else:
            cursor = await conn.execute(
                "SELECT value FROM memory WHERE namespace = ? AND key = ?",
                (self._namespace, key),
            )
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None

    async def forget(self, key: str) -> None:
        conn = await self._get_conn()
        if self._use_mybatis:
            await conn.execute(
                "DELETE FROM memory WHERE namespace = :ns AND key = :key",
                {"ns": self._namespace, "key": key},
            )
        else:
            await conn.execute(
                "DELETE FROM memory WHERE namespace = ? AND key = ?",
                (self._namespace, key),
            )
            await conn.commit()

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        conn = await self._get_conn()
        if self._use_mybatis:
            rows = await conn.fetch_all(
                "SELECT key, value FROM memory WHERE namespace = :ns AND (key LIKE :q1 OR value LIKE :q2) LIMIT :lim",
                {"ns": self._namespace, "q1": f"%{query}%", "q2": f"%{query}%", "lim": limit},
            )
            return [{"key": row[0], "value": json.loads(row[1])} for row in rows]
        else:
            cursor = await conn.execute(
                "SELECT key, value FROM memory WHERE namespace = ? AND (key LIKE ? OR value LIKE ?) LIMIT ?",
                (self._namespace, f"%{query}%", f"%{query}%", limit),
            )
            results = []
            async for row in cursor:
                results.append({"key": row[0], "value": json.loads(row[1])})
            return results

    async def list_keys(self, pattern: str = "*") -> list[str]:
        conn = await self._get_conn()
        sql_pattern = pattern.replace("*", "%")
        if self._use_mybatis:
            rows = await conn.fetch_all(
                "SELECT key FROM memory WHERE namespace = :ns AND key LIKE :pat",
                {"ns": self._namespace, "pat": sql_pattern},
            )
            return [row[0] for row in rows]
        else:
            cursor = await conn.execute(
                "SELECT key FROM memory WHERE namespace = ? AND key LIKE ?",
                (self._namespace, sql_pattern),
            )
            results = []
            async for row in cursor:
                results.append(row[0])
            return results

    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None


# ============================================================
#  RAG — 检索增强生成
# ============================================================

class RAG:
    """
    检索增强生成

    使用方法：
        await rag.add_document("Pancake 是一个 Python 框架...")
        results = await rag.query("什么是 Pancake？")
        answer = await rag.ask("什么是 Pancake？")
    """

    def __init__(self, config: dict):
        self._config = config
        self._collection_name = config.get("collection", "pancake_docs")
        self._chunk_size = config.get("chunk_size", 500)
        self._chunk_overlap = config.get("chunk_overlap", 50)
        self._top_k = config.get("top_k", 5)
        self._persist_dir = config.get("persist_dir", "resource/db/chroma")
        self._embedding_provider = config.get("embedding_provider")
        self._embedding_model = config.get("embedding_model", "text-embedding-3-small")
        self._collection = None

    async def _get_collection(self):
        if self._collection is None:
            import chromadb
            os.makedirs(self._persist_dir, exist_ok=True)
            client = chromadb.PersistentClient(path=self._persist_dir)
            self._collection = client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"ChromaDB 集合: {self._collection_name}")
        return self._collection

    async def _get_embedding(self, text: str) -> list[float]:
        """获取文本向量"""
        global _chat_model
        if _chat_model is None:
            raise RuntimeError("chat_model 未初始化，无法生成向量")

        provider_name = self._embedding_provider
        return await _chat_model.embed(text, model=provider_name)

    def _chunk_text(self, text: str) -> list[str]:
        """文本分块"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self._chunk_size
            chunks.append(text[start:end])
            start += self._chunk_size - self._chunk_overlap
        return chunks

    async def add_document(self, text: str, metadata: dict = None) -> None:
        """添加文档（自动分块 + 向量化）"""
        collection = await self._get_collection()
        chunks = self._chunk_text(text)

        for i, chunk in enumerate(chunks):
            embedding = await self._get_embedding(chunk)
            doc_id = f"doc_{collection.count() + 1}_{i}"
            meta = {"chunk_index": i, "total_chunks": len(chunks)}
            if metadata:
                meta.update(metadata)

            collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[meta],
            )

        logger.info(f"添加文档: {len(chunks)} 个分块")

    async def add_documents(self, docs: list[dict]) -> None:
        """批量添加文档 [{"text": "...", "metadata": {...}}, ...]"""
        for doc in docs:
            await self.add_document(doc["text"], doc.get("metadata"))

    async def query(self, question: str, top_k: int = None) -> list[dict]:
        """检索相关文档"""
        collection = await self._get_collection()
        embedding = await self._get_embedding(question)
        k = top_k or self._top_k

        results = collection.query(
            query_embeddings=[embedding],
            n_results=k,
        )

        docs = []
        for i in range(len(results["ids"][0])):
            docs.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None,
            })
        return docs

    async def ask(self, question: str, model: str = None,
                  system_prompt: str = None) -> str:
        """RAG 问答（检索 + 生成）"""
        global _chat_model
        if _chat_model is None:
            raise RuntimeError("chat_model 未初始化，无法 RAG 问答")

        # 检索相关文档
        docs = await self.query(question)

        # 构建 prompt
        messages = self.build_prompt(question, docs, system_prompt)

        # 生成回答
        return await _chat_model.chat(messages, model=model)

    def build_prompt(self, question: str, context: list[dict],
                     system_prompt: str = None) -> list[dict]:
        """
        构建 prompt — 用户可重写自定义 RAG prompt 模板

        Args:
            question: 用户问题
            context: 检索到的文档列表
            system_prompt: 自定义 system prompt
        """
        context_text = "\n\n".join(
            f"[资料{i+1}] {doc['text']}" for i, doc in enumerate(context)
        )

        sys_prompt = system_prompt or (
            "你是一个智能助手。请根据以下参考资料回答用户的问题。"
            "如果资料中没有相关信息，请如实说明。\n\n"
            f"参考资料：\n{context_text}"
        )

        return [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": question},
        ]

    async def delete(self, where: dict = None) -> None:
        """删除文档"""
        collection = await self._get_collection()
        if where:
            collection.delete(where=where)
        else:
            # 删除所有
            all_ids = collection.get()["ids"]
            if all_ids:
                collection.delete(ids=all_ids)


# ============================================================
#  全局实例
# ============================================================

_chat_model: Optional[ChatModel] = None
_short_term_memory: Optional[ShortTermMemory] = None
_long_term_memory: Optional[LongTermMemory] = None
_rag: Optional[RAG] = None


def get_chat_model() -> Optional[ChatModel]:
    return _chat_model


def get_short_term_memory() -> Optional[ShortTermMemory]:
    return _short_term_memory


def get_long_term_memory() -> Optional[LongTermMemory]:
    return _long_term_memory


def get_rag() -> Optional[RAG]:
    return _rag


# ============================================================
#  插件 Main 类
# ============================================================

class Main(InitAction):
    """AI 模块插件主类"""

    init_order = 4  # redis 之后，web 之前

    def __init__(self):
        global _chat_model, _short_term_memory, _long_term_memory, _rag

        # 从扁平化的 YAML 键重建嵌套配置
        user_config = self._build_config_from_flat_keys()
        config = _deep_merge(_DEFAULT_CONFIG, user_config)

        # 递归解析所有 ${ENV_VAR} 占位符
        config = _resolve_env_recursive(config)

        # 创建 ChatModel
        _chat_model = ChatModel(config)

        # 创建 ShortTermMemory
        _short_term_memory = ShortTermMemory(config.get("memory", {}).get("short_term", {}))

        # 创建 LongTermMemory
        lt_config = config.get("memory", {}).get("long_term", {})
        backend = lt_config.get("backend", "sqlite")
        if backend == "redis":
            _long_term_memory = RedisLongTermMemory(lt_config)
        else:
            _long_term_memory = SQLiteLongTermMemory(lt_config)

        # 创建 RAG
        _rag = RAG(config.get("rag", {}))

        # 保存到 oven
        oven.pancake_other["chat_model"] = _chat_model
        oven.pancake_other["short_term_memory"] = _short_term_memory
        oven.pancake_other["long_term_memory"] = _long_term_memory
        oven.pancake_other["rag"] = _rag

    @staticmethod
    def _build_config_from_flat_keys() -> dict:
        """从 pancake_yaml 的扁平键重建嵌套配置

        YAML 中的 ai.default_model → pancake_yaml["ai.default_model"]
        需要重建为 {"ai": {"default_model": ...}}
        """
        result = {}
        for flat_key, value in oven.pancake_yaml.items():
            if not flat_key.startswith("ai."):
                continue
            parts = flat_key.split(".")
            # ai.providers.deepseek.type → ["ai", "providers", "deepseek", "type"]
            current = result
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            current[parts[-1]] = value
        return result.get("ai", {})

    @staticmethod
    def check():
        try:
            import openai  # noqa: F401
        except ImportError:
            logger.warning("openai 包未安装，请运行: pip install pancake[ai]")

    def build(self):
        logger.info("AI 模块构建完成")

    def loop_method(self):
        """测试连接"""
        if _chat_model:
            logger.info(f"AI 模块就绪，默认模型: {_chat_model._default}")


# ============================================================
#  注册到 oven
# ============================================================

oven.muffin_flour["ChatModel"] = ChatModel
oven.muffin_flour["ShortTermMemory"] = ShortTermMemory
oven.muffin_flour["LongTermMemory"] = LongTermMemory
oven.muffin_flour["RAG"] = RAG
oven.muffin_flour["register_provider"] = register_provider

oven.muffin_suger["chat_model"] = get_chat_model
oven.muffin_suger["short_term_memory"] = get_short_term_memory
oven.muffin_suger["long_term_memory"] = get_long_term_memory
oven.muffin_suger["rag"] = get_rag
