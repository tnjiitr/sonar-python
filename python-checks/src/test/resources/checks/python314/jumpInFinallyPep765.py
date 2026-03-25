# PEP 765: Disallow return/break/continue in finally blocks
# Python 3.14 explicitly forbids these patterns at runtime
# The JumpInFinallyCheck (S1143) should detect all of these

# return in finally - basic case
def return_in_finally():
    try:
        foo()
    finally:
        return 42 # Noncompliant {{Remove this "return" statement from this "finally" block.}}

# return in finally - with value
def return_with_value_in_finally():
    try:
        result = compute()
    finally:
        return result # Noncompliant

# break in finally
def break_in_finally():
    for i in range(10):
        try:
            foo(i)
        finally:
            break # Noncompliant {{Remove this "break" statement from this "finally" block.}}

# continue in finally
def continue_in_finally():
    for i in range(10):
        try:
            foo(i)
        finally:
            continue # Noncompliant {{Remove this "continue" statement from this "finally" block.}}

# Nested try/finally - both levels detected
def nested_try_finally():
    try:
        try:
            pass
        finally:
            return 1 # Noncompliant
    finally:
        return 2 # Noncompliant

# return in finally with except clause
def return_in_finally_with_except():
    try:
        risky_operation()
    except ValueError:
        handle_error()
    finally:
        return "cleanup" # Noncompliant

# Compliant: return/break/continue NOT in finally
def compliant_return():
    try:
        return 42
    except Exception:
        return -1
    finally:
        cleanup()

def compliant_break():
    for i in range(10):
        try:
            if condition:
                break
        finally:
            cleanup()

def compliant_continue():
    for i in range(10):
        try:
            if condition:
                continue
        finally:
            cleanup()

# Compliant: break/continue in nested loop within finally
def compliant_nested_loop_in_finally():
    for i in range(3):
        try:
            foo(i)
        finally:
            for j in range(3):
                break
    for i in range(3):
        try:
            foo(i)
        finally:
            for j in range(3):
                continue

# Non-compliant: return in nested loop within finally (still in finally scope)
def return_in_nested_loop_in_finally():
    for i in range(3):
        try:
            foo(i)
        finally:
            for j in range(3):
                return j # Noncompliant

# Compliant: jump in nested function within finally
def jump_in_nested_function():
    for i in range(3):
        try:
            foo(i)
        finally:
            def nested_return():
                return
            nested_return()

# return in finally inside async function
async def async_return_in_finally():
    try:
        await some_coroutine()
    finally:
        return "result" # Noncompliant

# Python 3.14 PEP 758 syntax: except with unparenthesized multiple exceptions
def jump_in_finally_with_pep758_except():
    for i in range(3):
        try:
            foo(i)
        except ValueError, TypeError:
            handle()
        finally:
            break # Noncompliant
