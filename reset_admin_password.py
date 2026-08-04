"""
reset_admin_password.py — Redefine a senha do admin no banco local (SQLite),
ativando a troca obrigatória no primeiro login (trocar_senha=1).
Uso: python reset_admin_password.py
"""
import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'sistema.db'))
SENHA_TEMPORARIA = 'Admin@2026'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Descobre a coluna de senha (senha, password, senha_hash...)
cols = [r[1] for r in cur.execute('PRAGMA table_info(usuarios)')]
candidates = [c for c in cols if c.lower() in ('senha', 'password', 'senha_hash', 'hash', 'passwd')]
if not candidates:
    print('Colunas da tabela usuarios:', cols)
    raise SystemExit('Nao encontrei a coluna de senha — me cola a saida acima.')
col = candidates[0]

cur.execute(
    f'UPDATE usuarios SET "{col}" = ?, trocar_senha = 1 WHERE username = "admin"',
    (generate_password_hash(SENHA_TEMPORARIA),),
)
conn.commit()
print(f'OK! Senha temporaria do admin = {SENHA_TEMPORARIA}')
print(f'Coluna de senha usada: {col}. No primeiro login o sistema forca a troca.')
conn.close()