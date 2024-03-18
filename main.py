import sys
from abc import abstractmethod

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

class PrePro:
    @staticmethod
    def filter(expression):
        whitoutComments = expression.split("--")[0]
        return whitoutComments

class Tokenizer:
    def __init__(self, source):
        filtered_source = PrePro.filter(source)
        self.source = filtered_source
        self.position = 0
        self.next = None
        self.reserved = ['print']

    def selectNext(self):
        if self.position < len(self.source) and self.source[self.position] == "\n":
            self.next = Token("NEWLINE", None)
            self.position += 1
            return

        while self.position < len(self.source) and self.source[self.position].isspace():
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
        else:
            sys.stderr.write(f"Unexpected character: {self.source[self.position]}\n")
            sys.exit(1)

class Node:
    def __init__(self, value : int, children):
        self.value = value
        self.children = children

    @abstractmethod
    def evaluate(self):
        pass

class BinOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st):
        if self.value == '+':
            return self.children[0].evaluate(st) + self.children[1].evaluate(st)
        elif self.value == '-':
            return self.children[0].evaluate(st) - self.children[1].evaluate(st)
        elif self.value == '*':
            return self.children[0].evaluate(st) * self.children[1].evaluate(st)
        elif self.value == '/':
            return self.children[0].evaluate(st) // self.children[1].evaluate(st)
        
class UnOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st):
        if self.value == '+':
            return self.children[0].evaluate(st)
        elif self.value == '-':
            return -self.children[0].evaluate(st)
        
class IntVal(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def evaluate(self, st):
        return self.value
    
class NoOp(Node):
    def __init__(self):
        super().__init__(None, [])

    def evaluate(self, st):
        pass

class Block(Node):
    def __init__(self, children):
        super().__init__(None, children)

    def evaluate(self, st):
        for child in self.children:
            child.evaluate(st)

class Identifier(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def evaluate(self, st):
        return st.getter(self.value)
    
class Assignment(Node):
    def __init__(self, children):
        super().__init__(None, children)

    def evaluate(self, st):
        st.setter(self.children[0].value, self.children[1].evaluate(st))

class Print(Node):
    def __init__(self, children):
        super().__init__(None, children)

    def evaluate(self, st):
        print(self.children[0].evaluate(st))

class SymbolTable:
    def __init__(self):
        self.table = {}

    def setter(self, key, value):
        self.table[key] = value

    def getter(self, key):
        return self.table[key]

class Parser:
    @staticmethod
    def parseStatement(tokenizer):
        if tokenizer.next.type == 'IDENTIFIER':
            identifier = Identifier(tokenizer.next.value)
            tokenizer.selectNext()
            if tokenizer.next.type != 'ASSIGN':
                sys.stderr.write(f"Expected =\n")
                sys.exit(1)
            tokenizer.selectNext()
            expression = Parser.parseExpression(tokenizer)
            if tokenizer.next.type != 'EOF' and tokenizer.next.type != 'NEWLINE':
                sys.stderr.write(f"Expected \\n\n")
                sys.exit(1)
            return Assignment([identifier, expression])
        elif tokenizer.next.type == 'PRINT':
            tokenizer.selectNext()
            if tokenizer.next.type != 'LPAREN':
                sys.stderr.write(f"Expected (\n")
                sys.exit(1)
            tokenizer.selectNext()
            expression = Parser.parseExpression(tokenizer)
            if tokenizer.next.type != 'RPAREN':
                sys.stderr.write(f"Expected )\n")
                sys.exit(1)
            tokenizer.selectNext()
            if tokenizer.next.type != 'EOF' and tokenizer.next.type != 'NEWLINE':
                sys.stderr.write(f"Expected \\n\n")
                sys.exit(1)
            return Print([expression])
        elif tokenizer.next.type == 'NEWLINE':
            tokenizer.selectNext()
            return NoOp()
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
        while tokenizer.next.type in ['PLUS', 'MINUS']:
            if tokenizer.next.type == 'PLUS':
                tokenizer.selectNext()
                result = BinOp('+', [result, Parser.parseTerm(tokenizer)])
            elif tokenizer.next.type == 'MINUS':
                tokenizer.selectNext()
                result = BinOp('-', [result, Parser.parseTerm(tokenizer)])
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
        elif tokenizer.next.type == 'LPAREN':
            tokenizer.selectNext()
            result = Parser.parseExpression(tokenizer)
            if tokenizer.next.type != 'RPAREN':
                sys.stderr.write(f"Expected )\n")
                sys.exit(1)
            tokenizer.selectNext()
            return result
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
        result = Parser.run(code, st)
    except FileNotFoundError:
        sys.stderr.write(f"Error: File {filename} not found\n")
        sys.exit(1)