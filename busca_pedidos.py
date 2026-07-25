lines = open('static/index.html', 'r', encoding='utf-8').readlines()
for i in range(len(lines)):
    if 'pedido' in lines[i].lower():
        start = max(0, i - 1)
        end = min(len(lines), i + 4)
        print(f'--- Linha {i+1} ---')
        for j in range(start, end):
            print(f'{j+1}: {lines[j]}', end='')
        print()