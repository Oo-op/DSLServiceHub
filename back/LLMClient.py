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
        
        version_map = {
            "v3.5": ("wss://spark-api.xf-yun.com/v3.5/chat", "generalv3.5"),
            "max": ("wss://spark-api.xf-yun.com/v3.5/chat", "generalv3.5"), # 修正 max 指向
            "pro": ("wss://spark-api.xf-yun.com/v3.1/chat", "generalv3"),
        }
        
        if spark_version not in version_map:
            # 默认回退到 v3.5
            self.spark_url, self.domain = version_map["v3.5"]
        else:
            self.spark_url, self.domain = version_map[spark_version]
            
        self.host = urlparse(self.spark_url).netloc
        self.path = urlparse(self.spark_url).path

    def _get_auth_url(self) -> str:
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.path} HTTP/1.1"
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        v = {"authorization": authorization, "date": date, "host": self.host}
        return self.spark_url + '?' + urlencode(v)

    def recognize_intent(self, user_input: str, available_intents: List[str]) -> Optional[str]:
        intents_str = ", ".join([f"'{i}'" for i in available_intents])
        system_content = f"""你是一个故宫博物院客服系统的意图分类器。
请将用户的输入分类到以下标准意图之一：[{intents_str}]。

分类逻辑参考：
- 问价格、票种 -> '门票'
- 问怎么买、哪里买 -> '购票'
- 问带什么、身份证 -> '物品'
- 问几点开门、闭馆 -> '时间'
- 问怎么玩、路线 -> '游玩攻略'

要求：
1. 仅返回意图名称，不要包含任何标点或其他文字。
2. 如果无法匹配，返回 'unknown'。
"""
        
        result_container = []
        completed = threading.Event()

        def on_message(ws, message):
            try:
                data = json.loads(message)
                code = data['header']['code']
                if code != 0:
                    print(f'[API Error] code={code}, msg={data["header"]["message"]}')
                    ws.close()
                else:
                    choices = data["payload"]["choices"]
                    if "text" in choices:
                        content = choices["text"][0]["content"]
                    else:
                        content = ""
                    result_container.append(content)
                    if choices.get("status") == 2:
                        completed.set()
                        ws.close()
            except Exception as e:
                print(f"Message Error: {e}")
                completed.set()

        def on_error(ws, error):
            print(f"WebSocket Error: {error}")
            completed.set()

        def on_close(ws, *args):
            completed.set()

        def on_open(ws):
            data = {
                "header": {"app_id": self.app_id},
                "parameter": {"chat": {"domain": self.domain, "temperature": 0.1, "max_tokens": 20}},
                "payload": {"message": {"text": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": f"用户输入：{user_input}"}
                ]}}
            }
            ws.send(json.dumps(data))

        ws_url = self._get_auth_url()
        # 禁用 SSL 验证以避免某些环境下的证书问题
        ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
        
        thread = threading.Thread(target=lambda: ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}))
        thread.daemon = True
        thread.start()
        
        completed.wait(timeout=10) # 10秒超时
        if ws.sock and ws.sock.connected:
            ws.close()

        if result_container:
            full_response = "".join(result_container).strip().replace('"', '').replace("'", "")
            print(f"  [AI思考] '{user_input}' => '{full_response}'")
            
            # 1. 精确匹配
            if full_response in available_intents:
                return full_response
            # 2. 包含匹配 
            for intent in available_intents:
                if intent in full_response:
                    return intent
            return None
        else:
            return None