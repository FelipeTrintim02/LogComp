import sys
from abc import abstractmethod
import re

class AssemblyGenerator:
    code = []  

    @classmethod
    def add(cls, line):
        if not isinstance(line, str):
            line = str(line)
        cls.code.append(line + "\n")
        
    @classmethod
    def get_code(cls):
        return ''.join(cls.code)
    
class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

class PrePro:
    @staticmethod
    def filter(expression):
        return re.sub(r'--.*', '', expression)

class Tokenizer:
    def __init__(self, source):
        self.source = source
        self.position = 0
        self.next = None
        self.reserved = ['print', 'read', 'if', 'then', 'else', 'end', 'while', 'do', 'or', 'and', 'not', 'local']

    def selectNext(self):
        while self.position < len(self.source) and self.source[self.position].isspace():
            if self.source[self.position] == "\n":
                self.next = Token("NEWLINE", None)
                self.position += 1
                return
            self.position += 1

        if self.position >= len(self.source):
            self.next = Token('EOF', None)
        elif self.source[self.position].isdigit():
            number = ''
            while self.position < len(self.source) and self.source[self.position].isdigit():
                number += self.source[self.position]
                self.position += 1
            self.next = Token('INT', int(number))
        elif self.source[self.position].isalpha() or self.source[self.position] == "_":
            identifier = ''
            while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == "_"):
                identifier += self.source[self.position]
                self.position += 1
            if identifier in self.reserved:
                self.next = Token(identifier.upper(), None)
            else:
                self.next = Token('IDENTIFIER', identifier)
        elif self.source[self.position] == "=":
            if self.position + 1 < len(self.source) and self.source[self.position + 1] == "=":
                self.next = Token("EQ", None)
                self.position += 2
            else:
                self.next = Token("ASSIGN", None)
                self.position += 1
        elif self.source[self.position] == "+":
            self.next = Token("PLUS", None)
            self.position += 1
        elif self.source[self.position] == "-":
            self.next = Token("MINUS", None)
            self.position += 1
        elif self.source[self.position] == "*":
            self.next = Token("MULT", None)
            self.position += 1
        elif self.source[self.position] == "/":
            self.next = Token("DIV", None)
            self.position += 1
        elif self.source[self.position] == "(":
            self.next = Token("LPAREN", None)
            self.position += 1
        elif self.source[self.position] == ")":
            self.next = Token("RPAREN", None)
            self.position += 1
        elif self.source[self.position] == ">":
            self.next = Token("GT", None)
            self.position += 1
        elif self.source[self.position] == "<":
            self.next = Token("LT", None)
            self.position += 1
        elif self.source[self.position] == ".":
            if self.position + 1 < len(self.source) and self.source[self.position + 1] == ".":
                self.next = Token("CONCAT", None)
                self.position += 2
        elif self.source[self.position] == "\"":
            self.position += 1
            string_literal = ''
            while self.position < len(self.source):
                if self.source[self.position] == "\\":
                    self.position += 1
                    if self.position < len(self.source) and self.source[self.position] in "\"nt":
                        if self.source[self.position] == "\"":
                            string_literal += "\""
                        elif self.source[self.position] == "n":
                            string_literal += "\n"
                        elif self.source[self.position] == "t":
                            string_literal += "\t"
                    else:
                        string_literal += "\\"
                        continue
                elif self.source[self.position] == "\"":
                    self.position += 1
                    break
                else:
                    string_literal += self.source[self.position]
                self.position += 1
            else:
                raise Exception("String literal not closed")
            self.next = Token('STRING', string_literal)
        else:
            sys.stderr.write(f"Unexpected character: {self.source[self.position]}\n")
            sys.exit(1)

class SymbolTable:
    def __init__(self):
        self.table = {}
        self.shift = 0

    def setter(self, key, value, typ):
        self.table[key][0] = value
        self.table[key][1] = typ

    def getter(self, key):
        if key in self.table:
            return self.table[key]
        else:
            raise ValueError(f"Variable {key} not declared")
        
    def create(self, key):
        if key not in self.table:
            self.shift += 4
            self.table[key] = [None, None, self.shift]
        else:
            raise ValueError(f"Variable {key} already declared")

class Node:
    i = 0
    def __init__(self, value, children):
        self.value = value
        self.children = children
        self.id = Node.newId()
        
    def newId():
        Node.i += 1
        return Node.i

    def evaluate(self, st):
        raise NotImplementedError("Must override evaluate")

class BinOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st):
        right_val, right_type, *rest = self.children[1].evaluate(st)
        x = rest[0] if rest else None
        AssemblyGenerator.add(f"PUSH EAX")
        left_val, left_type, *resto = self.children[0].evaluate(st)
        y = resto[0] if resto else None
        AssemblyGenerator.add(f"POP EBX")
        
        
        if self.value in {'+', '-', '*', '/', 'and', 'or'}:
            if left_type != 'int' or right_type != 'int':
                raise TypeError(f"Arithmetic operations require integer types, got {left_type} and {right_type}")
            if self.value == '+':
                AssemblyGenerator.add(f"ADD EAX, EBX")
                return [left_val + right_val, 'int']
            elif self.value == '-':
                AssemblyGenerator.add(f"SUB EAX, EBX")
                return [left_val - right_val, 'int']
            elif self.value == '*':
                AssemblyGenerator.add(f"IMUL EAX, EBX")
                return [left_val * right_val, 'int']
            elif self.value == '/':
                AssemblyGenerator.add(f"IDIV EBX")
                return [left_val // right_val, 'int']
            elif self.value == 'and':
                AssemblyGenerator.add(f"AND EAX, EBX")
                return [left_val and right_val, 'int']
            elif self.value == 'or':
                AssemblyGenerator.add(f"OR EAX, EBX")
                return [left_val or right_val, 'int']

        elif self.value in {'==', '>', '<'}:
            if left_type != right_type:
                raise TypeError(f"Comparison operations require matching types, got {left_type} and {right_type}")
            if self.value == '==':
                AssemblyGenerator.add(f"CMP EAX, EBX")
                AssemblyGenerator.add(f"CALL binop_je")
                return [int(left_val == right_val), 'int']
            elif self.value == '>':
                AssemblyGenerator.add(f"CMP EAX, EBX")
                AssemblyGenerator.add(f"CALL binop_jg")
                return [int(left_val > right_val), 'int']
            elif self.value == '<':
                AssemblyGenerator.add(f"CMP EAX, EBX")
                AssemblyGenerator.add(f"CALL binop_jl")
                return [int(left_val < right_val), 'int']
            
        elif self.value == '..':
            return [str(left_val) + str(right_val), 'string']

        else:
            raise ValueError(f"Unsupported operator {self.value}")

class UnOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st):
        val, typ = self.children[0].evaluate(st)
        if typ != 'int':
            raise TypeError("Mismatched types in unary operation")
        if self.value == '+':
            return [val, typ]
        elif self.value == '-':
            AssemblyGenerator.add(f"NEG EAX")
            return [-val, typ]
        elif self.value == 'not':
            AssemblyGenerator.add(f"NOT EAX")
            return [not val, typ]

