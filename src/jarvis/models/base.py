from abc import ABC, abstractmethod
from typing import Dict, List

class BaseModel(ABC):
    """大语言模型基类"""
    
    @abstractmethod
    def chat(self, message: str) -> str:
        """执行对话"""
        pass 

    def reset(self):
        """重置模型"""
        pass
        