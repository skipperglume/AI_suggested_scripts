from math import log
def power_sumDigTerm(n):
    numbers = []  # List to store numbers with the desired property
    i = 81  # Start from 81, the first number in the sequence
    while len(numbers) < n:  # Loop until we have found the n-th number
        digits = [int(d) for d in str(i)]  # Split the number into its digits
        print(i," - ",sum(digits))
        if ( not sum(digits) == 1 and log(i,sum(digits)) == int(log(i,sum(digits)))  ):  # Check if the number has the desired property
            numbers.append(i)  # Add the number to our list
        i += 1  # Move on to the next number

    return numbers[-1]  # Return the n-th number in the sequence
print(power_sumDigTerm(4))
print(int(log(64,2)))