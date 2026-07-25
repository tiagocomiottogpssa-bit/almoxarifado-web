with open("database.py", "r", encoding="utf-8") as f:
    text = f.read()

n1 = text.count(chr(1))
n2 = text.count(chr(8))

text = text.replace(chr(1), "\1")
text = text.replace(chr(8), "\b")

with open("database.py", "w", encoding="utf-8") as f:
    f.write(text)

print(f"Substituidos {n1} bytes SOH e {n2} bytes BS")