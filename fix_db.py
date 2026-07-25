with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = "                # Boolean: converte 0/1 do SQLite para TRUE/FALSE do PostgreSQL
                sql = re.sub(
                    r\"COALESCE\(([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*),\s*0\)\s*=\s*1\",
                    r\"( IS TRUE)\",
                    sql
                )
                sql = re.sub(
                    r\"COALESCE\(([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*),\s*0\)\s*=\s*0\",
                    r\"( IS NOT TRUE)\",
                    sql
                )
                sql = re.sub(
                    r(controla_depreciacao|requer_calibracao|sobressalente|requer_equipamento|ativo)\s*=\s*\",
                    r\" = TRUE\",
                    sql
                )
                sql = re.sub(
                    r(controla_depreciacao|requer_calibracao|sobressalente|requer_equipamento|ativo)\s*=\s*\",
                    r\" = FALSE\",
                    sql
                )"

new = "                # Boolean: converte 0/1 do SQLite para TRUE/FALSE do PostgreSQL
                sql = re.sub(
                    r\"COALESCE\(([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*),\s*0\)\s*=\s*1\",
                    r\"(\1 IS TRUE)\",
                    sql
                )
                sql = re.sub(
                    r\"COALESCE\(([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*),\s*0\)\s*=\s*0\",
                    r\"(\1 IS NOT TRUE)\",
                    sql
                )
                sql = re.sub(
                    r\"\b(controla_depreciacao|requer_calibracao|sobressalente|requer_equipamento|ativo)\s*=\s*1\b\",
                    r\"\1 = TRUE\",
                    sql
                )
                sql = re.sub(
                    r\"\b(controla_depreciacao|requer_calibracao|sobressalente|requer_equipamento|ativo)\s*=\s*0\b\",
                    r\"\1 = FALSE\",
                    sql
                )"

if old in content:
    content = content.replace(old, new)
    with open('database.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK - Bloco boolean corrigido!')
else:
    print('ERRO - Bloco antigo nao encontrado')
