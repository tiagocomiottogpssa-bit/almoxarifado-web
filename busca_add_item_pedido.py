lines = open('static/index.html', 'r', encoding='utf-8').readlines()
# Procurar a funcao que renderiza itens do pedido ou adiciona item
for i in range(len(lines)):
    if 'adicionarItemPedido' in lines[i] or 'addItemPedido' in lines[i] or 'function adicionarItem' in lines[i]:
        start = max(0, i - 1)
        end = min(len(lines), i + 30)
        print(f'--- Linha {i+1} ---')
        for j in range(start, end):
            print(f'{j+1}: {lines[j]}', end='')
        print()