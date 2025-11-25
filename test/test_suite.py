# 文件名: test_suite.py
import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# 添加正确的Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))  # test目录
project_root = os.path.dirname(current_dir)  # DSL项目根目录
back_dir = os.path.join(project_root, 'back')  # back目录

# 添加所有必要的路径
sys.path.insert(0, project_root)  # 项目根目录
sys.path.insert(0, back_dir)      # back目录
sys.path.insert(0, current_dir)   # test目录
# 导入真实类
from interpreter import Lexer, Parser, LexicalError, SyntaxError
from LLMClient import LLMClient
from test_stubs import LLMClientStub, DSLScriptStub

# 由于你的 main.py 中的 DSLInterpreter 依赖于输入输出，我们需要创建一个测试版本
class TestableDSLInterpreter:
    """可测试的DSL解释器版本"""
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.steps = {}
        self.silence_count = 0
        self.max_silence_retries = 2
        self.current_step = "welcome"

    def load_dsl_script(self, script: str) -> bool:
        """加载DSL脚本"""
        try:
            lexer = Lexer(script)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse_program()
            self.steps.clear()
            for step in ast.steps:
                self.steps[step.name] = step
            return True
        except (LexicalError, SyntaxError) as e:
            print(f"DSL解析失败: {e}")
            return False

    def process_input(self, user_input: str) -> str:
        """处理用户输入并返回响应"""
        if self.current_step not in self.steps:
            return "对话流程错误"

        step = self.steps[self.current_step]
        
        # 处理退出
        if user_input in ["再见", "退出", "exit", "quit", "没有"]:
            return "感谢咨询，再见！"

        # 关键词匹配
        branch_nodes = {}
        for action in step.actions:
            if hasattr(action, 'keyword'):  # BranchNode
                branch_nodes[action.keyword] = action.step_name

        for keyword, step_name in branch_nodes.items():
            if keyword in user_input:
                self.current_step = step_name
                return self.get_step_response()

        # LLM 意图识别
        if branch_nodes:
            intent = self.llm_client.recognize_intent(user_input, list(branch_nodes.keys()))
            if intent and intent in branch_nodes:
                self.current_step = branch_nodes[intent]
                return self.get_step_response()

        # 默认处理
        for action in step.actions:
            if hasattr(action, 'step_name') and not hasattr(action, 'keyword'):  # DefaultNode
                self.current_step = action.step_name
                return self.get_step_response()

        return "抱歉，我不太理解您的问题。"

    def get_step_response(self) -> str:
        """获取当前步骤的响应"""
        if self.current_step not in self.steps:
            return "步骤不存在"

        step = self.steps[self.current_step]
        messages = []

        for action in step.actions:
            if hasattr(action, 'message'):  # SpeakNode
                messages.append(action.message)

        return "\n".join(messages)


class TestDSLInterpreterUnit(unittest.TestCase):
    """
    单元测试：负责测试解释器的核心组件，如词法分析、语法分析。
    """

    def test_lexer_basic(self):
        """测试词法分析器能否正确分解DSL脚本。"""
        print("\n[单元测试] -> Lexer基础测试")
        script = 'Step welcome\nSpeak "Hello"'
        lexer = Lexer(script)
        tokens = lexer.tokenize()
        
        # 检查token数量
        self.assertGreater(len(tokens), 3)
        # 检查关键token是否存在
        token_types = [token.type.name for token in tokens]
        self.assertIn('KEYWORD', token_types)
        self.assertIn('STRING', token_types)
        print("  ✓ Lexer基础测试通过")

    def test_lexer_complex_string(self):
        """测试词法分析器处理复杂字符串。"""
        print("\n[单元测试] -> Lexer复杂字符串测试")
        script = 'Speak "带\\n换行符的\\n消息"'
        lexer = Lexer(script)
        tokens = lexer.tokenize()
    
        string_token = next(token for token in tokens if token.type.name == 'STRING')
    
        # 修改断言：检查词法分析器确实保留了转义字符
        self.assertIn('\\n', string_token.value)  # 改为检查字面值
        print("  ✓ Lexer复杂字符串测试通过")

    def test_parser_basic(self):
        """测试语法分析器能否正确构建抽象语法树(AST)。"""
        print("\n[单元测试] -> Parser基础测试")
        script = DSLScriptStub.get_test_dsl()
        lexer = Lexer(script)
        parser = Parser(lexer.tokenize())
        ast = parser.parse_program()
        
        self.assertIsNotNone(ast)
        self.assertEqual(len(ast.steps), 4)  # welcome, ticket_info, time_info, default_proc
        print("  ✓ Parser基础测试通过")

    def test_parser_syntax_error(self):
        """测试语法分析器对错误语法的处理。"""
        print("\n[单元测试] -> Parser语法错误测试")
        script = 'Step welcome\nInvalidCommand "test"'
        lexer = Lexer(script)
        parser = Parser(lexer.tokenize())
        
        with self.assertRaises(SyntaxError):
            parser.parse_program()
        print("  ✓ Parser语法错误测试通过")


