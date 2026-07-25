import re

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the function
match = re.search(r'def _migrate_quantidade_transferida\(conn\):.*?(?=\n\ndef|\Z)', content, re.DOTALL)
if match:
    old_func = match.group(0)
    print("=== FUNCAO ANTIGA ===")
    print(old_func[:100])
    print("...")
    print(old_func[-100:])
    
    # Check if it uses try/except
    if 'try:' in old_func:
        # Build new function using _column_exists
        indent = '    '
        new_func = f'''def _migrate_quantidade_transferida(conn):
{indent}"""
{indent}Migration: adiciona coluna quantidade_transferida em pedidos_itens
{indent}para permitir transferencia parcial de itens do pedido.
{indent}"""
{indent}if not _column_exists(conn, 'pedidos_itens', 'quantidade_transferida'):
{indent}    conn.execute("""
{indent}        ALTER TABLE pedidos_itens
{indent}        ADD COLUMN quantidade_transferida INTEGER DEFAULT 0
{indent}    """)
{indent}    print("Migration: coluna 'quantidade_transferida' adicionada em pedidos_itens.")
{indent}else:
{indent}    print("Migration: coluna 'quantidade_transferida' ja existe.")

'''
        content = content.replace(old_func, new_func)
        with open('database.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("\n✅ FUNCAO SUBSTITUIDA!")
    else:
        print("\n❌ try/except nao encontrado na funcao")
else:
    print("❌ Funcao nao encontrada")
