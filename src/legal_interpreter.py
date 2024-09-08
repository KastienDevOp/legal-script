import re
import os
from dataclasses import dataclass
from typing import List, Union, Dict, Optional

# AST Node classes
@dataclass
class Statement:
    pass

@dataclass
class Summon(Statement):
    variable: str

@dataclass
class ReadEvidence(Statement):
    filename: str

@dataclass
class DeliverVerdict(Statement):
    message: str

@dataclass
class DefineStatute(Statement):
    name: str
    body: List[Statement]

@dataclass
class WriteVerdict(Statement):
    filename: str

@dataclass
class Assignment(Statement):
    variable: str
    expression: str

@dataclass
class StatuteCall(Statement):
    name: str

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
        self.lines = [line.strip() for line in code.strip().split('\n') if line.strip()]
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

        if line in ["BEGIN_LICENSE_AGREEMENT", "END_LICENSE_AGREEMENT"]:
            return None  # Skip these lines
        elif line == "COMMENCE_LEGAL_PROCEEDINGS":
            return None
        elif line.startswith("SUMMON"):
            parts = line.split(maxsplit=1)
            return Summon(parts[1]) if len(parts) > 1 else None
        elif line.startswith("READ_EVIDENCE"):
            parts = line.split(maxsplit=1)
            return ReadEvidence(parts[1]) if len(parts) > 1 else None
        elif line.startswith("DELIVER VERDICT"):
            return DeliverVerdict(line[15:].strip())
        elif line.startswith("DEFINE STATUTE"):
            return self.parse_statute()
        elif line.startswith("WRITE_VERDICT"):
            parts = line.split(maxsplit=1)
            return WriteVerdict(parts[1]) if len(parts) > 1 else None
        elif line == "CASE_DISMISSED":
            return None
        elif line.startswith("COMMENCE LEGAL_LOOPHOLE"):
            return self.parse_loophole()
        elif line.startswith("IF"):
            return self.parse_conditional()
        elif '=' in line:
            var, expr = line.split('=', 1)
            return Assignment(var.strip(), expr.strip())
        else:
            return StatuteCall(line)

    def parse_statute(self) -> DefineStatute:
        name = self.lines[self.current_line - 1].split(maxsplit=2)[-1]
        body = []
        while self.current_line < len(self.lines) and self.lines[self.current_line] != "END STATUTE":
            statement = self.parse_statement()
            if statement:
                body.append(statement)
        if self.current_line < len(self.lines):
            self.current_line += 1  # Skip END STATUTE
        return DefineStatute(name, body)

    def parse_loophole(self) -> LegalLoophole:
        condition = self.lines[self.current_line - 1].split("UNTIL", 1)[1].strip()
        body = []
        while self.current_line < len(self.lines) and self.lines[self.current_line] != "END LEGAL_LOOPHOLE":
            statement = self.parse_statement()
            if statement:
                body.append(statement)
        if self.current_line < len(self.lines):
            self.current_line += 1  # Skip END LEGAL_LOOPHOLE
        return LegalLoophole(condition, body)

    def parse_conditional(self) -> Conditional:
        condition = self.lines[self.current_line - 1].split("IF", 1)[1].strip()
        then_body = []
        else_body = []
        current_body = then_body
        while self.current_line < len(self.lines) and self.lines[self.current_line] != "END IF":
            if self.lines[self.current_line] == "ELSE":
                current_body = else_body
                self.current_line += 1
                continue
            statement = self.parse_statement()
            if statement:
                current_body.append(statement)
        if self.current_line < len(self.lines):
            self.current_line += 1  # Skip END IF
        return Conditional(condition, then_body, else_body)

