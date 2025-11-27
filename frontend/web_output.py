# 文件名: web_output.py

#cd frontend 
#python web_output.py

# 激活虚拟环境
#venv\Scripts\activate

#python test_suite.py 

from flask import Flask, render_template, request, jsonify
import sys
import os
import uuid
import time

# 路径配置
current_dir = os.path.dirname(os.path.abspath(__file__))
# 假设 back 目录与 webapp 目录同级
backend_dir = os.path.join(current_dir, '..', 'back')
if not os.path.exists(backend_dir): # 如果在同一目录下运行
    backend_dir = current_dir
sys.path.append(backend_dir)


from interpreter import Lexer, Parser, LexicalError, SyntaxError, \
    StepNode, SpeakNode, ListenNode, BranchNode, DefaultNode, ExitNode, SilenceNode
# 确保 LLMClient 在 sys.path 可找到
from LLMClient import LLMClient
from dotenv import load_dotenv

load_dotenv()

class WebDSLInterpreter:
    def __init__(self, llm_client: LLMClient, steps_data: dict):
        self.llm_client = llm_client
        self.steps = steps_data
        self.silence_count = 0  # 标记是否进入过静默提醒流程
        self.current_step = "welcome"
        self.last_interaction_time = time.time()  # 记录最后一次交互时间
        self.total_silence_start_time = None  # 记录总静默开始时间

    def process_user_input(self, user_input: str = "") -> dict:
        if self.current_step not in self.steps:
            return {"error": "对话流程错误，未找到当前步骤。", "end": True}

        step = self.steps[self.current_step]
        listen_node = next((a for a in step.actions if isinstance(a, ListenNode)), None)
        
        # --- 1. 处理用户有输入的情况 ---
        if user_input:
            print(f"[Debug] 用户输入: '{user_input}', 重置所有静默计时器")
            self.last_interaction_time = time.time()
            self.total_silence_start_time = None  # 重置总静默计时
            self.silence_count = 0 # 虽然不再主要依赖它，但重置是个好习惯

            # 处理退出关键词
            if user_input.lower() in ["再见", "退出", "exit", "quit", "没有", "没了"]:
                if "exitProc" in self.steps:
                    self.current_step = "exitProc"
                    return self.get_step_response()
                return {"message": "感谢您的咨询，再见！", "end": True}

            # 关键词精确匹配
            branch_nodes = {a.keyword: a for a in step.actions if isinstance(a, BranchNode)}
            for keyword, branch_action in branch_nodes.items():
                if keyword in user_input:
                    self.current_step = branch_action.step_name
                    return self.get_step_response()

            # LLM 意图识别
            if branch_nodes:
                intent = self.llm_client.recognize_intent(user_input, list(branch_nodes.keys()))
                if intent and intent in branch_nodes:
                    self.current_step = branch_nodes[intent].step_name
                    return self.get_step_response()

            # 默认处理
            default_node = next((a for a in step.actions if isinstance(a, DefaultNode)), None)
            if default_node:
                self.current_step = default_node.step_name
                return self.get_step_response()
            
            # 如果连默认处理都没有
            return {"message": "抱歉，我不太明白。您可以问我关于门票、时间或游玩攻略的问题。", "end": False}

        # --- 2. 处理用户无输入的情况 (超时轮询) ---
        else:
            current_time = time.time()
            single_timeout_sec = listen_node.timeout if listen_node else 10
            total_timeout_sec = listen_node.total_silence_timeout if listen_node else 30

            # 如果是第一次超时检测，初始化总静默计时器
            if self.total_silence_start_time is None:
                self.total_silence_start_time = self.last_interaction_time

            total_silence_elapsed = current_time - self.total_silence_start_time
            single_silence_elapsed = current_time - self.last_interaction_time
            
            print(f"[Debug] 静默检测: 单次已过={single_silence_elapsed:.1f}s (阈值 {single_timeout_sec}s), 总计已过={total_silence_elapsed:.1f}s (阈值 {total_timeout_sec}s)")

            # 检查总静默超时（最高优先级）
            if total_silence_elapsed >= total_timeout_sec:
                print(f"[Debug] 总静默超时({total_timeout_sec}s)达到，结束对话")
                # 尝试根据 DSL 优雅地结束
                current_silence_node = next((a for a in step.actions if isinstance(a, SilenceNode)), None)
                if current_silence_node:
                    self.current_step = current_silence_node.step_name
                    # 如果silenceProc本身再次超时，它的silence会指向exitProc
                    silence_step = self.steps.get(self.current_step)
                    if silence_step:
                       final_silence_node = next((a for a in silence_step.actions if isinstance(a, SilenceNode)), None)
                       if final_silence_node:
                           self.current_step = final_silence_node.step_name
                           return self.get_step_response()

                return {"message": "长时间无响应，对话已结束。", "end": True}

            # 检查单次静默超时
            if single_silence_elapsed >= single_timeout_sec:
                print(f"[Debug] 单次静默超时({single_timeout_sec}s)触发，执行提醒。")
                self.last_interaction_time = current_time  # 重置单次超时计时器

                silence_node = next((a for a in step.actions if isinstance(a, SilenceNode)), None)
                if silence_node:
                    print(f"[Debug] 跳转到静默处理步骤: {silence_node.step_name}")
                    self.current_step = silence_node.step_name
                    # 返回新步骤的响应，这是唯一的响应点
                    return self.get_step_response()
                else:
                    print("[Debug] 静默发生，但当前步骤未定义Silence处理，结束对话。")
                    return {"message": "长时间无响应，对话已结束。", "end": True}
            
            # **关键修复**: 如果没有达到任何超时条件，返回一个“无操作”的空消息响应
            else:
                print("[Debug] 轮询未超时，不发送消息。")
                response = self.get_step_response() # 获取状态信息
                response['message'] = '' # 清空消息体
                response['no_op'] = True # 添加一个无操作标记（可选，方便前端调试）
                return response

    def get_step_response(self) -> dict:
        """获取当前步骤的响应，包含正确的超时配置"""
        if self.current_step not in self.steps:
            return {"error": "步骤不存在", "end": True}

        step = self.steps[self.current_step]
        messages = []
        end_conversation = False

        # --- 获取超时配置 ---
        single_timeout_sec = 10
        total_timeout_sec = 30

        listen_node = next((a for a in step.actions if isinstance(a, ListenNode)), None)
        if listen_node:
            single_timeout_sec = listen_node.timeout
            total_timeout_sec = listen_node.total_silence_timeout

        # 收集所有消息，但避免重复内容
        seen_messages = set()
        for action in step.actions:
            if isinstance(action, SpeakNode):
                # 检查消息是否已经存在，避免重复
                if action.message not in seen_messages:
                    messages.append(action.message)
                    seen_messages.add(action.message)
            elif isinstance(action, ExitNode):
                end_conversation = True

        # 计算剩余总静默时间
        remaining_total_timeout = total_timeout_sec
        if self.total_silence_start_time is not None:
            elapsed = time.time() - self.total_silence_start_time
            remaining_total_timeout = max(0, total_timeout_sec - elapsed)

        response_data = {
            "message": "\n".join(messages),
            "end": end_conversation,
            "current_step": self.current_step,
            "timeout": single_timeout_sec * 1000,  # 单次超时(提醒用)
            "total_silence_timeout": total_timeout_sec, # 总超时配置
            "remaining_total_timeout": remaining_total_timeout, # 剩余总静默时间
            "current_silence_count": self.silence_count
        }
        print(f"[Debug] 发送响应: step={self.current_step}, 消息数量={len(messages)}, silence_count={self.silence_count}")
        return response_data

    def reset_conversation(self):
        self.current_step = "welcome"
        self.silence_count = 0
        self.last_interaction_time = time.time()
        self.total_silence_start_time = None
        return self.get_step_response()

