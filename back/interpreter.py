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
        self.script = script
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

    def get_token(self) -> Token:
        self.skip_whitespace_and_comments()
        if self.pos >= len(self.script):
            return Token(TokenType.EOF, None, self.line)
        char = self.script[self.pos]
        if char == '"':
            self.pos += 1
            start = self.pos
            while self.pos < len(self.script) and self.script[self.pos] != '"':
                if self.script[self.pos] == '\n': self.line += 1
                self.pos += 1
            if self.pos >= len(self.script): raise LexicalError(f"Line {self.line}: Unclosed string")
            val = self.script[start:self.pos]
            self.pos += 1
            return Token(TokenType.STRING, val, self.line)
        if char.isdigit():
            start = self.pos
            while self.pos < len(self.script) and self.script[self.pos].isdigit(): self.pos += 1
            return Token(TokenType.NUMBER, self.script[start:self.pos], self.line)
        if char.isalpha() or char == '_':
            start = self.pos
            while self.pos < len(self.script) and (self.script[self.pos].isalnum() or self.script[self.pos] == '_'): self.pos += 1
            val = self.script[start:self.pos]
            return Token(TokenType.KEYWORD if val in KEYWORDS else TokenType.IDENTIFIER, val, self.line)
        if char == ',':
            self.pos += 1
            return Token(TokenType.SYMBOL, ',', self.line)
        raise LexicalError(f"Line {self.line}: Illegal char '{char}'")

    def tokenize(self) -> List[Token]:
        tokens = []
        while True:
            t = self.get_token()
            tokens.append(t)
            if t.type == TokenType.EOF: break
        return tokens

class ASTNode: pass
class ProgramNode(ASTNode):
    def __init__(self, steps: List['StepNode']): self.steps = steps
class StepNode(ASTNode):
    def __init__(self, name: str, actions: List['ActionNode']): self.name, self.actions = name, actions
class SpeakNode(ASTNode):
    def __init__(self, message: str): self.message = message
# --- MODIFIED: ListenNode now stores total timeout ---
class ListenNode(ASTNode):
    def __init__(self, timeout: int = 10, total_silence_timeout: int = 30):
        self.timeout = timeout # 单次提醒超时
        self.total_silence_timeout = total_silence_timeout # 总静默超时，用于终止
class BranchNode(ASTNode):
    def __init__(self, keyword: str, step_name: str): self.keyword, self.step_name = keyword, step_name
class DefaultNode(ASTNode):
    def __init__(self, step_name: str): self.step_name = step_name
class ExitNode(ASTNode): pass
class SilenceNode(ASTNode):
    def __init__(self, step_name: str): self.step_name = step_name
ActionNode = Union[SpeakNode, ListenNode, BranchNode, DefaultNode, ExitNode, SilenceNode]

class Parser:
    def __init__(self, tokens: List[Token]): self.tokens, self.pos = tokens, 0
    def current(self) -> Token: return self.tokens[self.pos]
    def advance(self): self.pos += 1
    def expect(self, type: TokenType, value: Optional[str] = None):
        t = self.current()
        if t.type != type or (value and t.value != value): raise SyntaxError(f"Line {t.line}: Expected {type} {value}, got {t.type} {t.value}")
        self.advance()
        return t
    def parse_program(self) -> ProgramNode:
        steps = []
        while self.current().type != TokenType.EOF: steps.append(self.parse_step())
        return ProgramNode(steps)
    def parse_step(self) -> StepNode:
        self.expect(TokenType.KEYWORD, "Step")
        name = self.expect(TokenType.IDENTIFIER).value
        actions = []
        while self.current().type != TokenType.EOF and not (self.current().type == TokenType.KEYWORD and self.current().value == "Step"):
            k = self.current().value
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
    # --- MODIFIED: Correctly parse Listen parameters ---
    def parse_listen(self):
        self.expect(TokenType.KEYWORD, "Listen")
        timeout = 10  # Default single timeout
        total_silence_timeout = 30 # Default total timeout

        # Listen 10, 40
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