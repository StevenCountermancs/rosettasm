# RosettASM Language Specification

## Overview
RosettASM is a statically typed, block-structured language with C-style syntax.

---

## Statement Rules

- Statements end with `;`
- Blocks use `{ }`
- Conditions use parentheses `( )`
- `for` loops follow `(init; condition; update)`

---

## Comments

```rasm
// This is a comment
```

---

## Data Types

- int
- float
- bool
- char
> ⚠️ Note: Currently, only `int` is fully supported in the execution environment and UI.
> Other types are parsed but not yet supported during execution.
---

## Variables

### Declaration

```rasm
int x;
float y;
bool flag;
char c;
```

### Declaration with Initialization

```rasm
int x = 5;
float y = 3.14;
bool flag = True;
char c = 'a';
```

---

## Assignment

```rasm
x = 10;
x += 5;
x -= 3;
x++;
x--;
```

---

## Expressions

### Arithmetic

```rasm
a + b
a - b
a * b
a / b
a % b
```

### Unary

```rasm
-a
```

### Comparison

```rasm
a < b
a > b
a <= b
a >= b
a == b
a != b
```

---

## Conditionals

### If

```rasm
if (x < 10) {
    x = x + 1;
}
```

### If / Elif / Else

```rasm
if (x < 0) {
    x = 0;
}
elif (x < 10) {
    x = x + 1;
}
else {
    x = 100;
}
```

---

## Loops

### While

```rasm
while (x < 10) {
    x = x + 1;
}
```

### For

```rasm
for (int i = 0; i < 10; i++) {
    x = x + i;
}
```

### Infinite Loop

```rasm
for (;;) {
}
```

---

## Flow Control

```rasm
break;
continue;
> ⚠️ Note: Currently, break and continue are parsed but not fully supported during execution.
```

---

## Blocks

```rasm
{
    int x = 5;
    x = x + 1;
}
```

---

## Literals

```rasm
10
3.14
True
False
'a'
```

---

## Identifiers

```rasm
x
myVar
_counter
value2
```

Rules:
- Must start with letter or `_`
- Can contain digits
