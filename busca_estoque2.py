lines = open('static/index.html', 'r', encoding='utf-8').readlines()
# Procurar a seção HTML da aba estoque
in_estoque = False
for i in range(len(lines)):
    if 'estoque' in lines[i].lower() and ('subtab' in lines[i].lower() or 'id=' in lines[i].lower()):
        if 'id="subtab-estoque"' in lines[i] or 'subtab-estoque' in lines[i] or 'subtab_estoque' in lines[i]:
            start = max(0, i - 1)
            end = min(len(lines), i + 80)
            print(f'--- SUBABA ESTOQUE (linha {i+1}) ---')
            for j in range(start, end):
                print(f'{j+1}: {lines[j]}', end='')
            print()