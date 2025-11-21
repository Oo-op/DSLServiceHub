import sys
import os
import time
from interpreter import Lexer, Parser, LexicalError, SyntaxError, \
                          SpeakNode, ListenNode, BranchNode, DefaultNode, ExitNode, SilenceNode
from LLMNeed import LLMClient
from typing import Optional, List 
from dotenv import load_dotenv  # 新增导入

class DSLInterpreter:
    """DSL解释器：执行AST并管理对话状态"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.steps = {}
        self.silence_count = 0
        self.max_silence_retries = 1
        
    def load_dsl_script(self, script: str) -> bool:
        """加载并解析DSL脚本"""
        try:
            lexer = Lexer(script)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse_program()
            
            self.steps.clear()
            for step in ast.steps:
                if step.name in self.steps:
                    print(f"警告: 步骤 '{step.name}' 被重复定义。后边的定义会覆盖前边的。")
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
        """从指定步骤开始运行解释器"""
        if start_step_name not in self.steps:
            print(f"错误: 起始步骤 '{start_step_name}' 未在DSL脚本中定义。")
            return

        print("\n" + "="*50)
        print("欢迎使用故宫博物院智能客服系统")
        print("当前运行在AI模式，可以自然对话")
        print("您可以随时输入'没有'或'再见'来结束对话")
        print("="*50 + "\n")
        
        current_step_name = start_step_name
        while current_step_name:
            try:
                current_step_name = self.execute_step(current_step_name)
            except KeyboardInterrupt:
                print("\n\n对话被用户中断。感谢使用，再见！")
                break
            except Exception as e:
                print(f"\n执行过程中发生意外错误: {e}")
                print("系统遇到问题，对话结束。")
                break
        
        print("\n" + "="*50)
        print("对话已结束。")
        print("="*50)

    def execute_step(self, step_name: str) -> Optional[str]:
        """
        执行单个步骤的所有动作，并返回下一个步骤的名称。
        返回 None 表示对话结束。
        """
        if step_name not in self.steps:
            print(f"运行时错误: 尝试跳转到不存在的步骤 '{step_name}'。")
            return "exitProc" # 跳转到退出步骤以安全结束

        step = self.steps[step_name]
        print(f"\n进入步骤: {step_name}")
        
        if step_name != "silenceProc":
             self.silence_count = 0

        for action in step.actions:
            if isinstance(action, SpeakNode):
                print(f"客服: {action.message}")
                time.sleep(0.5) 
            
            elif isinstance(action, ListenNode):
                return self.execute_listen(action, step.actions)

            elif isinstance(action, ExitNode):
                return None

            elif isinstance(action, (BranchNode, DefaultNode, SilenceNode)):
                continue

        for action in step.actions:
            if isinstance(action, DefaultNode):
                return action.step_name
        
        print(f"警告: 步骤 '{step_name}' 执行完毕但没有后续指令 (如 Listen 或 Default)，对话流程中断。")
        return "exitProc"

    def execute_listen(self, listen_node: ListenNode, actions: List) -> Optional[str]:
        """执行Listen操作，获取用户输入并决定下一个步骤"""
        branch_actions = {a.keyword: a for a in actions if isinstance(a, BranchNode)}
        default_action = next((a for a in actions if isinstance(a, DefaultNode)), None)
        silence_action = next((a for a in actions if isinstance(a, SilenceNode)), None)

        try:
            user_input = input("您: ").strip()
        except EOFError: 
            user_input = ""

        if user_input:
            self.silence_count = 0
            
            recognized_intent = self.llm_client.recognize_intent(user_input, list(branch_actions.keys()))
            
            if recognized_intent and recognized_intent in branch_actions:
                return branch_actions[recognized_intent].step_name

            # 如果API识别失败，回退到关键词匹配
            for keyword, branch_action in branch_actions.items():
                if keyword.lower() in user_input.lower():
                    print(f"[关键词匹配] 命中 '{keyword}'")
                    return branch_action.step_name
            
            if default_action:
                print("  (未匹配到特定意图，执行默认流程...)")
                return default_action.step_name
        else:
            self.silence_count += 1
            print(f"检测到静默 (累计: {self.silence_count}次)")
            
            if silence_action:
                return silence_action.step_name
            elif default_action:
                return default_action.step_name

        print("警告: Listen 后无有效后续步骤 (Branch, Default, Silence)，对话无法继续。")
        return "exitProc"

def main():
    """主函数"""
    # 加载.env文件中的环境变量
    load_dotenv()
    
    dsl_file = "spotServer.dsl"
    if not os.path.exists(dsl_file):
        print(f"错误: DSL脚本文件 '{dsl_file}' 不存在于当前目录。")
        sys.exit(1)

    with open(dsl_file, 'r', encoding='utf-8') as f:
        script = f.read()

    # 从环境变量获取API密钥
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误: 请先设置DEEPSEEK_API_KEY环境变量")
        print("创建 .env 文件并在其中写入: DEEPSEEK_API_KEY=你的API密钥")
        sys.exit(1)
    
    # 创建LLM客户端
    try:
        llm_client = LLMClient(api_key=api_key)
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)
    
    interpreter = DSLInterpreter(llm_client)
    if interpreter.load_dsl_script(script):
        interpreter.run()
    else:
        print("\n程序因DSL脚本解析失败而终止。")

if __name__ == "__main__":
    main()