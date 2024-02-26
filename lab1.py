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
        else:
            sys.stderr.write(f"Unexpected character: {self.source[self.position]}\n")
            sys.exit(1)

class Parser:
    @staticmethod
    def parseExpression(tokenizer):
        result = 0
        has_operator = False
        tokenizer.selectNext()
        if tokenizer.next.type in ['PLUS', 'MINUS']:
            sys.stderr.write("Expression cannot start with an operator\n")
            sys.exit(1)
        while tokenizer.next.type != 'EOF':
            if tokenizer.next.type == 'INT':
                result += tokenizer.next.value
                tokenizer.selectNext()
                if tokenizer.next.type == 'INT':
                    sys.stderr.write("It is not possible to have space between two numbers\n")
                    sys.exit(1)
            elif tokenizer.next.type == 'PLUS':
                has_operator = True
                tokenizer.selectNext()
                result += tokenizer.next.value
                tokenizer.selectNext()
            elif tokenizer.next.type == 'MINUS':
                has_operator = True
                tokenizer.selectNext()
                result -= tokenizer.next.value
                tokenizer.selectNext()
            else:
                sys.stderr.write(f"Unexpected token: {tokenizer.next}\n")
                sys.exit(1)
        if not has_operator:
            sys.stderr.write("Expression must contain at least one operator (+ or -)\n")
            sys.exit(1)
        return result

    @staticmethod
    def run(code):
        tokenizer = Tokenizer(code)
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
