# 文件名: test_stubs.py
from typing import List, Optional
from unittest.mock import Mock

class LLMClientStub:
    """LLMClient 的测试桩，模拟AI意图识别"""
    def __init__(self):
        # 更新意图映射，与测试DSL脚本的关键词保持一致
        self.intent_mapping = {
            "怎么买票": "购票",
            "哪里买票": "购票", 
            "门票价格": "门票",
            "成人票多少钱": "门票",
            "开放时间": "时间",
            "几点开门": "时间",
            "要带什么": "物品",
            "需要证件吗": "物品",
            "游玩路线": "游玩攻略",
            "推荐景点": "游玩攻略",
            # 添加更多映射
            "买票": "购票",
            "怎么买": "购票",
            "需要带什么": "物品",
            "时间": "时间",
            "门票": "门票"
        }
    
    def recognize_intent(self, user_input: str, available_intents: List[str]) -> Optional[str]:
        """模拟意图识别"""
        #print(f"[Stub Debug] 输入: '{user_input}', 可用意图: {available_intents}")
        
        # 精确匹配
        intent = self.intent_mapping.get(user_input)
        if intent and intent in available_intents:
            #print(f"[Stub Debug] 精确匹配到意图: {intent}")
            return intent
        
        # 关键词匹配
        for keyword, mapped_intent in self.intent_mapping.items():
            if keyword in user_input and mapped_intent in available_intents:
                #print(f"[Stub Debug] 关键词匹配: '{keyword}' -> '{mapped_intent}'")
                return mapped_intent
        
        #print("[Stub Debug] 未匹配到任何意图")
        return None

class DSLScriptStub:
    """DSL脚本测试桩"""
    
    @staticmethod
    def get_test_dsl():
        """用于测试的DSL脚本 - 与桩的意图映射保持一致"""
        return """
Step welcome
  Speak "您好，请问有什么可以帮您？"
  Listen 5, 30
  Branch "门票", ticket_info
  Branch "购票", how_to_buy
  Branch "时间", time_info
  Branch "物品", what_to_bring
  Branch "游玩攻略", play_guide
  Default default_proc

Step ticket_info
  Speak "门票信息：成人票60元"
  Speak "请问还有其他问题吗？"
  Listen 5, 30
  Branch "门票", ticket_info
  Branch "购票", how_to_buy
  Branch "时间", time_info
  Default default_proc

Step how_to_buy
  Speak "购票方式：请通过官方小程序预约"
  Speak "请问还有其他问题吗？"
  Listen 5, 30
  Branch "门票", ticket_info
  Branch "购票", how_to_buy
  Branch "时间", time_info
  Default default_proc

Step time_info
  Speak "开放时间：8:30-17:00"
  Speak "请问还有其他问题吗？"
  Listen 5, 30
  Branch "门票", ticket_info
  Branch "购票", how_to_buy
  Branch "时间", time_info
  Default default_proc

Step what_to_bring
  Speak "需要携带身份证等有效证件"
  Speak "请问还有其他问题吗？"
  Listen 5, 30
  Branch "门票", ticket_info
  Branch "购票", how_to_buy
  Branch "时间", time_info
  Default default_proc

Step play_guide
  Speak "推荐游览路线：沿中轴线参观"
  Speak "请问还有其他问题吗？"
  Listen 5, 30
  Branch "门票", ticket_info
  Branch "购票", how_to_buy
  Branch "时间", time_info
  Default default_proc

Step default_proc
  Speak "抱歉，我不太理解"
  Speak "请问还有其他问题吗？"
  Listen 5, 30
  Branch "门票", ticket_info
  Branch "购票", how_to_buy
  Branch "时间", time_info
  Default default_proc
"""