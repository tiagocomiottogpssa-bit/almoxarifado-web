import os
import sqlite3
from contextlib import contextmanager
import datetime

# ============================================================
# DETECÇÃO DE BANCO DE DADOS
# ============================================================
# Se a variável DATABASE_URL existir, usa PostgreSQL (produção/Railway).
# Caso contrário, usa SQLite (desenvolvimento local).

DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Railway às vezes fornece como postgres:// em vez de postgresql://
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

USE_POSTGRES = bool(DATABASE_URL)

# ============================================================
# ADAPTADOR POSTGRESQL
# ============================================================
if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    class _PgCursor:
        """Wrapper de cursor que simula o comportamento do sqlite3."""
        def __init__(self, cursor):
            self._cursor = cursor

        def execute(self, sql, params=None):
            sql = sql.replace('?', '%s')
            if params is not None:
                self._cursor.execute(sql, params)
            else:
                self._cursor.execute(sql)
            return self

        def fetchall(self):
            return self._cursor.fetchall()

        def fetchone(self):
            return self._cursor.fetchone()

        @property
        def rowcount(self):
            return self._cursor.rowcount

    class _PgConnection:
        """Wrapper de conexão que simula o comportamento do sqlite3."""
        def __init__(self, conn):
            self._conn = conn

        def execute(self, sql, params=None):
            # Conversões automáticas de sintaxe SQLite → PostgreSQL
            sql = sql.replace('?', '%s')
            sql = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')

            cursor = self._conn.cursor(cursor_factory=RealDictCursor)
            if params is not None:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return _PgCursor(cursor)

        def commit(self):
            self._conn.commit()

        def rollback(self):
            self._conn.rollback()

        def close(self):
            self._conn.close()

    @contextmanager
    def get_connection():
        """Context manager que retorna uma conexão PostgreSQL."""
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield _PgConnection(conn)
        finally:
            conn.close()

else:
    # ============================================================
    # MODO DESENVOLVIMENTO (SQLite)
    # ============================================================
    import os
    DATABASE = os.environ.get('DB_PATH', '/tmp/sistema.db')

    @contextmanager
    def get_connection():
        """Context manager que retorna uma conexão sqlite3.Row."""
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


# ============================================================
# HELPERS DE ESQUEMA (funcionam em ambos os bancos)
# ============================================================

def _table_exists(conn, name):
    """Verifica se uma tabela existe no banco."""
    if USE_POSTGRES:
        row = conn.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name = ?",
            (name,)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (name,)
        ).fetchone()
    return row is not None


def _column_exists(conn, table, column):
    """Verifica se uma coluna existe em uma tabela."""
    if not _table_exists(conn, table):
        return False
    if USE_POSTGRES:
        row = conn.execute(
            "SELECT 1 FROM information_schema.columns WHERE table_name = ? AND column_name = ?",
            (table, column)
        ).fetchone()
        return row is not None
    else:
        return any(
            row['name'] == column
            for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
        )


