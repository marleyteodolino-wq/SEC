from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from banco import conectar_banco, dar_baixa
import json

app = Flask(__name__)


app.secret_key = "chave secreta"

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "usuario" not in session:
            return redirect("/")

        return func(*args, **kwargs)

    return wrapper


#Rota principal: exibe a página de login
@app.route("/")
def login():
    return render_template("index.html")

#Rota de logout: encerra a sessão do usuário e volta pro login
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

#página que exibe a página de cadastro de produtos
@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")

#rota que exibe o formulário de cadastro de usuários
@app.route("/produtos")
@login_required
def produtos():
    termo = request.args.get("busca", "").strip()

    banco = conectar_banco()

    if termo:
        produtos = banco.execute(
            """
            SELECT * FROM produto
            WHERE nome LIKE ? OR CAST(id AS TEXT) LIKE ?
            """,
            (f"%{termo}%", f"%{termo}%")
        ).fetchall()
    else:
        produtos = banco.execute(
            "SELECT * FROM produto"
            ).fetchall()

    banco.close()

    return render_template("produtos.html", produtos=produtos, busca=termo
                               )

@app.route("/vendas")
@login_required
def vendas():
    termo = request.args.get("busca", "").strip()

    banco = conectar_banco()

    if termo:
        produtos = banco.execute(
            """
            SELECT * FROM produto
            WHERE nome LIKE? OR CAST(id AS TEXT) LIKE?
            """,
            (f"%{termo}%", f"%{termo}%")
            ).fetchall()
    else:
        produtos = banco.execute(
            "SELECT * FROM produto"
            ).fetchall()

    banco.close()

    return render_template(
            "vendas.html",
            produtos=produtos,
            busca=termo
            )



#rota que recebe os dadaos do formulário e registra um novo usuário no banco
@app.route("/cadastrar", methods=["POST"])
@login_required
def cadastrar():
    nome = request.form["nome"]
    quantidade = request.form["quantidade"]
    preco = request.form["preco"]

    banco = conectar_banco()

    banco.execute(
        "INSERT INTO produto (nome, quantidade, preco) VALUES (?, ?, ?)",
        (nome, quantidade, preco)
        )

    banco.commit()
    banco.close()

    flash("Produto cadastrado com sucesso!", "success")
    return redirect("/produtos")

#rota que busca um produto pelo ID e exibe seus dados para edição
@app.route("/editar/<int:id>")
@login_required
def editar(id):
    banco = conectar_banco()

    produto = banco.execute(
        "SELECT * FROM produto WHERE id = ?", 
        (id,)
        ).fetchone()

    banco.close()

    return render_template("editar.html", produto=produto)

#rota que exclui um produto do banco pelo ID, usando POST
@app.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir(id):
    banco = conectar_banco()


    banco.execute(
        "DELETE FROM produto WHERE id= ?",
        (id,)
    )

    banco.commit()
    banco.close()

    return redirect("/produtos")

#rota que recebe os novos dados e atualiza um produto pelo ID
@app.route("/atualizar/<int:id>", methods=["POST"])
@login_required
def atualizar(id):

    nome = request.form["nome"]
    quantidade = request.form["quantidade"]
    preco = request.form["preco"]

    banco = conectar_banco()

    banco.execute(
        "UPDATE produto SET nome = ?, quantidade = ?, preco = ? WHERE id = ?",
        (nome, quantidade, preco, id)
        )

    banco.commit()
    banco.close()
    return redirect("/produtos")
    

#rota que recebe email e senha, verifica as credenciais e inicia a sessão
@app.route("/cadastro_usuario")
def cadastro_usuario():
    return render_template("cadastro_usuario.html")


