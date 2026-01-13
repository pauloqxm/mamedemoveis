from .db_connector import get_db_connection
from .auth import hash_password

SCHEMA = "bd_marcenaria"


def init_database():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 1) garante schema e aponta search_path
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
                cur.execute(f"SET search_path TO {SCHEMA}, public")

                # 2) tabelas (todas dentro do schema)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id SERIAL PRIMARY KEY,
                        nome VARCHAR(200) NOT NULL,
                        email VARCHAR(200) UNIQUE NOT NULL,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        senha_hash VARCHAR(255) NOT NULL,
                        perfil VARCHAR(50) DEFAULT 'leitura',
                        setor VARCHAR(100) DEFAULT '',
                        ativo BOOLEAN DEFAULT TRUE,
                        data_cadastro TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        ultimo_login TIMESTAMPTZ
                    )
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS clientes (
                        id SERIAL PRIMARY KEY,
                        nome VARCHAR(200) NOT NULL,
                        fantasia VARCHAR(200) DEFAULT '',
                        cpf_cnpj VARCHAR(30) DEFAULT '',
                        telefone VARCHAR(50) DEFAULT '',
                        whatsapp VARCHAR(50) DEFAULT '',
                        email VARCHAR(200) DEFAULT '',
                        endereco TEXT DEFAULT '',
                        observacoes TEXT DEFAULT '',
                        ativo BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS funcionarios (
                        id SERIAL PRIMARY KEY,
                        nome VARCHAR(200) NOT NULL,
                        funcao VARCHAR(120) DEFAULT '',
                        telefone VARCHAR(50) DEFAULT '',
                        data_admissao DATE,
                        ativo BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS orcamentos (
                        id SERIAL PRIMARY KEY,
                        codigo VARCHAR(20) UNIQUE,
                        cliente_id INTEGER REFERENCES clientes(id),
                        status VARCHAR(30) DEFAULT 'Aberto',
                        total_estimado DECIMAL(12,2) DEFAULT 0,
                        validade DATE,
                        observacoes TEXT DEFAULT '',
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS orcamento_itens (
                        id SERIAL PRIMARY KEY,
                        orcamento_id INTEGER REFERENCES orcamentos(id) ON DELETE CASCADE,
                        descricao TEXT NOT NULL,
                        qtd DECIMAL(12,2) DEFAULT 1,
                        unidade VARCHAR(20) DEFAULT 'Unid.',
                        valor_unit DECIMAL(12,2) DEFAULT 0,
                        subtotal DECIMAL(12,2) DEFAULT 0
                    )
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS pedidos (
                        id SERIAL PRIMARY KEY,
                        codigo VARCHAR(20) UNIQUE,
                        cliente_id INTEGER REFERENCES clientes(id),
                        orcamento_id INTEGER REFERENCES orcamentos(id),
                        status VARCHAR(30) DEFAULT 'Aberto',
                        etapa_atual VARCHAR(60) DEFAULT 'Medição técnica',
                        status_etapa VARCHAR(20) DEFAULT 'A fazer',
                        responsavel_id INTEGER REFERENCES funcionarios(id),
                        data_entrega_prevista DATE,
                        total DECIMAL(12,2) DEFAULT 0,
                        observacoes TEXT DEFAULT '',
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS pedido_itens (
                        id SERIAL PRIMARY KEY,
                        pedido_id INTEGER REFERENCES pedidos(id) ON DELETE CASCADE,
                        descricao TEXT NOT NULL,
                        qtd DECIMAL(12,2) DEFAULT 1,
                        unidade VARCHAR(20) DEFAULT 'Unid.',
                        valor_unit DECIMAL(12,2) DEFAULT 0,
                        subtotal DECIMAL(12,2) DEFAULT 0
                    )
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS producao_etapas (
                        id SERIAL PRIMARY KEY,
                        pedido_id INTEGER REFERENCES pedidos(id) ON DELETE CASCADE,
                        etapa VARCHAR(60) NOT NULL,
                        status VARCHAR(20) DEFAULT 'A fazer',
                        responsavel_id INTEGER REFERENCES funcionarios(id),
                        inicio_em TIMESTAMPTZ,
                        fim_em TIMESTAMPTZ,
                        observacoes TEXT DEFAULT '',
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 3) fila de automação (Make/WhatsApp) - necessária pro mover_pedido_etapa
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS producao_eventos (
                        id SERIAL PRIMARY KEY,
                        pedido_id INTEGER REFERENCES pedidos(id) ON DELETE CASCADE,
                        cliente_id INTEGER REFERENCES clientes(id),
                        cliente_nome VARCHAR(200) DEFAULT '',
                        cliente_whatsapp VARCHAR(50) DEFAULT '',
                        etapa VARCHAR(60) NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        responsavel_id INTEGER REFERENCES funcionarios(id),
                        observacoes TEXT DEFAULT '',
                        processado BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 4) índices
                cur.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_etapa ON pedidos(etapa_atual)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_status ON pedidos(status)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_orcamentos_cliente ON orcamentos(cliente_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_cliente ON pedidos(cliente_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_eventos_processado ON producao_eventos(processado)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_eventos_pedido ON producao_eventos(pedido_id)")

                # 5) admin padrão
                cur.execute("SELECT COUNT(*) FROM usuarios WHERE username='admin'")
                if cur.fetchone()[0] == 0:
                    cur.execute("""
                        INSERT INTO usuarios (nome,email,username,senha_hash,perfil,setor,ativo)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        "Administrador",
                        "admin@marcenaria.com",
                        "admin",
                        hash_password("admin123"),
                        "admin",
                        "Admin",
                        True
                    ))

                conn.commit()

        return True, "✅ Banco inicializado no schema bd_marcenaria."
    except Exception as e:
        return False, f"❌ Erro init: {str(e)}"
