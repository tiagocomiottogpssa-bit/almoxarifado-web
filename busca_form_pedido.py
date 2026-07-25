lines = open('static/index.html', 'r', encoding='utf-8').readlines()
# Mostrar o formulario de pedidos por completo
for i in range(1095, 1120):
    print(f'{i+1}: {lines[i]}', end='')