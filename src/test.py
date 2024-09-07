import re
from enum import Enum, auto
from typing import List, Tuple, Union, Optional, Dict, Callable
import operator

class TokenType(Enum):
    KEYWORD = auto()
    COMMAND = auto()
    TEXT = auto()
    EXPRESSION = auto()

class ASTNodeType(Enum):
    COMMAND = auto()
    LEGAL_PROCEEDINGS = auto()
    CASE_DISMISSED = auto()
    LEGAL_LOOPHOLE = auto()
    CONDITIONAL = auto()
    CUSTOM_FUNCTION = auto()
    FUNCTION_CALL = auto()
    EXPRESSION = auto()
    LICENSE_AGREEMENT = auto()
    TEXT = auto()

Token = Tuple[TokenType, Union[str, Tuple[str, Optional[str]]]]
ASTNode = Tuple[ASTNodeType, Union[None, List['ASTNode'], Tuple[str, Optional[str]], str]]

KEYWORDS = {
    'BEGIN_LICENSE_AGREEMENT', 'END_LICENSE_AGREEMENT', 'WHEREAS', 'AND WHEREAS', 'NOW, THEREFORE',
    'EXECUTE_AGREEMENT', 'GRANT OF LICENSE', 'TERM AND TERMINATION', 'LOOPHOLES', 'END_LOOPHOLES',
    'COMMENCE_LEGAL_PROCEEDINGS', 'HEAR YE, HEAR YE!', 'THE COURT HEREBY ORDERS:', 'SUMMON', 'SWEAR',
    'COMMENCE LEGAL_LOOPHOLE', 'UNTIL', 'INITIATE CROSS_EXAMINATION', 'OBJECTION_IF', 'OVERRULED',
    'DELIVER VERDICT', 'SUSTAINED_OTHERWISE', 'COURT_ADJOURNED', 'SENTENCE', 'END LEGAL_LOOPHOLE',
    'CASE_DISMISSED', 'EXECUTE_JUSTICE', 'IF', 'ELSE', 'END IF', 'DEFINE STATUTE', 'END STATUTE',
    'INVOKE', 'READ_EVIDENCE', 'WRITE_VERDICT'
}

def tokenize(text: str) -> List[Token]:
    tokens = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line in KEYWORDS:
            tokens.append((TokenType.KEYWORD, line))
        elif match := re.match(r'^(SUMMON|SWEAR|DELIVER VERDICT|SENTENCE|IF|INVOKE|READ_EVIDENCE|WRITE_VERDICT)\s*(.*)', line):
            command, args = match.groups()
            tokens.append((TokenType.COMMAND, (command, args.strip() if args else None)))
        elif re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*=', line):
            tokens.append((TokenType.EXPRESSION, line))
        else:
            tokens.append((TokenType.TEXT, line))
    return tokens

def parse(tokens: List[Token]) -> List[ASTNode]:
    def parse_block(start: int, end_keyword: str) -> Tuple[List[ASTNode], int]:
        body = []
        i = start
        while i < len(tokens) and not (tokens[i][0] == TokenType.KEYWORD and tokens[i][1] == end_keyword):
            if tokens[i][0] == TokenType.KEYWORD:
                if tokens[i][1] == 'BEGIN_LICENSE_AGREEMENT':
                    license_body, i = parse_block(i + 1, 'END_LICENSE_AGREEMENT')
                    body.append((ASTNodeType.LICENSE_AGREEMENT, license_body))
                elif tokens[i][1] == 'COMMENCE LEGAL_LOOPHOLE':
                    inner_body, i = parse_block(i + 1, 'END LEGAL_LOOPHOLE')
                    body.append((ASTNodeType.LEGAL_LOOPHOLE, inner_body))
                elif tokens[i][1] == 'IF':
                    condition = tokens[i+1][1] if i+1 < len(tokens) else ''
                    then_body, i = parse_block(i + 2, 'ELSE')
                    else_body, i = parse_block(i + 1, 'END IF')
                    body.append((ASTNodeType.CONDITIONAL, (condition, then_body, else_body)))
                elif tokens[i][1] == 'DEFINE STATUTE':
                    func_name = tokens[i+1][1] if i+1 < len(tokens) else ''
                    func_body, i = parse_block(i + 2, 'END STATUTE')
                    body.append((ASTNodeType.CUSTOM_FUNCTION, (func_name, func_body)))
                else:
                    body.append(token_to_ast_node(tokens[i]))
            else:
                body.append(token_to_ast_node(tokens[i]))
            i += 1
        return body, i

    def token_to_ast_node(token: Token) -> ASTNode:
        if token[0] == TokenType.KEYWORD:
            if token[1] == 'COMMENCE_LEGAL_PROCEEDINGS':
                return (ASTNodeType.LEGAL_PROCEEDINGS, None)
            elif token[1] == 'CASE_DISMISSED':
                return (ASTNodeType.CASE_DISMISSED, None)
            else:
                return (ASTNodeType.COMMAND, (token[1], None))
        elif token[0] == TokenType.COMMAND:
            return (ASTNodeType.COMMAND, token[1])
        elif token[0] == TokenType.EXPRESSION:
            return (ASTNodeType.EXPRESSION, token[1])
        elif token[0] == TokenType.TEXT:
            return (ASTNodeType.TEXT, token[1])
        raise ValueError(f"Unexpected token: {token}")

    ast, _ = parse_block(0, '')
    return ast

