# Browser-Use 记忆模块设计与实现指南

本文档详细介绍了如何为 `browser-use` Agent 添加长短期记忆功能。该模块旨在通过记录过去成功的任务路径，在遇到类似用户需求时提供“即席学习 (Few-Shot Learning)”的上下文，从而提高 Agent 的执行效率和成功率。

## 1. 设计思路 (Design Logic)

我们的记忆模块将遵循 **"Retrieve-and-Generate" (RAG)** 的设计模式，具体针对 Agent 的行为轨迹 (Trajectory)。

### 核心流程
1.  **存储 (Memorize)**: 当 Agent **成功** 完成一个任务后，系统提取该任务的 **User Task** (用户指令) 和 **Successful Actions** (成功的操作序列)，将其结构化存储。
2.  **检索 (Recall)**: 在新任务开始前，系统计算新任务与历史任务的语义相似度 (Semantic Similarity)。
3.  **复用 (Reuse)**: 如果找到相似的历史任务，将其作为 **Reference Trajectory** (参考轨迹) 注入到 Agent 的 **System Prompt** 中。Agent 会收到提示：“类似的很多任务是这样解决的：[步骤...]，请参考这个思路。”

### 数据结构
我们需要存储的最小单元 (Memory Unit) 包含：
*   `task_query`: 用户的原始指令 (用于检索匹配)。
*   `trajectory`: 清清洗后的动作序列 (去除冗余的错误尝试，只保留通向成功的路径)。
*   `metadata`: 执行时间、成功率等。

---

## 2. 代码实现方案

我们需要新增一个文件来管理记忆逻辑，并修改 Agent 的核心服务代码来挂载这个模块。

### 步骤 1: 创建记忆服务模块

新建文件: `browser_use/agent/memory.py`

我们可以先实现一个基于本地 JSON 文件的简单版本。如果生产环境使用，建议替换为 ChromaDB 或 FAISS。

```python
import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class MemoryItem:
    task: str
    actions: List[Dict[str, Any]]
    timestamp: float

class MemoryService:
    def __init__(self, storage_path: str = "agent_memory.json"):
        self.storage_path = storage_path
        self._memory: List[MemoryItem] = self._load_memory()

    def _load_memory(self) -> List[MemoryItem]:
        if not os.path.exists(self.storage_path):
            return []
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [MemoryItem(**item) for item in data]
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
            return []

    def _save_memory(self):
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(m) for m in self._memory], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def add_memory(self, task: str, actions: List[Dict[str, Any]]):
        """保存一次成功的执行记录"""
        # 简单去重：如果完全一样的任务已存在，通过比较动作长度或时间更新（这里简化为直接追加）
        import time
        item = MemoryItem(task=task, actions=actions, timestamp=time.time())
        self._memory.append(item)
        self._save_memory()
        logger.info(f"💾 Memory saved for task: {task[:50]}...")

    def retrieve_relevant_memory(self, current_task: str, threshold: float = 0.5) -> Optional[MemoryItem]:
        """
        检索最相似的历史任务。
        注意：此处为了演示使用了简单的关键词重合度 (Jaccard Similarity)。
        生产环境请替换为 OpenAI Embeddings 或 Sentence-Transformers 计算余弦相似度。
        """
        best_match = None
        best_score = 0.0

        current_tokens = set(current_task.lower().split())

        for item in self._memory:
            item_tokens = set(item.task.lower().split())
            intersection = current_tokens.intersection(item_tokens)
            union = current_tokens.union(item_tokens)
            
            if not union:
                continue
                
            score = len(intersection) / len(union)
            
            if score > best_score:
                best_score = score
                best_match = item

        if best_score >= threshold and best_match:
            logger.info(f"🧠 Detailed memory recalled (Score: {best_score:.2f})")
            return best_match
        
        return None
```

### 步骤 2: 修改 Agent 服务以集成记忆

我们需要修改 `browser_use/agent/service.py`。主要改动点有两个：
1.  **初始化**: 加载 MemoryService。
2.  **运行前 (Pre-run)**: 检索记忆并注入 System Prompt。
3.  **运行后 (Post-run)**: 如果任务成功，保存记忆。

**修改文件**: `browser_use/agent/service.py`

#### 2.1 引入模块和初始化

