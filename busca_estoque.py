lines = open('static/index.html', 'r', encoding='utf-8').readlines()
for i in range(len(lines)):
    if 'estoque' in lines[i].lower() and ('tab' in lines[i].lower() or 'subtab' in lines[i].lower() or 'id=' in lines[i].lower()):
        start = max(0, i - 1)
        end = min(len(lines), i + 5)
        print(f'--- Linha {i+1} ---')
        for j in range(start, end):
            print(f'{j+1}: {lines[j]}', end='')
        print()