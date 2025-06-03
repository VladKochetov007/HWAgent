
import math

def is_prime(n):
    """
    Checks if a number is prime.
    A prime number is a natural number greater than 1 that has no positive divisors other than 1 and itself.
    """
    if n <= 1:
        return False
    if n == 2:
        return True # 2 is the only even prime number
    if n % 2 == 0:
        return False # Other even numbers are not prime
    
    # Check for divisibility from 3 up to sqrt(n) with a step of 2
    # We only need to check odd divisors because even divisors are already handled
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True

# Test cases
test_numbers = [0, 1, 2, 3, 4, 5, 7, 10, 11, 13, 17, 29, 31, 97, 100, 101, 103, 1000, 1009]
results = {}
for num in test_numbers:
    results[num] = is_prime(num)

# Print results for LaTeX document
print("Prime Checker Test Results:")
for num, is_p in results.items():
    print(f"{num}: {is_p}")

# You can also save results to a file if needed for LaTeX
with open("prime_test_results.txt", "w") as f:
    f.write("Prime Checker Test Results:\n")
    for num, is_p in results.items():
        f.write(f"{num}: {is_p}\n")
