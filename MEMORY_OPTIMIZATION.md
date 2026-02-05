# Browser-Use 记忆模块优化指南 (Sentence-Transformers 版)

本文档旨在指导如何使用 `sentence-transformers` 替代简单的关键词匹配，为 Browser-Use Agent 实现基于语义向量的记忆检索功能。

## 1. 环境安装

本项目使用 `uv` 进行依赖管理。请在项目根目录下运行以下命令安装 `sentence-transformers`：

```bash
uv add sentence-transformers
# 或者如果不使用 pyproject.toml 管理，仅在环境中安装：
# uv pip install sentence-transformers
```

这将自动安装 `sentence-transformers` 及其依赖 (如 `torch`, `transformers`, `huggingface-hub` 等)。

## 2. 基础使用示例

以下是一个简单的 Python 脚本，演示如何将自然语言任务转换为向量，并计算余弦相似度。

```python
from sentence_transformers import SentenceTransformer, util

# 1. 加载预训练模型
# 'all-MiniLM-L6-v2' 是一个轻量且效果优秀的通用模型，非常适合 CPU 运行
print("正在加载模型...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. 准备数据
stored_tasks = [
    "在亚马逊上查找 iPhone 15 的价格",
    "登录 Gmail 并查看最新邮件",
    "查询北京明天的天气"
]
new_task = "帮我看看 iPhone 15 多少钱"

# 3. 向量化 (Encoding)
print("正在计算向量...")
stored_embeddings = model.encode(stored_tasks, convert_to_tensor=True)
new_task_embedding = model.encode(new_task, convert_to_tensor=True)

# 4. 计算相似度 (Cosine Similarity)
# util.cos_sim 返回一个矩阵，这里我们取第一个结果
cosine_scores = util.cos_sim(new_task_embedding, stored_embeddings)[0]

# 5. 输出结果
print(f"当前任务: {new_task}")
for i, score in enumerate(cosine_scores):
    print(f"与 '{stored_tasks[i]}' 的相似度: {score:.4f}")

# 预期输出: 与 '在亚马逊上查找 iPhone 15 的价格' 的相似度最高 (>0.7)
```

## 3. 具体的优化方案

我们将修改 `browser_use/agent/memory.py` 中的 `MemoryService` 类。

### 优化策略

1.  **模型加载**: 在 `MemoryService` 初始化时加载模型。为了避免每次启动都下载，`sentence-transformers` 会自动利用本地缓存。
2.  **向量缓存**:
    *   **写入时**: 当保存新的 MemoryItem 时，立即计算其 `task` 的向量并存储（或者在加载时计算）。为了保持 JSON 可读性，我们可以在运行时计算向量并保存在内存中，或者将向量序列化存储（稍微复杂，暂不推荐存入 JSON）。
    *   **简单方案**: 每次启动服务加载 JSON 后，在内存中批量计算一次所有历史任务的向量。由于历史记录通常不会达到百万级，这个操作非常快。
3.  **检索逻辑**: 使用 `util.cos_sim` 替代 Jaccard 相似度。

### 代码实现

请参考以下代码修改 `browser_use/agent/memory.py`。

#### 修改后的 `browser_use/agent/memory.py`

```python
import json
import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import time

# 新增依赖
from sentence_transformers import SentenceTransformer, util
import torch

logger = logging.getLogger(__name__)

@dataclass
class MemoryItem:
    task: str
    actions: List[Dict[str, Any]]
    timestamp: float

class MemoryService:
    def __init__(self, storage_path: str = "agent_memory.json", model_name: str = 'all-MiniLM-L6-v2'):
        self.storage_path = storage_path
        
        # 1. 加载模型
        logger.info(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        
        # 2. 加载数据
        self._memory: List[MemoryItem] = self._load_memory()
        
        # 3. 初始化向量缓存 (Tensor)
        self._memory_embeddings = None
        self._refresh_embeddings()

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

    def _refresh_embeddings(self):
        """刷新内存中的向量索引"""
        if not self._memory:
            self._memory_embeddings = None
            return
            
        tasks = [item.task for item in self._memory]
        # convert_to_tensor=True 返回 PyTorch tensor，便于 GPU/CPU 加速计算
        self._memory_embeddings = self.model.encode(tasks, convert_to_tensor=True)

    def add_memory(self, task: str, actions: List[Dict[str, Any]]):
        """保存一次成功的执行记录"""
        # 简单去重逻辑...
        item = MemoryItem(task=task, actions=actions, timestamp=time.time())
        self._memory.append(item)
        self._save_memory()
        
        # 增量更新向量 (简单起见，这里直接全部重新计算，数据量大时可优化为只append新向量)
        self._refresh_embeddings()
        
        logger.info(f"💾 Memory saved for task: {task[:50]}...")

    def retrieve_relevant_memory(self, current_task: str, threshold: float = 0.6) -> Optional[MemoryItem]:
        """
        基于语义向量检索最相似的任务
        """
        if not self._memory or self._memory_embeddings is None:
            return None

        # 1. 计算当前任务的向量
        query_embedding = self.model.encode(current_task, convert_to_tensor=True)

        # 2. 计算余弦相似度
        # cos_sim 返回 shape 为 (1, N) 的矩阵
        cos_scores = util.cos_sim(query_embedding, self._memory_embeddings)[0]

        # 3. 找到最佳匹配
        best_score_idx = torch.argmax(cos_scores).item()
        best_score = cos_scores[best_score_idx].item()
        
        if best_score >= threshold:
            best_match = self._memory[best_score_idx]
            logger.info(f"🧠 Detailed memory recalled (Score: {best_score:.4f}) | Task: {best_match.task}")
            return best_match
        
        return None
```

## 4. 进阶优化建议

1.  **持久化向量**: 如果 `agent_memory.json` 变得很大，每次启动重新计算向量会很慢。可以将向量保存为 `.pt` (PyTorch) 或 `.npy` (NumPy) 文件，与 JSON 共同加载。
2.  **向量数据库**: 当记忆条目超过 10,000 条时，建议迁移到 **ChromaDB** 或 **FAISS**，它们专门针对向量检索进行了索引优化。
3.  **模型微调**: 通用的 `all-MiniLM-L6-v2` 足以应付大多数情况。如果涉及特定领域的专业术语，可以考虑使用更强大的模型 (如 `all-mpnet-base-v2`) 或使用自己的数据微调模型。
