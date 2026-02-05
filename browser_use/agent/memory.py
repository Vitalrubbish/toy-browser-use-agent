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