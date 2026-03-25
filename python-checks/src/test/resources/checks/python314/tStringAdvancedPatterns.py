# Advanced t-string patterns for Python 3.14 (PEP 750)
# Testing t-string + str concatenation detection

name = "Alice"
age = 30

# Basic t-string + str concatenation (noncompliant)
result1 = t"Hello {name}" + " , welcome."  # Noncompliant {{Template strings should not be concatenated with regular strings.}}
#         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#         ^^^^^^^^^^^^^^^@-1< {{Template string}}
#                           ^^^^^^^^^^^^^@-2< {{Regular string}}

# str + t-string concatenation (noncompliant)
result2 = "Hello" + t" {name}"  # Noncompliant {{Template strings should not be concatenated with regular strings.}}
#         ^^^^^^^^^^^^^^^^^^^^
#         ^^^^^^^@-1< {{Regular string}}
#                   ^^^^^^^^^^@-2< {{Template string}}

# Multiple t-strings concatenation (compliant - both are template strings)
result3 = t"Hello {name}" + t" you are {age}"  # Compliant

# t-string with raw prefix + str (noncompliant)
result4 = tr"Hello {name}" + " world"  # Noncompliant
result5 = rt"Hello {name}" + " world"  # Noncompliant

# Uppercase T prefix + str (noncompliant)
result6 = T"Hello {name}" + " world"  # Noncompliant

# f-string + str (compliant - not a template string check)
result7 = f"Hello {name}" + "world"  # Compliant

# t-string + t-string with different prefixes (compliant)
result8 = t"Hello {name}" + T" you are {age}"  # Compliant
result9 = rt"Hello {name}" + tr" you are {age}"  # Compliant

# Non-concatenation operations (compliant)
result10 = t"Hello {name}" == " world"  # Compliant
result11 = t"Hello {name}" - " world"  # Compliant

# Number addition (compliant)
result12 = 1 + 2  # Compliant

# Implicit concatenation (compliant)
result13 = "Hello" " world"  # Compliant
result14 = t"Hello {name}" t" world {age}"  # Compliant
