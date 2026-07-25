html = open('static/index.html', 'r', encoding='utf-8').read()
# Find all tab/subtab sections
import re
matches = list(re.finditer(r'(subtab|tab).*?pedido', html, re.IGNORECASE))
for m in matches:
    start = max(0, m.start() - 50)
    end = min(len(html), m.end() + 50)
    # Get line number
    line_num = html[:m.start()].count("\n") + 1
    print(f'Linha ~{line_num}: ...{html[start:end].replace(chr(10), " ")}...')
    print()
if not matches:
    print('Nenhum match encontrado')