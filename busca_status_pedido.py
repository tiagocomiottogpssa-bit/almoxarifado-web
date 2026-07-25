lines = open('static/index.html', 'r', encoding='utf-8').readlines()
# Procurar status_pedido no HTML
for i in range(len(lines)):
    if 'status_pedido' in lines[i]:
        print(f'{i+1}: {lines[i]}', end='')
if not any('status_pedido' in l for l in lines):
    print('status_pedido NAO ENCONTRADO no HTML')