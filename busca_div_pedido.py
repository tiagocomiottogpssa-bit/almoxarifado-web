lines = open('static/index.html', 'r', encoding='utf-8').readlines()
# Procurar onde fica a div de pedidos
found = []
for i in range(len(lines)):
    if 'pedido' in lines[i].lower() and ('div' in lines[i].lower() or 'section' in lines[i].lower()):
        found.append(i)
# Mostrar contexto ao redor
for idx in found[:10]:
    start = max(0, idx - 2)
    end = min(len(lines), idx + 3)
    print(f'--- Linha {idx+1} ---')
    for j in range(start, end):
        print(f'{j+1}: {lines[j]}', end='')
    print()