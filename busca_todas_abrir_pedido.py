lines = open('static/index.html', 'r', encoding='utf-8').readlines()
for i in range(len(lines)):
    if 'abrirFormularioPedido' in lines[i]:
        print(f'{i+1}: {lines[i]}', end='')