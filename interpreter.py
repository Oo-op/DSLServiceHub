# interpreter.py

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

# 关键词集
KEYWORDS = {"Step", "Speak", "Listen", "Branch", "Silence", "Default", "Exit"}

class Token:
    def __init__(self, type: TokenType, value: Optional[str]):
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
        self.script = script
        self.pos = 0
        self.length = len(script)

    def peek(self) -> str:
        return self.script[self.pos] if self.pos < self.length else ""

    def advance(self):
        self.pos += 1

    def skip_whitespace_and_comments(self):
        """跳过所有空白符和注释"""
        while self.pos < self.length:
            if self.script[self.pos].isspace():
                self.pos += 1
            elif self.script[self.pos] == '#':
                while self.pos < self.length and self.script[self.pos] != '\n':
                    self.pos += 1
            else:
                break

    def parse_string(self) -> str:
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
        number_value = []
        while self.pos < self.length and self.script[self.pos].isdigit():
            number_value.append(self.script[self.pos])
            self.advance()
        return ''.join(number_value)

    def parse_identifier_or_keyword(self) -> Token:
        start_pos = self.pos
        while self.pos < self.length and (self.script[self.pos].isalnum() or self.script[self.pos] == '_'):
            self.advance()
        id_str = self.script[start_pos:self.pos]
        if id_str in KEYWORDS:
            return Token(TokenType.KEYWORD, id_str)
        return Token(TokenType.IDENTIFIER, id_str)

    def next_token(self) -> Token:
        self.skip_whitespace_and_comments()

        if self.pos >= self.length:
            return Token(TokenType.EOF, None)

        current_char = self.peek()

        if current_char == '"':
            return Token(TokenType.STRING, self.parse_string())
        if current_char.isdigit():
            return Token(TokenType.NUMBER, self.parse_number())
        if current_char == ',':
            self.advance()
            return Token(TokenType.SYMBOL, ',')
        if current_char.isalpha() or current_char == '_':
            return self.parse_identifier_or_keyword()

        raise LexicalError(f"非法字符：{current_char}（位置：{self.pos}）")

    def tokenize(self) -> List[Token]:
        tokens = []
        while True:
            token = self.next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return tokens

# --- 抽象语法树 (AST) 节点定义 ---

class ASTNode:
    """抽象语法树节点基类"""
    pass

class Program(ASTNode):
    def __init__(self, steps: List['StepNode']):
        self.steps = steps

class StepNode(ASTNode):
    def __init__(self, name: str, actions: List['ActionNode']):
        self.name = name
        self.actions = actions

ActionNode = Union['SpeakNode', 'ListenNode', 'BranchNode', 'DefaultNode', 'ExitNode', 'SilenceNode']

class SpeakNode(ASTNode):
    def __init__(self, message: str):
        self.message = message

class ListenNode(ASTNode):
    def __init__(self, min_time: int, max_time: int):
        self.min_time = min_time
        self.max_time = max_time

class BranchNode(ASTNode):
    def __init__(self, keyword: str, step_name: str):
        self.keyword = keyword
        self.step_name = step_name

class DefaultNode(ASTNode):
    def __init__(self, step_name: str):
        self.step_name = step_name

class ExitNode(ASTNode):
    pass

class SilenceNode(ASTNode):
    def __init__(self, step_name: str):
        self.step_name = step_name

class SyntaxError(Exception):
    """语法错误异常"""
    pass

# --- 语法分析器 (Parser) ---

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else Token(TokenType.EOF, None)

    def advance(self):
        self.pos += 1

    def expect(self, token_type: TokenType, value: Optional[str] = None) -> Token:
        """检查当前Token是否符合预期，如果符合则消耗它并返回，否则抛出异常"""
        token = self.current_token()
        if token.type != token_type:
            raise SyntaxError(f"在位置 {self.pos}，期望的Token类型是 {token_type.name}，但实际是 {token.type.name}")
        if value is not None and token.value != value:
            raise SyntaxError(f"在位置 {self.pos}，期望的Token值是 '{value}'，但实际是 '{token.value}'")
        self.advance()
        return token

    def parse_program(self) -> Program:
        steps = []
        while self.current_token().type != TokenType.EOF:
            steps.append(self.parse_step())
        return Program(steps)

    def parse_step(self) -> StepNode:
        """
        解析一个完整的Step块。
        这是关键的修正点。
        """
        self.expect(TokenType.KEYWORD, "Step")
        step_name = self.expect(TokenType.IDENTIFIER).value
        actions = []

        # **核心修正**: 循环解析动作，直到遇到下一个 Step 或文件结束
        while self.current_token().type != TokenType.EOF and \
              not (self.current_token().type == TokenType.KEYWORD and self.current_token().value == "Step"):
            
            action_token = self.current_token()
            if action_token.type != TokenType.KEYWORD:
                raise SyntaxError(f"在步骤 '{step_name}' 中，期望一个动作关键词 (如 Speak, Listen)，但得到 {action_token}")

            if action_token.value == "Speak":
                actions.append(self.parse_speak())
            elif action_token.value == "Listen":
                actions.append(self.parse_listen())
            elif action_token.value == "Branch":
                actions.append(self.parse_branch())
            elif action_token.value == "Default":
                actions.append(self.parse_default())
            elif action_token.value == "Silence":
                actions.append(self.parse_silence())
            elif action_token.value == "Exit":
                actions.append(self.parse_exit())
            else:
                raise SyntaxError(f"在步骤 '{step_name}' 中，遇到未知的关键词 '{action_token.value}'")
        
        return StepNode(name=step_name, actions=actions)

    def parse_speak(self) -> SpeakNode:
        self.expect(TokenType.KEYWORD, "Speak")
        message = self.expect(TokenType.STRING).value
        return SpeakNode(message)

    def parse_listen(self) -> ListenNode:
        self.expect(TokenType.KEYWORD, "Listen")
        min_time = int(self.expect(TokenType.NUMBER).value)
        self.expect(TokenType.SYMBOL, ",")
        max_time = int(self.expect(TokenType.NUMBER).value)
        return ListenNode(min_time, max_time)

    def parse_branch(self) -> BranchNode:
        self.expect(TokenType.KEYWORD, "Branch")
        keyword = self.expect(TokenType.STRING).value
        self.expect(TokenType.SYMBOL, ",")
        step_name = self.expect(TokenType.IDENTIFIER).value
        return BranchNode(keyword, step_name)

    def parse_default(self) -> DefaultNode:
        self.expect(TokenType.KEYWORD, "Default")
        step_name = self.expect(TokenType.IDENTIFIER).value
        return DefaultNode(step_name)

    def parse_silence(self) -> SilenceNode:
        self.expect(TokenType.KEYWORD, "Silence")
        step_name = self.expect(TokenType.IDENTIFIER).value
        return SilenceNode(step_name)

    def parse_exit(self) -> ExitNode:
        self.expect(TokenType.KEYWORD, "Exit")
        return ExitNode()
