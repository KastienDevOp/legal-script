import re
import os
from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import defaultdict

@dataclass
class Statement: pass

@dataclass
class Summon(Statement): variable: str
@dataclass
class ReadEvidence(Statement): filename: str
@dataclass
class DeliverVerdict(Statement): message: str
@dataclass
class DefineStatute(Statement):
    name: str
    body: List[Statement]
@dataclass
class WriteVerdict(Statement): filename: str
@dataclass
class Assignment(Statement):
    variable: str
    expression: str
@dataclass
class StatuteCall(Statement): name: str
@dataclass
class LegalLoophole(Statement):
    condition: str
    body: List[Statement]
@dataclass
class Conditional(Statement):
    condition: str
    then_body: List[Statement]
    else_body: List[Statement]
@dataclass
class LegalProgram:
    statements: List[Statement]

class LegalParser:
    def __init__(self):
        self.current_line = 0
        self.lines: List[str] = []

    def parse(self, code: str) -> LegalProgram:
        self.lines = [line.strip() for line in code.strip().splitlines() if line.strip()]
        if self.lines[0] != "BEGIN_LICENSE_AGREEMENT" or self.lines[-1] != "END_LICENSE_AGREEMENT":
            raise SyntaxError("Invalid license agreement structure")

        statements = []
        self.current_line = 1
        while self.current_line < len(self.lines) - 1:
            statement = self.parse_statement()
            if statement:
                statements.append(statement)

        return LegalProgram(statements)

    def parse_statement(self) -> Optional[Statement]:
        if self.current_line >= len(self.lines):
            return None
        
        line = self.lines[self.current_line]
        self.current_line += 1

        statement_map = {
            "SUMMON": lambda: Summon(line.split(maxsplit=1)[1]),
            "READ_EVIDENCE": lambda: ReadEvidence(line.split(maxsplit=1)[1]),
            "DELIVER VERDICT": lambda: DeliverVerdict(line[15:].strip()),
            "DEFINE STATUTE": self.parse_statute,
            "WRITE_VERDICT": lambda: WriteVerdict(line.split(maxsplit=1)[1]),
            "COMMENCE LEGAL_LOOPHOLE": self.parse_loophole,
            "IF": self.parse_conditional
        }

        for key, func in statement_map.items():
            if line.startswith(key):
                return func()

        if '=' in line:
            var, expr = line.split('=', 1)
            return Assignment(var.strip(), expr.strip())
        elif line not in ["BEGIN_LICENSE_AGREEMENT", "END_LICENSE_AGREEMENT", "COMMENCE_LEGAL_PROCEEDINGS", "CASE_DISMISSED"]:
            return StatuteCall(line)

        return None

    def parse_statute(self) -> DefineStatute:
        name = self.lines[self.current_line - 1].split(maxsplit=2)[-1]
        body = []
        while self.current_line < len(self.lines) and self.lines[self.current_line] != "END STATUTE":
            statement = self.parse_statement()
            if statement:
                body.append(statement)
        self.current_line += 1  # Skip END STATUTE
        return DefineStatute(name, body)

    def parse_loophole(self) -> LegalLoophole:
        condition = self.lines[self.current_line - 1].split("UNTIL", 1)[1].strip()
        body = []
        while self.current_line < len(self.lines) and self.lines[self.current_line] != "END LEGAL_LOOPHOLE":
            statement = self.parse_statement()
            if statement:
                body.append(statement)
        self.current_line += 1  # Skip END LEGAL_LOOPHOLE
        return LegalLoophole(condition, body)

    def parse_conditional(self) -> Conditional:
        condition = self.lines[self.current_line - 1].split("IF", 1)[1].strip()
        then_body, else_body = [], []
        current_body = then_body
        while self.current_line < len(self.lines) and self.lines[self.current_line] != "END IF":
            if self.lines[self.current_line] == "ELSE":
                current_body = else_body
                self.current_line += 1
                continue
            statement = self.parse_statement()
            if statement:
                current_body.append(statement)
        self.current_line += 1  # Skip END IF
        return Conditional(condition, then_body, else_body)