@app.route("/cadastrar_usuario", methods=["POST"])
def cadastrar_usuario():
    nome = request.form["nome"]
    email = request.form["email"]
    senha = request.form["senha"]

    senha_hash = generate_password_hash(senha)

    banco = conectar_banco()
    banco.execute(
        "INSERT INTO usuario (nome, email, senha) VALUES (?, ?, ?)", 
        (nome, email, senha_hash)
    )

    banco.commit()
    banco.close()

    return redirect("/")

@app.route("/login", methods=["POST"])
def fazer_login():
    email = request.form["email"]
    senha = request.form["senha"]

    banco = conectar_banco()

    usuario = banco.execute(
        "SELECT * FROM usuario WHERE email = ?", 
        (email,)
        ).fetchone()

    banco.close()

    if usuario and check_password_hash(usuario[3], senha):
        session["usuario"]= usuario[0]
        return redirect("/inicio")
    else:
        return "Email o senha incorretos!"

#rota do menu inicial
@app.route("/inicio")
def inicio():
    if "usuario" not in session:
        return redirect("/")

    return render_template("inicio.html")



@app.route("/dar_baixa", methods=["POST"])
@login_required
def confirmar_baixa():
    try:
        itens = json.loads(request.form.get("itens", "[]"))
        pagamento = request.form.get("pagamento", "")

        if pagamento not in ("dinheiro", "debito", "pix", "credito"):
            flash("Selecione uma forma de pagamento válida", "error")
            return redirect("/vendas")

        if not isinstance(itens, list) or not itens:
            flash("Nenhum produto foi selecionado.", "error")
            return redirect("/vendas")

        banco = conectar_banco()

        try:
            # Impede que uma venda seja registrada pela metade.
            banco.execute("BEGIN")

            for item in itens:
                produto_id = item.get("id")
                quantidade = item.get("quantidade")

                if (
                    not isinstance(produto_id, int)
                    or isinstance(produto_id, bool)
                    or not isinstance(quantidade, int)
                    or isinstance(quantidade, bool)
                    or produto_id <= 0
                    or quantidade <= 0
                ):
                    raise ValueError("Produto ou quantidade inválidos.")

                produto = banco.execute(
                    "SELECT id, nome, quantidade, preco "
                    "FROM produto WHERE id = ?",
                    (produto_id,)
                ).fetchone()

                if produto is None:
                    raise ValueError("Um dos produtos não foi encontrado.")

                cursor = banco.execute(
                    """
                    UPDATE produto
                    SET quantidade = quantidade - ?
                    WHERE id = ? AND quantidade >= ?
                    """,
                    (quantidade, produto_id, quantidade)
                )

                if cursor.rowcount != 1:
                    raise ValueError(
                        f"Estoque insuficiente para {produto['nome']}."
                    )

                preco = float(produto["preco"])
                total = preco * quantidade

                banco.execute(
                    """
                    INSERT INTO venda (
                        produto_id,
                        produto_nome,
                        quantidade,
                        preco_unitario,
                        total,
                        metodo_pagamento,
                        status_pagamento
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        produto_id,
                        produto["nome"],
                        quantidade,
                        preco,
                        total,
                        pagamento,
                        "pendente"
                    )
                )

            banco.commit()
            flash("Baixa realizada e vendas registradas!", "success")

        except Exception:
            banco.rollback()
            raise

        finally:
            banco.close()

    except (ValueError, TypeError, json.JSONDecodeError) as erro:
        flash(str(erro) or "Dados inválidos para a baixa.", "error")

    except Exception:
        flash("Não foi possível concluir a baixa. Nenhuma alteração foi salva.", "error")

    return redirect("/vendas")


@app.route("/usuario")
@login_required
def minha_conta():
    banco = conectar_banco()

    usuario = banco.execute(
        "SELECT id, nome, email FROM usuario WHERE id= ?",
        (session["usuario"],)
        ).fetchone()

    banco.close()

    if usuario is None:
        session.clear()
        return redirect("/")

    return render_template("usuario.html", usuario=usuario)


if __name__ == "__main__":
    app.run(debug=True)