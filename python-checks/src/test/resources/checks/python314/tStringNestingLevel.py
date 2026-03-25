
# Test that deeply nested t-strings are detected like f-strings
# PEP 750 - Template String Literals should follow same nesting rules

def non_compliant(hello, name):
    my_string = t"{t"{t"{hello}"},"} {name}!" # Noncompliant {{Do not nest f-strings too deeply.}}
    #           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    greeting = t"{t"{hello}"},"
    my_string = t"hello:{greeting}, {name}, {t"end: { t"done" }"}!" # Noncompliant
#               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    my_string = t"hello { t"format specifier: {greeting :{T"1"}.{2}}"}" # Noncompliant
#               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

def compliant(hello, name):
    greeting = t"{t"{hello}"},"
    my_string = t"{greeting} {name}!" # Compliant

    my_string = t"{greeting} {name : { t"1" }.{2}}!"
