import re

with open("database.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1) Fix COALESCE backreferences (missing \1)
content = content.replace(
    'r"( IS TRUE)"',
    'r"(\1 IS TRUE)"'
)
content = content.replace(
    'r"( IS NOT TRUE)"',
    'r"(\1 IS NOT TRUE)"'
)

# 2) Fix broken simple-boolean regex (missing quotes and \b)
old_true = (
    '                    r(controla_depreciacao|requer_calibracao'
    '|sobressalente|requer_equipamento|ativo)\s*=\s*",\n'
    '                    r" = TRUE",'
)
new_true = (
    '                    r"\b(controla_depreciacao|requer_calibracao'
    '|sobressalente|requer_equipamento|ativo)\s*=\s*1\b",\n'
    '                    r"\1 = TRUE",'
)

old_false = (
    '                    r(controla_depreciacao|requer_calibracao'
    '|sobressalente|requer_equipamento|ativo)\s*=\s*",\n'
    '                    r" = FALSE",'
)
new_false = (
    '                    r"\b(controla_depreciacao|requer_calibracao'
    '|sobressalente|requer_equipamento|ativo)\s*=\s*0\b",\n'
    '                    r"\1 = FALSE",'
)

if old_true in content:
    content = content.replace(old_true, new_true)
    print("TRUE regex fixed!")
else:
    print("TRUE regex NOT FOUND - checking exact content...")
    # debug
    idx = content.find('controla_depreciacao|requer_calibracao')
    if idx >= 0:
        print("Found at:", repr(content[idx-10:idx+150]))

if old_false in content:
    content = content.replace(old_false, new_false)
    print("FALSE regex fixed!")
else:
    print("FALSE regex NOT FOUND")

with open("database.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Done!")
