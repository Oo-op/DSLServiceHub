# 文件名: test_suite.py
import unittest#标准单元测试框架
import sys
import os
from unittest.mock import MagicMock, patch#用于模拟对象

# 设置模块导入路径
def setup_module_paths():
    """设置模块导入路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))  # test目录
    project_root = os.path.dirname(current_dir)  # DSL项目根目录
    # 添加所有可能的目录路径
    possible_paths = [
        project_root,
        os.path.join(project_root, 'back'),
        os.path.join(project_root, 'webapp'),
        current_dir
    ]
     # 将这些路径加入 sys.path
    for path in possible_paths:
        if path not in sys.path and os.path.exists(path):
            sys.path.insert(0, path)

setup_module_paths()#执行路径设置

from interpreter import Lexer, Parser, LexicalError, SyntaxError
from LLMClient import LLMClient
from test_stubs import LLMClientStub, DSLScriptStub


class TestableDSLInterpreter:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.steps = {}
        self.silence_count = 0
        self.current_step = "welcome"

    def load_dsl_script(self, script: str) -> bool:
        """加载DSL脚本并解析为AST"""
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
            return "对话流程错误，未找到当前步骤。"  

        step = self.steps[self.current_step]
        # 处理退出
        exit_keywords = ["再见", "退出", "exit", "quit", "没有", "没了"]
        if any(keyword in user_input.lower() for keyword in exit_keywords):
            return "感谢咨询，再见！"

         # 收集当前步骤下所有的分支节点 (关键词 -> 下一步骤名)
        branch_nodes = {}
        for action in step.actions:#检查 action 对象是否有 keyword 属性
            if hasattr(action, 'keyword') and hasattr(action, 'step_name'):  # BranchNode
                branch_nodes[action.keyword] = action.step_name

        # 精确匹配
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
        default_node = next((a for a in step.actions if hasattr(a, 'step_name') and not hasattr(a, 'keyword')), None)
        if default_node:
            self.current_step = default_node.step_name
            return self.get_step_response()

        return "抱歉，我不太理解您的问题。"

    def get_step_response(self) -> str:
        """获取当前步骤的响应"""
        if self.current_step not in self.steps:
            return "步骤不存在"  # 与实际实现保持一致

        step = self.steps[self.current_step]
        messages = []

        for action in step.actions:
            if hasattr(action, 'message'):  # SpeakNode
                messages.append(action.message)

        return "\n".join(messages)

    def reset_conversation(self):
        """重置对话状态"""
        self.current_step = "welcome"
        self.silence_count = 0
        return self.get_step_response()


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
        
        # 验证具体token内容
        expected_values = ['Step', 'welcome', 'Speak', 'Hello']
        actual_values = [token.value for token in tokens if token.value]
        for expected in expected_values:
            self.assertIn(expected, actual_values)
        print("  Lexer基础测试通过")

    def test_lexer_complex_string(self):
        """测试词法分析器处理复杂字符串。"""
        print("\n[单元测试] -> Lexer复杂字符串测试")
        script = 'Speak "带\\n换行符的\\n消息"'
        lexer = Lexer(script)
        tokens = lexer.tokenize()
    
        string_tokens = [token for token in tokens if token.type.name == 'STRING']
        self.assertGreater(len(string_tokens), 0, "未找到字符串token")
    
        string_token = string_tokens[0]
        # 检查词法分析器是否正确处理了转义字符
        self.assertEqual(string_token.value, "带\\n换行符的\\n消息")
        print("  Lexer复杂字符串测试通过")

    def test_lexer_multiline_string(self):
        """测试词法分析器处理多行字符串。"""
        print("\n[单元测试] -> Lexer多行字符串测试")
        script = '''Speak "第一行
第二行
第三行"'''
        lexer = Lexer(script)
        tokens = lexer.tokenize()
        
        string_tokens = [token for token in tokens if token.type.name == 'STRING']
        self.assertEqual(len(string_tokens), 1)
        self.assertIn("第一行", string_tokens[0].value)
        self.assertIn("第二行", string_tokens[0].value)
        print("  Lexer多行字符串测试通过")

    def test_parser_basic(self):
        """测试语法分析器能否正确构建抽象语法树(AST)。"""
        print("\n[单元测试] -> Parser基础测试")
        script = DSLScriptStub.get_test_dsl()
        lexer = Lexer(script)
        parser = Parser(lexer.tokenize())
        ast = parser.parse_program()
        
        self.assertIsNotNone(ast)
        self.assertEqual(len(ast.steps), 7)  # welcome, ticket_info, how_to_buy, time_info, what_to_bring, play_guide, default_proc
        
        # 验证步骤名称
        step_names = [step.name for step in ast.steps]
        expected_names = ['welcome', 'ticket_info', 'how_to_buy', 'time_info', 'what_to_bring', 'play_guide', 'default_proc']
        for name in expected_names:
            self.assertIn(name, step_names)
        print("  Parser基础测试通过")

    def test_parser_listen_timeout(self):
        """测试语法分析器解析Listen超时参数。"""
        print("\n[单元测试] -> Parser Listen超时测试")
        script = 'Step test\nListen 5, 30'
        lexer = Lexer(script)
        parser = Parser(lexer.tokenize())
        ast = parser.parse_program()
        
        self.assertEqual(len(ast.steps), 1)
        step = ast.steps[0]
        listen_nodes = [action for action in step.actions if hasattr(action, 'timeout')]
        self.assertEqual(len(listen_nodes), 1)
        self.assertEqual(listen_nodes[0].timeout, 5)
        self.assertEqual(listen_nodes[0].total_silence_timeout, 30)
        print("  Parser Listen超时测试通过")

    def test_parser_syntax_error(self):
        """测试语法分析器对错误语法的处理。"""
        print("\n[单元测试] -> Parser语法错误测试")
        script = 'Step welcome\nInvalidCommand "test"'
        lexer = Lexer(script)
        parser = Parser(lexer.tokenize())
        
        with self.assertRaises(SyntaxError):
            parser.parse_program()
        print("  Parser语法错误测试通过")

    def test_parser_empty_script(self):
        """测试语法分析器处理空脚本。"""
        print("\n[单元测试] -> Parser空脚本测试")
        script = ''
        lexer = Lexer(script)
        parser = Parser(lexer.tokenize())
        ast = parser.parse_program()
        
        self.assertIsNotNone(ast)
        self.assertEqual(len(ast.steps), 0)
        print("  Parser空脚本测试通过")


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

    def tearDown(self):
        """清理测试数据"""
        self.llm_stub = None
        self.interpreter = None

    def test_intent_recognition_stub(self):
        """测试LLM桩的意图识别是否符合预期。"""
        print("\n[集成测试] -> 意图识别测试")
        test_cases = [
            {"input": "怎么买票", "expected": "购票"},
            {"input": "哪里买票", "expected": "购票"},
            {"input": "门票价格", "expected": "门票"},
            {"input": "成人票多少钱", "expected": "门票"},
            {"input": "开放时间", "expected": "时间"},
            {"input": "几点开门", "expected": "时间"},
            {"input": "要带什么", "expected": "物品"},
            {"input": "需要证件吗", "expected": "物品"},
            {"input": "游玩路线", "expected": "游玩攻略"},
            {"input": "推荐景点", "expected": "游玩攻略"},
            {"input": "无关输入", "expected": None},
        ]
        
        for case in test_cases:
            with self.subTest(msg=f"输入: '{case['input']}'"):
                intent = self.llm_stub.recognize_intent(case["input"], ["门票", "购票", "时间", "物品", "游玩攻略"])
                self.assertEqual(intent, case["expected"])
        print("  意图识别测试通过")

    def test_conversation_flow(self):
        """测试完整的对话流程。"""
        print("\n[集成测试] -> 对话流程测试")
        
        # 测试门票查询
        response1 = self.interpreter.process_input("门票")
        self.assertIn("门票信息", response1)
        self.assertIn("成人票60元", response1)
        
        # 测试购票查询
        response2 = self.interpreter.process_input("购票")
        self.assertIn("购票方式", response2)
        self.assertIn("官方小程序", response2)
        
        # 测试时间查询
        response3 = self.interpreter.process_input("时间")
        self.assertIn("开放时间", response3)
        self.assertIn("8:30-17:00", response3)
        
        # 测试未知输入
        response4 = self.interpreter.process_input("无关问题")
        self.assertIn("抱歉", response4)
        self.assertIn("不太理解", response4)
        
        print("  对话流程测试通过")

    def test_keyword_matching(self):
        """测试关键词匹配功能。"""
        print("\n[集成测试] -> 关键词匹配测试")
        
        response = self.interpreter.process_input("门票")
        self.assertIn("门票信息", response)
        self.assertIn("成人票60元", response)
        
        response = self.interpreter.process_input("时间")
        self.assertIn("开放时间", response)
        self.assertIn("8:30-17:00", response)
        
        print("  关键词匹配测试通过")

    def test_multiple_conversation_turns(self):
        """测试多轮对话"""
        print("\n[集成测试] -> 多轮对话测试")
        
        # 第一轮：门票查询
        response1 = self.interpreter.process_input("门票")
        self.assertIn("门票信息", response1)
        
        # 第二轮：在门票信息步骤中继续问时间
        response2 = self.interpreter.process_input("时间")
        self.assertIn("开放时间", response2)
        
        # 第三轮：退出
        response3 = self.interpreter.process_input("没有")
        self.assertIn("感谢", response3)
        
        print("  多轮对话测试通过")

    def test_conversation_reset(self):
        """测试对话重置功能"""
        print("\n[集成测试] -> 对话重置测试")
        
        # 进行一些对话
        self.interpreter.process_input("门票")
        self.assertEqual(self.interpreter.current_step, "ticket_info")
        
        # 重置对话
        reset_response = self.interpreter.reset_conversation()
        self.assertEqual(self.interpreter.current_step, "welcome")
        self.assertIn("您好", reset_response)
        
        print("  对话重置测试通过")

    def test_llm_intent_fallback(self):
        """测试LLM意图识别作为关键词匹配的备选方案"""
        print("\n[集成测试] -> LLM意图回退测试")
        
        # 重置对话状态
        self.interpreter.reset_conversation()
        
        # 测试用例1: "怎么买票" 应该匹配到 "购票" 意图
        response = self.interpreter.process_input("怎么买票")
        print(f"[测试调试] 输入 '怎么买票' -> 响应: {response}")
        # 检查是否成功跳转到了购票相关的步骤（不包含默认的抱歉消息）
        self.assertNotIn("抱歉，我不太理解", response)
        
        # 重置对话状态
        self.interpreter.reset_conversation()
        
        # 测试用例2: "几点开门" 应该匹配到 "时间" 意图  
        response = self.interpreter.process_input("几点开门")
        print(f"[测试调试] 输入 '几点开门' -> 响应: {response}")
        # 检查是否成功跳转到了时间相关的步骤
        self.assertNotIn("抱歉，我不太理解", response)
        
        print("  LLM意图回退测试通过")

    def test_exit_keywords(self):
        """测试退出关键词处理"""
        print("\n[集成测试] -> 退出关键词测试")
        
        exit_keywords = ["再见", "退出", "exit", "quit", "没有", "没了"]
        
        for keyword in exit_keywords:
            with self.subTest(msg=f"退出关键词: '{keyword}'"):
                self.interpreter.reset_conversation()  # 重置状态
                response = self.interpreter.process_input(keyword)
                self.assertIn("感谢", response)
        
        print("  退出关键词测试通过")


class TestLLMClientIntegration(unittest.TestCase):
    """LLM客户端集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.llm_client = LLMClient("test_id", "test_key", "test_secret")

    @patch('websocket.WebSocketApp')
    def test_llm_client_initialization(self, mock_websocket):
        """测试LLM客户端初始化"""
        print("\n[集成测试] -> LLM客户端初始化测试")
        
        # 验证客户端属性
        self.assertEqual(self.llm_client.app_id, "test_id")
        self.assertEqual(self.llm_client.api_key, "test_key")
        self.assertEqual(self.llm_client.api_secret, "test_secret")
        self.assertIsNotNone(self.llm_client.spark_url)
        self.assertIsNotNone(self.llm_client.domain)
        
        print("  LLM客户端初始化测试通过")

    @patch('websocket.WebSocketApp')
    def test_llm_client_auth_url_generation(self, mock_websocket):
        """测试LLM客户端认证URL生成"""
        print("\n[集成测试] -> LLM客户端认证URL测试")
        
        auth_url = self.llm_client._get_auth_url()
        self.assertIsInstance(auth_url, str)
        self.assertIn("wss://", auth_url)
        self.assertIn("authorization", auth_url)
        self.assertIn("date", auth_url)
        self.assertIn("host", auth_url)
        
        print("  LLM客户端认证URL测试通过")

    def test_llm_client_different_versions(self):
        """测试LLM客户端不同版本配置"""
        print("\n[集成测试] -> LLM客户端版本测试")
        
        # 测试v3.5版本
        client_v35 = LLMClient("test_id", "test_key", "test_secret", "v3.5")
        self.assertIn("v3.5", client_v35.spark_url)
        self.assertEqual(client_v35.domain, "generalv3.5")
        
        # 测试pro版本
        client_pro = LLMClient("test_id", "test_key", "test_secret", "pro")
        self.assertIn("v3.1", client_pro.spark_url)
        self.assertEqual(client_pro.domain, "generalv3")
        
        # 测试默认版本
        client_default = LLMClient("test_id", "test_key", "test_secret")
        self.assertIn("v3.5", client_default.spark_url)
        
        # 测试未知版本回退
        client_unknown = LLMClient("test_id", "test_key", "test_secret", "unknown")
        self.assertIn("v3.5", client_unknown.spark_url)
        
        print("  LLM客户端版本测试通过")

    def test_llm_client_invalid_credentials(self):
        """测试LLM客户端无效凭证处理"""
        print("\n[集成测试] -> LLM客户端无效凭证测试")
        
        with self.assertRaises(ValueError):
            LLMClient("", "test_key", "test_secret")
        
        with self.assertRaises(ValueError):
            LLMClient("test_id", "", "test_secret")
            
        with self.assertRaises(ValueError):
            LLMClient("test_id", "test_key", "")
        
        print("  LLM客户端无效凭证测试通过")


