lines = open('static/index.html', 'r', encoding='utf-8').readlines()
# Procurar a subaba pedidos
in_pedido = False
for i in range(len(lines)):
    if 'subtab-pedidos' in lines[i] or 'subtab_pedidos' in lines[i]:
        start = i
        end = min(len(lines), i + 60)
        print(f'--- SUBABA PEDIDOS (linha {i+1}) ---')
        for j in range(start, end):
            print(f'{j+1}: {lines[j]}', end='')
        print()
        break