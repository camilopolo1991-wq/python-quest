# Lesson 5 · input()

`input()` waits for the user to type something, and gives it back as **text**.

```python
name = input("What's your name? ")
print(f"Hola, {name}!")
```

To do math, turn the text into a number:

```python
age = int(input("Age: "))        # whole number
height = float(input("Height: ")) # decimal number
```

**Common mistake:** `input("Age: ") + 1` gives a `TypeError`, because text + number doesn't work.
