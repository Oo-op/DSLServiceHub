# 文件名: app.py
from flask import Flask, render_template, request, jsonify
import sys
import os
import time
from typing import Optional

# 添加后端目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '..', 'back')
sys.path.append(backend_dir)

from interpreter import Lexer, Parser, LexicalError, SyntaxError, \
    StepNode, SpeakNode, ListenNode, BranchNode, DefaultNode, ExitNode, SilenceNode
from LLMClient import LLMClient
from dotenv import load_dotenv

load_dotenv()

class WebDSLInterpreter:
    """Web版本的DSL解释器"""
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.steps = {}
        self.silence_count = 0
        self.max_silence_retries = 2
        self.current_step = "welcome"

    def load_dsl_script(self, script: str) -> bool:
        try:
            lexer = Lexer(script)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse_program()
            self.steps.clear()
            for step in ast.steps:
                self.steps[step.name] = step
            print(f"成功加载 DSL，共 {len(self.steps)} 个步骤。")
            return True
        except (LexicalError, SyntaxError) as e:
            print(f"DSL 解析失败: {e}")
            return False

    def process_user_input(self, user_input: str = "") -> dict:
        """处理用户输入并返回响应"""
        if self.current_step not in self.steps:
            return {"error": "对话流程错误"}

        step = self.steps[self.current_step]
        
        # 处理静默/空输入
        if not user_input:
            self.silence_count += 1
            if self.silence_count >= self.max_silence_retries:
                # 查找静默处理节点
                silence_node = next((a for a in step.actions if isinstance(a, SilenceNode)), None)
                if silence_node:
                    self.current_step = silence_node.step_name
                    return self.get_step_response()
                return {"message": "长时间无响应，对话结束", "end": True}
            return {"message": "请告诉我您的问题..."}

        # 重置静默计数
        self.silence_count = 0

        # 处理退出
        if user_input in ["再见", "退出", "exit", "quit", "没有"]:
            exit_node = next((a for a in step.actions if isinstance(a, ExitNode)), None)
            if exit_node:
                self.current_step = "exitProc"
                return self.get_step_response()
            return {"message": "感谢咨询，再见！", "end": True}

        # 关键词匹配
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

        return {"message": "抱歉，我不太理解您的问题。", "end": False}

    def get_step_response(self) -> dict:
        """获取当前步骤的响应"""
        if self.current_step not in self.steps:
            return {"error": "步骤不存在"}

        step = self.steps[self.current_step]
        messages = []
        end_conversation = False

        for action in step.actions:
            if isinstance(action, SpeakNode):
                messages.append(action.message)
            elif isinstance(action, ExitNode):
                end_conversation = True
                break

        return {
            "message": "\n".join(messages),
            "end": end_conversation,
            "current_step": self.current_step
        }

    def reset_conversation(self):
        """重置对话"""
        self.current_step = "welcome"
        self.silence_count = 0
        return self.get_step_response()

# 初始化 Flask 应用
app = Flask(__name__)

# 初始化解释器
def create_interpreter():
    app_id = os.getenv("SPARK_APP_ID")
    api_key = os.getenv("SPARK_API_KEY")
    api_secret = os.getenv("SPARK_API_SECRET")
    
    if not all([app_id, api_key, api_secret]):
        raise ValueError("请配置 SPARK_APP_ID, SPARK_API_KEY, SPARK_API_SECRET")
    
    llm_client = LLMClient(app_id, api_key, api_secret, spark_version="v3.5")
    interpreter = WebDSLInterpreter(llm_client)
    
    # 加载 DSL 脚本 - 修复路径问题
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)  # 获取项目根目录
    dsl_file = os.path.join(project_root, 'back', 'spotServer.dsl')
    
    print(f"尝试加载 DSL 文件: {dsl_file}")  # 调试信息
    
    if not os.path.exists(dsl_file):
        # 如果上述路径不存在，尝试其他可能的路径
        alternative_paths = [
            os.path.join(project_root, 'spotServer.dsl'),  # 可能在项目根目录
            os.path.join(current_dir, 'spotServer.dsl'),   # 可能在前端目录
            'spotServer.dsl'  # 可能在当前工作目录
        ]
        
        for path in alternative_paths:
            if os.path.exists(path):
                dsl_file = path
                print(f"找到 DSL 文件在: {dsl_file}")
                break
        else:
            # 如果所有路径都找不到，列出目录内容帮助调试
            print(f"项目根目录内容: {os.listdir(project_root)}")
            print(f"前端目录内容: {os.listdir(current_dir)}")
            raise FileNotFoundError(f"找不到 spotServer.dsl 文件。请确保文件存在。")
    
    with open(dsl_file, 'r', encoding='utf-8') as f:
        script = f.read()
    
    if not interpreter.load_dsl_script(script):
        raise RuntimeError("DSL 脚本加载失败")
    
    return interpreter

try:
    interpreter = create_interpreter()
    print("DSL 解释器初始化成功！")
except Exception as e:
    print(f"初始化失败: {e}")
    interpreter = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_conversation():
    """开始新对话"""
    if not interpreter:
        return jsonify({"error": "系统初始化失败"})
    response = interpreter.reset_conversation()
    return jsonify(response)

@app.route('/api/message', methods=['POST'])
def handle_message():
    """处理用户消息"""
    if not interpreter:
        return jsonify({"error": "系统初始化失败"})
    user_input = request.json.get('message', '')
    response = interpreter.process_user_input(user_input)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)