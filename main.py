import sys

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

class Tokenizer:
    def __init__(self, source):
        self.source = source
        self.position = 0
        self.next = None

    def selectNext(self):
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

class Parser:
    @staticmethod
    def parseExpression(tokenizer):
        result = Parser.parseTerm(tokenizer)
        while tokenizer.next.type in ['PLUS', 'MINUS']:
            if tokenizer.next.type == 'PLUS':
                tokenizer.selectNext()
                result += Parser.parseTerm(tokenizer)
            elif tokenizer.next.type == 'MINUS':
                tokenizer.selectNext()
                result -= Parser.parseTerm(tokenizer)
        return result

    @staticmethod
    def parseTerm(tokenizer):
        result = Parser.parseFactor(tokenizer)
        while tokenizer.next.type in ['MULT', 'DIV']:
            if tokenizer.next.type == 'MULT':
                tokenizer.selectNext()
                result *= Parser.parseFactor(tokenizer)
            elif tokenizer.next.type == 'DIV':
                tokenizer.selectNext()
                result //= Parser.parseFactor(tokenizer)
        return result

    @staticmethod
    def parseFactor(tokenizer):
        if tokenizer.next.type == 'INT':
            result = tokenizer.next.value
            tokenizer.selectNext()
            return result
        elif tokenizer.next.type == 'PLUS':
            tokenizer.selectNext()
            return Parser.parseFactor(tokenizer)
        elif tokenizer.next.type == 'MINUS':
            tokenizer.selectNext()
            return -Parser.parseFactor(tokenizer)
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
    def run(code):
        tokenizer = Tokenizer(code)
        tokenizer.selectNext()  # Initialize the tokenizer
        result = Parser.parseExpression(tokenizer)
        if tokenizer.next.type != 'EOF':
            sys.stderr.write("Unexpected tokens after expression\n")
            sys.exit(1)
        return result

if __name__ == "__main__":
    expression = sys.argv[1]
    try:
        result = Parser.run(expression)
        print(result)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
