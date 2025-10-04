# Import necessary libraries
import ast  # For safely parsing and evaluating expressions from strings
import operator as op  # Provides functions corresponding to Python's intrinsic operators
import math  # For mathematical functions like sqrt, sin, cos, etc.
import csv  # For creating and handling CSV data
import io  # Used to handle in-memory text streams (for CSV generation)
import re  # For regular expressions, used in parsing user input
from statistics import mean, median  # For calculating statistical mean and median

# -----------------------------
# 1. Safe Expression Evaluator
# -----------------------------

# A whitelist of allowed mathematical operations. Maps AST nodes to operator functions.
ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}

# A whitelist of allowed function names and constants from the math module.
ALLOWED_NAMES = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
# Manually add other safe, built-in functions.
ALLOWED_NAMES.update({"abs": abs, "round": round, "min": min, "max": max})


def safe_eval(expr: str):
    """Safely evaluate a math expression string using Abstract Syntax Trees (AST).

    This prevents arbitrary code execution, which would be a risk with eval().
    """

    # Inner recursive function to traverse the AST.
    def _eval(node):
        # If the node is a number, return its value.
        if isinstance(node, ast.Num):  # numbers
            return node.n
        # If the node is a binary operation (e.g., 2 + 3), evaluate both sides and apply the operator.
        elif isinstance(node, ast.BinOp):  # binary operations
            return ALLOWED_OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
        # If the node is a unary operation (e.g., -5), evaluate the operand and apply the operator.
        elif isinstance(node, ast.UnaryOp):  # unary (+/-)
            return ALLOWED_OPERATORS[type(node.op)](_eval(node.operand))
        # If the node is a function call (e.g., sqrt(9)), check if it's in the whitelist.
        elif isinstance(node, ast.Call):  # function calls
            func = node.func.id
            # If the function is allowed, evaluate its arguments and call the function.
            if func in ALLOWED_NAMES:
                args = [_eval(arg) for arg in node.args]
                return ALLOWED_NAMES[func](*args)
            else:
                # If the function is not in the whitelist, raise an error.
                raise ValueError(f"Function {func} not allowed")
        # The top-level node is an Expression, so we evaluate its body.
        elif isinstance(node, ast.Expression):
            return _eval(node.body)
        else:
            # If the node type is not supported, raise an error.
            raise TypeError(f"Unsupported expression: {node}")

    # Parse the input expression into an AST. 'eval' mode means it expects a single expression.
    node = ast.parse(expr, mode="eval")
    # Start the recursive evaluation from the body of the parsed expression.
    return _eval(node.body)


# -----------------------------
# 2. Unit Conversion
# -----------------------------

# A dictionary to store unit conversion functions.
# Each key is a tuple (from_unit, to_unit), and the value is a lambda function for the conversion.
UNIT_MAP = {
    ("m", "cm"): lambda x: x * 100,
    ("cm", "m"): lambda x: x / 100,
    ("kg", "lb"): lambda x: x / 0.45359237,
    ("lb", "kg"): lambda x: x * 0.45359237,
}


def convert_units(value: float, from_unit: str, to_unit: str):
    """Converts a value from one unit to another using the UNIT_MAP."""
    # Create a key from the units (lowercase) to look up in the map.
    key = (from_unit.lower(), to_unit.lower())
    # If a converter for this pair of units exists, apply it.
    if key in UNIT_MAP:
        return UNIT_MAP[key](value)
    # If no converter is found, raise an error.
    raise ValueError(f"No converter registered for {from_unit} -> {to_unit}")


# -----------------------------
# 3. Intent Classification
# -----------------------------

def classify_intent(text: str):
    """Classifies the user's intent based on keywords in the input text."""
    # Normalize the text to lowercase and remove leading/trailing whitespace.
    text_l = text.lower().strip()
    # If keywords related to conversion are found, classify as 'convert'.
    if re.search(r"\b(convert|to (?:cm|m|kg|lb))", text_l):
        return "convert"
    # If keywords for statistics are found, classify as 'stats'.
    if re.search(r"\b(mean|median|average)", text_l):
        return "stats"
    # If keywords for CSV generation are found, classify as 'generate_csv'.
    if re.search(r"\b(csv|spreadsheet|save)", text_l):
        return "generate_csv"
    # If the text starts with 'calculate' or contains math symbols, classify as 'calculate'.
    if text_l.startswith("calculate") or any(tok in text_l for tok in ["+", "-", "*", "/", "sqrt", "^"]):
        return "calculate"
    # If no specific intent is matched, return 'unknown'.
    return "unknown"


# -----------------------------
# 4. Helpers
# -----------------------------

def extract_numbers_from_text(text: str):
    """Extracts all numbers (integers and floats) from a string using regex."""
    # Find all sequences of digits, optionally with a decimal point and a leading minus sign.
    nums = re.findall(r"-?\d+\.?\d*", text)
    # Convert the extracted strings to float numbers.
    return [float(n) for n in nums]


