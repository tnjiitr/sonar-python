# Comprehensive Python 3.14 syntax test file for parser validation

# === PEP 750: Template String Literals (t-strings) ===

from string.templatelib import Template

name = "World"
template: Template = t"Hello {name}"

# Various prefix forms
t''
t""
t''''''
t'a'
t"a"
t'''a'''
T'a'
T"a"
tr'a'
tR'a'
Tr'a'
TR'a'
rt'a'
rT'a'
Rt'a'
RT'a'

# t-string with interpolation
t'hello {var}!'
t'''hello '{var}'!'''
t'{{abc}}'
t'{{abc}}{xyz}'
t'{x} {+y}!'

# t-string with escape sequences
t'''hello\n {var}'''
t'\N{RIGHTWARDS ARROW}'
t" \\"
T"\\ \"{a}\":\\"

# t-string with format specifiers
t'{x!a}'
t"{foo("!a")!a}"
t'{user=!s}'
t'{today:%B %d, %Y}'
t'{number:#0x}'
t'result: {value:{width}.{precision}}'
t'{delta.days=:,d}'

# t-string with nested expressions
t"This is the playlist: {"\n".join(songs)}"

# t-string multiline
t"Foo {
    h
    }"

# t-string with escaped quotes
t"Current value: \"{value}\" (type: {type(value)}). "

# raw t-strings
tr"""\s*\{{(.+)\}}"""
rt'^add_example\(\s*"[^"]*",\s*{foo()},\s*\d+,\s*async \(client, console\) => \{{\n(.*?)^(?:\}}| *\}},\n)\);$'
tr'\"foo\"\s*{42}'
tr'\\\\'
rT'\\'

# === PEP 758: Simplified Exception Syntax ===

try:
    foo()
except FileNotFoundError as e:
    print(e)
except (ChildProcessError, EOFError):
    print("Tuple syntax")
except ArithmeticError, ValueError:
    print("New python 3.14 syntax")
except (BrokenPipeError, BufferError) as e:
    print("Parenthesis are required")
except (MemoryError, OverflowError), TypeError:
    print("Mixed parenthesis and unparenthesis")
except OSError, e:
    print("Old python 2 syntax")

# except* syntax
try:
    some_async_op()
except* ValueError:
    pass
except* TypeError:
    pass

# Multiple exceptions without parentheses - three types
try:
    risky()
except ValueError, TypeError, KeyError:
    pass

# === PEP 649: Deferred Annotations ===

class Node:
    left: Node
    right: Node
    value: int

def process(items: list[int | str]) -> dict[str, list[int]]:
    pass

x: int | str = 42
y: list[tuple[int, ...]] = []

type TreeNode = Node | None

# === PEP 765: Control Flow in Finally Blocks ===

def example():
    try:
        pass
    finally:
        pass

for i in range(3):
    try:
        pass
    finally:
        pass
