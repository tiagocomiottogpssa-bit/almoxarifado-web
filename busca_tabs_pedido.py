lines = open('static/index.html', 'r', encoding='utf-8').readlines()
for i in range(len(lines)):
    if 'pedido' in lines[i].lower() and ('subtab' in lines[i].lower() or 'tab' in lines[i].lower() or 'id=' in lines[i].lower()):
        print(f'{i+1}: {lines[i]}', end='')