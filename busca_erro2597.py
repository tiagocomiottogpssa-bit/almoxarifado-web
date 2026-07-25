lines = open('static/index.html', 'r', encoding='utf-8').readlines()
# Mostrar linha 2597 com contexto
start = max(0, 2596 - 3)
end = min(len(lines), 2596 + 15)
print(f'--- Linha 2597 (indice real {2596}) ---')
for j in range(start, end):
    print(f'{j+1}: {lines[j]}', end='')