在文件头部引入我们刚写的类，并在 `__init__` 中初始化它。

```python
# ... existing imports ...
from browser_use.agent.memory import MemoryService  # 新增引用

class Agent(Generic[Context, AgentStructuredOutput]):
    def __init__(
        self,
        # ... existing args ...
        use_memory: bool = False, # 新增参数开关
        memory_file: str = "agent_memory.json", # 新增参数路径
        # ... existing args ...
    ):
        # ... existing init code ...
        
        # 初始化记忆模块
        self.use_memory = use_memory
        self.memory_service = MemoryService(storage_path=memory_file) if use_memory else None
```

#### 2.2 注入记忆到 Prompt (修改 `run` 方法)

我们需要在 `run` 方法的一开始检索记忆，并将其添加到 `extend_system_message` 中。

```python
    async def run(
        self,
        max_steps: int = 100,
        # ...
    ) -> AgentHistoryList[AgentStructuredOutput]:
        
        # === MEMORY RETRIEVAL START ===
        if self.use_memory and self.memory_service:
            relevant_memory = self.memory_service.retrieve_relevant_memory(self.task)
            if relevant_memory:
                # 将过去的经验格式化为文本
                memory_text = (
                    f"\n\n=========== MEMORY RECALL ===========\n"
                    f"You have solved a similar task before provided below.\n"
                    f"User Task: {relevant_memory.task}\n"
                    f"Successful Action Sequence used:\n"
                )
                for idx, action in enumerate(relevant_memory.actions):
                    memory_text += f"{idx+1}. {str(action)}\n"
                memory_text += "You may use this as a reference but adapt to the current page state.\n"
                memory_text += "=====================================\n"
                
                # 注入到 extend_system_message
                if self.settings.extend_system_message:
                    self.settings.extend_system_message += memory_text
                else:
                    self.settings.extend_system_message = memory_text
        # === MEMORY RETRIEVAL END ===
        
        # ... 原有的 run 代码 ...
```

#### 2.3 保存成功的记忆 (修改 `run` 方法末尾)

在任务循环结束且判断为成功后，记录数据。

```python
        # ... inside the run Loop, after is_done check ...
        
        if is_done:
            # Agent has marked the task as done
            
            # === MEMORY SAVE START ===
            if self.use_memory and self.memory_service and self.history.is_successful():
                # 提取成功的动作序列 (简化版：提取所有动作，生产环境可能需要过滤 failed actions)
                actions_to_save = []
                for result in self.history.action_results():
                     # 这里的逻辑通过 history 对象获取 executed actions
                     # 假设我们可以从 history 中反向构建出 params
                     pass 
                
                # 更简单的获取方式：遍历 history.model_actions()
                model_actions = self.history.model_actions()
                # 过滤掉 None 或者无效步骤
                clean_actions = [a.model_dump() for a in model_actions if a]
                
                self.memory_service.add_memory(self.task, clean_actions)
            # === MEMORY SAVE END ===

            if self._demo_mode_enabled and self.history.history:
                 # ... existing code ...
```

---

## 3. 增强：如何实现更高级的检索

上述代码使用的是简单的文本匹配。为了让 Agent 真正理解“我要买票”和“帮我预订车票”是相似任务，你需要引入 **Vector Database**。

**推荐升级路径**:
1.  **Embeddings**: 使用 `sentence-transformers` (开源免费) 或 `OpenAI Embeddings API` 将 `task` 转化为向量。
2.  **Vector Store**: 使用 `chromadb` (轻量本地) 存储向量。
3.  **Logic**:
    *   `save_memory`: `chroma_client.add(documents=[task], metadatas=[json.dumps(actions)], ids=[id])`
    *   `retrieve`: `results = chroma_client.query(query_texts=[current_task])`

## 4. 总结

通过以上两步修改，你的 Agent 就拥有了初步的“大脑皮层”。

1.  **`browser_use/agent/memory.py`**: 负责记忆的物理存储和算法检索。
2.  **`browser_use/agent/service.py`**: 负责在生命周期的关键节点（开始前、结束后）调用记忆服务。

这种方式是非侵入式的，不需要修改 Prompt Template 文件，而是动态地将记忆追加 (Append) 到系统提示中，类似于 RAG 的做法，效果通常很好且稳定。