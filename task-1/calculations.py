import math

def calculate_factorial(n):
    return math.factorial(n)

def calculate_fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

def calculate_mean(numbers):
    return sum(numbers) / len(numbers)
