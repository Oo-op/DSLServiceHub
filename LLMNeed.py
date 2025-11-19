import json
import time
from typing import Dict, Any, List, Optional

class LLMClient:
    """LLM客户端，用于意图识别"""
    
    def __init__(self, api_key: str = None, model: str = "deepseek-chat"):
        """
        初始化LLM客户端
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        # 如果没有API密钥或安装requests失败，强制使用模拟模式
        self.use_mock = True  # 强制使用模拟模式避免依赖问题
        
    def recognize_intent(self, user_input: str, available_intents: List[str]) -> str:
        """
        识别用户输入的意图
        
        Args:
            user_input: 用户输入文本
            available_intents: 可用的意图列表
            
        Returns:
            识别出的意图字符串
        """
        return self._mock_intent_recognition(user_input, available_intents)
    
    def _mock_intent_recognition(self, user_input: str, available_intents: List[str]) -> str:
        """模拟意图识别（用于测试，无需API密钥）"""
        print(f"[模拟模式] 用户输入: {user_input}")
        print(f"[模拟模式] 可用意图: {available_intents}")
        
        # 简单的关键词匹配 - 针对故宫客服场景优化
        user_input_lower = user_input.lower()
        
        # 针对故宫客服的关键词映射
        intent_keywords = {
            "门票": ["门票", "票务", "买票", "票价", "票", "门票价格", "成人票", "学生票", "老人票"],
            "开放时间": ["时间", "开放", "几点", "开门", "关门", "营业", "开放时间", "几点开门", "几点关门"],
            "游玩攻略": ["攻略", "游玩", "怎么玩", "推荐", "路线", "必看", "景点", "游玩攻略", "旅游攻略"],
            "人工": ["人工", "客服", "转人工", "真人", "人工服务", "人工客服"],
            "预约方式": ["预约", "预订", "怎么预约", "预约方式", "如何预约"],
            "退出": ["退出", "结束", "再见", "拜拜", "quit", "exit", "结束对话"]
        }
        
        # 检查每个意图的关键词
        for intent, keywords in intent_keywords.items():
            if intent in available_intents:  # 只检查可用的意图
                for keyword in keywords:
                    if keyword in user_input_lower:
                        print(f"[模拟模式] 识别意图: {intent}")
                        return intent
        
        # 如果用户输入包含"门票"相关词汇但意图不在可用列表中，尝试匹配更具体的门票类型
        if "成人" in user_input_lower and "门票" in available_intents:
            return "门票"
        elif "学生" in user_input_lower and "门票" in available_intents:
            return "门票"
        elif "老人" in user_input_lower and "门票" in available_intents:
            return "门票"
            
        # 默认返回第一个可用意图
        default_intent = available_intents[0] if available_intents else "unknown"
        print(f"[模拟模式] 未匹配到关键词，返回默认意图: {default_intent}")
        return default_intent

# 配置管理类
class Config:
    """配置管理"""
    
    @staticmethod
    def load_api_key() -> str:
        """从配置文件或环境变量加载API密钥"""
        try:
            # 尝试从环境变量获取
            import os
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if api_key:
                return api_key
            
            # 尝试从配置文件获取
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("deepseek_api_key", "")
            except FileNotFoundError:
                return ""
                
        except Exception:
            return ""

# 测试函数
def test_llm_client():
    """测试LLM客户端"""
    
    # 可用的意图列表（根据故宫客服DSL定义）
    available_intents = ["门票", "开放时间", "游玩攻略", "人工", "预约方式", "退出"]
    
    # 创建LLM客户端（使用模拟模式）
    llm_client = LLMClient()
    
    # 测试用例 - 针对故宫客服场景
    test_cases = [
        "我想买门票",
        "故宫几点开门",
        "有什么好玩的推荐吗",
        "转人工客服",
        "怎么预约门票",
        "成人票多少钱",
        "学生有优惠吗",
        "老人免票吗",
        "退出系统",
        "我不知道该问什么"
    ]
    
    print("=== LLM客户端测试 ===")
    for user_input in test_cases:
        intent = llm_client.recognize_intent(user_input, available_intents)
        print(f"用户: '{user_input}' → 意图: '{intent}'")
        print("-" * 40)

if __name__ == "__main__":
    test_llm_client()