lines = open('static/index.html', 'r', encoding='utf-8').readlines()
for i in range(len(lines)):
    if 'renderizarEstoque' in lines[i] or 'function carregarEstoque' in lines[i]:
        start = i
        end = min(len(lines), i + 80)
        print(f'--- Funcao inicio linha {i+1} ---')
        for j in range(start, end):
            print(f'{j+1}: {lines[j]}', end='')
        print()
        break