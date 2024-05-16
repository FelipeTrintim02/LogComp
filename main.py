import sys
from abc import abstractmethod
import re

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
        self.reserved = ['print', 'read', 'if', 'then', 'else', 'end', 'while', 'do', 'or', 'and', 'not', 'local', 'function', 'return']

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
        elif self.source[self.position] == ",":
            self.next = Token("COMMA", None)
            self.position += 1
        else:
            sys.stderr.write(f"Unexpected character: {self.source[self.position]}\n")
            sys.exit(1)

class SymbolTable:
    def __init__(self):
        self.table = {}

    def setter(self, key, value, typ):
        self.table[key] = (value, typ)

    def getter(self, key):
        if key in self.table:
            return self.table[key]
        else:
            raise ValueError(f"Variable {key} not declared")
        
class FuncTable:
    def __init__(self):
        self.table = {}

    def setter(self, name, node):
        self.table[name] = node

    def getter(self, name):
        if name in self.table:
            return self.table[name]
        else:
            raise ValueError(f"Function {name} not declared")

class Node:
    def __init__(self, value, children):
        self.value = value
        self.children = children

    def evaluate(self, st, ft):
        raise NotImplementedError("Must override evaluate")

class BinOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st, ft):
        left_val, left_type = self.children[0].evaluate(st, ft)
        right_val, right_type = self.children[1].evaluate(st, ft)

        if self.value in {'+', '-', '*', '/', 'and', 'or'}:
            if left_type != 'int' or right_type != 'int':
                raise TypeError(f"Arithmetic operations require integer types, got {left_type} and {right_type}")
            if self.value == '+':
                return (left_val + right_val, 'int')
            elif self.value == '-':
                return (left_val - right_val, 'int')
            elif self.value == '*':
                return (left_val * right_val, 'int')
            elif self.value == '/':
                return (left_val // right_val, 'int')
            elif self.value == 'and':
                return (left_val and right_val, 'int')
            elif self.value == 'or':
                return (left_val or right_val, 'int')

        elif self.value in {'==', '>', '<'}:
            if left_type != right_type:
                raise TypeError(f"Comparison operations require matching types, got {left_type} and {right_type}")
            if self.value == '==':
                return (int(left_val == right_val), 'int')
            elif self.value == '>':
                return (int(left_val > right_val), 'int')
            elif self.value == '<':
                return (int(left_val < right_val), 'int')

        elif self.value == '..':
            return (str(left_val) + str(right_val), 'string')

        else:
            raise ValueError(f"Unsupported operator {self.value}")

class UnOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st, ft):
        val, typ = self.children[0].evaluate(st, ft)
        if typ != 'int':
            raise TypeError("Mismatched types in unary operation")
        if self.value == '+':
            return (val, typ)
        elif self.value == '-':
            return (-val, typ)
        elif self.value == 'not':
            return (not val, typ)

