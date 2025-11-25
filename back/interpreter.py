# 文件名: interpreter.py
from enum import Enum
from typing import List, Optional, Union

class TokenType(Enum):
    KEYWORD = 1      # Step, Speak, Listen 等
    IDENTIFIER = 2   # 步骤名
    STRING = 3       # 字符串
    NUMBER = 4       # 数字
    SYMBOL = 5       # 符号 ,
    EOF = 6          # 文件结束

KEYWORDS = {"Step", "Speak", "Listen", "Branch", "Silence", "Default", "Exit"}

class Token:
    def __init__(self, type: TokenType, value: Optional[str], line: int):
        self.type = type
        self.value = value
        self.line = line  

    def __str__(self): return f"Line {self.line}: ({self.type.name}, {repr(self.value)})"

class LexicalError(Exception): pass
class SyntaxError(Exception): pass

class Lexer:
    """词法分析器：将DSL脚本转换为Token流"""
    def __init__(self, script: str):
        self.script = script
        self.pos = 0
        self.line = 1  # 当前行号

    def skip_whitespace_and_comments(self):
        while self.pos < len(self.script):
            char = self.script[self.pos]
            if char == '\n':
                self.line += 1
                self.pos += 1
            elif char.isspace():
                self.pos += 1
            elif char == '#':
                while self.pos < len(self.script) and self.script[self.pos] != '\n':
                    self.pos += 1
            else:
                break

    def get_token(self) -> Token:
        self.skip_whitespace_and_comments()
        if self.pos >= len(self.script):
            return Token(TokenType.EOF, None, self.line)

        char = self.script[self.pos]

        # 字符串处理
        if char == '"':
            self.pos += 1
            start_pos = self.pos
            while self.pos < len(self.script) and self.script[self.pos] != '"':
                if self.script[self.pos] == '\n': self.line += 1
                self.pos += 1
            if self.pos >= len(self.script):
                raise LexicalError(f"Line {self.line}: 未闭合的字符串")
            value = self.script[start_pos:self.pos]
            self.pos += 1
            return Token(TokenType.STRING, value, self.line)

        # 数字处理
        if char.isdigit():
            start_pos = self.pos
            while self.pos < len(self.script) and self.script[self.pos].isdigit():
                self.pos += 1
            return Token(TokenType.NUMBER, self.script[start_pos:self.pos], self.line)

        # 标识符/关键词处理
        if char.isalpha() or char == '_':
            start_pos = self.pos
            while self.pos < len(self.script) and (self.script[self.pos].isalnum() or self.script[self.pos] == '_'):
                self.pos += 1
            value = self.script[start_pos:self.pos]
            if value in KEYWORDS:
                return Token(TokenType.KEYWORD, value, self.line)
            return Token(TokenType.IDENTIFIER, value, self.line)

        # 符号处理
        if char == ',':
            self.pos += 1
            return Token(TokenType.SYMBOL, ',', self.line)

        raise LexicalError(f"Line {self.line}: 非法字符 '{char}'")

    def tokenize(self) -> List[Token]:
        tokens = []
        while True:
            token = self.get_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return tokens

# --- AST 节点定义 ---
class ASTNode: pass

class ProgramNode(ASTNode):
    def __init__(self, steps: List['StepNode']): self.steps = steps

class StepNode(ASTNode):
    def __init__(self, name: str, actions: List['ActionNode']): 
        self.name, self.actions = name, actions

class SpeakNode(ASTNode):
    def __init__(self, message: str): self.message = message

class ListenNode(ASTNode):
    def __init__(self, timeout: int = 10, retries: int = 3):
        self.timeout = timeout
        self.retries = retries

class BranchNode(ASTNode):
    def __init__(self, keyword: str, step_name: str): 
        self.keyword, self.step_name = keyword, step_name

class DefaultNode(ASTNode):
    def __init__(self, step_name: str): self.step_name = step_name

class ExitNode(ASTNode): pass

class SilenceNode(ASTNode):
    def __init__(self, step_name: str): self.step_name = step_name

ActionNode = Union[SpeakNode, ListenNode, BranchNode, DefaultNode, ExitNode, SilenceNode]

# --- 解析器 ---
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token: return self.tokens[self.pos]
    
    def advance(self): self.pos += 1

    def expect(self, type: TokenType, value: Optional[str] = None):
        token = self.current()
        if token.type != type or (value is not None and token.value != value):
            raise SyntaxError(f"Line {token.line}: 语法错误 - 期望 {type.name}({value}), 得到 {token.type.name}({token.value})")
        self.advance()
        return token

    def parse_program(self) -> ProgramNode:
        steps = []
        while self.current().type != TokenType.EOF:
            steps.append(self.parse_step())
        return ProgramNode(steps)

    def parse_step(self) -> StepNode:
        self.expect(TokenType.KEYWORD, "Step")
        step_name = self.expect(TokenType.IDENTIFIER).value
        actions = []
        # 读取直到遇到下一个 Step 或 EOF
        while self.current().type != TokenType.EOF and not (self.current().type == TokenType.KEYWORD and self.current().value == "Step"):
            keyword = self.current().value
            if keyword == "Speak": actions.append(self.parse_speak())
            elif keyword == "Listen": actions.append(self.parse_listen())
            elif keyword == "Branch": actions.append(self.parse_branch())
            elif keyword == "Default": actions.append(self.parse_default())
            elif keyword == "Silence": actions.append(self.parse_silence())
            elif keyword == "Exit": actions.append(self.parse_exit())
            else: raise SyntaxError(f"Line {self.current().line}: 未知指令 '{keyword}' 在步骤 '{step_name}' 中")
        return StepNode(name=step_name, actions=actions)

    def parse_speak(self) -> SpeakNode:
        self.expect(TokenType.KEYWORD, "Speak")
        message = self.expect(TokenType.STRING).value
        message = message.replace('\\n', '\n')
        return SpeakNode(message)

    def parse_listen(self) -> ListenNode:
        self.expect(TokenType.KEYWORD, "Listen")
        timeout = 10  # 默认值
        retries = 3   # 默认值
        
        # 尝试解析参数: Listen [timeout], [retries]
        if self.current().type == TokenType.NUMBER:
            timeout = int(self.current().value)
            self.advance()
            if self.current().type == TokenType.SYMBOL and self.current().value == ',':
                self.advance()
                if self.current().type == TokenType.NUMBER:
                    retries = int(self.current().value)
                    self.advance()
        
        return ListenNode(timeout, retries)

    def parse_branch(self) -> BranchNode:
        self.expect(TokenType.KEYWORD, "Branch")
        keyword = self.expect(TokenType.STRING).value
        if self.current().type == TokenType.SYMBOL and self.current().value == ',':
            self.advance()
        step_name = self.expect(TokenType.IDENTIFIER).value
        return BranchNode(keyword, step_name)

    def parse_default(self) -> DefaultNode:
        self.expect(TokenType.KEYWORD, "Default")
        return DefaultNode(self.expect(TokenType.IDENTIFIER).value)

    def parse_silence(self) -> SilenceNode:
        self.expect(TokenType.KEYWORD, "Silence")
        return SilenceNode(self.expect(TokenType.IDENTIFIER).value)

    def parse_exit(self) -> ExitNode:
        self.expect(TokenType.KEYWORD, "Exit")
        return ExitNode()