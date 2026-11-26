# Lección 5 · input()

`input()` espera a que el usuario escriba algo y lo devuelve como **texto**.

```python
nombre = input("¿Cómo te llamas? ")
print(f"¡Hola, {nombre}!")
```

Para hacer cuentas, convierte el texto en número:

```python
edad = int(input("Edad: "))          # número entero
estatura = float(input("Estatura: ")) # número decimal
```

**Error común:** `input("Edad: ") + 1` da un `TypeError`, porque texto + número no funciona.
