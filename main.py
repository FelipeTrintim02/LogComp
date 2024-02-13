import sys

class Calculator:
    def __init__(self):
        pass

    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
    
    def calculate(self, expression):
        if not expression:
            sys.stderr.write("Erro: Expressão vazia.\n")
            return None
        
        expression = expression.replace(' ','')
        number = []
        operation = []
        num = ''

        for i in expression:
            if i.isdigit():
                num += i
            else:
                number.append(int(num))
                operation.append(i)
                num = ''
        
        if num:
            number.append(int(num))

        result = number[0]

        if len(operation) == 0:
            sys.stderr.write("Erro: Operação não especificada.\n")
            return None
        else:
            for i, op in enumerate(operation):
                if op == "+":
                    result = self.add(result, number[i+1])
                elif op == "-":
                    result = self.subtract(result, number[i+1])

        return result    

if __name__ == "__main__":

    if len(sys.argv) > 1:
        expression = sys.argv[1]
    else:
        expression = ''

    result = Calculator().calculate(expression)

    if result is not None:
        print(result)
