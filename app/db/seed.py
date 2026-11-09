"""
Popula o banco com os dados de demonstração da Bulbe Energia
(clientes Ana e Bruno, pedidos, faturas, catálogo de benefícios, indicações,
notificações, textos de ajuda e boas-vindas).

Uso:  python -m app.db.seed
Rode depois de "alembic upgrade head". Pode rodar de novo: se já houver
clientes cadastrados, não faz nada.

Os dados passam pelos repositórios, como em qualquer cadastro. As senhas de
demonstração (bulbe-dev-123) já chegam com hash.
"""

from app.core.estado import Repositorios, repositorios
from app.db.unidade_de_trabalho import unidade_de_trabalho
from app.repositories import dados_iniciais


def banco_vazio(repos: Repositorios = repositorios) -> bool:
    return not repos.clientes.listar()


def popular(repos: Repositorios = repositorios) -> None:
    """Grava todos os dados de demonstração numa única transação."""
    with unidade_de_trabalho():
        for cliente in dados_iniciais.clientes():
            repos.clientes.salvar(cliente)
        for pedido in dados_iniciais.pedidos():
            repos.pedidos.salvar(pedido)
        for fatura in dados_iniciais.faturas():
            repos.pedidos.salvar_fatura(fatura)
        for parceiro in dados_iniciais.parceiros():
            repos.beneficios.salvar_parceiro(parceiro)
        for trilha in dados_iniciais.trilhas():
            repos.beneficios.salvar_trilha(trilha)
        for beneficio in dados_iniciais.beneficios():
            repos.beneficios.salvar_beneficio(beneficio)
        for dica in dados_iniciais.dicas():
            repos.ajuda.salvar(dica)
        for indicacao in dados_iniciais.indicacoes():
            repos.indicacoes.salvar(indicacao)
        for cliente_id, codigo in dados_iniciais.codigos_de_indicacao().items():
            repos.indicacoes.salvar_codigo(cliente_id, codigo)
        for notificacao in dados_iniciais.notificacoes():
            repos.notificacoes.salvar(notificacao)
        repos.conteudos.salvar_boas_vindas(dados_iniciais.boas_vindas())


def main() -> None:
    if not banco_vazio():
        print("Já existem clientes cadastrados. Nada a fazer.")
        return
    popular()
    for cliente in repositorios.clientes.listar():
        print(f"Cliente {cliente.id}: {cliente.nome} <{cliente.email}> (senha: {dados_iniciais.SENHA_DEV})")
    print("Dados de demonstração gravados: pedidos, faturas, benefícios, indicações, notificações e conteúdos.")


if __name__ == "__main__":
    main()