class LegalInterpreter:
    def __init__(self):
        self.variables: Dict[str, float] = {}
        self.statutes: Dict[str, List[Statement]] = {}
        self.verdict: List[str] = []
        self.current_directory: str = os.getcwd()
        self.loop_iterations: int = 0

    def execute(self, program: LegalProgram):
        for statement in program.statements:
            self.execute_statement(statement)

    def execute_statement(self, statement: Statement):
        if isinstance(statement, Summon):
            self.variables[statement.variable] = 0
        elif isinstance(statement, ReadEvidence):
            self.read_evidence(statement.filename)
        elif isinstance(statement, DeliverVerdict):
            self.deliver_verdict(statement.message)
        elif isinstance(statement, DefineStatute):
            self.statutes[statement.name] = statement.body
        elif isinstance(statement, WriteVerdict):
            self.write_verdict(statement.filename)
        elif isinstance(statement, Assignment):
            self.variables[statement.variable] = self.evaluate(statement.expression)
        elif isinstance(statement, StatuteCall):
            self.execute_statute(statement.name)
        elif isinstance(statement, LegalLoophole):
            self.execute_loophole(statement)
        elif isinstance(statement, Conditional):
            self.execute_conditional(statement)

    def read_evidence(self, filename: str):
        full_path = os.path.join(self.current_directory, filename)
        try:
            with open(full_path, 'r') as f:
                content = f.read()
                parser = LegalParser()
                evidence_program = parser.parse(content)
                self.execute(evidence_program)
        except FileNotFoundError:
            print(f"Error: Evidence file '{filename}' not found.")
        except IOError:
            print(f"Error: Unable to read evidence file '{filename}'.")
        except SyntaxError as e:
            print(f"Syntax Error in evidence file '{filename}': {str(e)}")

    def deliver_verdict(self, message: str):
        result = re.sub(r'\(([^)]+)\)', lambda m: str(self.evaluate(m.group(1))), message)
        self.verdict.append(result)
        print(result)

    def write_verdict(self, filename: str):
        try:
            with open(filename, 'w') as f:
                f.write("\n".join(self.verdict))
        except IOError:
            print(f"Error: Unable to write verdict to file '{filename}'.")

    def execute_statute(self, name: str):
        if name in self.statutes:
            for statement in self.statutes[name]:
                self.execute_statement(statement)
        else:
            print(f"Error: Statute '{name}' not found.")

    def execute_loophole(self, loophole: LegalLoophole):
        self.loop_iterations = 0
        while self.evaluate(loophole.condition):
            for statement in loophole.body:
                self.execute_statement(statement)
            # Add a safety check to prevent infinite loops
            if self.loop_iterations > 1000:
                print("Warning: Possible infinite loop detected. Terminating loophole execution.")
                break
            self.loop_iterations += 1

    def execute_conditional(self, conditional: Conditional):
        if self.evaluate(conditional.condition):
            for statement in conditional.then_body:
                self.execute_statement(statement)
        else:
            for statement in conditional.else_body:
                self.execute_statement(statement)

    def evaluate(self, expr: str) -> float:
        expr = re.sub(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', lambda m: str(self.variables.get(m.group(1), 0)), expr)
        try:
            result = float(eval(expr, {"__builtins__": None}, {"abs": abs, "max": max, "min": min}))
            return round(result, 2)  # Round to 2 decimal places
        except (NameError, SyntaxError, TypeError, ZeroDivisionError) as e:
            print(f"Error evaluating expression '{expr}': {str(e)}")
            return 0.0

def read_file(filename: str) -> str:
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return file.read()
    elif os.path.exists(filename + '.lspl'):
        with open(filename + '.lspl', 'r') as file:
            return file.read()
    else:
        raise FileNotFoundError(f"No file found with name '{filename}' or '{filename}.lspl'")

def run_legal_code():
    try:
        # Read the LICENSE file
        license_code = read_file('LICENSE')
        
        parser = LegalParser()
        interpreter = LegalInterpreter()
        
        try:
            ast = parser.parse(license_code)
            interpreter.execute(ast)
        except SyntaxError as e:
            print(f"Syntax Error: {str(e)}")
        except Exception as e:
            print(f"Unexpected Error: {str(e)}")
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
    except IOError:
        print("Error: Unable to read LICENSE file.")

if __name__ == "__main__":
    run_legal_code()