# --- 全局初始化 ---
app = Flask(__name__)
user_sessions = {}
global_steps_ast = {}
global_llm_client = None

def init_system():
    global global_llm_client, global_steps_ast
    app_id = os.getenv("SPARK_APP_ID")
    api_key = os.getenv("SPARK_API_KEY")
    api_secret = os.getenv("SPARK_API_SECRET")
    if not all([app_id, api_key, api_secret]):
        raise ValueError("请在 .env 文件中配置星火大模型的 SPARK_APP_ID, SPARK_API_KEY, SPARK_API_SECRET")

    global_llm_client = LLMClient(app_id, api_key, api_secret, spark_version="v3.5")

    # 适应不同运行环境的路径
    dsl_path = os.path.join(current_dir, '..', 'spotServer.dsl')
    if not os.path.exists(dsl_path):
        dsl_path = os.path.join(current_dir, 'spotServer.dsl')
    if not os.path.exists(dsl_path):
        raise FileNotFoundError("无法找到 spotServer.dsl 文件")

    with open(dsl_path, 'r', encoding='utf-8') as f:
        script = f.read()

    try:
        lexer = Lexer(script)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse_program()
    except (LexicalError, SyntaxError) as e:
        raise RuntimeError(f"解析DSL文件失败: {e}")

    for step in program.steps:
        global_steps_ast[step.name] = step

    print(f"系统初始化完成，加载了 {len(global_steps_ast)} 个步骤。")

try:
    init_system()
except Exception as e:
    print(f"FATAL: 系统初始化失败: {e}")
    global_llm_client = None # 标记服务不可用

# --- Flask 路由定义 ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_conversation():
    if not global_llm_client or not global_steps_ast:
        return jsonify({"error": "服务正在初始化或初始化失败，请稍后重试。", "end": True}), 503
    session_id = str(uuid.uuid4())
    interpreter = WebDSLInterpreter(global_llm_client, global_steps_ast)
    user_sessions[session_id] = interpreter
    response = interpreter.reset_conversation()
    response['session_id'] = session_id
    return jsonify(response)

@app.route('/api/message', methods=['POST'])
def handle_message():
    if not global_llm_client or not global_steps_ast:
        return jsonify({"error": "服务未就绪。", "end": True}), 503

    data = request.json
    session_id = data.get('session_id')
    user_input = data.get('message', '').strip()

    if not session_id or session_id not in user_sessions:
        return jsonify({"error": "会话已过期，请刷新页面开始新的对话。", "end": True})

    interpreter = user_sessions[session_id]
    response = interpreter.process_user_input(user_input)

    if response.get('end'):
        if session_id in user_sessions:
            del user_sessions[session_id]
            print(f"会话 {session_id} 已结束并清理。")

    return jsonify(response)

# 添加会话状态检查接口
@app.route('/api/session_status', methods=['POST'])
def check_session_status():
    """检查会话状态和静默超时"""
    if not global_llm_client or not global_steps_ast:
        return jsonify({"error": "服务未就绪。", "end": True}), 503

    data = request.json
    session_id = data.get('session_id')

    if not session_id or session_id not in user_sessions:
        return jsonify({"error": "会话不存在", "end": True})

    interpreter = user_sessions[session_id]
    
    # 模拟超时检查（空输入触发静默处理）
    response = interpreter.process_user_input("")
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
