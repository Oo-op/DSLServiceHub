#!/usr/bin/env python3
"""
故宫客服DSL解释器 - 主程序
集成词法分析、语法分析、语义执行和LLM意图识别
"""

import sys
import os
import time
from interpreter import Lexer, Parser, LexicalError, SyntaxError
from interpreter import SpeakNode, ListenNode, BranchNode, DefaultNode, ExitNode, SilenceNode
from LLMNeed import LLMClient, Config

class DSLInterpreter:
    """DSL解释器：执行AST并管理对话状态"""
    
    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()
        self.current_step = "welcome"  # 初始步骤
        self.steps = {}  # 存储所有步骤
        self.user_input_history = []  # 用户输入历史
        self.silence_count = 0  # 静默次数计数
        self.max_silence_count = 3  # 最大静默次数
        
    def load_dsl_script(self, script: str):
        """加载并解析DSL脚本"""
        try:
            # 词法分析
            lexer = Lexer(script)
            tokens = lexer.tokenize()
            
            # 语法分析
            parser = Parser(tokens)
            ast = parser.parse_program()
            
            # 构建步骤字典
            for step in ast.steps:
                self.steps[step.name] = step
                
            print(f"成功加载DSL脚本，包含 {len(self.steps)} 个步骤")
            return True
            
        except LexicalError as e:
            print(f"词法错误: {e}")
            return False
        except SyntaxError as e:
            print(f"语法错误: {e}")
            return False
        except Exception as e:
            print(f"加载脚本错误: {e}")
            return False
    
    def execute_step(self, step_name: str):
        """执行指定步骤"""
        if step_name not in self.steps:
            print(f"错误: 步骤 '{step_name}' 不存在")
            return False
            
        step = self.steps[step_name]
        print(f"\n{'='*40}")
        print(f"执行步骤: {step_name}")
        print(f"{'='*40}")
        
        # 重置静默计数（进入新步骤时重置）
        self.silence_count = 0
        
        for action in step.actions:
            if isinstance(action, SpeakNode):
                self.execute_speak(action)
            elif isinstance(action, ListenNode):
                next_step = self.execute_listen(action, step.actions)
                if next_step:
                    return self.execute_step(next_step)
                else:
                    return True  # 没有下一步，结束当前步骤
            elif isinstance(action, ExitNode):
                print("\n" + "="*50)
                print("对话结束，感谢使用故宫客服！")
                print("="*50)
                return True
                
        return True
    
    def execute_speak(self, speak_node):
        """执行Speak操作"""
        print(f"🤖 客服: {speak_node.message}")
        # 模拟说话时间
        time.sleep(1)
        
    def execute_listen(self, listen_node, step_actions):
        """执行Listen操作并处理用户输入"""
        min_time, max_time = listen_node.min_time, listen_node.max_time
        
        print(f"\n⏰ 等待用户输入 ({min_time}-{max_time}秒)...")
        print("💡 提示: 您可以询问『门票』、『开放时间』、『游玩攻略』，或说『人工』转人工客服")
        
        # 收集所有Branch的关键词用于提示
        branch_keywords = []
        branch_actions = {}
        for action in step_actions:
            if isinstance(action, BranchNode):
                branch_keywords.append(action.keyword)
                branch_actions[action.keyword] = action
        
        if branch_keywords:
            print(f"🎯 可用关键词: {', '.join(branch_keywords)}")
        
        # 获取用户输入
        try:
            user_input = input("\n👤 您: ").strip()
        except KeyboardInterrupt:
            print("\n\n收到中断信号，结束对话...")
            return "transferHuman"
        
        if user_input:
            self.user_input_history.append(user_input)
            self.silence_count = 0  # 有输入时重置静默计数
            
            print(f"🔍 正在分析您的输入...")
            time.sleep(0.5)  # 模拟分析时间
            
            # 使用LLM进行意图识别
            if self.llm_client and branch_keywords:
                intent = self.llm_client.recognize_intent(user_input, branch_keywords)
                print(f"✅ 识别意图: {intent}")
                
                # 根据意图找到对应的Branch
                if intent in branch_actions:
                    return branch_actions[intent].step_name
            
            # 如果LLM识别失败，使用关键词匹配
            for keyword in branch_keywords:
                if keyword in user_input:
                    print(f"✅ 关键词匹配: {keyword}")
                    return branch_actions[keyword].step_name
            
            # 没有匹配的Branch，执行Default
            for action in step_actions:
                if isinstance(action, DefaultNode):
                    print("⚠️  未识别到明确意图，执行默认流程")
                    return action.step_name
                    
        else:
            # 处理静默情况
            self.silence_count += 1
            print(f"🔇 检测到静默 (第{self.silence_count}次)")
            
            # 检查是否超过最大静默次数
            if self.silence_count >= self.max_silence_count:
                print("❌ 静默次数过多，转人工客服")
                return "transferHuman"
            
            # 执行Silence分支
            for action in step_actions:
                if isinstance(action, SilenceNode):
                    print("🔇 执行静默处理流程")
                    return action.step_name
            
            # 如果没有Silence分支但有Default，执行Default
            for action in step_actions:
                if isinstance(action, DefaultNode):
                    print("🔇 静默状态下执行默认流程")
                    return action.step_name
        
        return None
    
    def run(self):
        """启动解释器"""
        if "welcome" not in self.steps:
            print("错误: 未找到初始步骤 'welcome'")
            return
            
        print("\n" + "="*60)
        print("🏛️  故宫客服机器人启动")
        print("="*60)
        print("欢迎使用故宫博物院智能客服系统！")
        print("="*60)
        
        try:
            self.execute_step("welcome")
        except Exception as e:
            print(f"\n❌ 系统错误: {e}")
            print("正在转接人工客服...")
            if "transferHuman" in self.steps:
                self.execute_step("transferHuman")

def load_dsl_file(file_path: str) -> str:
    """从文件加载DSL脚本"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 不存在")
        return None
    except Exception as e:
        print(f"读取文件错误: {e}")
        return None

def main():
    """主函数"""
    print("正在初始化故宫客服系统...")
    
    # 创建解释器（使用模拟模式的LLM客户端）
    interpreter = DSLInterpreter()
    
    # 加载DSL脚本
    dsl_file = "spotServer.dsl"
    if not os.path.exists(dsl_file):
        print(f"错误: DSL文件 {dsl_file} 不存在")
        print("请确保 spotServer.dsl 文件在当前目录中")
        return
    
    script = load_dsl_file(dsl_file)
    if not script:
        return
    
    # 解析脚本
    print("正在解析DSL脚本...")
    if not interpreter.load_dsl_script(script):
        print("DSL脚本解析失败，请检查脚本语法")
        return
    
    # 运行解释器
    try:
        interpreter.run()
    except KeyboardInterrupt:
        print("\n\n👋 感谢使用故宫客服，再见！")
    except Exception as e:
        print(f"\n💥 系统发生错误: {e}")

if __name__ == "__main__":
    main()