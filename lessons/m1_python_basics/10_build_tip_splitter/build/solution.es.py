cuenta = float(input("Cuenta: "))
personas = int(input("Personas: "))
propina = float(input("Propina %: "))
cada_uno = cuenta * (1 + propina / 100) / personas
print(f"Cada uno paga: {cada_uno:.2f}")
if cada_uno > 50000:
    print("¡Noche cara!")
