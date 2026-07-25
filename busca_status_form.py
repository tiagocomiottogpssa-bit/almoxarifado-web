lines = open('static/index.html', 'r', encoding='utf-8').readlines()
# Procurar hidden fields ou inputs de status no formulário
for i in range(1095, 1200):
    if 'status' in lines[i].lower() or 'hidden' in lines[i].lower():
        print(f'{i+1}: {lines[i]}', end='')