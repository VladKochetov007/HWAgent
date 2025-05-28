from sympy import symbols, integrate

# Define the variable
x = symbols('x')

# Define the function
f = x**2 + x

# Calculate the definite integral from -4 to 5
result = integrate(f, (x, -4, 5))

# Print the result
print(f"The definite integral of x^2 + x from -4 to 5 is: {result}")