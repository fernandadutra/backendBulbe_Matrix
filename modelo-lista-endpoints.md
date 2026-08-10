# Lista de Endpoints da API, [Nome do Projeto]

> Preencha os campos entre colchetes. Remova esta linha de instrução antes da entrega.

## Identificação

- **Projeto:** [nome do projeto]
- **Empresa parceira:** [nome da empresa]
- **Equipe:** [nome do grupo]
- **Integrantes:** [nome 1], [nome 2], [nome 3]
- **Data:** [dd/mm/aaaa]
- **Sprint / Etapa:** Sprint 1, Design da API

## Convenções desta API

- **URL base:** `/v1`
- **Formato de dados:** JSON, tanto na requisição quanto na resposta
- **Autenticação:** [a definir na Aula 29, Autenticação e Autorização]
- **Nomenclatura:** recursos no plural, kebab-case para múltiplas palavras, sem verbos na URL

## Visão Geral dos Endpoints

Um endpoint por linha, cobrindo o CRUD de cada entidade do domínio. A coluna Requisito de Origem conecta cada endpoint ao documento de requisitos entregue na Aula 03.

| Método | Recurso (URI) | Descrição | Requisito de Origem | Status |
|---|---|---|---|---|
| GET | `/v1/assinantes` | Lista os assinantes cadastrados | RF-01 | 200 |
| POST | `/v1/assinantes` | Cria um novo assinante | RF-01 | 201 |
| GET | `/v1/assinantes/{id}` | Retorna um assinante específico | RF-02 | 200 / 404 |
| PUT | `/v1/assinantes/{id}` | Atualiza os dados de um assinante | RF-03 | 200 / 404 |
| DELETE | `/v1/assinantes/{id}` | Remove um assinante | RF-04 | 204 / 404 |
| | | | | |
| | | | | |
| | | | | |

## Detalhamento dos Endpoints

Um exemplo completo abaixo, como referência. Replique esta estrutura para cada endpoint da tabela acima.

### GET /v1/assinantes

- **Descrição:** lista todos os assinantes cadastrados, com paginação.
- **Requisito de origem:** RF-01
- **Parâmetros de query:** `page` (número da página, opcional), `limit` (itens por página, opcional)
- **Corpo da requisição:** não se aplica
- **Exemplo de resposta (200):**

```json
{
  "data": [
    {
      "id": "1",
      "nome": "[nome do assinante]",
      "email": "[email do assinante]",
      "status_assinatura": "ativa"
    }
  ],
  "page": 1,
  "total": 1
}
```

- **Status codes:** `200` sucesso

### POST /v1/assinantes

- **Descrição:** cria um novo assinante.
- **Requisito de origem:** RF-01
- **Corpo da requisição:**

```json
{
  "nome": "[nome do assinante]",
  "email": "[email do assinante]",
  "cpf": "[cpf do assinante]",
  "endereco": "[endereço do assinante]"
}
```

- **Exemplo de resposta (201):**

```json
{
  "id": "1",
  "nome": "[nome do assinante]",
  "status_assinatura": "pendente"
}
```

- **Status codes:** `201` criado, `400` dados inválidos

### [MÉTODO] [Recurso (URI)]

- **Descrição:** [ ]
- **Requisito de origem:** [ ]
- **Parâmetros de query:** [ ]
- **Corpo da requisição:**

```json
{

}
```

- **Exemplo de resposta ([status]):**

```json
{

}
```

- **Status codes:** [ ]

## Observações

[Anote aqui premissas assumidas pela equipe, pontos que ficaram em dúvida, ou endpoints que dependem de validação futura com o professor ou com a empresa parceira.]

## Próximos passos

Este documento será formalizado em OpenAPI/Swagger em `docs/api/openapi.yaml` e servirá de base para a modelagem dos casos de uso na Aula 06 (Modelagem Comportamental, Casos de Uso da API).
