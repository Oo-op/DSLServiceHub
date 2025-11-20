# LLMNeed.py (无人工版本)

import json
from typing import List, Optional

class LLMClient:
    """LLM客户端，用于意图识别（当前为模拟模式）"""
    
    def __init__(self, api_key: str = None, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        # 强制使用模拟模式，以确保代码无需额外配置即可运行
        self.use_mock = True
        print("LLMClient initialized in MOCK mode (Human-agent transfer is disabled).")
        
    def recognize_intent(self, user_input: str, available_intents: List[str]) -> Optional[str]:
        """
        识别用户输入的意图。
        """
        if self.use_mock:
            return self._mock_intent_recognition(user_input, available_intents)
        else:
            # 此处可以实现真实的API调用
            print("Real LLM API call is not implemented.")
            return self._mock_intent_recognition(user_input, available_intents)
    
    def _mock_intent_recognition(self, user_input: str, available_intents: List[str]) -> Optional[str]:
        """模拟意图识别（用于测试，无需API密钥）"""
        user_input_lower = user_input.lower()
        
        # 关键词到意图的映射 (已移除"人工")
        intent_keywords = {
            "门票": ["门票", "票务", "买票", "票价", "票"],
            "开放时间": ["时间", "开放", "几点", "开门", "关门"],
            "游玩攻略": ["攻略", "游玩", "怎么玩", "推荐", "路线"],
            "必看景点": ["景点", "必看", "太和殿", "乾清宫", "御花园"],
            "预约方式": ["预约", "预订", "怎么预约"],
            "成人票": ["成人票", "成人", "大人"],
            "学生票": ["学生票", "学生"],
            "老人票": ["老人票", "老人", "老年"],
            "没有": ["没有", "不用", "不需要", "没了"],
            "退出": ["退出", "结束", "再见", "拜拜"],
        }
        
        # 优先匹配可用意图
        for intent in available_intents:
            if intent in intent_keywords:
                for keyword in intent_keywords[intent]:
                    if keyword in user_input_lower:
                        print(f"[模拟识别] 用户输入 '{user_input}' -> 匹配关键词 '{keyword}' -> 识别意图: {intent}")
                        return intent
        
        # 如果没有匹配到，则返回 None，让解释器决定如何处理（通常是走Default分支）
        print(f"[模拟识别] 用户输入 '{user_input}' -> 未在可用意图 {available_intents} 中匹配到关键词。")
        return None