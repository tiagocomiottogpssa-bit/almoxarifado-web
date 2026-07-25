lines = open('static/index.html', 'r', encoding='utf-8').readlines()
for i in range(len(lines)):
    if 'abrirFormularioPedido' in lines[i] or 'function abrirFormulario' in lines[i]:
        start = max(0, i - 1)
        end = min(len(lines), i + 50)
        print(f'--- Linha {i+1} ---')
        for j in range(start, end):
            print(f'{j+1}: {lines[j]}', end='')
        print()
        break