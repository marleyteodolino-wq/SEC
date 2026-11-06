
# Importa a biblioteca SQLite
import sqlite3

# Função responsável por conectar ao banco de dados
def conectar_banco():
    banco = sqlite3.connect("banco.db")
    banco.row_factory = sqlite3.Row
    return banco


# Cria a tabela de produtos, caso não exista
def criar_tabela():
    banco = conectar_banco()

    banco.execute("""
        CREATE TABLE IF NOT EXISTS produto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco REAL NOT NULL
        )
    """)

    banco.commit()
    banco.close()


# Cria a tabela de usuários, caso não exista
def criar_tabela_usuario():
    banco = conectar_banco()

    banco.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    """)

    banco.commit()
    banco.close()

#tabela de vendas do sic
def criar_tabela_venda():
    banco = conectar_banco()

    banco.execute("""
    CREATE TABLE IF NOT EXISTS venda (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER NOT NULL,
    produto_nome TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_unitario REAL NOT NULL,
    total REAL NOT NULL,
    metodo_pagamento TEXT NOT NULL,
    status_pagamento TEXT NOT NULL DEFAULT 'pendente',
    data_venda TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """)

    banco.commit()
    banco.close()

#busca de produtos pelo banco
def buscar_produto(id_produto):
    banco = conectar_banco()

    produto = banco.execute(
        "SELECT * FROM produto WHERE id= ?",
        (id_produto,)
        ).fetchone()

    banco.close()

    return produto

#Registrar a baixa de produtos no estoque
def dar_baixa(produto_id, quantidade):
    banco = conectar_banco()

    try:
        cursor = banco.execute(
            """
            UPDATE produto
            SET quantidade = quantidade - ?
            WHERE id= ? AND quantidade >= ?
            """,
            (quantidade, produto_id, quantidade)
        )

        banco.commit()

        #verificar se algum produto foi atualizado
        return cursor.rowcount > 0

    except sqlite3.Error:
        banco.rollback()
        raise

    finally:
        banco.close()

def consultar_vendas():
    banco = conectar_banco()

    vendas = banco.execute(
        "SELECT id, produto_nome, quantidade, metodo_pagamento "
        "FROM venda ORDER BY id DESC"
    ).fetchall()

    banco.close()
    return vendas
        



# Garante que as tabelas existam
criar_tabela()
criar_tabela_usuario()
criar_tabela_venda()
