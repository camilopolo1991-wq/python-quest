# Lección 7 · Ciclos for

Un ciclo `for` repite código para cada elemento.

```python
for n in range(3):
    print(n)      # 0, 1, 2
```

`range(inicio, fin, paso)` cuenta desde inicio hasta fin, **sin incluir** fin:

```python
range(1, 4)       # 1, 2, 3
range(10, 0, -1)  # 10, 9, ... 1
```

El código dentro del ciclo lleva 4 espacios. El código después del ciclo no.
