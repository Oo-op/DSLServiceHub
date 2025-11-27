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
# 加密相关：hashlib, base64, hmac - 用于API认证签名
# 网络相关：urlencode, urlparse, ssl, websocket - 用于WebSocket连接
# 时间相关：datetime, mktime, format_date_time - 用于时间戳生成
# 并发：threading - 用于异步处理WebSocket消息

class LLMClient:
    """LLM客户端，用于意图识别（使用讯飞星火 API）"""
    
    def __init__(self, app_id: str, api_key: str, api_secret: str, spark_version: str = "v3.5"):
        if not all([app_id, api_key, api_secret]):
            raise ValueError("APP_ID, API_KEY, 和 API_SECRET 都不能为空")
        
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        
        # 版本映射表：不同模型版本对应的WebSocket地址和领域参数
        version_map = {
            "v3.5": ("wss://spark-api.xf-yun.com/v3.5/chat", "generalv3.5"),
            "max": ("wss://spark-api.xf-yun.com/v3.5/chat", "generalv3.5"),  # max版本指向v3.5
            "pro": ("wss://spark-api.xf-yun.com/v3.1/chat", "generalv3"),
        }
        
        # 确定模型地址和领域
        if spark_version not in version_map:
            self.spark_url, self.domain = version_map["v3.5"]  # 默认使用v3.5
        else:
            self.spark_url, self.domain = version_map[spark_version]
        
        # 解析主机和路径
        parsed_url = urlparse(self.spark_url)
        self.host = parsed_url.netloc
        self.path = parsed_url.path

    def _get_auth_url(self) -> str:
        """生成带认证信息的WebSocket连接URL"""
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))  # 格式化时间
        
        # 构建签名原始字符串
        signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.path} HTTP/1.1"
        # 计算HMAC-SHA256签名
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        # 签名Base64编码
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        # 构建认证信息
        authorization_origin = (
            f'api_key="{self.api_key}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature_sha_base64}"'
        )
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        # 拼接最终URL
        params = {"authorization": authorization, "date": date, "host": self.host}
        return f"{self.spark_url}?{urlencode(params)}"

    def recognize_intent(self, user_input: str, available_intents: List[str]) -> Optional[str]:
        """
        识别用户输入的意图
        """
        # 构建系统提示词
        intents_str = ", ".join([f"'{i}'" for i in available_intents])
        system_content = f"""你是一个故宫博物院客服系统的意图分类器。
请将用户的输入分类到以下标准意图之一：[{intents_str}]。

分类逻辑参考：
问价格、票种 -> '门票'
问怎么买、哪里买 -> '购票'
问带什么、身份证 -> '物品'
问几点开门、闭馆 -> '时间'
问怎么玩、路线 -> '游玩攻略'

要求：
仅返回意图名称，不要包含任何标点或其他文字。
如果无法匹配，返回 'unknown'。
"""
        
        # 用于存储API返回结果和同步线程
        result_container = []
        completed = threading.Event()

        # WebSocket回调函数 ws - WebSocket连接对象，message - 接收到的原始消息
        def on_message(ws, message):
            try:
                data = json.loads(message)#将接收到的JSON字符串解析为Python字典对象
                code = data['header']['code']#检查返回码,0表示成功
                if code != 0:
                    print(f'[API Error] code={code}, msg={data["header"]["message"]}')
                    ws.close()
                else:
                    choices = data["payload"]["choices"]#从响应数据中提取AI回复内容所在的部分
                    # 提取回复内容
                    if "text" in choices:
                        content = choices["text"][0]["content"]
                        result_container.append(content)
                    # 检查是否完成（status=2表示对话结束）
                    if choices.get("status") == 2:
                        completed.set()#通知主线程处理完成
                        ws.close()#关闭WebSocket连接
            except Exception as e:
                print(f"Message Error: {e}")
                completed.set()

        def on_error(ws, error):
            print(f"WebSocket Error: {error}")
            completed.set()

        def on_close(ws, *args):
            completed.set()

        def on_open(ws):# WebSocket连接建立后发送请求
            # 构建请求数据
            request_data = {
                "header": {"app_id": self.app_id},
                "parameter": {
                    "chat": {
                        "domain": self.domain,
                        "temperature": 0.1,  # 低温度确保输出稳定
                        "max_tokens": 20     # 限制输出长度
                    }
                },
                "payload": {
                    "message": {
                        "text": [
                            {"role": "system", "content": system_content},
                            {"role": "user", "content": f"用户输入：{user_input}"}
                        ]
                    }
                }
            }
            ws.send(json.dumps(request_data))# 发送请求数据

        # 建立WebSocket连接
        ws_url = self._get_auth_url()
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        # 启动WebSocket线程
        thread = threading.Thread(
            target=lambda: ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})  # 禁用SSL验证（仅建议测试环境）
        )
        thread.daemon = True
        thread.start()

        # 等待结果（超时10秒）
        completed.wait(timeout=10)
        # 确保连接关闭
        if ws.sock and ws.sock.connected:
            ws.close()

        # 处理返回结果
        if result_container:
            full_response = "".join(result_container).strip().replace('"', '').replace("'", "")
            print(f"  [AI思考] '{user_input}' => '{full_response}'")
            
            # 1. 精确匹配
            if full_response in available_intents:
                return full_response
            # 2. 包含匹配 AI回复中包含意图名称
            for intent in available_intents:
                if intent in full_response:
                    return intent
            return None
        else:
            return None