# Lesson 4 · f-strings

Put an `f` before the quotes and you can drop variables inside `{ }`:

```python
food = "arepa"
price = 3500
print(f"One {food} costs {price} pesos")
```

You can even do math inside: `{price * 2}`.

Format decimals with `:.2f` (2 decimals): `f"{12.5:.2f}"` → `12.50`.
Thousands separator: `f"{1500000:,}"` → `1,500,000`.