class IntVal(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def evaluate(self, st, ft):
        return (self.value, 'int')

class StringVal(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def evaluate(self, st, ft):
        return (self.value, 'string')

class NoOp(Node):
    def __init__(self):
        super().__init__(None, [])

    def evaluate(self, st, ft):
        return (None, 'Null')

class Block(Node):
    def __init__(self, children):
        super().__init__(None, children)

    def evaluate(self, st, ft):
        for child in self.children:
            child.evaluate(st, ft)
            if isinstance(child, Return):
                return child.evaluate(st, ft)

class Identifier(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def evaluate(self, st, ft):
        return st.getter(self.value)

class Assignment(Node):
    def __init__(self, children):
        super().__init__(None, children)

    def evaluate(self, st, ft):
        if self.children[0].value in st.table:
            var_name = self.children[0].value
            value, typ = self.children[1].evaluate(st, ft)
            st.setter(var_name, value, typ)
        else:
            raise ValueError(f"Variable {self.children[0].value} not declared")

class VarDec(Node):
    def __init__(self, children):
        super().__init__(None, children)

    def evaluate(self, st, ft):
        if self.children[0].value in st.table:
            raise ValueError(f"Variable {self.children[0].value} already declared")
        var_name = self.children[0].value
        value, typ = self.children[1].evaluate(st, ft)
        st.setter(var_name, value, typ)

class Print(Node):
    def __init__(self, children):
        super().__init__(None, children)

    def evaluate(self, st, ft):
        value, typ = self.children[0].evaluate(st, ft)
        print(value)

class While(Node):
    def __init__(self, children):
        super().__init__(None, children)

    def evaluate(self, st, ft):
        while self.children[0].evaluate(st, ft)[0]:
            for child in self.children[1]:
                child.evaluate(st, ft)

class If(Node):
    def __init__(self, children):
        super().__init__(None, children)

    def evaluate(self, st, ft):
        condition, _ = self.children[0].evaluate(st, ft)
        if condition:
            for stmt in self.children[1]:
                stmt.evaluate(st, ft)
        else:
            for stmt in self.children[2]:
                stmt.evaluate(st, ft)
            
class Read(Node):
    def __init__(self, children):
        super().__init__(None, children)
        
    def evaluate(self, st, ft):
        return (self.children[0], 'int')
    
class FuncDec(Node):
    def __init__(self, children):
        super().__init__(None, children)
        
    def evaluate(self, st, ft):
        func_name = self.children[0].value
        ft.setter(func_name, self) 
        
class FuncCall(Node):
    def __init__(self, children):
        super().__init__(None, children)
        
    def evaluate(self, st, ft):
        func_name = self.children[0].value
        func_node = ft.getter(func_name)
        args = self.children[1]
        original_args = func_node.children[1]
        
        if len(func_node.children)-1 != len(self.children):
            raise ValueError(f"Function {func_name} expected {len(func_node.children)-2} arguments, got {len(self.children)}")        

        local_st = SymbolTable()

        for i in range(0, len(args)):
            value, typ = args[i].evaluate(st, ft)
            local_st.setter(original_args[i].value, value, typ)
            
        return func_node.children[-1].evaluate(local_st, ft)
            
class Return(Node):
    def __init__(self, children):
        super().__init__(None, children)
        
    def evaluate(self, st, ft):
        return self.children[0].evaluate(st, ft)

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
        #LOCAL
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
            
        #IDENTIFIER
        elif tokenizer.next.type == 'IDENTIFIER':
            identifier = Identifier(tokenizer.next.value)
            tokenizer.selectNext()
            if tokenizer.next.type != 'ASSIGN' and tokenizer.next.type != 'LPAREN':
                sys.stderr.write(f"Expected = or (\n")
                sys.exit(1)
            if tokenizer.next.type == 'LPAREN':
                tokenizer.selectNext()
                arguments = []
                while tokenizer.next.type != 'RPAREN':
                    expression = Parser.boolExpression(tokenizer)
                    arguments.append(expression)
                    if tokenizer.next.type == 'COMMA':
                        tokenizer.selectNext()
                if tokenizer.next.type != 'RPAREN':
                    sys.stderr.write(f"Expected )\n")
                    sys.exit(1)
                tokenizer.selectNext()
                if tokenizer.next.type != 'EOF' and tokenizer.next.type != 'NEWLINE':
                    sys.stderr.write(f"Expected \\n\n")
                    sys.exit(1)
                tokenizer.selectNext()
                return FuncCall([identifier, arguments])
            elif tokenizer.next.type == 'ASSIGN':
                tokenizer.selectNext()
                expression = Parser.boolExpression(tokenizer)
                if tokenizer.next.type != 'EOF' and tokenizer.next.type != 'NEWLINE':
                    sys.stderr.write(f"Expected \\n\n")
                    sys.exit(1)
                tokenizer.selectNext()
                return Assignment([identifier, expression])
        
        #PRINT
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
        
        #NEWLINE
        elif tokenizer.next.type == 'NEWLINE':
            tokenizer.selectNext()
            return NoOp()
        
        #WHILE
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
        
        #IF
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
            
        #FUNCTION
        elif tokenizer.next.type == 'FUNCTION':
            tokenizer.selectNext()
            if tokenizer.next.type != 'IDENTIFIER':
                sys.stderr.write(f"Expected identifier\n")
                sys.exit(1)
            identifier = Identifier(tokenizer.next.value)
            tokenizer.selectNext()
            if tokenizer.next.type != 'LPAREN':
                sys.stderr.write(f"Expected (\n")
                sys.exit(1)
            tokenizer.selectNext()
            arguments = []
            while tokenizer.next.type != 'RPAREN':
                if tokenizer.next.type != 'IDENTIFIER':
                    sys.stderr.write(f"Expected identifier\n")
                    sys.exit(1)
                arguments.append(Identifier(tokenizer.next.value))
                tokenizer.selectNext()
                if tokenizer.next.type == 'COMMA':
                    tokenizer.selectNext()
            if tokenizer.next.type != 'RPAREN':
                sys.stderr.write(f"Expected )\n")
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
                sys.stderr.write(f"Expected\\n\n")
                sys.exit(1)
            block = Block(statements)
            return FuncDec([identifier, arguments, block])
        
        #RETURN
        elif tokenizer.next.type == 'RETURN':
            tokenizer.selectNext()
            expression = Parser.boolExpression(tokenizer)
            if tokenizer.next.type != 'EOF' and tokenizer.next.type != 'NEWLINE':
                sys.stderr.write(f"Expected \\n\n")
                sys.exit(1)
            tokenizer.selectNext()
            return Return([expression])
        
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
            if tokenizer.next.type == 'LPAREN':
                tokenizer.selectNext()
                arguments = []
                while tokenizer.next.type != 'RPAREN':
                    expression = Parser.boolExpression(tokenizer)
                    arguments.append(expression)
                    if tokenizer.next.type == 'COMMA':
                        tokenizer.selectNext()
                if tokenizer.next.type != 'RPAREN':
                    sys.stderr.write(f"Expected )\n")
                    sys.exit(1)
                tokenizer.selectNext()
                return FuncCall([Identifier(result), arguments])
            else:
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
                sys.stderr.write(f"Expected )\n")
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
    def run(code, st, ft):
        tokenizer = Tokenizer(code)
        tokenizer.selectNext()  # Initialize the tokenizer
        result = Parser.parseBlock(tokenizer)
        result = result.evaluate(st, ft)
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
        ft = FuncTable()
        code = PrePro.filter(code)
        result = Parser.run(code, st, ft)
    except FileNotFoundError:
        sys.stderr.write(f"Error: File {filename} not found\n")
        sys.exit(1)