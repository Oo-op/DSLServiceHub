from enum import Enum
import re

class TokenType(Enum):
    KEYWORD = 1      # Step, Speak, Listen 等
    IDENTIFIER = 2   # 步骤名（welcome, ticketProc）
    STRING = 3       # 双引号包裹的字符串
    NUMBER = 4       # 非负整数
    SYMBOL = 5       # 逗号 ,
    EOF = 6          # 文件结束

# 关键词集
KEYWORDS = {"Step", "Speak", "Listen", "Branch", "Silence", "Default", "Exit"}

class Token:
    def __init__(self, type: TokenType, value: str):
        self.type = type
        self.value = value

    def __str__(self):
        return f"({self.type.name}, {repr(self.value)})"

class LexicalError(Exception):
    """词法错误异常"""
    pass

class Lexer:
    """词法分析器：将DSL脚本转换为Token流"""
    def __init__(self, script: str):
        self.script = script  # 输入的DSL脚本
        self.pos = 0  # 当前扫描位置（索引）
        self.length = len(script)  # 脚本总长度

    def peek(self) -> str:
        """查看当前位置的字符，不移动指针"""
        if self.pos < self.length:
            return self.script[self.pos]
        else:
            return ""

    def advance(self):
        """移动指针到下一个字符"""
        self.pos += 1

    def skip_whitespace(self):
        """跳过空白符（空格、制表符、换行、回车）"""
        while self.pos < self.length and self.script[self.pos].isspace():
            self.advance()

    def skip_comment(self):
        """跳过注释（# 到行尾）"""
        if self.peek() == "#":
            while self.pos < self.length and self.script[self.pos] != "\n":
                self.advance()
            self.advance()  # 跳过换行符

    def parse_string(self) -> str:
        """解析字符串（双引号包裹）"""
        self.advance()  # 跳过开头的 "
        string_value = []
        while self.pos < self.length and self.script[self.pos] != '"':
            string_value.append(self.script[self.pos])
            self.advance()
        if self.pos >= self.length or self.script[self.pos] != '"':
            raise LexicalError(f"未闭合的字符串：{''.join(string_value)}")
        self.advance()  # 跳过结尾的 "
        return ''.join(string_value)

    def parse_number(self) -> str:
        """解析数字（非负整数）"""
        number_value = []
        while self.pos < self.length and self.script[self.pos].isdigit():
            number_value.append(self.script[self.pos])
            self.advance()
        return ''.join(number_value)

    def parse_identifier_or_keyword(self) -> Token:
        """解析标识符或关键词（字母/下划线开头）"""
        id_value = []
        while self.pos < self.length and (self.script[self.pos].isalnum() or self.script[self.pos] == '_'):
            id_value.append(self.script[self.pos])
            self.advance()
        id_str = ''.join(id_value)
        # 判断是否为关键词
        if id_str in KEYWORDS:
            return Token(TokenType.KEYWORD, id_str)
        return Token(TokenType.IDENTIFIER, id_str)

    def next_token(self) -> Token:
        """获取下一个Token（核心方法）"""
        while self.pos < self.length:
            current_char = self.peek()

            # 1. 跳过空白符
            if current_char.isspace():
                self.skip_whitespace()
                continue

            # 2. 跳过注释
            if current_char == "#":
                self.skip_comment()
                continue

            # 3. 匹配字符串（"开头）
            if current_char == '"':
                string_val = self.parse_string()
                return Token(TokenType.STRING, string_val)

            # 4. 匹配数字（0-9开头）
            if current_char.isdigit():
                number_val = self.parse_number()
                return Token(TokenType.NUMBER, number_val)

            # 5. 匹配符号（逗号）
            if current_char == ',':
                self.advance()
                return Token(TokenType.SYMBOL, ',')

            # 6. 匹配标识符或关键词（字母/下划线开头）
            if current_char.isalpha() or current_char == '_':
                return self.parse_identifier_or_keyword()

            # 7. 未匹配到任何规则，抛出错误
            raise LexicalError(f"非法字符：{current_char}（位置：{self.pos}）")

        # 8. 脚本结束，返回EOF Token
        return Token(TokenType.EOF, None)

    def tokenize(self) -> list[Token]:
        """将整个脚本转换为Token列表"""
        tokens = []
        while True:
            token = self.next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return tokens

