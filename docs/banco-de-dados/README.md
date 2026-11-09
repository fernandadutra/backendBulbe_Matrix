# Banco de dados

A API grava todas as entidades do domínio Bulbe num banco relacional, usando
**SQLAlchemy** (ORM) e **Alembic** (migrations). Por padrão é um SQLite em
arquivo (`bulbe.db`, fora do Git); trocar para PostgreSQL é só mudar o endereço.

## Como rodar

Na raiz do projeto (a pasta que contém `app/` e `alembic.ini`):

```bash
pip install -r requirements.txt
```

```bash
alembic upgrade head
```

```bash
python -m app.db.seed
```

```bash
uvicorn app.main:app --reload
```

`alembic upgrade head` cria as tabelas, e o seed grava os dados de demonstração
para a review. Rodar o seed de novo não duplica nada. Para entrar, use
`ana@exemplo.com.br` ou `bruno@exemplo.com.br`, ambos com a senha `bulbe-dev-123`.

Para usar outro banco, defina `BULBE_DATABASE_URL` antes dos comandos acima, por exemplo
`postgresql+psycopg://bulbe:bulbe@localhost:5432/bulbe` (é preciso instalar o driver: `pip install "psycopg[binary]"`).

## Testes

```bash
pytest
```

Os testes usam um banco separado, `bulbe_test.db`, que é recriado a cada teste
e apagado ao final. Eles nunca tocam no `bulbe.db`.

- `tests/test_repositorios_sql.py`: testes de integração dos repositórios SQL.
- `tests/test_migrations.py`: aplica as migrations num banco vazio e confere que
  o resultado é igual aos modelos. Se alguém mudar `app/db/models.py` e esquecer
  de gerar a migration, esse teste falha.
- Os demais testes de API passam a exercitar o banco de verdade.

## Onde fica cada coisa

| Arquivo | Papel |
|---|---|
| `app/core/config.py` | `DATABASE_URL` (variável `BULBE_DATABASE_URL`) |
| `app/db/database.py` | `engine`, `SessionLocal` e `Base` |
| `app/db/models.py` | Tabelas (modelos SQLAlchemy). Só os repositórios os conhecem |
| `app/db/tipos.py` | `DataHora`: data e hora com fuso, igual em qualquer banco |
| `app/db/unidade_de_trabalho.py` | Uma sessão por requisição, com commit único no fim |
| `app/db/repositorio_sql.py` | Base comum dos repositórios SQL |
| `app/db/seed.py` | Dados de demonstração (`python -m app.db.seed`) |
| `app/repositories/*_repository.py` | Contrato (`Protocol`), versão `InMemory...` e versão `Sql...` |
| `alembic.ini`, `migrations/` | Migrations. O schema é criado **somente** por aqui |
| `schema.puml` | Diagrama das tabelas (PlantUML) |

## Services e Controllers não mudaram

Nenhuma linha de `app/services`, `app/controllers`, `app/models` ou `app/schemas`
foi alterada na troca. Cada repositório virou um contrato (`AdesaoRepository`,
`PedidoRepository`...) com duas implementações, e `app/core/estado.py` passou a
montar as versões SQL.

O que mudou fora da camada de persistência:
- `app/main.py` ganhou uma linha, o middleware da unidade de trabalho;
- em 5 arquivos de teste, poucas linhas que liam atributos internos da versão em
  memória (como `_interessados`) passaram a usar métodos do repositório.

### Um ponto para a retrospectiva: services que alteram objetos sem salvar

Vários services alteram direto o objeto que receberam do repositório e não chamam
`salvar` depois:

```python
sessao.revogada = True              # autenticacao_service
notificacao.lida = lida             # notificacao_service
adesao.anexos.append(anexo)         # adesao_service
indicacao.situacao = "convertida"   # indicacao_service
```

Na versão em memória isso funcionava porque o objeto *era* o dado guardado. Com
banco, o objeto é uma cópia da linha, e essas mudanças se perderiam. Isso é um
acoplamento escondido entre os services e a implementação em memória.

Para não alterar os services, usamos o padrão **Unidade de Trabalho** (Unit of Work):

1. o middleware abre uma unidade por requisição HTTP;
2. o repositório SQL registra cada objeto que entrega ao service (`rastrear`);
3. antes de enviar a resposta, a unidade copia de volta para o banco o estado de
   todos esses objetos e faz **um único commit**;
4. se a requisição quebrar com erro inesperado (500), nada é gravado (rollback).

Respostas de erro de negócio (401, 404, 409...) também gravam. Exemplo: reusar um
token de renovação revoga a sessão **e** responde 401, e a revogação precisa ir
para o banco.

Fora de uma requisição (seed, testes, terminal Python), cada chamada de
repositório abre e confirma a própria unidade. Para alterar objetos e gravar a
alteração, use um bloco:

```python
from app.db.unidade_de_trabalho import unidade_de_trabalho

with unidade_de_trabalho():
    repositorios.beneficios.obter_beneficio("ben_inter_cashback").ativo = False
```

Uma alternativa para o futuro é cada service chamar `salvar` explicitamente depois
de alterar um objeto. Assim o contrato do repositório deixa claro quando há escrita.

### Resgate de benefício

`salvar_resgate` grava o resgate e soma `total_resgates` com
`UPDATE ... SET total_resgates = total_resgates + 1` na mesma transação, e faz o
commit ainda com a trava tomada. A próxima requisição já enxerga o resgate. A
restrição única `(cliente_id, chave_idempotencia)` impede, no próprio banco, dois
resgates com a mesma chave de idempotência.

## Comandos do Alembic

| Comando | O que faz |
|---|---|
| `alembic revision --autogenerate -m "mensagem"` | Compara modelos e banco e gera uma nova migration |
| `alembic upgrade head` | Aplica todas as migrations pendentes |
| `alembic downgrade -1` | Desfaz a última migration |
| `alembic current` | Mostra a versão atual do banco |
| `alembic history` | Lista todas as migrations |
| `alembic upgrade head --sql` | Mostra o SQL que seria executado, sem executar |
| `alembic check` | Diz se os modelos têm mudanças sem migration |

Sempre leia a migration gerada antes de aplicar. O autogenerate não detecta, por
exemplo, uma coluna renomeada: ele entende isso como apagar uma coluna e criar outra.
