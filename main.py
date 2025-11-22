# 文件名: main.py

import sys
import os
import time
from typing import Optional
        #from dotenv import load_dotenv

# 从修正后的 interpreter.py 导入所有需要的类
from interpreter import Lexer, Parser, LexicalError, SyntaxError, \
                          ProgramNode, StepNode, SpeakNode, ListenNode, \
                          BranchNode, DefaultNode, ExitNode, SilenceNode

from LLMClient import LLMClient

class DSLInterpreter:
    """DSL解释器：执行AST并管理对话状态"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.steps = {}
        self.silence_count = 0
        self.max_silence_retries = 2

    def load_dsl_script(self, script: str) -> bool:
        """加载并解析DSL脚本，生成并存储步骤"""
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
                
            print(f"成功加载并解析DSL脚本，共 {len(self.steps)} 个步骤。")
            return True
        except (LexicalError, SyntaxError) as e:
            print(f"解析DSL脚本失败: {e}")
            return False
        except Exception as e:
            print(f"加载脚本时发生未知错误: {e}")
            return False

    def run(self, start_step_name: str = "welcome"):
        if not self.steps: print("错误: 未加载任何DSL脚本。"); return
        if start_step_name not in self.steps: print(f"错误: 起始步骤 '{start_step_name}' 不存在。"); return

        print("\n" + "="*50 + "\n欢迎使用故宫博物院智能客服系统\n您可以随时输入'再见'来结束对话\n" + "="*50 + "\n")

        current_step_name = start_step_name
        while current_step_name:
            try:
                current_step_name = self.execute_step(current_step_name)
            except KeyboardInterrupt: print("\n\n对话被用户中断。再见！"); break
            except Exception as e:
                import traceback
                print(f"\n执行过程中发生意外错误: {e}"); traceback.print_exc(); break
        
        print("\n" + "="*50 + "\n对话已结束。感谢您的使用！\n" + "="*50)

    def execute_step(self, step_name: str) -> Optional[str]:
        step = self.steps[step_name]
        print(f"\n>>>>> 进入步骤: {step_name} <<<<<")
        
        # 重置静默计数器
        self.silence_count = 0

        # 按顺序执行指令
        for action in step.actions:
            if isinstance(action, SpeakNode):
                print(f"客服: {action.message}")
                time.sleep(0.5)
            elif isinstance(action, ListenNode):
                return self.execute_listen(step)
            elif isinstance(action, ExitNode):
                return None
            elif isinstance(action, DefaultNode):
                # 如果步骤最后是Default，直接跳转
                return action.step_name
        
        print(f"警告: 步骤 '{step_name}' 执行完毕但没有后续指令，对话中断。")
        return None

    def execute_listen(self, current_step: StepNode) -> Optional[str]:
        branch_nodes = {a.keyword: a for a in current_step.actions if isinstance(a, BranchNode)}
        default_node = next((a for a in current_step.actions if isinstance(a, DefaultNode)), None)
        silence_node = next((a for a in current_step.actions if isinstance(a, SilenceNode)), None)

        try: user_input = input("您: ").strip()
        except EOFError: user_input = ""

        if user_input:
            self.silence_count = 0
            
            # 策略1: 优先使用LLM进行意图识别 (这更符合项目要求)
            if branch_nodes:
                print("  (正在使用AI理解您的意图...)")
                recognized_intent = self.llm_client.recognize_intent(user_input, list(branch_nodes.keys()))
                if recognized_intent and recognized_intent in branch_nodes:
                    return branch_nodes[recognized_intent].step_name
            
            # 策略2: 如果LLM失败，回退到关键词匹配
            print("  (AI未能匹配，尝试关键词匹配...)")
            for keyword, branch_action in branch_nodes.items():
                if keyword.lower() in user_input.lower():
                    print(f"  (关键词匹配命中: '{keyword}')")
                    return branch_action.step_name
            
            if default_node: return default_node.step_name
        else: # 用户静默
            self.silence_count += 1
            print(f"  (检测到静默，累计: {self.silence_count}次)")
            if self.silence_count >= self.max_silence_retries and silence_node:
                return silence_node.step_name
            elif default_node:
                return default_node.step_name

        print("警告: Listen后无有效后续步骤，对话中断。")
        return None

def main():
    #load_dotenv()
    
    dsl_file = "spotServer.dsl"
    if not os.path.exists(dsl_file):
        print(f"错误: DSL脚本文件 '{dsl_file}' 不存在。")
        sys.exit(1)

    with open(dsl_file, 'r', encoding='utf-8') as f:
        script = f.read()

    # from dotenv import load_dotenv

    # 在main函数中
# load_dotenv()
# 直接使用环境变量或硬编码测试（仅用于调试）
    app_id = os.getenv("SPARK_APP_ID") or "d48801c2"
    api_key = os.getenv("SPARK_API_KEY") or "bf818c60404ba8d6d6297a4aeb677a5d"
    api_secret = os.getenv("SPARK_API_SECRET") or "NzUwN2M1MTMyOTA5YTU1N2UxYjQyNWMw"
    
    if not all([app_id, api_key, api_secret]):
        print("错误: 请在项目根目录下创建 .env 文件并填入讯飞星火的凭证。")
        sys.exit(1)
    
    try:
        # 你可以指定版本，如 "v1.5", "v2.0" 等，默认为 "v3.5"
        llm_client = LLMClient(app_id=app_id, api_key=api_key, api_secret=api_secret, spark_version="max")
    except ValueError as e:
        print(f"错误: {e}"); sys.exit(1)
    
    interpreter = DSLInterpreter(llm_client)
    if interpreter.load_dsl_script(script):
        interpreter.run()
    else:
        print("\n程序因DSL脚本解析失败而终止。")

if __name__ == "__main__":
    main()