# ------------------------------
# 测试：用你的DSL脚本验证词法分析器
# ------------------------------
if __name__ == "__main__":
    # 读取你的DSL脚本（这里直接嵌入示例脚本）
    dsl_script = """Step welcome
  Speak "您好，请问有什么可以帮您的？"
  Listen 5, 20  # 等待用户输入
    #若0-5秒内用户有输入：直接执行后续的Branch关键词匹配；
  Branch "门票", ticketProc  
  Default defaultProc
Exit"""

    # 初始化词法分析器并分词
    lexer = Lexer(dsl_script)
    try:
        tokens = lexer.tokenize()
        # 打印Token流
        print("DSL脚本 → Token流：")
        for token in tokens:
            print(token)
    except LexicalError as e:
        print(f"词法错误：{e}")



class ASTNode:
    """抽象语法树节点基类"""
    pass

class Program(ASTNode):  # 修正：类名应该大写
    """根节点，程序节点，包含多个步骤"""
    def __init__(self, steps: list['StepNode']):
        self.steps = steps

class StepNode(ASTNode):
    """步骤节点，包含步骤名和多个操作"""
    def __init__(self, name: str, actions: list['ActionNode']):
        self.name = name
        self.actions = actions

# 语句节点（Stmt）：对应DSL中的具体操作
class SpeakNode(ASTNode):
    """Speak语句节点"""
    def __init__(self, message: str):
        self.message = message

class ListenNode(ASTNode):
    """Listen语句节点"""
    def __init__(self, min_time: int, max_time: int):
        self.min_time = min_time
        self.max_time = max_time

class BranchNode(ASTNode):
    """Branch语句节点"""
    def __init__(self, keyword: str, step_name: str):
        self.keyword = keyword
        self.step_name = step_name

class DefaultNode(ASTNode):
    """Default语句节点"""
    def __init__(self, step_name: str):
        self.step_name = step_name

class ExitNode(ASTNode):
    """Exit语句节点"""
    pass

class SilenceNode(ASTNode):
    """Silence语句节点"""
    def __init__(self, step_name: str):
        self.step_name = step_name

class SyntaxError(Exception):  # 修正：拼写错误
    """语法错误异常"""
    pass

class Parser:
    """语法分析器：将Token流转换为抽象语法树（AST）"""
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens  # 输入的Token列表
        self.pos = 0  # 当前解析位置（索引）
        self.length = len(tokens)  # Token总数

    def peek_token(self) -> Token:
        """查看当前Token，不移动指针"""
        if self.pos < self.length:
            return self.tokens[self.pos]
        else:
            return Token(TokenType.EOF, None)
    
    def move(self, expected_type: TokenType, expected_value: str = None) -> Token:
        """移动到下一个Token，并返回当前Token"""
        if self.pos >= self.length:
            raise SyntaxError("意外的文件结尾")
        current_token = self.tokens[self.pos]
        if current_token.type != expected_type:
            raise SyntaxError(f"预期的Token类型：{expected_type.name}，实际类型：{current_token.type.name}")
        if expected_value is not None and current_token.value != expected_value:
            raise SyntaxError(f"预期的Token值：{expected_value}，实际值：{current_token.value}")
        self.pos += 1
        return current_token
    
    def parse_program(self) -> Program:  # 修正：方法名拼写
        """解析程序"""
        steps = []
        while self.peek_token().type != TokenType.EOF:
            if self.peek_token().type == TokenType.KEYWORD and self.peek_token().value == "Step":
                steps.append(self.parse_step())
            else:
                raise SyntaxError(f"预期的Step关键词，实际：{self.peek_token().value}")
        return Program(steps)
    
    def parse_step(self) -> StepNode:
        """解析步骤"""
        self.move(TokenType.KEYWORD, "Step")
        step_name_token = self.move(TokenType.IDENTIFIER)
        actions = []
        
        # 持续解析直到遇到下一个Step或文件结束
        while (self.peek_token().type != TokenType.EOF and 
               not (self.peek_token().type == TokenType.KEYWORD and self.peek_token().value == "Step")):
            
            current_token = self.peek_token()
            if current_token.type == TokenType.KEYWORD:
                if current_token.value == "Speak":
                    actions.append(self.parse_speak())
                elif current_token.value == "Listen":
                    actions.append(self.parse_listen())
                elif current_token.value == "Branch":
                    actions.append(self.parse_branch())
                elif current_token.value == "Default":
                    actions.append(self.parse_default())
                elif current_token.value == "Exit":
                    actions.append(self.parse_exit())
                elif current_token.value == "Silence":
                    actions.append(self.parse_silence())
                else:
                    raise SyntaxError(f"未知的关键词：{current_token.value}")
            else:
                # 如果不是关键词，可能是意外的Token
                raise SyntaxError(f"预期的关键词，实际：{current_token.type.name} ({current_token.value})")
                
        return StepNode(step_name_token.value, actions)
    
    def parse_speak(self) -> SpeakNode:  # 修正：移除了class关键字
        """解析Speak语句"""
        self.move(TokenType.KEYWORD, "Speak")
        string_token = self.move(TokenType.STRING)
        return SpeakNode(string_token.value)

    def parse_listen(self) -> ListenNode:  # 修正：移除了class关键字
        """解析Listen语句"""
        self.move(TokenType.KEYWORD, "Listen")
        min_time_token = self.move(TokenType.NUMBER)
        self.move(TokenType.SYMBOL, ",")
        max_time_token = self.move(TokenType.NUMBER)
        return ListenNode(int(min_time_token.value), int(max_time_token.value))

    def parse_branch(self) -> BranchNode:  # 修正：移除了class关键字
        """解析Branch语句"""
        self.move(TokenType.KEYWORD, "Branch")
        keyword_token = self.move(TokenType.STRING)
        self.move(TokenType.SYMBOL, ",")  # 添加：解析逗号
        step_name_token = self.move(TokenType.IDENTIFIER)
        return BranchNode(keyword_token.value, step_name_token.value)

    def parse_default(self) -> DefaultNode:  # 修正：移除了class关键字
        """解析Default语句"""
        self.move(TokenType.KEYWORD, "Default")
        step_name_token = self.move(TokenType.IDENTIFIER)
        return DefaultNode(step_name_token.value)

    def parse_exit(self) -> ExitNode:  # 修正：移除了class关键字
        """解析Exit语句"""
        self.move(TokenType.KEYWORD, "Exit")
        return ExitNode()   

    def parse_silence(self) -> SilenceNode:  # 修正：移除了class关键字
        """解析Silence语句"""
        self.move(TokenType.KEYWORD, "Silence")
        step_name_token = self.move(TokenType.IDENTIFIER)
        return SilenceNode(step_name_token.value)


