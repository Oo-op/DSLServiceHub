import json
import requests
from typing import List, Optional

class LLMClient:
    """LLM客户端，用于意图识别（仅支持真实API）"""
    
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        if not api_key:
            raise ValueError("API密钥不能为空，请提供有效的DeepSeek API密钥")
            
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        
        print("LLMClient initialized with real DeepSeek API.")
    
    def recognize_intent(self, user_input: str, available_intents: List[str]) -> Optional[str]:
        """
        识别用户输入的意图。
        """
        return self._real_intent_recognition(user_input, available_intents)
    
    def _real_intent_recognition(self, user_input: str, available_intents: List[str]) -> Optional[str]:
        """使用真实API进行意图识别"""
        try:
            # 构建系统提示词
            system_prompt = f"""你是一个故宫博物院客服系统的意图识别助手。请分析用户的输入，判断其意图属于以下哪个类别：

可用意图：{', '.join(available_intents)}

请严格按照以下规则处理：
1. 只返回意图名称，不要返回其他任何内容
2. 如果用户的输入明显匹配某个意图，返回该意图名称
3. 如果无法确定意图，返回 "unknown"
4. 确保返回的意图名称必须完全匹配上述可用意图列表中的名称

示例：
用户输入："门票多少钱" -> 返回："门票"
用户输入："几点开门" -> 返回："开放时间"
用户输入："有什么好玩的" -> 返回："游玩攻略"
用户输入："不知道怎么买票" -> 返回："购票"
用户输入："需要带什么东西" -> 返回："需要带什么"
用户输入："我不需要帮助了" -> 返回："没有"
用户输入："再见" -> 返回："退出"

现在请分析用户输入："{user_input}"
"""

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                "temperature": 0.1,
                "max_tokens": 10
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            intent = result["choices"][0]["message"]["content"].strip()
            
            print(f"[API识别] 用户输入 '{user_input}' -> API返回: '{intent}'")
            
            # 验证返回的意图是否在可用意图中
            if intent in available_intents:
                return intent
            elif intent == "unknown":
                return None
            else:
                print(f"[API识别] API返回了不在可用列表中的意图: '{intent}'")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"[API识别] API调用失败: {e}")
            return None
        except Exception as e:
            print(f"[API识别] 处理API响应时出错: {e}")
            return None