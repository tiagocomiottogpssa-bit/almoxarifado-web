"""
reset_dados.py — Limpa dados de teste do banco local (SQLite) antes do go-live.
Uso: python reset_dados.py
Seguro: faz backup automático antes de limpar e preserva a tabela de usuários.
"""
import sqlite3
import shutil
import datetime
import os

# Ajuste para o nome do seu banco local (confirme na raiz do projeto)
DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'sistema.db'))

def backup():
    """Cria uma cópia do banco antes de qualquer alteração."""
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = f'backup_pre_reset_{ts}.db'
    shutil.copy2(DB_PATH, dest)
    print(f'✅ Backup criado: {dest}')

def reset():
    """Apaga os dados de todas as tabelas, exceto usuarios. Reinicia os IDs."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Descobre todas as tabelas do schema (exceto tabelas internas e usuarios)
    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
          AND name NOT LIKE 'sqlite_%'
          AND name != 'usuarios'
        ORDER BY name
    """)
    tabelas = [r[0] for r in cur.fetchall()]
    if not tabelas:
        print('⚠️ Nenhuma tabela de dados encontrada (ou o banco ainda não foi criado).')
        conn.close()
        return

    cur.execute('PRAGMA foreign_keys = OFF')
    for t in tabelas:
        cur.execute(f'DELETE FROM "{t}"')
        print(f'   - {t} limpa')
    # Reinicia os contadores de autoincremento (IDs voltam a 1)
    cur.execute('DELETE FROM sqlite_sequence')
    cur.execute('PRAGMA foreign_keys = ON')
    conn.commit()
    conn.close()
    print(f'✅ {len(tabelas)} tabela(s) limpa(s). Tabela usuarios preservada.')

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print(f'❌ Banco não encontrado: {DB_PATH}. Rode o sistema uma vez para criá-lo.')
    else:
        backup()
        reset()
        print('Pronto. Dados fictícios removidos. O sistema recomeça com schema limpo.')