# ------------------------------
# 测试语法分析器
# ------------------------------
def test_parser():
    """测试语法分析器"""
    dsl_script = """Step welcome
  Speak "您好，请问有什么可以帮您的？"
  Listen 5, 20
  Branch "门票", ticketProc  
  Default defaultProc
  Silence timeoutProc
Exit

Step ticketProc
  Speak "您想查询门票信息吗？"
  Exit

Step defaultProc
  Speak "抱歉，我不理解您的意思"
  Exit"""

    try:
        # 1. 词法分析
        lexer = Lexer(dsl_script)
        tokens = lexer.tokenize()
        
        print("=== 词法分析结果 ===")
        for token in tokens:
            print(token)
        print()
        
        # 2. 语法分析
        parser = Parser(tokens)
        ast = parser.parse_program()
        
        print("=== 语法分析成功 ===")
        print(f"程序包含 {len(ast.steps)} 个步骤")
        for i, step in enumerate(ast.steps):
            print(f"步骤 {i+1}: {step.name}, 包含 {len(step.actions)} 个操作")
            for j, action in enumerate(step.actions):
                action_type = type(action).__name__
                if isinstance(action, SpeakNode):
                    print(f"  - {action_type}: '{action.message}'")
                elif isinstance(action, ListenNode):
                    print(f"  - {action_type}: {action.min_time}-{action.max_time}秒")
                elif isinstance(action, BranchNode):
                    print(f"  - {action_type}: 关键词 '{action.keyword}' -> 步骤 '{action.step_name}'")
                elif isinstance(action, DefaultNode):
                    print(f"  - {action_type}: -> 步骤 '{action.step_name}'")
                elif isinstance(action, SilenceNode):
                    print(f"  - {action_type}: -> 步骤 '{action.step_name}'")
                elif isinstance(action, ExitNode):
                    print(f"  - {action_type}")
        
        return ast
        
    except LexicalError as e:
        print(f"❌ 词法错误：{e}")
    except SyntaxError as e:
        print(f"❌ 语法错误：{e}")
    except Exception as e:
        print(f"❌ 其他错误：{e}")

if __name__ == "__main__":
    test_parser()