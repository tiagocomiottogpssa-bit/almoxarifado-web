lines = open('static/index.html', 'r', encoding='utf-8').readlines()
for i in range(len(lines)):
    if 'function abrirFormularioPedido' in lines[i]:
        start = i
        end = min(len(lines), i + 30)
        print(f'--- Linha {i+1} ---')
        for j in range(start, end):
            print(f'{j+1}: {lines[j]}', end='')
        print()
        break
else:
    print('Funcao nao encontrada')