class Interpreter:
    def __init__(self):
        self.variables: Dict[str, int] = {}
        self.custom_functions: Dict[str, List[ASTNode]] = {}
        self.functions: Dict[str, Callable] = {
            'SUMMON': self.summon,
            'SWEAR': self.swear,
            'DELIVER VERDICT': self.deliver_verdict,
            'SENTENCE': self.sentence,
            'INVOKE': self.invoke_function,
            'READ_EVIDENCE': self.read_evidence,
            'WRITE_VERDICT': self.write_verdict,
        }

    def summon(self, name: str) -> None:
        self.variables[name] = 0

    def swear(self, args: str) -> None:
        name, value = args.split(' TO ')
        self.variables[name.strip()] = int(value.strip())

    def deliver_verdict(self, message: str) -> None:
        for var_name, var_value in self.variables.items():
            message = message.replace(f"({var_name})", str(var_value))
        print(message)

    def sentence(self, name: Optional[str]) -> None:
        if name:
            self.variables[name] += 1
        else:
            for var in self.variables:
                self.variables[var] += 1

    def invoke_function(self, func_name: str) -> None:
        if func_name in self.custom_functions:
            self.execute(self.custom_functions[func_name])
        else:
            raise ValueError(f"Unknown function: {func_name}")

    def read_evidence(self, filename: str) -> None:
        with open(filename, 'r') as file:
            for line in file:
                name, value = line.strip().split('=')
                self.variables[name.strip()] = int(value.strip())

    def write_verdict(self, filename: str) -> None:
        with open(filename, 'w') as file:
            for name, value in self.variables.items():
                file.write(f"{name} = {value}\n")

    def evaluate_expression(self, expr: str) -> int:
        for var, value in self.variables.items():
            expr = expr.replace(var, str(value))
        return eval(expr, {"__builtins__": None}, {"abs": abs, "max": max, "min": min})

    def execute(self, ast: List[ASTNode]) -> None:
        for node in ast:
            node_type, node_value = node

            if node_type == ASTNodeType.COMMAND:
                command, args = node_value
                if command in self.functions:
                    self.functions[command](args)
            elif node_type == ASTNodeType.LEGAL_PROCEEDINGS:
                print("Court is now in session!")
            elif node_type == ASTNodeType.CASE_DISMISSED:
                print("Court is adjourned. Case dismissed!")
            elif node_type == ASTNodeType.LEGAL_LOOPHOLE:
                while any(v <= 5 for v in self.variables.values()):
                    self.execute(node_value)
            elif node_type == ASTNodeType.CONDITIONAL:
                condition, then_body, else_body = node_value
                if self.evaluate_expression(condition):
                    self.execute(then_body)
                else:
                    self.execute(else_body)
            elif node_type == ASTNodeType.CUSTOM_FUNCTION:
                func_name, func_body = node_value
                self.custom_functions[func_name] = func_body
            elif node_type == ASTNodeType.EXPRESSION:
                var_name, expr = node_value.split('=')
                self.variables[var_name.strip()] = self.evaluate_expression(expr.strip())
            elif node_type == ASTNodeType.LICENSE_AGREEMENT:
                self.execute(node_value)
            elif node_type == ASTNodeType.TEXT:
                pass  # Ignore text nodes or handle them as needed

def main():
    try:
        with open('LICENSE', 'r') as file:
            text = file.read()
    except FileNotFoundError:
        print("Error: The 'LICENSE' file was not found.")
        return

    tokens = tokenize(text)
    ast = parse(tokens)
    interpreter = Interpreter()
    interpreter.execute(ast)

if __name__ == "__main__":
    main()