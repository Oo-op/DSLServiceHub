# 文件名: main.py
import sys
import os
import time
from typing import Optional
from dotenv import load_dotenv #从.env文件中加载环境变量

from interpreter import Lexer, Parser, LexicalError, SyntaxError, \
    StepNode, SpeakNode, ListenNode, BranchNode, DefaultNode, ExitNode, SilenceNode
from LLMClient import LLMClient

class DSLInterpreter:
    """DSL解释器：执行AST并管理对话状态"""
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.steps = {}
        self.silence_count = 0
        self.max_silence_retries = 2 # 全局默认，会被Listen指令覆盖

    def load_dsl_script(self, script: str) -> bool:
        try:
            lexer = Lexer(script)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse_program()
            self.steps.clear()
            for step in ast.steps:
                if step.name in self.steps:
                    print(f"警告: 步骤 '{step.name}' 被重复定义。")
                self.steps[step.name] = step
            print(f"成功加载 DSL，共 {len(self.steps)} 个步骤。")
            return True
        except (LexicalError, SyntaxError) as e:
            print(f"DSL 解析失败: {e}")
            return False
        except Exception as e:
            import traceback
            print(f"未知错误: {e}")
            traceback.print_exc()
            return False

    def type_print(self, text: str, delay: float = 0.03):
        """打字机效果输出"""
        print("客服: ", end="")
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print() # 换行

    def run(self, start_step_name: str = "welcome"):
        if not self.steps: print("错误: 未加载 DSL。"); return
        if start_step_name not in self.steps: print(f"错误: 起始步骤 '{start_step_name}' 不存在。"); return

        print("\n" + "="*50 + "\n欢迎使用故宫博物院智能客服系统\n您可以输入 '再见' 结束对话\n" + "="*50 + "\n")
        
        current_step_name = start_step_name
        while current_step_name:
            try:
                current_step_name = self.execute_step(current_step_name)
            except KeyboardInterrupt:
                print("\n\n对话被用户中断。"); break
            except Exception as e:
                import traceback
                print(f"\n运行时错误: {e}"); traceback.print_exc(); break
        
        print("\n" + "="*50 + "\n对话结束。\n" + "="*50)

    def execute_step(self, step_name: str) -> Optional[str]:
        step = self.steps[step_name]
        # print(f"\n[DEBUG] 进入步骤: {step_name}") # 调试用

        # 执行动作
        for action in step.actions:
            if isinstance(action, SpeakNode):
                self.type_print(action.message)
                time.sleep(0.3)
            elif isinstance(action, ListenNode):
                return self.execute_listen(step, action)
            elif isinstance(action, ExitNode):
                return None
            elif isinstance(action, DefaultNode):
                return action.step_name
        
        print(f"警告: 步骤 '{step_name}' 结束无跳转。")
        return None

    def execute_listen(self, current_step: StepNode, listen_config: ListenNode) -> Optional[str]:
        branch_nodes = {a.keyword: a for a in current_step.actions if isinstance(a, BranchNode)}
        default_node = next((a for a in current_step.actions if isinstance(a, DefaultNode)), None)
        silence_node = next((a for a in current_step.actions if isinstance(a, SilenceNode)), None)
        
        # 使用 Listen 指令中定义的重试次数
        max_retries = listen_config.retries if listen_config.retries is not None else self.max_silence_retries

        try:
            user_input = input("您: ").strip()
        except EOFError:
            return None

        # 1. 处理静默/空输入
        if not user_input:
            self.silence_count += 1
            print(f"  (检测到静默 {self.silence_count}/{max_retries}次)")
            
            if self.silence_count >= max_retries:
                if silence_node: return silence_node.step_name
                if default_node: return default_node.step_name
                return None # 结束
            
            # 静默但未达上限，通常应该留在这个步骤或提示用户
            # 这里简单处理：重新执行当前步骤（会再次Speak）
            return current_step.name

        # 用户有输入，重置计数器
        self.silence_count = 0

        # 2. 处理全局退出
        if user_input in ["再见", "退出", "exit", "quit"]:
            return None

        # 3. 关键词优先匹配 
        for keyword, branch_action in branch_nodes.items():
            if keyword in user_input:
                print(f"  (关键词命中: '{keyword}')")
                return branch_action.step_name

        # 4. LLM 意图识别
        if branch_nodes:
            print("  (AI正在思考...)")
            intent = self.llm_client.recognize_intent(user_input, list(branch_nodes.keys()))
            if intent and intent in branch_nodes:
                return branch_nodes[intent].step_name

        # 5. 默认处理
        if default_node:
            return default_node.step_name
            
        print("  (无匹配且无默认流程，对话结束)")
        return None

def main():
    load_dotenv() # 加载 .env 文件
    dsl_file = "../spotServer.dsl"
    if not os.path.exists(dsl_file):
        print(f"错误: 找不到 {dsl_file}")
        sys.exit(1)

    with open(dsl_file, 'r', encoding='utf-8') as f:
        script = f.read()

    # 获取Key
    app_id = os.getenv("SPARK_APP_ID")
    api_key = os.getenv("SPARK_API_KEY")
    api_secret = os.getenv("SPARK_API_SECRET")

    if not all([app_id, api_key, api_secret]):
        print("错误: 请在 .env 文件中配置 SPARK_APP_ID, SPARK_API_KEY, SPARK_API_SECRET")
        sys.exit(1)

    try:
        llm_client = LLMClient(app_id, api_key, api_secret, spark_version="v3.5")
    except ValueError as e:
        print(f"配置错误: {e}")
        sys.exit(1)

    interpreter = DSLInterpreter(llm_client)
    if interpreter.load_dsl_script(script):
        interpreter.run()

if __name__ == "__main__":
    main()