class LegalInterpreter:
    def __init__(self):
        self.variables: Dict[str, float] = defaultdict(float)
        self.statutes: Dict[str, List[Statement]] = {}
        self.verdict: List[str] = []
        self.current_directory: str = os.getcwd()
        self.loop_iterations: int = 0
        self.MAX_LOOP_ITERATIONS = 1000

    def execute(self, program: LegalProgram):
        for statement in program.statements:
            self.execute_statement(statement)

    def execute_statement(self, statement: Statement):
        statement_map = {
            Summon: lambda s: None,  # Variables are initialized to 0 by defaultdict
            ReadEvidence: lambda s: self.read_evidence(s.filename),
            DeliverVerdict: lambda s: self.deliver_verdict(s.message),
            DefineStatute: lambda s: self.statutes.update({s.name: s.body}),
            WriteVerdict: lambda s: self.write_verdict(s.filename),
            Assignment: lambda s: self.variables.update({s.variable: self.evaluate(s.expression)}),
            StatuteCall: lambda s: self.execute_statute(s.name),
            LegalLoophole: lambda s: self.execute_loophole(s),
            Conditional: lambda s: self.execute_conditional(s)
        }
        statement_map[type(statement)](statement)

    def read_evidence(self, filename: str):
        try:
            with open(os.path.join(self.current_directory, filename), 'r') as f:
                content = f.read()
                evidence_program = LegalParser().parse(content)
                self.execute(evidence_program)
        except (FileNotFoundError, IOError, SyntaxError) as e:
            print(f"Error reading evidence file '{filename}': {str(e)}")

    def deliver_verdict(self, message: str):
        result = re.sub(r'\(([^)]+)\)', lambda m: str(self.evaluate(m.group(1))), message)
        self.verdict.append(result)
        print(result)

    def write_verdict(self, filename: str):
        try:
            with open(filename, 'w') as f:
                f.write("\n".join(self.verdict))
        except IOError as e:
            print(f"Error writing verdict to file '{filename}': {str(e)}")

    def execute_statute(self, name: str):
        if name in self.statutes:
            for statement in self.statutes[name]:
                self.execute_statement(statement)
        else:
            print(f"Error: Statute '{name}' not found.")

    def execute_loophole(self, loophole: LegalLoophole):
        self.loop_iterations = 0
        while self.evaluate(loophole.condition) and self.loop_iterations < self.MAX_LOOP_ITERATIONS:
            for statement in loophole.body:
                self.execute_statement(statement)
            self.loop_iterations += 1
        if self.loop_iterations == self.MAX_LOOP_ITERATIONS:
            print(f"Warning: Loophole execution terminated after {self.MAX_LOOP_ITERATIONS} iterations.")

    def execute_conditional(self, conditional: Conditional):
        body = conditional.then_body if self.evaluate(conditional.condition) else conditional.else_body
        for statement in body:
            self.execute_statement(statement)

    def evaluate(self, expr: str) -> float:
        expr = re.sub(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', lambda m: str(self.variables[m.group(1)]), expr)
        try:
            return round(float(eval(expr, {"__builtins__": None}, {"abs": abs, "max": max, "min": min})), 2)
        except (NameError, SyntaxError, TypeError, ZeroDivisionError) as e:
            print(f"Error evaluating expression '{expr}': {str(e)}")
            return 0.0

def read_file(filename: str) -> str:
    for ext in ['', '.lspl']:
        try:
            with open(filename + ext, 'r') as file:
                return file.read()
        except FileNotFoundError:
            continue
    raise FileNotFoundError(f"No file found with name '{filename}' or '{filename}.lspl'")

def run_legal_code():
    try:
        license_code = read_file('LICENSE')
        parser = LegalParser()
        interpreter = LegalInterpreter()
        
        try:
            ast = parser.parse(license_code)
            interpreter.execute(ast)
        except (SyntaxError, Exception) as e:
            print(f"Error executing legal code: {type(e).__name__}: {str(e)}")
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
    except IOError:
        print("Error: Unable to read LICENSE file.")

if __name__ == "__main__":
    run_legal_code()