def _columns_of(conn, table):
    """Retorna lista de nomes de colunas de uma tabela."""
    if USE_POSTGRES:
        rows = conn.execute(
            "SELECT column_name as name FROM information_schema.columns WHERE table_name = ? ORDER BY ordinal_position",
            (table,)
        ).fetchall()
        return [row['name'] for row in rows]
    else:
        return [row['name'] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _copy_common_columns(conn, source, dest, columns):
    """Copia para `dest` apenas as colunas de `source` que existem em `columns`."""
    if not _table_exists(conn, source):
        return
    common = [c for c in columns if c in _columns_of(conn, source)]
    if not common:
        return
    cols_sql = ', '.join(common)
    conn.execute(f"INSERT INTO {dest} ({cols_sql}) SELECT {cols_sql} FROM {source}")


# ============================================================
# CRIAÇÃO E MIGRAÇÃO DE TABELAS
# ============================================================

def init_db():
    """Cria/atualiza todas as tabelas do banco."""
    with get_connection() as conn:
        _create_usuarios(conn)
        _migrate_almoxarifados(conn)
        _migrate_produtos(conn)
        _migrate_produtos_custo_medio(conn)
        _create_estoque(conn)
        _create_colaboradores(conn)
        _migrate_movimentacoes(conn)
        _migrate_movimentacoes_extras(conn)
        _create_unidades(conn)
        _create_manutencoes_unidades(conn)
        _migrate_unidades_depreciacao(conn)
        _migrate_produtos_depreciacao(conn) 
        _create_equipamentos(conn)
        _create_pedidos_compra(conn)

        # Migração do perfil na tabela usuarios
        # (usa verificação em vez de try/except — PostgreSQL aborta transação em erro)
        if not _column_exists(conn, 'usuarios', 'perfil'):
            conn.execute(
                "ALTER TABLE usuarios ADD COLUMN perfil TEXT DEFAULT 'operador' "
                "CHECK(perfil IN ('admin', 'operador', 'visualizador'))"
            )

         # Migração da coluna ativo
        if not _column_exists(conn, 'usuarios', 'ativo'):
            conn.execute(
                "ALTER TABLE usuarios ADD COLUMN ativo BOOLEAN DEFAULT TRUE"
            )
        
        # Migração da coluna email
        if not _column_exists(conn, 'usuarios', 'email'):
            conn.execute(
                "ALTER TABLE usuarios ADD COLUMN email TEXT"
            )

        # Tabela de log de auditoria
        conn.execute('''CREATE TABLE IF NOT EXISTS log_auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            usuario_nome TEXT,
            acao TEXT NOT NULL,
            tabela TEXT NOT NULL,
            descricao TEXT,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )''')
        _create_transferencias(conn)
                # Criar usuário admin padrão se não existir
        cursor = conn.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()['count'] == 0:
            from werkzeug.security import generate_password_hash
            conn.execute(
                "INSERT INTO usuarios (username, password, perfil) VALUES (?, ?, ?)",
                ('admin', generate_password_hash('admin123'), 'admin')
            )
        conn.commit()


def _create_usuarios(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def _migrate_almoxarifados(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS almoxarifados_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            codigo TEXT UNIQUE,
            responsavel TEXT,
            localizacao TEXT,
            descricao TEXT,
            status TEXT DEFAULT 'ativo',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    if _table_exists(conn, 'almoxarifados') and not _column_exists(conn, 'almoxarifados', 'codigo'):
        _copy_common_columns(conn, 'almoxarifados', 'almoxarifados_new',
                             ['id', 'nome', 'created_at'])
        conn.execute("DROP TABLE almoxarifados")
        conn.execute("ALTER TABLE almoxarifados_new RENAME TO almoxarifados")
    elif not _table_exists(conn, 'almoxarifados'):
        conn.execute("ALTER TABLE almoxarifados_new RENAME TO almoxarifados")
    else:
        conn.execute("DROP TABLE IF EXISTS almoxarifados_new")


def _migrate_produtos(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS produtos_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            categoria TEXT,
            tipo TEXT,
            unidade TEXT,
            codigo_interno TEXT,
            codigo_fabricante TEXT,
            codigo_barras TEXT,
            preco REAL,
            valor_unitario REAL,
            rastreabilidade TEXT,
            estoque_minimo INTEGER DEFAULT 0,
            almoxarifado_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (almoxarifado_id) REFERENCES almoxarifados(id)
        )
    """)

    if _table_exists(conn, 'produtos') and not _column_exists(conn, 'produtos', 'descricao'):
        _copy_common_columns(conn, 'produtos', 'produtos_new',
                             ['id', 'nome', 'codigo_interno', 'codigo_fabricante',
                              'codigo_barras', 'preco', 'rastreabilidade',
                              'created_at', 'updated_at'])
        conn.execute("DROP TABLE produtos")
        conn.execute("ALTER TABLE produtos_new RENAME TO produtos")
    elif not _table_exists(conn, 'produtos'):
        conn.execute("ALTER TABLE produtos_new RENAME TO produtos")
    else:
        conn.execute("DROP TABLE IF EXISTS produtos_new")

def _migrate_produtos_custo_medio(conn):
    """Adiciona a coluna custo_medio (REAL) à tabela produtos, se ainda não existir."""
    if not _column_exists(conn, 'produtos', 'custo_medio'):
        conn.execute(
            '''ALTER TABLE produtos ADD COLUMN custo_medio REAL DEFAULT 0'''
        )

def _create_estoque(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            almoxarifado_id INTEGER NOT NULL,
            quantidade INTEGER DEFAULT 0,
            estoque_minimo INTEGER DEFAULT 0,
            UNIQUE(produto_id, almoxarifado_id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id),
            FOREIGN KEY (almoxarifado_id) REFERENCES almoxarifados(id)
        )
    """)


def _create_colaboradores(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT,
            setor TEXT,
            telefone TEXT,
            cargo TEXT,
            status TEXT DEFAULT 'ativo',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def _migrate_movimentacoes(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            almoxarifado_id INTEGER,
            colaborador_id INTEGER,
            tipo TEXT NOT NULL CHECK(tipo IN ('entrada', 'saida')),
            quantidade INTEGER NOT NULL,
            valor_unitario REAL,
            documento TEXT,
            tecnico TEXT,
            ordem_servico TEXT,
            observacao TEXT,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos(id),
            FOREIGN KEY (almoxarifado_id) REFERENCES almoxarifados(id),
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores(id)
        )
    """)

    common_columns = [
        'id', 'produto_id', 'tipo', 'quantidade', 'documento',
        'tecnico', 'ordem_servico', 'observacao', 'data'
    ]

    recriar = False

    if _table_exists(conn, 'movimentacoes'):
        if not _column_exists(conn, 'movimentacoes', 'valor_unitario'):
            _copy_common_columns(conn, 'movimentacoes', 'movimentacoes_new', common_columns)
            conn.execute("DROP TABLE movimentacoes")
            recriar = True
    else:
        recriar = True

    if _table_exists(conn, 'movimentacoes_old'):
        destino = 'movimentacoes_new' if recriar or not _table_exists(conn, 'movimentacoes') else 'movimentacoes'
        _copy_common_columns(conn, 'movimentacoes_old', destino, common_columns)
        conn.execute("DROP TABLE movimentacoes_old")
        if destino == 'movimentacoes_new':
            recriar = True

    if recriar:
        conn.execute("ALTER TABLE movimentacoes_new RENAME TO movimentacoes")
    else:
        conn.execute("DROP TABLE IF EXISTS movimentacoes_new")

def _migrate_movimentacoes_extras(conn):
    """Adiciona colunas lote_corrida e equipamento_id na tabela movimentacoes."""
    if not _column_exists(conn, 'movimentacoes', 'lote_corrida'):
        conn.execute("ALTER TABLE movimentacoes ADD COLUMN lote_corrida TEXT")
    if not _column_exists(conn, 'movimentacoes', 'equipamento_id'):
        conn.execute("ALTER TABLE movimentacoes ADD COLUMN equipamento_id INTEGER")
    conn.commit()


def _create_unidades(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS unidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            almoxarifado_id INTEGER,
            tag TEXT,
            numero_serie TEXT,
            status TEXT DEFAULT 'disponivel',
            localizacao TEXT,
            data_aquisicao TEXT,
            requer_calibracao BOOLEAN DEFAULT FALSE,
            data_validade_calibracao TEXT,
            numero_certificado TEXT,
            data_ultima_manutencao TEXT,
            status_manutencao TEXT DEFAULT 'disponivel',
            observacao TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos(id),
            FOREIGN KEY (almoxarifado_id) REFERENCES almoxarifados(id)
        )
    """)

def _create_manutencoes_unidades(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS manutencoes_unidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            fornecedor TEXT,
            custo REAL,
            data_envio TEXT,
            data_retorno TEXT,
            status TEXT DEFAULT 'em_manutencao' CHECK(status IN ('em_manutencao', 'concluida')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (unidade_id) REFERENCES unidades(id)
        )
    """)

def _create_equipamentos(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS equipamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT,
            status TEXT DEFAULT 'ativo',
            numero_serie TEXT,
            localizacao TEXT,
            data_aquisicao TEXT,
            data_ultima_manutencao TEXT,
            data_validade_calibracao TEXT,
            observacao TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def _create_pedidos_compra(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pedidos_compra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            quantidade_solicitada INTEGER NOT NULL,
            status TEXT DEFAULT 'aberto' CHECK(status IN ('aberto', 'em_compra', 'comprado')),
            fornecedor TEXT,
            preco_unitario REAL,
            observacao TEXT,
            data_prevista_chegada TEXT,
            solicitante TEXT,
            data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')
    conn.commit()

def _create_transferencias(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transferencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            almoxarifado_origem_id INTEGER NOT NULL,
            almoxarifado_destino_id INTEGER NOT NULL,
            quantidade_total INTEGER NOT NULL,
            quantidade_recebida INTEGER DEFAULT 0,
            status TEXT DEFAULT 'enviada' CHECK(status IN ('enviada', 'parcial', 'recebida', 'rejeitada')),
            valor_unitario REAL,
            documento TEXT,
            tecnico TEXT,
            ordem_servico TEXT,
            observacao TEXT,
            enviado_por TEXT,
            recebido_por TEXT,
            data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_recebimento TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos(id),
            FOREIGN KEY (almoxarifado_origem_id) REFERENCES almoxarifados(id),
            FOREIGN KEY (almoxarifado_destino_id) REFERENCES almoxarifados(id)
        )
    """)

def _migrate_unidades_depreciacao(conn):
    """
    Migração da tabela 'unidades' para adicionar colunas relacionadas à depreciação.
    
    Adiciona as colunas:
    - valor_aquisicao: valor de aquisição da unidade
    - vida_util_meses: vida útil em meses para cálculo da depreciação
    - valor_residual: valor residual após depreciação total
    - status_depreciacao: status da depreciação (ativo, depreciado, baixado)
    """
    colunas = [
        {
            "nome": "valor_aquisicao",
            "definicao": "REAL DEFAULT 0"
        },
        {
            "nome": "vida_util_meses",
            "definicao": "INTEGER"
        },
        {
            "nome": "valor_residual",
            "definicao": "REAL DEFAULT 0"
        },
        {
            "nome": "status_depreciacao",
            "definicao": "TEXT DEFAULT 'ativo' CHECK(status_depreciacao IN ('ativo', 'depreciado', 'baixado'))"
        }
    ]
    
    for coluna in colunas:
        if not _column_exists(conn, "unidades", coluna["nome"]):
            sql = f'ALTER TABLE unidades ADD COLUMN {coluna["nome"]} {coluna["definicao"]}'
            conn.execute(sql)
    
    conn.commit()


def _migrate_produtos_depreciacao(conn):
    """
    Migração da tabela 'produtos' para adicionar flag de controle de depreciação.
    
    Adiciona a coluna:
    - controla_depreciacao: indica se o produto controla depreciação (0 = não, 1 = sim)
    """
    if not _column_exists(conn, "produtos", "controla_depreciacao"):
        conn.execute("ALTER TABLE produtos ADD COLUMN controla_depreciacao BOOLEAN DEFAULT TRUE")
    
    conn.commit()

    # Migração para campos de equipamento
    if not _column_exists(conn, "produtos", "requer_equipamento"):
        conn.execute("ALTER TABLE produtos ADD COLUMN requer_equipamento BOOLEAN DEFAULT FALSE")
    if not _column_exists(conn, "produtos", "equipamentos_compativeis"):
        conn.execute("ALTER TABLE produtos ADD COLUMN equipamentos_compativeis TEXT")

def calcular_vlc_unidade(valor_aquisicao, valor_residual, vida_util_meses, data_aquisicao):
    """
    Calcula o Valor Líquido Contábil (VLC) de uma unidade usando depreciação linear.
    
    Fórmula: VLC = max(valor_residual, valor_aquisicao - ((valor_aquisicao - valor_residual) / vida_util_meses) * meses_decorridos)
    
    Args:
        valor_aquisicao: valor de aquisição da unidade
        valor_residual: valor residual após depreciação total
        vida_util_meses: vida útil em meses
        data_aquisicao: data de aquisição (datetime.date ou string no formato YYYY-MM-DD)
    
    Returns:
        float: Valor Líquido Contábil (VLC) da unidade
    """
    # Se a vida útil for 0 ou None, não há depreciação - retorna o valor de aquisição
    if not vida_util_meses or vida_util_meses == 0:
        return valor_aquisicao
    
    # Se não houver data de aquisição, não é possível calcular meses decorridos
    if data_aquisicao is None:
        return valor_aquisicao
    
    # Converte data_aquisicao para date se for string
    if isinstance(data_aquisicao, str):
        try:
            data_aquisicao = datetime.strptime(data_aquisicao, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return valor_aquisicao
    
    # Calcula os meses decorridos desde a aquisição até a data atual
    data_atual = datetime.now().date()
    meses_decorridos = (data_atual.year - data_aquisicao.year) * 12 + (data_atual.month - data_aquisicao.month)
    
    # Se a data de aquisição for no futuro, não há meses decorridos
    if meses_decorridos < 0:
        meses_decorridos = 0
    
    # Limita os meses decorridos à vida útil (não deprecia além do valor residual)
    meses_decorridos = min(meses_decorridos, vida_util_meses)
    
    # Calcula a depreciação mensal
    depreciacao_mensal = (valor_aquisicao - valor_residual) / vida_util_meses
    
    # Calcula o VLC garantindo que não seja inferior ao valor residual
    vlc = valor_aquisicao - (depreciacao_mensal * meses_decorridos)
    vlc = max(valor_residual, vlc)
    
    return vlc


def calcular_vlc_total(conn, produto_id=None):
    """
    Calcula o VLC total de todas as unidades ativas, opcionalmente filtradas por produto.
    
    Args:
        conn: conexão com o banco de dados SQLite
        produto_id: ID do produto para filtrar (opcional). Se None, considera todas as unidades.
    
    Returns:
        dict: Dicionário com os totais:
            - valor_aquisicao_total: soma do valor de aquisição de todas as unidades ativas
            - vlc_total: soma do VLC de todas as unidades ativas
            - valor_residual_total: soma do valor residual de todas as unidades ativas
            - depreciacao_acumulada_total: soma da depreciação acumulada (valor_aquisicao - vlc)
    """
    resultado = {
        "valor_aquisicao_total": 0.0,
        "vlc_total": 0.0,
        "valor_residual_total": 0.0,
        "depreciacao_acumulada_total": 0.0
    }
    
    # Monta a consulta SQL para buscar unidades ativas
    if produto_id is not None:
        cursor = conn.execute(
            """
            SELECT valor_aquisicao, valor_residual, vida_util_meses, data_aquisicao
            FROM unidades
            WHERE status_depreciacao = 'ativo' AND produto_id = ?
            """,
            (produto_id,)
        )
    else:
        cursor = conn.execute(
            """
            SELECT valor_aquisicao, valor_residual, vida_util_meses, data_aquisicao
            FROM unidades
            WHERE status_depreciacao = 'ativo'
            """
        )
    
    # Itera sobre as unidades e calcula os totais
    for row in cursor.fetchall():
        valor_aquisicao = row[0] or 0.0
        valor_residual = row[1] or 0.0
        vida_util_meses = row[2]
        data_aquisicao = row[3]
        
        # Calcula o VLC da unidade
        vlc = calcular_vlc_unidade(valor_aquisicao, valor_residual, vida_util_meses, data_aquisicao)
        
        # Acumula os totais
        resultado["valor_aquisicao_total"] += valor_aquisicao
        resultado["vlc_total"] += vlc
        resultado["valor_residual_total"] += valor_residual
        resultado["depreciacao_acumulada_total"] += (valor_aquisicao - vlc)
    
    return resultado

if __name__ == '__main__':
    init_db()