class TestErrorScenarios(unittest.TestCase):
    """错误场景测试"""
    
    def setUp(self):
        self.llm_stub = LLMClientStub()
        self.interpreter = TestableDSLInterpreter(self.llm_stub)

    def test_invalid_dsl_script(self):
        """测试无效DSL脚本处理"""
        print("\n[错误场景测试] -> 无效DSL脚本测试")
        
        invalid_scripts = [
            'Step test\nInvalidAction',  # 无效动作
            'Step test\nSpeak',  # 缺少字符串参数
            'Step test\nBranch "key"',  # 缺少步骤名
        ]
        
        for script in invalid_scripts:
            with self.subTest(msg=f"脚本: {script[:30]}..."):
                success = self.interpreter.load_dsl_script(script)
                self.assertFalse(success, "应该检测到DSL语法错误")
        
        print("  无效DSL脚本测试通过")

    def test_missing_step_handling(self):
        """测试缺失步骤处理"""
        print("\n[错误场景测试] -> 缺失步骤处理测试")
        
        # 加载一个不完整的DSL脚本
        incomplete_script = """
Step welcome
  Speak "欢迎"
  Branch "下一步", non_existent_step
  Default default_proc

Step default_proc
  Speak "默认处理"
"""
        success = self.interpreter.load_dsl_script(incomplete_script)
        self.assertTrue(success)
        
        # 触发跳转到不存在的步骤
        response = self.interpreter.process_input("下一步")
        # 更新断言以匹配实际实现
        self.assertIn("步骤不存在", response)
        
        print("  缺失步骤处理测试通过")

    def test_empty_user_input(self):
        """测试空用户输入处理"""
        print("\n[错误场景测试] -> 空用户输入测试")
        
        success = self.interpreter.load_dsl_script(DSLScriptStub.get_test_dsl())
        self.assertTrue(success)
        
        # 测试空输入
        response = self.interpreter.process_input("")
        self.assertIn("抱歉", response)
        self.assertIn("不太理解", response)
        
        # 测试只有空格的输入
        response = self.interpreter.process_input("   ")
        self.assertIn("抱歉", response)
        self.assertIn("不太理解", response)
        
        print("  空用户输入测试通过")


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
    suite.addTests(loader.loadTestsFromTestCase(TestErrorScenarios))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)#2表示详细模式
    result = runner.run(suite)
    
    # 输出测试结果摘要
    print("\n" + "="*50)
    print("测试结果摘要:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    # 输出失败的测试详情
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback.splitlines()[-1]}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback.splitlines()[-1]}")
    
    print("="*50)
    
    # 如果有失败或错误，退出码为1
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)