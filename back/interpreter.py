# 文件名: interpreter.py
from enum import Enum
from typing import List, Optional, Union

class TokenType(Enum):
    KEYWORD = 1
    IDENTIFIER = 2
    STRING = 3
    NUMBER = 4
    SYMBOL = 5
    EOF = 6

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
    def __init__(self, script: str):
        self.script = script# 源代码
        self.pos = 0
        self.line = 1

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

    def get_token(self) -> Token:#获取单个Token
        self.skip_whitespace_and_comments()
        if self.pos >= len(self.script):
            return Token(TokenType.EOF, None, self.line)
        char = self.script[self.pos]

        # 字符串解析：从"开始到"结束
        if char == '"':
            self.pos += 1
            start = self.pos#字符串开始位置
            while self.pos < len(self.script) and self.script[self.pos] != '"':
                if self.script[self.pos] == '\n': self.line += 1
                self.pos += 1
            if self.pos >= len(self.script): 
                raise LexicalError(f"Line {self.line}: Unclosed string")
            val = self.script[start:self.pos]
            self.pos += 1
            return Token(TokenType.STRING, val, self.line)
        
        # 数字解析：连续数字字符
        if char.isdigit():
            start = self.pos
            while self.pos < len(self.script) and self.script[self.pos].isdigit(): self.pos += 1
            return Token(TokenType.NUMBER, self.script[start:self.pos], self.line)
        
        # 标识符和关键字：字母或下划线开头
        if char.isalpha() or char == '_':
            start = self.pos
            while self.pos < len(self.script) and (self.script[self.pos].isalnum() or self.script[self.pos] == '_'): self.pos += 1
            val = self.script[start:self.pos]
            #检查是否是关键字
            return Token(TokenType.KEYWORD if val in KEYWORDS else TokenType.IDENTIFIER, val, self.line)
        
        # 符号：逗号
        if char == ',':
            self.pos += 1
            return Token(TokenType.SYMBOL, ',', self.line)
        # 非法字符
        raise LexicalError(f"Line {self.line}: Illegal char '{char}'")

    #词法分析主函数，获取所有token，生成token序列
    def tokenize(self) -> List[Token]:
        tokens = []
        while True:
            t = self.get_token()
            tokens.append(t)
            if t.type == TokenType.EOF: break
        return tokens

class ASTNode: pass # 抽象语法树节点基类

class ProgramNode(ASTNode):# 程序节点，包含多个步骤
    def __init__(self, steps: List['StepNode']): self.steps = steps
class StepNode(ASTNode):# 步骤节点，包含多个动作
    def __init__(self, name: str, actions: List['ActionNode']): self.name, self.actions = name, actions
class SpeakNode(ASTNode):# 说话节点
    def __init__(self, message: str): self.message = message
class ListenNode(ASTNode):# 听取节点
    def __init__(self, timeout: int = 10, total_silence_timeout: int = 40):
        self.timeout = timeout # 单次提醒超时
        self.total_silence_timeout = total_silence_timeout # 总静默超时，用于终止
class BranchNode(ASTNode):# 分支节点
    def __init__(self, keyword: str, step_name: str): self.keyword, self.step_name = keyword, step_name
class DefaultNode(ASTNode):# 默认节点
    def __init__(self, step_name: str): self.step_name = step_name
class ExitNode(ASTNode): pass# 退出节点
class SilenceNode(ASTNode):# 静默处理节点
    def __init__(self, step_name: str): self.step_name = step_name
ActionNode = Union[SpeakNode, ListenNode, BranchNode, DefaultNode, ExitNode, SilenceNode]# 动作节点类型别名

class Parser:
    def __init__(self, tokens: List[Token]): 
        self.tokens, self.pos = tokens, 0 #词法单元列表
    def current(self) -> Token: return self.tokens[self.pos]# 获取当前Token
    def advance(self): self.pos += 1# 移动到下一个Token
    def expect(self, type: TokenType, value: Optional[str] = None):
        t = self.current()#检查当前token是否符合预期
        if t.type != type or (value and t.value != value): raise SyntaxError(f"Line {t.line}: Expected {type} {value}, got {t.type} {t.value}")
        self.advance()
        return t
    def parse_program(self) -> ProgramNode:
        steps = []# 解析所有步骤
        while self.current().type != TokenType.EOF: steps.append(self.parse_step())
        return ProgramNode(steps)
    
    def parse_step(self) -> StepNode:
        self.expect(TokenType.KEYWORD, "Step")
        name = self.expect(TokenType.IDENTIFIER).value# 步骤名称
        actions = []# 解析步骤内的所有动作，直到遇到下一个step或eof
        while self.current().type != TokenType.EOF and not (self.current().type == TokenType.KEYWORD and self.current().value == "Step"):
            k = self.current().value
            # 根据动作类型调用相应的解析方法
            if k == "Speak": actions.append(self.parse_speak())
            elif k == "Listen": actions.append(self.parse_listen())
            elif k == "Branch": actions.append(self.parse_branch())
            elif k == "Default": actions.append(self.parse_default())
            elif k == "Silence": actions.append(self.parse_silence())
            elif k == "Exit": actions.append(self.parse_exit())
            else: raise SyntaxError(f"Line {self.current().line}: Unknown action '{k}'")
        return StepNode(name, actions)
    
    def parse_speak(self):
        self.expect(TokenType.KEYWORD, "Speak")
        return SpeakNode(self.expect(TokenType.STRING).value.replace('\\n', '\n'))
    def parse_listen(self):
        self.expect(TokenType.KEYWORD, "Listen")
        timeout = 10  # Default single timeout
        total_silence_timeout = 30 # Default total timeout

        # Listen 10, 50
        if self.current().type == TokenType.NUMBER:
            # First number is the single timeout for reminder
            timeout = int(self.current().value)
            self.advance()
            if self.current().type == TokenType.SYMBOL and self.current().value == ',':
                self.advance()
                if self.current().type == TokenType.NUMBER:
                    # Second number is the total silence duration before termination
                    total_silence_timeout = int(self.current().value)
                    self.advance()
        return ListenNode(timeout, total_silence_timeout)
    def parse_branch(self):
        self.expect(TokenType.KEYWORD, "Branch")
        k = self.expect(TokenType.STRING).value
        if self.current().type == TokenType.SYMBOL: self.advance()
        return BranchNode(k, self.expect(TokenType.IDENTIFIER).value)
    def parse_default(self): self.expect(TokenType.KEYWORD, "Default"); return DefaultNode(self.expect(TokenType.IDENTIFIER).value)
    def parse_silence(self): self.expect(TokenType.KEYWORD, "Silence"); return SilenceNode(self.expect(TokenType.IDENTIFIER).value)
    def parse_exit(self): self.expect(TokenType.KEYWORD, "Exit"); return ExitNode()