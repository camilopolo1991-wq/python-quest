# Lección 4 · f-strings

Pon una `f` antes de las comillas y puedes meter variables dentro de `{ }`:

```python
comida = "arepa"
precio = 3500
print(f"Una {comida} cuesta {precio} pesos")
```

Hasta puedes hacer cuentas adentro: `{precio * 2}`.

Decimales con `:.2f` (2 decimales): `f"{12.5:.2f}"` → `12.50`.
Separador de miles: `f"{1500000:,}"` → `1,500,000`.
