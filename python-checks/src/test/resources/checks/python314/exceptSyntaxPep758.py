# PEP 758 - Simplified Exception Syntax test scenarios
# Testing that sonar-python correctly parses the new unparenthesized multiple exception syntax

# Basic unparenthesized multiple exceptions (PEP 758)
try:
    foo()
except ArithmeticError, ValueError:
    print("caught")

# Three exceptions without parentheses
try:
    bar()
except ValueError, TypeError, KeyError:
    print("caught")

# Traditional parenthesized syntax still works
try:
    baz()
except (ValueError, TypeError):
    print("caught")

# Single exception (unchanged)
try:
    qux()
except ValueError:
    print("caught")

# except* with single exception
try:
    some_async_op()
except* ValueError:
    print("caught")

# except with as clause
try:
    risky()
except FileNotFoundError as e:
    print(e)

# Parenthesized with as
try:
    risky()
except (BrokenPipeError, BufferError) as e:
    print(e)

# Multiple except clauses with mixed syntax
try:
    operation()
except FileNotFoundError as e:
    print(e)
except ArithmeticError, ValueError:
    print("new syntax")
except (MemoryError, OverflowError):
    print("old syntax")

# Old Python 2 style comma syntax (binding exception to variable)
try:
    operation()
except OSError, e:
    print(e)

# Mixed parenthesized and unparenthesized (parser should handle)
try:
    operation()
except (MemoryError, OverflowError), TypeError:
    print("mixed")

# try/except/else/finally combination with PEP 758 syntax
try:
    risky_call()
except ValueError, TypeError:
    handle_errors()
else:
    success()
finally:
    cleanup()

# Nested try with PEP 758 syntax
def nested():
    try:
        try:
            foo()
        except ValueError, TypeError:
            pass
    except RuntimeError, OSError:
        pass
