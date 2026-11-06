document.addEventListener("DOMContentLoaded", function () {
    const formularioCodigo = document.getElementById("form-busca-codigo");
    const campoCodigo = document.getElementById("codigo-produto");
    const listaSelecionados = document.getElementById("lista-selecionados");
    const contadorSelecionados = document.getElementById("contador-selecionados");
    const totalUnidades = document.getElementById("total-unidades");
    const valorTotal = document.getElementById("valor-total");
    const botaoConfirmar = document.getElementById("btn-confirmar-baixa");


    // Se não estiver na página de produtos, não executa nada.
    if (!formularioCodigo || !listaSelecionados) return;

    const selecionados = new Map();

    function moeda(valor) {
        return valor.toLocaleString("pt-BR", {
            style: "currency",
            currency: "BRL"
        });
    }

    function renderizar() {
        listaSelecionados.innerHTML = "";

        if (selecionados.size === 0) {
            listaSelecionados.innerHTML = `
                <div class="carrinho-vazio">
                    <span class="icone-vazio">🛒</span>
                    <strong>Nenhum produto selecionado</strong>
                    <p>Pesquise e selecione os produtos desejados.</p>
                </div>
            `;

            contadorSelecionados.textContent = "0 itens";
            totalUnidades.textContent = "0";
            valorTotal.textContent = moeda(0);
            botaoConfirmar.disabled = true;
            return;
        }

        let unidades = 0;
        let total = 0;

        selecionados.forEach((produto) => {
            unidades += produto.quantidade;
            total += produto.quantidade * produto.preco;

            const item = document.createElement("div");
            item.className = "item-selecionado";

            const informacoes = document.createElement("div");
            informacoes.innerHTML = `
                <strong>${produto.nome}</strong>
                <p>Código: ${produto.id} · ${moeda(produto.preco)} por unidade</p>
            `;

            const controles = document.createElement("div");
            controles.className = "controles-quantidade";

            const diminuir = document.createElement("button");
            diminuir.type = "button";
            diminuir.textContent = "−";
            diminuir.setAttribute("aria-label", "Diminuir quantidade");

            diminuir.addEventListener("click", () => {
                produto.quantidade--;

                if (produto.quantidade <= 0) {
                    selecionados.delete(produto.id);
                }

                renderizar();
            });

            const quantidade = document.createElement("span");
            quantidade.textContent = produto.quantidade;

            const aumentar = document.createElement("button");
            aumentar.type = "button";
            aumentar.textContent = "+";
            aumentar.setAttribute("aria-label", "Aumentar quantidade");

            aumentar.addEventListener("click", () => {
                if (produto.quantidade < produto.estoque) {
                    produto.quantidade++;
                    renderizar();
                } else {
                    alert("Quantidade maior que o estoque disponível.");
                }
            });

            const remover = document.createElement("button");
            remover.type = "button";
            remover.textContent = "Remover";
            remover.className = "botao-excluir";

            remover.addEventListener("click", () => {
                selecionados.delete(produto.id);
                renderizar();
            });

            controles.append(diminuir, quantidade, aumentar, remover);
            item.append(informacoes, controles);
            listaSelecionados.appendChild(item);
        });

        contadorSelecionados.textContent =
            `${selecionados.size} ${selecionados.size === 1 ? "item" : "itens"}`;

        totalUnidades.textContent = unidades;
        valorTotal.textContent = moeda(total);
        botaoConfirmar.disabled = false;
    }

    function selecionarBotao(botao) {
        const id = Number(botao.dataset.id);
        const nome = botao.dataset.nome;
        const estoque = Number(botao.dataset.quantidade);
        const preco = Number(botao.dataset.preco);

        if (estoque <= 0) {
            alert("Este produto está sem estoque.");
            return;
        }

        if (selecionados.has(id)) {
            const produto = selecionados.get(id);

            if (produto.quantidade >= estoque) {
                alert("Você já selecionou todo o estoque disponível.");
                return;
            }

            produto.quantidade++;
        } else {
            selecionados.set(id, {
                id,
                nome,
                estoque,
                preco,
                quantidade: 1
            });
        }

        renderizar();
    }

    document.querySelectorAll(".botao-selecionar").forEach((botao) => {
        botao.addEventListener("click", () => selecionarBotao(botao));
    });

    formularioCodigo.addEventListener("submit", function (evento) {
        evento.preventDefault();

        const codigo = Number(campoCodigo.value);

        const botao = Array.from(
            document.querySelectorAll(".botao-selecionar")
        ).find((item) => Number(item.dataset.id) === codigo);

        if (!botao) {
            alert("Produto não encontrado na lista atual. Confira o filtro por nome.");
            return;
        }

        selecionarBotao(botao);
        campoCodigo.value = "";
        campoCodigo.focus();
    });

   botaoConfirmar.addEventListener("click", async function () {
    if (selecionados.size === 0) {
        alert("Selecione pelo menos um produto.");
        return;
    }

    const pagamento = document.querySelector(
        'input[name="metodo-pagamento"]:checked'
    );

    if (!pagamento) {
        alert("Selecione uma forma de pagamento.");
        return;
    }

    const confirmar = confirm(
        "Deseja confirmar a baixa dos produtos selecionados?"
    );

    if (!confirmar) return;

    const itens = Array.from(selecionados.values()).map(produto => ({
        id: produto.id,
        quantidade: produto.quantidade
    }));

    const formulario = document.createElement("form");
    formulario.method = "POST";
    formulario.action = "/dar_baixa";

    const campoPagamento = document.createElement("input");
    campoPagamento.type = "hidden";
    campoPagamento.name = "pagamento";
    campoPagamento.value = pagamento.value;

    formulario.appendChild(campoPagamento);

    const campoItens = document.createElement("input");
    campoItens.type = "hidden";
    campoItens.name = "itens";
    campoItens.value = JSON.stringify(itens);

    formulario.appendChild(campoItens);
    document.body.appendChild(formulario);

    botaoConfirmar.disabled = true;
    formulario.submit();
});

    renderizar();
});


