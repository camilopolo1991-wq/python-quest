bill = float(input("Bill: "))
people = int(input("People: "))
tip = float(input("Tip %: "))
each = bill * (1 + tip / 100) / people
print(f"Each pays: {each:.2f}")
if each > 50000:
    print("Expensive night!")