class IntVal(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def evaluate(self, st):
        AssemblyGenerator.add(f"MOV EAX, {self.value}")
        return [self.value, 'int']

class StringVal(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def evaluate(self, st):
        return [self.value, 'string']

class NoOp(Node):
    def __init__(self):
        super().__init__(None, [])

    def evaluate(self, st):
        return [None, 'Null']

class Block(Node):
    def __init__(self, children):
        super().__init__(None, children)

    def evaluate(self, st):
        for child in self.children:
            if child is not None: 
                child.evaluate(st)

class Identifier(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def evaluate(self, st):
        AssemblyGenerator.add(f"MOV EAX, [EBP - {st.getter(self.value)[2]}]")
        return st.getter(self.value)

class Assignment(Node):
    def __init__(self, children):
        super().__init__(None, children)

    def evaluate(self, st):
        var_name = self.children[0].value
        if var_name in st.table:
            value, typ, *resto = self.children[1].evaluate(st)
            x = resto[0] if resto else None
            st.setter(var_name, value, typ)
            AssemblyGenerator.add(f"MOV [EBP - {st.getter(var_name)[2]}], EAX")
        else:
            raise ValueError(f"Variable {var_name} not declared")

class VarDec(Node):
    def __init__(self, children):
        super().__init__(None, children)

    def evaluate(self, st):
        st.create(self.children[0].value)
        if len(self.children) > 1:
            value, typ = self.children[1].evaluate(st)
            st.setter(self.children[0].value, value, typ)
        else:
            st.setter(self.children[0].value, None, None)
        AssemblyGenerator.add("PUSH DWORD 0")

class Print(Node):
    def __init__(self, children):
        super().__init__(None, children)

    def evaluate(self, st):
        value, typ, *shift = self.children[0].evaluate(st)
        y = shift[0] if shift else None
        AssemblyGenerator.add(f"PUSH EAX")
        AssemblyGenerator.add(f"PUSH formatout")
        AssemblyGenerator.add(f"CALL printf")
        AssemblyGenerator.add(f"ADD ESP, 8")
        print(value)

class While(Node):
    counter = 0

    def __init__(self, children):
        super().__init__(None, children)
        self.while_id = While.newId()

    @staticmethod
    def newId():
        While.counter += 1
        return While.counter

    def evaluate(self, st):
        start_label = f"LOOP_{self.while_id}"
        end_label = f"EXIT_{self.while_id}"
        
        AssemblyGenerator.add(f"{start_label}:")
        self.children[0].evaluate(st)
        AssemblyGenerator.add("CMP EAX, False") 
        AssemblyGenerator.add(f"JE {end_label}")  
        while self.children[0].evaluate(st)[0]:
            for child in self.children[1]:
                child.evaluate(st)
        AssemblyGenerator.add(f"JMP {start_label}") 
        AssemblyGenerator.add(f"{end_label}:")

class If(Node):
    def __init__(self, children):
        # Expected children layout: [condition, if_block, else_block (optional)]
        super().__init__(None, children)

    def evaluate(self, st):
        condition, _ = self.children[0].evaluate(st)
        
        if condition:
            for stmt in self.children[1]:
                stmt.evaluate(st)
        elif len(self.children) > 2:
            for stmt in self.children[2]:
                stmt.evaluate(st)

    def generate_assembly(self):
        label_else = f"ELSE_{Node.newId()}"
        label_end = f"END_IF_{Node.newId()}"

        # Condition
        condition_code = self.children[0].generate_assembly()
        AssemblyGenerator.add(condition_code)
        AssemblyGenerator.add(f"CMP EAX, 0")  # Check if the condition is false
        AssemblyGenerator.add(f"JE {label_else}")  # Jump to else if false

        # If block
        if_code = '\n'.join([stmt.generate_assembly() for stmt in self.children[1]])
        AssemblyGenerator.add(if_code)
        AssemblyGenerator.add(f"JMP {label_end}")  # Skip else block

        # Else block
        if len(self.children) > 2:
            AssemblyGenerator.add(f"{label_else}:")
            else_code = '\n'.join([stmt.generate_assembly() for stmt in self.children[2]])
            AssemblyGenerator.add(else_code)

        # End label
        AssemblyGenerator.add(f"{label_end}:")

class Read(Node):
    def __init__(self, children):
        super().__init__(None, children)
        
    def evaluate(self, st):
        AssemblyGenerator.add("PUSH scanint")
        AssemblyGenerator.add("PUSH formatin")
        AssemblyGenerator.add("CALL scanf")
        AssemblyGenerator.add("ADD ESP, 8")
        AssemblyGenerator.add("MOV EAX, DWORD [scanint]")
        return [self.children[0], 'int']
    
class Parser:
    
    @staticmethod
    def boolExpression(tokenizer):
        result = Parser.boolTerm(tokenizer)
        while tokenizer.next.type == 'OR':
            tokenizer.selectNext()
            result = BinOp('or', [result, Parser.boolTerm(tokenizer)])
        return result
    
    @staticmethod
    def boolTerm(tokenizer):
        result = Parser.relExpression(tokenizer)
        while tokenizer.next.type == 'AND':
            tokenizer.selectNext()
            result = BinOp('and', [result, Parser.relExpression(tokenizer)])
        return result
    
    @staticmethod
    def relExpression(tokenizer):
        result = Parser.parseExpression(tokenizer)
        if tokenizer.next.type == 'GT':
            tokenizer.selectNext()
            return BinOp('>', [result, Parser.parseExpression(tokenizer)])
        elif tokenizer.next.type == 'LT':
            tokenizer.selectNext()
            return BinOp('<', [result, Parser.parseExpression(tokenizer)])
        elif tokenizer.next.type == 'EQ':
            tokenizer.selectNext()
            return BinOp('==', [result, Parser.parseExpression(tokenizer)])
        else:
            return result
    
    @staticmethod
    def parseStatement(tokenizer):
        if tokenizer.next.type == 'LOCAL':
            tokenizer.selectNext()
            if tokenizer.next.type != 'IDENTIFIER':
                sys.stderr.write(f"Expected identifier\n")
                sys.exit(1)
            identifier = Identifier(tokenizer.next.value)
            tokenizer.selectNext()
            if tokenizer.next.type != 'ASSIGN' and tokenizer.next.type != 'EOF' and tokenizer.next.type != 'NEWLINE':
                sys.stderr.write(f"error\n")
                sys.exit(1)
            if tokenizer.next.type == 'ASSIGN':
                tokenizer.selectNext()
                expression = Parser.boolExpression(tokenizer)
                if tokenizer.next.type != 'EOF' and tokenizer.next.type != 'NEWLINE':
                    sys.stderr.write(f"Expected \\n\n")
                    sys.exit(1)
                tokenizer.selectNext()
                return VarDec([identifier, expression])
            else:
                return VarDec([identifier, NoOp()])
        elif tokenizer.next.type == 'IDENTIFIER':
            identifier = Identifier(tokenizer.next.value)
            tokenizer.selectNext()
            if tokenizer.next.type != 'ASSIGN':
                sys.stderr.write(f"Expected =\n")
                sys.exit(1)
            tokenizer.selectNext()
            expression = Parser.boolExpression(tokenizer)
            if tokenizer.next.type != 'EOF' and tokenizer.next.type != 'NEWLINE':
                sys.stderr.write(f"Expected \\n\n")
                sys.exit(1)
            tokenizer.selectNext()
            return Assignment([identifier, expression])
        elif tokenizer.next.type == 'PRINT':
            tokenizer.selectNext()
            if tokenizer.next.type != 'LPAREN':
                sys.stderr.write(f"Expected (\n")
                sys.exit(1)
            tokenizer.selectNext()
            expression = Parser.boolExpression(tokenizer)
            if tokenizer.next.type != 'RPAREN':
                sys.stderr.write(f"Expected )\n")
                sys.exit(1)
            tokenizer.selectNext()
            if tokenizer.next.type != 'EOF' and tokenizer.next.type != 'NEWLINE':
                sys.stderr.write(f"Expected \\n\n")
                sys.exit(1)
            tokenizer.selectNext() 
            return Print([expression])
        elif tokenizer.next.type == 'NEWLINE':
            tokenizer.selectNext()
            return NoOp()
        elif tokenizer.next.type == 'WHILE':
            tokenizer.selectNext()
            expression = Parser.boolExpression(tokenizer)
            if tokenizer.next.type != 'DO':
                sys.stderr.write(f"Expected do\n")
                sys.exit(1)
            tokenizer.selectNext()
            if tokenizer.next.type != 'NEWLINE':
                sys.stderr.write(f"Expected \\n\n")
                sys.exit(1)
            tokenizer.selectNext()
            statements = []
            while tokenizer.next.type != 'END':
                statement = Parser.parseStatement(tokenizer)
                statements.append(statement)
            if tokenizer.next.type != 'END':
                sys.stderr.write(f"Expected end\n")
                sys.exit(1)
            tokenizer.selectNext()
            if tokenizer.next.type != 'EOF' and tokenizer.next.type != 'NEWLINE':
                sys.stderr.write(f"Expected \\n\n")
                sys.exit(1)
            return While([expression, statements])
        elif tokenizer.next.type == 'IF':
            tokenizer.selectNext()
            expression = Parser.boolExpression(tokenizer)
            if tokenizer.next.type != 'THEN':
                sys.stderr.write(f"Expected then\n")
                sys.exit(1)
            tokenizer.selectNext()
            if tokenizer.next.type != 'NEWLINE':
                sys.stderr.write(f"Expected \\n\n")
                sys.exit(1)
            tokenizer.selectNext()
            statement1 = []
            while tokenizer.next.type != 'ELSE' and tokenizer.next.type != 'END':
                statement = Parser.parseStatement(tokenizer)
                statement1.append(statement)
            if tokenizer.next.type != 'ELSE' and tokenizer.next.type != 'END':
                sys.stderr.write(f"Expected else\n")
                sys.exit(1)
            if tokenizer.next.type == 'ELSE':
                tokenizer.selectNext()
                if tokenizer.next.type != 'NEWLINE':
                    sys.stderr.write(f"Expected \\n\n")
                    sys.exit(1)
                tokenizer.selectNext()
                statement2 = []
                while tokenizer.next.type != 'END':
                    statement = Parser.parseStatement(tokenizer)
                    statement2.append(statement)
                if tokenizer.next.type != 'END':
                    sys.stderr.write(f"Expected end\n")
                    sys.exit(1)
                tokenizer.selectNext()
                if tokenizer.next.type != 'EOF' and tokenizer.next.type != 'NEWLINE':
                    sys.stderr.write(f"Expected \\n\n")
                    sys.exit(1)
                return If([expression, statement1, statement2])
            if tokenizer.next.type == 'END':
                tokenizer.selectNext()
                if tokenizer.next.type != 'EOF' and tokenizer.next.type != 'NEWLINE':
                    sys.stderr.write(f"Expected \\n\n")
                    sys.exit(1)
                return If([expression, statement1, []])
        else:
            sys.stderr.write(f"Expected identifier or print\n")
            sys.exit(1)
    
    @staticmethod
    def parseBlock(tokenizer):
        statements = []
        while tokenizer.next.type != 'EOF':
            statement = Parser.parseStatement(tokenizer)
            if not isinstance(statement, NoOp):
                statements.append(statement)
        return Block(statements)

    @staticmethod
    def parseExpression(tokenizer):
        result = Parser.parseTerm(tokenizer)
        while tokenizer.next.type in ['PLUS', 'MINUS', 'CONCAT']:
            if tokenizer.next.type == 'PLUS':
                tokenizer.selectNext()
                result = BinOp('+', [result, Parser.parseTerm(tokenizer)])
            elif tokenizer.next.type == 'MINUS':
                tokenizer.selectNext()
                result = BinOp('-', [result, Parser.parseTerm(tokenizer)])
            elif tokenizer.next.type == 'CONCAT':
                tokenizer.selectNext()
                result = BinOp('..', [result, Parser.parseTerm(tokenizer)])
        return result

    @staticmethod
    def parseTerm(tokenizer):
        result = Parser.parseFactor(tokenizer)
        while tokenizer.next.type in ['MULT', 'DIV']:
            if tokenizer.next.type == 'MULT':
                tokenizer.selectNext()
                result = BinOp('*', [result, Parser.parseFactor(tokenizer)])
            elif tokenizer.next.type == 'DIV':
                tokenizer.selectNext()
                result = BinOp('/', [result, Parser.parseFactor(tokenizer)])
        return result

    @staticmethod
    def parseFactor(tokenizer):
        if tokenizer.next.type == 'INT':
            result = tokenizer.next.value
            tokenizer.selectNext()
            return IntVal(result)
        elif tokenizer.next.type == 'STRING':
            result = tokenizer.next.value
            tokenizer.selectNext()
            return StringVal(result)
        elif tokenizer.next.type == 'IDENTIFIER':
            result = tokenizer.next.value
            tokenizer.selectNext()
            return Identifier(result)
        elif tokenizer.next.type == 'PLUS':
            tokenizer.selectNext()
            return UnOp('+', [Parser.parseFactor(tokenizer)])
        elif tokenizer.next.type == 'MINUS':
            tokenizer.selectNext()
            return UnOp('-', [Parser.parseFactor(tokenizer)])
        elif tokenizer.next.type == 'NOT':
            tokenizer.selectNext()
            return UnOp('not', [Parser.parseFactor(tokenizer)])
        elif tokenizer.next.type == 'LPAREN':
            tokenizer.selectNext()
            result = Parser.boolExpression(tokenizer)
            if tokenizer.next.type != 'RPAREN':
                sys.stderr.write(f"Expected )aaaaaa\n")
                sys.exit(1)
            tokenizer.selectNext()
            return result
        elif tokenizer.next.type == 'READ':
            tokenizer.selectNext()
            if tokenizer.next.type != 'LPAREN':
                sys.stderr.write(f"Expected (\n")
                sys.exit(1)
            tokenizer.selectNext()
            if tokenizer.next.type != 'RPAREN':
                sys.stderr.write(f"Expected )\n")
                sys.exit(1)
            tokenizer.selectNext()
            return Read([int(input())])
        else:
            sys.stderr.write(f"Expected number or (expression)\n")
            sys.exit(1)


    @staticmethod
    def run(code, st):
        tokenizer = Tokenizer(code)
        tokenizer.selectNext()  # Initialize the tokenizer
        result = Parser.parseBlock(tokenizer)
        result = result.evaluate(st)
        if tokenizer.next.type != 'EOF':
            sys.stderr.write("Unexpected tokens after expression\n")
            sys.exit(1)
        return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python main.py <filename.lua>\n")
        sys.exit(1)

    filename = sys.argv[1]

    if not filename.endswith(".lua"):
        sys.stderr.write("Error: File extension must be .lua\n")
        sys.exit(1)

    try:
        with open(filename, 'r') as file:
            code = file.read()
        st = SymbolTable()
        code = PrePro.filter(code)
        result = Parser.run(code, st)
        
        # Prepare assembly code output
        with open('cabecalho.txt', 'r') as header_file:
            header_content = header_file.read()
        with open('footer.txt', 'r') as footer_file:
            footer_content = footer_file.read()
        
        assembly_code = header_content + "\n" + "\n" + AssemblyGenerator.get_code() + "\n" + footer_content
        
        # Save the final assembly code to a file
        filename = filename.replace('.lua', '.asm')
        with open(filename, 'w') as asm_file:
            asm_file.write(assembly_code)
        
    except FileNotFoundError:
        sys.stderr.write(f"Error: File {filename} not found\n")
        sys.exit(1)