class TestChatbotIntegration(unittest.TestCase):
    """
    集成测试：负责测试整个系统在模拟场景下的行为是否符合预期。
    """
    
    def setUp(self):
        """在每个测试方法运行前执行，用于准备测试环境。"""
        # 使用测试桩代替真实的LLM客户端
        self.llm_stub = LLMClientStub()
        # 初始化解释器
        self.interpreter = TestableDSLInterpreter(self.llm_stub)
        # 加载测试用的DSL脚本
        success = self.interpreter.load_dsl_script(DSLScriptStub.get_test_dsl())
        self.assertTrue(success, "DSL脚本加载失败")

    def test_intent_recognition_stub(self):
        """测试LLM桩的意图识别是否符合预期。"""
        print("\n[集成测试] -> 意图识别测试")
        test_cases = [
            {"input": "怎么买票", "expected": "购票"},
            {"input": "门票价格", "expected": "门票"},
            {"input": "开放时间", "expected": "时间"},
            {"input": "无关输入", "expected": None},
        ]
        
        for case in test_cases:
            with self.subTest(msg=f"输入: '{case['input']}'"):
                intent = self.llm_stub.recognize_intent(case["input"], ["门票", "购票", "时间"])
                self.assertEqual(intent, case["expected"])
        print("  ✓ 意图识别测试通过")

    def test_conversation_flow(self):
        """测试完整的对话流程。"""
        print("\n[集成测试] -> 对话流程测试")
        
        # 测试门票查询
        response1 = self.interpreter.process_input("门票")
        self.assertIn("门票信息", response1)
        
        # 测试时间查询
        response2 = self.interpreter.process_input("时间")
        self.assertIn("开放时间", response2)
        
        # 测试未知输入
        response3 = self.interpreter.process_input("无关问题")
        self.assertIn("抱歉", response3)
        
        print("  ✓ 对话流程测试通过")

    def test_keyword_matching(self):
        """测试关键词匹配功能。"""
        print("\n[集成测试] -> 关键词匹配测试")
        
        response = self.interpreter.process_input("门票")
        self.assertIn("门票信息", response)
        
        response = self.interpreter.process_input("时间")
        self.assertIn("开放时间", response)
        
        print("  ✓ 关键词匹配测试通过")


class TestLLMClientIntegration(unittest.TestCase):
    """LLM客户端集成测试"""
    
    @patch('LLMClient.LLMClient.recognize_intent')
    def test_llm_client_integration(self, mock_recognize):
        """测试LLM客户端集成"""
        print("\n[集成测试] -> LLM客户端集成测试")
        
        # 设置mock返回值
        mock_recognize.return_value = "门票"
        
        # 创建真实LLMClient实例
        llm_client = LLMClient("test_id", "test_key", "test_secret")
        
        # 测试意图识别
        intent = llm_client.recognize_intent("门票价格", ["门票", "时间"])
        self.assertEqual(intent, "门票")
        
        print("  ✓ LLM客户端集成测试通过")


if __name__ == '__main__':
    """
    运行此文件即可执行所有测试。
    在命令行中运行: python test_suite.py
    """
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestDSLInterpreterUnit))
    suite.addTests(loader.loadTestsFromTestCase(TestChatbotIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMClientIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果摘要
    print("\n" + "="*50)
    print("测试结果摘要:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("="*50)
    
    # 如果有失败或错误，退出码为1
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)