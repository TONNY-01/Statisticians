print("Simple Calculator")  # Prints the title of the calculator
print('1. Addition')        # Prints option 1: Addition
print('2. Subtraction')     # Prints option 2: Subtraction
print('3. Multiplication')  # Prints option 3: Multiplication
print('4. Division')        # Prints option 4: Division

option = int(input("Choose and operation: "))  # Asks user to choose an operation and converts input to integer

if option in (1, 2, 3, 4):  # Checks if the chosen option is valid (1-4)
        num1 = int(input("Enter first number: "))    # Prompts user for the first number and converts input to integer
        num2 = int(input("Enter second number: "))   # Prompts user for the second number and converts input to integer

        if (option == 1): 
                result = num1 + num2    # If option is 1, adds the numbers

        elif (option == 2):
                result = num1 - num2    # If option is 2, subtracts the numbers

        elif (option == 3):
                result = num1 * num2    # If option is 3, multiplies the numbers

        elif (option == 4):
                result = num1 / num2    # If option is 4, divides the numbers

else:
        print("Invalid input")  # Prints error message if option is not valid

print("The result is {}".format(result))  # Prints the result of the calculation










