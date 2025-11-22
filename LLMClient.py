# 文件名: LLMClient.py

import json
import hashlib
import base64
import hmac
from urllib.parse import urlencode, urlparse
import ssl
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time
import websocket
from typing import List, Optional
import threading

class LLMClient:
    """LLM客户端，用于意图识别（使用讯飞星火 API）"""

    def __init__(self, app_id: str, api_key: str, api_secret: str, spark_version: str = "v3.5"):
        if not all([app_id, api_key, api_secret]):
            raise ValueError("APP_ID, API_KEY, 和 API_SECRET 都不能为空")

        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        
        # 根据最新讯飞星火版本更新映射
        # 在 LLMClient.py 中更新版本映射
        version_map = {
        "v3.5": ("wss://spark-api.xf-yun.com/v3.5/chat", "generalv3.5"),
        "lite": ("wss://spark-api.xf-yun.com/v3.1/chat", "generalv3"),
        "pro": ("wss://spark-api.xf-yun.com/v3.1/chat", "generalv3"),
        "max": ("wss://spark-api.xf-yun.com/v3.1/chat", "generalv3"),
        "ultra": ("wss://spark-api.xf-yun.com/v3.1/chat", "generalv3"),
        "v3.0": ("wss://spark-api.xf-yun.com/v3.1/chat", "generalv3"),
        }
        
        
        if spark_version not in version_map:
            raise ValueError(f"不支持的星火版本: {spark_version}，可用版本: {list(version_map.keys())}")
            
        self.spark_url, self.domain = version_map[spark_version]
        self.host = urlparse(self.spark_url).netloc
        self.path = urlparse(self.spark_url).path
        print(f"LLMClient 初始化成功，使用讯飞星火 {spark_version}。")
        print(f"API地址: {self.spark_url}, Domain: {self.domain}")

    def _get_auth_url(self) -> str:
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = f"host: {self.host}\n"
        signature_origin += f"date: {date}\n"
        signature_origin += f"GET {self.path} HTTP/1.1"
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        v = {"authorization": authorization, "date": date, "host": self.host}
        return self.spark_url + '?' + urlencode(v)

    def recognize_intent(self, user_input: str, available_intents: List[str]) -> Optional[str]:
        system_content = f"""你是一个故宫博物院客服系统的意图分类器。请严格分析用户输入并分类到以下意图之一：
可用意图列表：{', '.join(available_intents)}

分类规则：
1. 只返回意图名称，不要任何解释或多余的文字。
2. 如果用户输入明显匹配某个意图，返回对应的意图名称。
3. 如果用户输入与任何意图都不匹配，或者意图不明确，返回 "unknown"。
4. 确保返回的意图名称与列表中的完全一致。
"""
        result_container = []
        completed = threading.Event()

        def on_message(ws, message):
            try:
                data = json.loads(message)
                code = data['header']['code']
                if code != 0:
                    print(f'[星火API错误] code={code}, sid={data["header"]["sid"]}, message={data["header"]["message"]}')
                    ws.close()
                else:
                    content = data["payload"]["choices"]["text"][0]["content"]
                    result_container.append(content)
                    if data["payload"]["choices"]["status"] == 2: 
                        ws.close()
            except Exception as e: 
                print(f"[星火API] 处理消息时出错: {e}")
            finally: 
                completed.set()

        def on_error(ws, error):
            print(f"[星火API] WebSocket错误: {error}")
            completed.set()

        def on_close(ws, close_status_code, close_msg):
            print(f"[星火API] 连接关闭，状态码: {close_status_code}, 消息: {close_msg}")
            completed.set()

        def on_open(ws):
            data = {
                "header": {"app_id": self.app_id},
                "parameter": {"chat": {"domain": self.domain, "temperature": 0.1, "max_tokens": 50}},
                "payload": {"message": {"text": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": f"用户输入：\"{user_input}\""}
                ]}}
            }
            ws.send(json.dumps(data))
        
        try:
            ws_url = self._get_auth_url()
            print(f"[星火API] 连接URL: {ws_url}")
            
            ws = websocket.WebSocketApp(ws_url, 
                                      on_message=on_message, 
                                      on_error=on_error, 
                                      on_close=on_close, 
                                      on_open=on_open)
            
            thread = threading.Thread(target=lambda: ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}))
            thread.daemon = True
            thread.start()
            
            completed.wait(timeout=15)
            
            if ws.sock and ws.sock.connected: 
                ws.close()

            if result_container:
                full_response = "".join(result_container).strip().replace('"', '')
                print(f"[星火识别] 用户: '{user_input}' -> AI识别结果: '{full_response}'")
                return full_response if full_response in available_intents else None
            else:
                print("[星火识别] 未收到有效API响应或超时。")
                return None
        except Exception as e:
            print(f"[星火识别] API调用异常: {e}")
            return None