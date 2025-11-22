# 文件名: interpreter.py

from enum import Enum
import re
from typing import List, Optional, Union

class TokenType(Enum):
    KEYWORD = 1      # Step, Speak, Listen 等
    IDENTIFIER = 2   # 步骤名（welcome, ticketProc）
    STRING = 3       # 双引号包裹的字符串
    NUMBER = 4       # 非负整数
    SYMBOL = 5       # 逗号 ,
    EOF = 6          # 文件结束

KEYWORDS = {"Step", "Speak", "Listen", "Branch", "Silence", "Default", "Exit"}

class Token:
    def __init__(self, type: TokenType, value: Optional[str]):
        self.type = type
        self.value = value
    def __str__(self): return f"({self.type.name}, {repr(self.value)})"

class LexicalError(Exception): pass

class Lexer:
    """词法分析器：将DSL脚本转换为Token流"""
    def __init__(self, script: str):
        self.script = script
        self.pos = 0

    def skip_whitespace_and_comments(self):
        while self.pos < len(self.script):
            if self.script[self.pos].isspace():
                self.pos += 1
            elif self.script[self.pos] == '#':
                while self.pos < len(self.script) and self.script[self.pos] != '\n':
                    self.pos += 1
            else:
                break

    def get_token(self) -> Token:
        self.skip_whitespace_and_comments()
        if self.pos >= len(self.script): return Token(TokenType.EOF, None)
        
        char = self.script[self.pos]
        if char == '"':
            self.pos += 1
            start_pos = self.pos
            # 支持多行字符串
            while self.pos < len(self.script) and self.script[self.pos] != '"':
                self.pos += 1
            if self.pos >= len(self.script): raise LexicalError("未闭合的字符串")
            value = self.script[start_pos:self.pos]
            self.pos += 1
            return Token(TokenType.STRING, value)

        if char.isdigit():
            start_pos = self.pos
            while self.pos < len(self.script) and self.script[self.pos].isdigit():
                self.pos += 1
            return Token(TokenType.NUMBER, self.script[start_pos:self.pos])

        if char.isalpha() or char == '_':
            start_pos = self.pos
            while self.pos < len(self.script) and (self.script[self.pos].isalnum() or self.script[self.pos] == '_'):
                self.pos += 1
            value = self.script[start_pos:self.pos]
            if value in KEYWORDS:
                return Token(TokenType.KEYWORD, value)
            return Token(TokenType.IDENTIFIER, value)

        if char == ',':
            self.pos += 1
            return Token(TokenType.SYMBOL, ',')

        raise LexicalError(f"非法字符: '{char}' at position {self.pos}")

    def tokenize(self) -> List[Token]:
        tokens = []
        while True:
            token = self.get_token()
            if token.type == TokenType.EOF:
                tokens.append(token)
                break
            tokens.append(token)
        return tokens


class ASTNode: pass
class ProgramNode(ASTNode):
    def __init__(self, steps: List['StepNode']): self.steps = steps
class StepNode(ASTNode):
    def __init__(self, name: str, actions: List['ActionNode']): self.name, self.actions = name, actions
class SpeakNode(ASTNode):
    def __init__(self, message: str): self.message = message
class ListenNode(ASTNode):
    # 根据你的DSL，Listen可以不带参数
    pass
class BranchNode(ASTNode):
    def __init__(self, keyword: str, step_name: str): self.keyword, self.step_name = keyword, step_name
class DefaultNode(ASTNode):
    def __init__(self, step_name: str): self.step_name = step_name
class ExitNode(ASTNode): pass
class SilenceNode(ASTNode):
    def __init__(self, step_name: str): self.step_name = step_name

ActionNode = Union[SpeakNode, ListenNode, BranchNode, DefaultNode, ExitNode, SilenceNode]
class SyntaxError(Exception): pass

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token: return self.tokens[self.pos]
    def advance(self): self.pos += 1

    def expect(self, type: TokenType, value: Optional[str] = None):
        token = self.current()
        if token.type != type or (value is not None and token.value != value):
            raise SyntaxError(f"语法错误: 期望 {type.name}({value}), 得到 {token.type.name}({token.value})")
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
        while self.current().type != TokenType.EOF and not (self.current().type == TokenType.KEYWORD and self.current().value == "Step"):
            keyword = self.current().value
            if keyword == "Speak": actions.append(self.parse_speak())
            elif keyword == "Listen": actions.append(self.parse_listen())
            elif keyword == "Branch": actions.append(self.parse_branch())
            elif keyword == "Default": actions.append(self.parse_default())
            elif keyword == "Silence": actions.append(self.parse_silence())
            elif keyword == "Exit": actions.append(self.parse_exit())
            else: raise SyntaxError(f"未知指令 '{keyword}' 在步骤 '{step_name}' 中")
        return StepNode(name=step_name, actions=actions)

    def parse_speak(self) -> SpeakNode:
        self.expect(TokenType.KEYWORD, "Speak")
        message = self.expect(TokenType.STRING).value
        # 处理转义字符
        message = message.replace('\\n', '\n')
        return SpeakNode(message)

    def parse_listen(self) -> ListenNode:
        self.expect(TokenType.KEYWORD, "Listen")
        # 解析Listen后面的参数：数字,数字
        if self.current().type == TokenType.NUMBER:
            self.advance()  # 第一个数字
            if self.current().type == TokenType.SYMBOL and self.current().value == ',':
                self.advance()  # 逗号
                if self.current().type == TokenType.NUMBER:
                    self.advance()  # 第二个数字
        return ListenNode()

    def parse_branch(self) -> BranchNode:
        self.expect(TokenType.KEYWORD, "Branch")
        # DSL中Branch的第一个参数是字符串
        keyword = self.expect(TokenType.STRING).value
        # DSL中有逗号，需要处理
        if self.current().type == TokenType.SYMBOL and self.current().value == ',':
            self.advance()  # 跳过逗号
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