# -----------------------------
# 5. Handlers
# -----------------------------

def handle_calculate(text: str):
    """Handles the 'calculate' intent."""
    # Remove trigger words like 'calculate' from the beginning of the string.
    t = re.sub(r"^(calculate|what is|evaluate)\s*", "", text).strip()
    # Replace the user-friendly power operator '^' with Python's '**'.
    t = t.replace("^", "**")
    # Evaluate the cleaned expression safely.
    result = safe_eval(t)
    # Return a dictionary with the result.
    return {"status": "ok", "intent": "calculate", "result": result}


def handle_convert(text: str):
    """Handles the 'convert' intent."""
    # Use regex to parse out the value, from_unit, and to_unit.
    m = re.search(r"(-?\d+\.?\d*)\s*([a-zA-Z]+)\s*(?:to|in)\s*([a-zA-Z]+)", text)
    # If the regex doesn't match, the format is invalid.
    if not m:
        return {"status": "error", "intent": "convert", "error": "Invalid conversion format"}
    # Extract the captured groups from the match object.
    value, from_unit, to_unit = m.groups()
    # Perform the conversion.
    result = convert_units(float(value), from_unit, to_unit)
    # Return a dictionary with the conversion result.
    return {"status": "ok", "intent": "convert", "result": result, "from": from_unit, "to": to_unit}


def handle_stats(text: str):
    """Handles the 'stats' intent."""
    # Extract all numbers from the input text.
    nums = extract_numbers_from_text(text)
    # If no numbers were found, return an error.
    if not nums:
        return {"status": "error", "intent": "stats", "error": "No numbers found"}
    # If 'mean' or 'average' is in the text, calculate the mean.
    if "mean" in text or "average" in text:
        return {"status": "ok", "intent": "stats", "operation": "mean", "result": mean(nums)}
    # If 'median' is in the text, calculate the median.
    if "median" in text:
        return {"status": "ok", "intent": "stats", "operation": "median", "result": median(nums)}
    # If neither mean nor median is requested, return an error.
    return {"status": "error", "intent": "stats", "error": "No valid operation found"}


def handle_generate_csv(text: str):
    """Handles the 'generate_csv' intent."""
    # Extract all numbers from the input text.
    nums = extract_numbers_from_text(text)
    # If no numbers were found, return an error.
    if not nums:
        return {"status": "error", "intent": "generate_csv", "error": "No numbers found"}
    # Create an in-memory string buffer to write the CSV data to.
    output = io.StringIO()
    # Create a CSV writer object.
    writer = csv.writer(output)
    # Write the header row.
    writer.writerow(["index", "value"])
    # Write each number to a new row in the CSV with an index.
    for i, v in enumerate(nums, start=1):
        writer.writerow([i, v])
    # Return the CSV data as a string.
    return {"status": "ok", "intent": "generate_csv", "csv": output.getvalue()}


def handle_unknown(text: str):
    """Handles any request that couldn't be classified."""
    # Return a generic error message.
    return {"status": "error", "intent": "unknown", "error": "Sorry, I couldn't understand your request."}


# -----------------------------
# 6. Dispatcher
# -----------------------------

# A dispatcher dictionary that maps intent names to their corresponding handler functions.
INTENT_HANDLERS = {
    "calculate": handle_calculate,
    "convert": handle_convert,
    "stats": handle_stats,
    "generate_csv": handle_generate_csv,
    "unknown": handle_unknown,
}


def agent_process(text: str):
    """The main processing function for the agent."""
    # First, classify the user's intent.
    intent = classify_intent(text)
    # Look up the appropriate handler function for the intent.
    handler = INTENT_HANDLERS.get(intent, handle_unknown)
    # Call the handler and return its result.
    return handler(text)


# -----------------------------
# 7. CLI Loop
# -----------------------------

# This block runs when the script is executed directly.
if __name__ == "__main__":
    # Print a welcome message and example commands.
    print("Calculator Agent - try commands like:")
    print("  calculate 2 + 3 * 4")
    print("  10 kg to lb")
    print("  mean of 5, 10, 15")
    print("  generate csv 1 2 3 4 5")
    print("Type 'quit' or 'exit' to stop.\n")

    # Start an infinite loop to read user input.
    while True:
        # Prompt the user and read a line of text.
        text = input(">> ").strip()
        # If the user types 'quit' or 'exit', break the loop.
        if text.lower() in ("quit", "exit"):
            break
        # Process the user's input through the agent.
        resp = agent_process(text)
        # Special handling for CSV generation to print it nicely.
        if resp["intent"] == "generate_csv" and resp["status"] == "ok":
            print("Generated CSV:\n", resp["csv"])
        else:
            # For all other responses, print the result dictionary directly.
            print(resp)
