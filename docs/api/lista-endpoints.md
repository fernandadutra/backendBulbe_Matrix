# Lista de Endpoints da API, Bulbe Matrix

## Identificação

- **Projeto:** Bulbe Evolution
- **Empresa parceira:** Bulbe Energia
- **Equipe:** Squad Matrix
- **Integrantes:** Augusto Gama, Felipe Lara, Fernanda Dutra, Leandro Dias, Mariana Maia e Rafael Bentes
- **Data:** 23/08/2026
- **Sprint / Etapa:** Sprint 1, Design da API
- **Documentos de origem:** Documento de Requisitos Técnicos (`docs/requisitos.md`), Documento de User Stories (`docs/user-stories.md`)
- **Frontend consumidor:** https://github.com/fernandadutra/bulbe-squad-matrix

## Como este documento foi construído

Este documento traduz os requisitos funcionais da Sprint 1 e as user stories em um contrato concreto de endpoints. Para chegar até aqui, a equipe percorreu as doze telas já implementadas no frontend do Projeto Ciência de Dados I e, para cada elemento renderizado em tela, identificou de onde aquele dado precisará vir quando a API existir.

O ponto de partida importante é que **o frontend hoje não faz nenhuma chamada HTTP**. Toda a lógica está em `src/script.js`, que guarda o valor da fatura em `sessionStorage`, aplica uma constante `DISCOUNT_RATE = 0.15` e distingue usuário logado de visitante por uma flag `bulbe.logado`. Os textos de status, as etapas da homologação, os parceiros do clube de benefícios e o conteúdo das dicas do Bulbinho estão escritos diretamente no HTML. Cada um desses dados fixos no código é, na prática, a especificação de um campo de resposta desta API, e foi assim que os payloads abaixo foram derivados.

O documento está organizado em dois blocos. O **Bloco 1** reúne os endpoints com requisito de origem formal (RF-01 a RF-04) e constitui o escopo da Sprint 1. O **Bloco 2** reúne os endpoints que a integração com o frontend exige, mas que ainda não possuem RF correspondente, ampliando a tabela "Lacunas identificadas" já registrada no documento de user stories. A separação é deliberada: mantém a rastreabilidade exigida na disciplina sem esconder o fato de que o frontend não integra apenas com o Bloco 1.

## Convenções desta API

- **URL base:** `/api/v1`
- **Formato de dados:** JSON em requisição e resposta, `Content-Type: application/json`, exceto no envio de anexos da adesão, que usa `multipart/form-data`
- **Autenticação:** token JWT no cabeçalho `Authorization`, no esquema `Bearer`, conforme RNF-03. Endpoints marcados como públicos não exigem token
- **Idioma:** **rotas, recursos e campos em português**, em `snake_case` para campos e `kebab-case` para rotas com mais de uma palavra. Permanecem em inglês apenas os nomes padronizados pelo protocolo HTTP, como os cabeçalhos `Authorization`, `Content-Type`, `Cache-Control` e `Idempotency-Key`
- **Nomenclatura de rotas:** recursos no plural e **sem verbos na URL**. A ação é expressa pelo método HTTP ou por um recurso substantivado, como `POST /adesoes/{id}/submissao`
- **Valores monetários:** sempre inteiros em **centavos**, com sufixo `_centavos` no nome do campo. A decisão evita erro de arredondamento de ponto flutuante e conversa com o frontend, cuja função `parseCurrency` já trabalha em centavos internamente. A formatação para exibição continua no cliente, via `toLocaleString('pt-BR')`
- **Datas e horários:** ISO 8601 com fuso (`2026-08-23T14:30:00-03:00`). Datas sem hora em `YYYY-MM-DD`
- **Percentuais:** número decimal entre 0 e 1 (`0.15` para 15%)
- **Paginação:** parâmetros de query `pagina` (padrão 1) e `limite` (padrão 20, máximo 100). Respostas paginadas trazem `dados`, `pagina`, `limite` e `total`
- **Identificadores:** string opaca com prefixo de três letras indicando a entidade, como `ped_7f3a9c21`. O prefixo facilita a leitura de logs e impede que o identificador de um recurso seja usado por engano em outro
- **Idioma do conteúdo:** todo texto voltado ao usuário final vem pronto do backend em pt-BR, para atender ao critério de atualização sem novo release (RF-04)

### Prefixos de identificador por entidade

| Prefixo | Entidade |
|---|---|
| `cli_` | Cliente |
| `ped_` | Pedido de homologação |
| `sim_` | Simulação |
| `par_` | Parceiro |
| `ben_` | Benefício |
| `rsg_` | Resgate de benefício |
| `int_` | Interessado (lead) |
| `ade_` | Adesão |
| `anx_` | Anexo da adesão |
| `fat_` | Fatura Bulbe |
| `ind_` | Indicação |
| `not_` | Notificação |

### Envelope de erro padrão

Todas as respostas de erro seguem o mesmo formato, para que o frontend tenha um único caminho de tratamento:

```json
{
  "erro": {
    "codigo": "CONSUMO_FORA_DA_FAIXA",
    "mensagem": "O valor da fatura deve estar entre R$ 50,00 e R$ 5.000,00.",
    "detalhes": [
      { "campo": "valor_fatura_centavos", "problema": "abaixo do mínimo aceito" }
    ]
  }
}
```

O campo `mensagem` é redigido para ser exibido ao usuário sem reescrita no cliente. O campo `codigo` é estável e destina-se a lógica condicional. O campo `detalhes` só aparece em erros de validação.

### Códigos de status utilizados

| Código | Quando é usado |
|---|---|
| `200` | Consulta ou operação concluída com sucesso |
| `201` | Recurso criado (simulação, resgate, adesão, indicação) |
| `204` | Operação concluída sem corpo de resposta |
| `400` | Corpo malformado ou parâmetro inválido |
| `401` | Token ausente, expirado ou inválido |
| `403` | Token válido, mas o cliente não tem acesso ao recurso |
| `404` | Recurso inexistente ou não pertencente ao cliente autenticado |
| `409` | Conflito de estado, como benefício de uso único já resgatado |
| `410` | Recurso expirou entre a listagem e a confirmação |
| `413` | Arquivo acima do tamanho máximo permitido |
| `415` | Formato de arquivo não suportado |
| `422` | Regra de negócio violada, como consumo fora da faixa aceita |
| `429` | Limite de requisições excedido, aplicável aos endpoints públicos |
| `503` | Dependência externa indisponível sem dado em cache para devolver |

### Requisitos não funcionais aplicáveis a todos os endpoints

Herdados da Definition of Done do squad, valem para toda a lista e não são repetidos endpoint a endpoint:

- Tráfego exclusivamente sobre HTTPS/TLS (RNF-03)
- Rotas não públicas exigem JWT válido (RNF-03)
- Dados pessoais e faturas tratados conforme a LGPD (RNF-03)
- Consultas de status e simulação respondem em menos de 400ms (RNF-02)
- Payloads carregam rótulo textual junto de cada valor, para que o frontend anuncie rótulo e valor a leitores de tela sem inventar texto (RNF-01)
- Endpoint documentado em OpenAPI/Swagger e coberto por testes de caminho felizes e infelizes

## Mapeamento das rotas citadas nos documentos anteriores

O Documento de Requisitos Técnicos e as tarefas técnicas das user stories nomearam os endpoints **em inglês**. Este documento adota o português, conforme a convenção acima, e a tabela abaixo preserva a rastreabilidade textual entre os dois. A equipe deve atualizar `docs/requisitos.md` e `docs/user-stories.md` para refletir os nomes definitivos, ou referenciar esta tabela nos dois arquivos.

| Rota citada nos RFs e nas user stories | Rota adotada neste documento | Motivo da mudança |
|---|---|---|
| `GET /api/v1/orders/{id}/status` | `GET /api/v1/pedidos/{id}/status` | Tradução do recurso |
| `POST /api/v1/simulator/calculate` | `POST /api/v1/simulacoes` | Tradução e remoção do verbo `calculate` da URL. Criar uma simulação é criar um recurso, o que o `POST` já expressa |
| `GET /api/v1/benefits` | `GET /api/v1/beneficios` | Tradução do recurso |
| `GET /api/v1/help/tooltips` | `GET /api/v1/ajuda/dicas` | Tradução de `help` e de `tooltips`, que passa a "dicas", termo já usado nos documentos do projeto ao descrever as "Dicas Contextuais do mascote Bulbinho" |

---

# Bloco 1, Escopo formal da Sprint 1

Endpoints com requisito de origem no Documento de Requisitos Técnicos. Este é o conjunto que a equipe se compromete a entregar na Sprint 1.

## Visão geral dos endpoints, Bloco 1

| Método | Recurso (URI) | Descrição | Origem | Auth | Status |
|---|---|---|---|---|---|
| GET | `/api/v1/pedidos` | Lista os pedidos do cliente autenticado | RF-01 / US-01 | Sim | 200 / 401 |
| GET | `/api/v1/pedidos/{id}/status` | Retorna a etapa atual, as etapas concluídas e a previsão da próxima atualização | RF-01 / US-01 | Sim | 200 / 401 / 404 / 503 |
| POST | `/api/v1/simulacoes` | Cria uma simulação e retorna a economia estimada com a memória de cálculo | RF-02 / US-02 | Não | 201 / 400 / 422 / 429 |
| GET | `/api/v1/simulacoes` | Lista o histórico de simulações do cliente autenticado | RF-02 / US-02 | Sim | 200 / 401 |
| GET | `/api/v1/simulacoes/{id}` | Retorna uma simulação específica com a memória de cálculo completa | RF-02 / US-02 | Sim | 200 / 401 / 404 |
| GET | `/api/v1/beneficios` | Lista os benefícios ativos e as empresas parceiras | RF-03 / US-03 | Sim | 200 / 401 |
| GET | `/api/v1/beneficios/{id}` | Retorna um benefício com regras de uso, validade e condições de resgate | RF-03 / US-03 | Sim | 200 / 401 / 404 |
| GET | `/api/v1/trilhas` | Lista as trilhas do clube e o estado de desbloqueio de cada uma | RF-03 / US-03 | Sim | 200 / 401 |
| POST | `/api/v1/beneficios/{id}/resgates` | Registra a utilização de um benefício | RF-03 / US-04 | Sim | 201 / 400 / 401 / 404 / 409 / 410 / 422 |
| GET | `/api/v1/resgates` | Lista os resgates já realizados pelo cliente | RF-03 / US-04 | Sim | 200 / 401 |
| GET | `/api/v1/ajuda/dicas` | Retorna os textos de ajuda contextual do Bulbinho | RF-04 / US-05 | Não | 200 / 400 |

## Rastreabilidade, requisito, história, endpoint e tela

| Requisito | User Story | Endpoint | Tela do frontend que passa a ser alimentada |
|---|---|---|---|
| RF-01 | US-01 | `GET /pedidos`, `GET /pedidos/{id}/status` | `status-pedido.html`, componente `<bulbe-instalacao>` |
| RF-02 | US-02 | `POST /simulacoes` | `simular-desconto.html`, `simular-desconto-nao-logado.html`, `resultado.html` |
| RF-02 | US-02 | `GET /simulacoes`, `GET /simulacoes/{id}` | Accordion "Detalhamento das simulações" em `simular-desconto.html` |
| RF-03 | US-03 | `GET /beneficios`, `GET /beneficios/{id}` | `impulsione-fatura.html` |
| RF-03 | US-03 | `GET /trilhas` | `beneficios.html` |
| RF-03 | US-04 | `POST /beneficios/{id}/resgates`, `GET /resgates` | Ação "Acessar" nos cards de parceiro em `impulsione-fatura.html` |
| RF-04 | US-05 | `GET /ajuda/dicas` | Botão `.title__help` presente em `simular-desconto.html`, `status-pedido.html` e `beneficios.html` |
| RNF-01 | US-06 | Nenhum endpoint próprio | Critério transversal, atendido pelos rótulos textuais nos payloads |

## Detalhamento dos endpoints, Bloco 1

### GET /api/v1/pedidos

- **Descrição:** lista os pedidos do cliente autenticado. Existe porque o componente `<bulbe-instalacao>` do frontend renderiza um seletor com o número da instalação (`3013588579` no protótipo) e um `caret` de dropdown, o que pressupõe que um mesmo cliente possa ter mais de uma instalação e, portanto, mais de um pedido em andamento.
- **Requisito de origem:** RF-01, US-01
- **Autenticação:** obrigatória. O identificador do cliente vem do JWT, nunca da query, para impedir que um cliente liste pedidos de outro
- **Parâmetros de query:** `situacao` (opcional, filtra por situação), `pagina`, `limite`
- **Corpo da requisição:** não se aplica
- **Exemplo de resposta (200):**

```json
{
  "dados": [
    {
      "id": "ped_7f3a9c21",
      "numero_instalacao": "3013588579",
      "distribuidora": "CEMIG",
      "situacao": "em_andamento",
      "etapa_atual_ordem": 1,
      "etapa_atual_nome": "Em análise pela Bulbe",
      "criado_em": "2026-06-02T09:14:00-03:00"
    }
  ],
  "pagina": 1,
  "limite": 20,
  "total": 1
}
```

- **Status codes:** `200` sucesso, `401` token ausente ou inválido

### GET /api/v1/pedidos/{id}/status

- **Descrição:** retorna a linha do tempo completa da homologação junto à CEMIG. O payload reproduz as quatro etapas fixas hoje escritas em `status-pedido.html` e o card "Status atual" exibido abaixo do tracker.
- **Requisito de origem:** RF-01, US-01
- **Autenticação:** obrigatória. Retorna `404` quando o pedido não pertence ao cliente do token, para não revelar a existência de pedidos de terceiros
- **Parâmetros de path:** `id`, identificador do pedido
- **Corpo da requisição:** não se aplica
- **Exemplo de resposta (200):**

```json
{
  "pedido_id": "ped_7f3a9c21",
  "numero_instalacao": "3013588579",
  "situacao": "em_andamento",
  "etapa_atual": {
    "ordem": 1,
    "chave": "analise_bulbe",
    "nome": "Em análise pela Bulbe",
    "descricao": "Sua solicitação está sendo analisada pela equipe Bulbe.",
    "situacao": "em_andamento",
    "iniciada_em": "2026-06-02T09:14:00-03:00"
  },
  "etapas": [
    {
      "ordem": 1,
      "chave": "analise_bulbe",
      "nome": "Em análise pela Bulbe",
      "descricao": "Sua solicitação está sendo analisada pela equipe Bulbe.",
      "situacao": "em_andamento",
      "concluida_em": null
    },
    {
      "ordem": 2,
      "chave": "enviado_cemig",
      "nome": "Enviado para Cemig",
      "descricao": "Depois da primeira análise, o pedido é enviado para a Cemig.",
      "situacao": "pendente",
      "concluida_em": null
    },
    {
      "ordem": 3,
      "chave": "analise_cemig",
      "nome": "Em análise pela Cemig",
      "descricao": "A Cemig avalia e aprova o processo.",
      "situacao": "pendente",
      "concluida_em": null
    },
    {
      "ordem": 4,
      "chave": "aprovado",
      "nome": "Aprovado",
      "descricao": "Após a aprovação, os benefícios ficam disponíveis no ecossistema Bulbe.",
      "situacao": "pendente",
      "concluida_em": null
    }
  ],
  "previsao_proxima_atualizacao": "2026-09-15",
  "prazo_estimado_dias": { "minimo": 90, "maximo": 120 },
  "consultado_em": "2026-08-23T14:30:00-03:00",
  "dado_desatualizado": false
}
```

- **Comportamento em indisponibilidade da CEMIG:** o critério de aceite 3 da US-01 exige que o cliente nunca veja tela de erro nessa consulta. O backend persiste o resultado da última consulta bem-sucedida e, quando a integração externa falha, devolve `200` com esse dado em cache, sinalizando `"dado_desatualizado": true` e mantendo em `consultado_em` a data em que o dado foi realmente obtido. O `503` fica reservado ao caso em que a consulta externa falha e **não existe** nenhuma consulta anterior armazenada.
- **Nota de acessibilidade (RNF-01):** cada etapa carrega `nome` e `situacao` como campos próprios, de modo que o leitor de tela possa anunciar "Em análise pela Bulbe, em andamento" sem que o frontend precise inferir a situação a partir de uma classe CSS, como ocorre hoje com `.is-active`.
- **Status codes:** `200` sucesso, incluindo resposta com dado em cache, `401` não autenticado, `404` pedido inexistente ou de outro cliente, `503` sem dado em cache e integração indisponível

### POST /api/v1/simulacoes

- **Descrição:** cria uma simulação e devolve a economia estimada a partir do valor da última fatura do interessado. É o endpoint que substitui a constante `DISCOUNT_RATE = 0.15` hoje embutida em `src/script.js`, passando a alíquota e a memória de cálculo para o domínio do backend.
- **Requisito de origem:** RF-02, US-02
- **Autenticação:** **não exigida**, conforme o critério de aceite 4 da US-02, que garante simulação sem cadastro. Se um token válido for enviado, a simulação é vinculada ao cliente e passa a aparecer em `GET /simulacoes`. Simulações anônimas também são persistidas, sem vínculo com cliente, porque o `POST /interessados` referencia `simulacao_id` para ligar o lead à simulação que o motivou
- **Proteção contra abuso:** por ser público, o endpoint aplica limite por IP e responde `429` quando excedido. A escolha protege o RNF-02, já que a ausência de limite permitiria degradar o tempo de resposta de toda a API
- **Corpo da requisição:**

```json
{
  "valor_fatura_centavos": 35000,
  "consumo_kwh": 249,
  "distribuidora": "CEMIG"
}
```

`valor_fatura_centavos` é obrigatório, porque é o único dado que o frontend coleta hoje, no campo `#fatura` de `<bulbe-fatura-card>`, rotulado "Valor da sua fatura atual". `consumo_kwh` e `distribuidora` são opcionais e, quando presentes, refinam a memória de cálculo. Essa modelagem está registrada nas Observações como ponto a validar com a Bulbe, conforme já apontado na US-02.

- **Faixa de validação:** o critério de aceite 2 da US-02 exige recusar consumo zero, negativo ou acima do limite previsto. A faixa adotada é de `5000` a `500000` centavos, ou seja, de R$ 50,00 a R$ 5.000,00, e precisa ser confirmada com a empresa parceira
- **Exemplo de resposta (201):**

```json
{
  "id": "sim_2c81b40e",
  "calculado_em": "2026-08-23T14:30:00-03:00",
  "percentual_desconto": 0.15,
  "valor_sem_desconto_centavos": 35000,
  "valor_com_bulbe_centavos": 29750,
  "economia_mensal_centavos": 5250,
  "economia_anual_centavos": 63000,
  "rotulos": {
    "economia_mensal": "Você vai economizar por mês",
    "economia_anual": "Sua economia anual estimada",
    "valor_sem_desconto": "Sem desconto, tarifa cheia",
    "valor_com_bulbe": "Com Bulbe, até 15% desconto"
  },
  "memoria_calculo": {
    "consumo_total_kwh": 249,
    "linhas": [
      {
        "fonte": "CEMIG",
        "consumo_kwh": 50,
        "valor_centavos": 5118,
        "valor_com_desconto_centavos": null,
        "possui_desconto": false
      },
      {
        "fonte": "Bulbe Energia",
        "consumo_kwh": 199,
        "valor_centavos": 19913,
        "valor_com_desconto_centavos": 16926,
        "possui_desconto": true
      }
    ],
    "subtotal": {
      "rotulo": "Subtotal 1",
      "consumo_kwh": 249,
      "valor_centavos": 22044
    },
    "observacao": "A taxa de economia é de até 15% e varia conforme o frete da distribuidora."
  }
}
```

- **Nota sobre o status `201`:** a resposta é `201`, e não `200`, porque a operação cria um recurso durável, endereçável por `GET /simulacoes/{id}`. Foi essa característica que permitiu eliminar o verbo `calculate` da URL original prevista no RF-02.
- **Nota sobre a memória de cálculo:** a estrutura de `linhas` e `subtotal` foi desenhada a partir do bloco `.sim-detalhe__linhas`, que aparece tanto em `resultado.html` quanto em `simular-desconto.html`. O par `valor_centavos` e `valor_com_desconto_centavos` corresponde ao preço riscado e ao preço novo que o frontend já renderiza para a linha da Bulbe Energia.
- **Nota de acessibilidade (RNF-01):** o objeto `rotulos` existe para que o critério de aceite 5 da US-02 seja cumprido com texto vindo do backend, garantindo que rótulo e valor sejam anunciados juntos e permaneçam consistentes se a regra de desconto mudar.
- **Status codes:** `201` simulação criada, `400` corpo malformado, `422` valor fora da faixa aceita, `429` limite de requisições excedido

### GET /api/v1/simulacoes

- **Descrição:** lista o histórico de simulações do cliente autenticado, alimentando o accordion "Detalhamento das simulações" de `simular-desconto.html`. O frontend hoje exibe esse bloco apenas quando `sessionStorage` contém `bulbe.logado === '1'`, o que confirma que o histórico é recurso de cliente autenticado.
- **Requisito de origem:** RF-02, US-02
- **Autenticação:** obrigatória
- **Parâmetros de query:** `pagina`, `limite`
- **Exemplo de resposta (200):**

```json
{
  "dados": [
    {
      "id": "sim_2c81b40e",
      "calculado_em": "2026-06-17T10:22:00-03:00",
      "valor_sem_desconto_centavos": 22044,
      "economia_mensal_centavos": 2987
    },
    {
      "id": "sim_91ade773",
      "calculado_em": "2026-06-09T18:41:00-03:00",
      "valor_sem_desconto_centavos": 22139,
      "economia_mensal_centavos": 2187
    },
    {
      "id": "sim_44bc0f15",
      "calculado_em": "2026-05-23T08:07:00-03:00",
      "valor_sem_desconto_centavos": 27129,
      "economia_mensal_centavos": 3124
    }
  ],
  "pagina": 1,
  "limite": 20,
  "total": 3
}
```

- **Nota de desenho:** a listagem devolve apenas o resumo que o accordion mostra fechado, data e dois valores. A memória de cálculo completa fica em `GET /simulacoes/{id}`, carregada quando o item é expandido. A escolha evita transportar a memória de cálculo de todas as simulações em uma tela onde, no máximo, uma está aberta por vez.
- **Status codes:** `200` sucesso, `401` não autenticado

### GET /api/v1/simulacoes/{id}

- **Descrição:** retorna uma simulação específica com a memória de cálculo completa, no mesmo formato devolvido por `POST /api/v1/simulacoes`.
- **Requisito de origem:** RF-02, US-02
- **Autenticação:** obrigatória. Retorna `404` se a simulação não pertencer ao cliente do token
- **Exemplo de resposta (200):** idêntico ao corpo de resposta de `POST /api/v1/simulacoes`
- **Status codes:** `200` sucesso, `401` não autenticado, `404` simulação inexistente ou de outro cliente

### GET /api/v1/beneficios

- **Descrição:** lista os benefícios ativos e as empresas parceiras, alimentando o grid `.parceiro-grid` de `impulsione-fatura.html`, que hoje traz Inter, Livelo, Canal do Frossard e Araújo com textos fixos no HTML.
- **Requisito de origem:** RF-03, US-03
- **Autenticação:** obrigatória
- **Parâmetros de query:** `trilha` (opcional, filtra por trilha do clube), `pagina`, `limite`
- **Filtro obrigatório no servidor:** o critério de aceite 2 da US-03 determina que benefício expirado ou desativado pelo parceiro não apareça na lista. O filtro é aplicado na consulta, não no cliente, para que a regra não dependa da versão do aplicativo instalada
- **Exemplo de resposta (200):**

```json
{
  "dados": [
    {
      "id": "ben_inter_cashback",
      "trilha": "connect",
      "parceiro": {
        "id": "par_inter",
        "nome": "Inter",
        "url_logo": "https://cdn.bulbe.com.br/parceiros/inter.png",
        "cor_marca": "#ff7200"
      },
      "titulo": "Até 77% de cashback!",
      "descricao": "Cashback em compras realizadas pelo app do Inter.",
      "regras_de_uso": "Válido para novas contas abertas pelo link Bulbe. Cashback creditado em até 60 dias.",
      "condicoes_resgate": {
        "tipo": "uso_unico",
        "exige_pedido_aprovado": false,
        "elegivel": true,
        "motivo_inelegibilidade": null
      },
      "validade": {
        "inicio": "2026-08-01",
        "fim": "2026-12-31",
        "rotulo": "Válido até 31/12/2026"
      },
      "acao": {
        "rotulo": "Acessar",
        "exige_resgate": true
      }
    },
    {
      "id": "ben_livelo_pontos",
      "trilha": "connect",
      "parceiro": {
        "id": "par_livelo",
        "nome": "Livelo",
        "url_logo": "https://cdn.bulbe.com.br/parceiros/livelo.png",
        "cor_marca": "#f62791"
      },
      "titulo": "12 pontos por R$ 1,00",
      "descricao": "Acúmulo de pontos Livelo nas faturas Bulbe.",
      "regras_de_uso": "Pontuação creditada após o pagamento da fatura.",
      "condicoes_resgate": {
        "tipo": "recorrente",
        "exige_pedido_aprovado": true,
        "elegivel": false,
        "motivo_inelegibilidade": "Disponível após a aprovação do seu pedido pela Cemig."
      },
      "validade": { "inicio": "2026-08-01", "fim": null, "rotulo": "Sem prazo definido" },
      "acao": { "rotulo": "Acessar", "exige_resgate": true }
    }
  ],
  "pagina": 1,
  "limite": 20,
  "total": 4
}
```

- **Estado vazio:** o critério de aceite 3 da US-03 exige mensagem explicativa em vez de tela em branco. Quando não há benefício ativo, a resposta é `200` com `dados` vazio e um objeto `estado_vazio` no corpo, trazendo `titulo` e `mensagem` prontos para exibição. A mensagem vem do backend para poder ser ajustada sem novo release, na mesma lógica adotada no RF-04
- **Nota de desenho:** `condicoes_resgate.elegivel` e `motivo_inelegibilidade` chegam resolvidos pelo backend. Sem isso, o frontend precisaria conhecer as regras de elegibilidade para decidir se habilita o botão, o que duplicaria a regra de negócio no cliente
- **Status codes:** `200` sucesso, `401` não autenticado

### GET /api/v1/beneficios/{id}

- **Descrição:** retorna um benefício isolado, com o mesmo schema de item usado na listagem. Serve à tela de detalhe e à revalidação imediatamente antes da confirmação do resgate.
- **Requisito de origem:** RF-03, US-03
- **Autenticação:** obrigatória
- **Exemplo de resposta (200):** um objeto único, no formato dos itens de `dados` em `GET /api/v1/beneficios`
- **Status codes:** `200` sucesso, `401` não autenticado, `404` benefício inexistente ou não disponível para o cliente

### GET /api/v1/trilhas

- **Descrição:** lista as trilhas do clube de benefícios e o estado de desbloqueio de cada uma, alimentando os três cards de `beneficios.html`: Bulbe Connect, hoje ativa, e Bulbe Movement e Bulbe Experience, hoje com ícone de cadeado.
- **Requisito de origem:** RF-03, US-03
- **Autenticação:** obrigatória
- **Nota sobre a rota:** o recurso ficou na raiz, e não como `/beneficios/trilhas`, para não colidir com `/beneficios/{id}`. Um caminho aninhado faria o roteador precisar distinguir a palavra reservada `trilhas` de um identificador de benefício, ambiguidade desnecessária
- **Exemplo de resposta (200):**

```json
{
  "dados": [
    {
      "chave": "connect",
      "nome": "Bulbe Connect",
      "descricao": "Cliente possui acesso imediato a benefícios e parceiros.",
      "desbloqueada": true,
      "motivo_bloqueio": null,
      "cor_tema": "verde",
      "url_icone": "https://cdn.bulbe.com.br/trilhas/connect.svg",
      "quantidade_beneficios_ativos": 4,
      "parceiros_destaque": [
        { "id": "par_araujo", "nome": "Araújo", "url_logo": "https://cdn.bulbe.com.br/parceiros/araujo.png" },
        { "id": "par_inter", "nome": "Inter", "url_logo": "https://cdn.bulbe.com.br/parceiros/inter.png" }
      ]
    },
    {
      "chave": "movement",
      "nome": "Bulbe Movement",
      "descricao": "Novas experiências serão liberadas ao longo da sua jornada.",
      "desbloqueada": false,
      "motivo_bloqueio": "Disponível após a aprovação do seu pedido pela Cemig.",
      "cor_tema": "azul",
      "url_icone": "https://cdn.bulbe.com.br/trilhas/movement.svg",
      "quantidade_beneficios_ativos": 0,
      "parceiros_destaque": []
    },
    {
      "chave": "experience",
      "nome": "Bulbe Experience",
      "descricao": "Uma experiência ainda mais exclusiva aguarda você.",
      "desbloqueada": false,
      "motivo_bloqueio": "Disponível para clientes com fatura Bulbe ativa.",
      "cor_tema": "laranja",
      "url_icone": "https://cdn.bulbe.com.br/trilhas/experience.svg",
      "quantidade_beneficios_ativos": 0,
      "parceiros_destaque": []
    }
  ]
}
```

- **Nota sobre as chaves:** os valores de `chave` permanecem `connect`, `movement` e `experience` porque são **nomes de marca**, definidos pela Bulbe nos cards do frontend como "Bulbe Connect", "Bulbe Movement" e "Bulbe Experience". Traduzir marca não é traduzir vocabulário técnico
- **Nota de acessibilidade (RNF-01):** o campo `motivo_bloqueio` resolve um problema real do protótipo atual, em que o bloqueio é comunicado apenas por um ícone de cadeado com `alt="Bloqueado"`, sem explicar a razão. Com o motivo textual vindo da API, o leitor de tela anuncia por que a trilha está indisponível
- **Nota de desenho:** `cor_tema` é uma chave semântica, não um código hexadecimal, para que a paleta continue sob controle do CSS do frontend
- **Status codes:** `200` sucesso, `401` não autenticado

### POST /api/v1/beneficios/{id}/resgates

- **Descrição:** registra a utilização de um benefício e devolve as instruções ou o código necessários para usufruir. É a única escrita de dados do Bloco 1 além da criação de simulações.
- **Requisito de origem:** RF-03, US-04
- **Autenticação:** obrigatória
- **Cabeçalhos:** `Idempotency-Key`, obrigatório. Um UUID gerado pelo cliente a cada tentativa de resgate. Requisições repetidas com a mesma chave devolvem o resgate já criado, com `201`, em vez de criar um segundo registro
- **Corpo da requisição:**

```json
{
  "pedido_id": "ped_7f3a9c21"
}
```

`pedido_id` é opcional e só se aplica a benefícios cuja elegibilidade dependa de um pedido específico, situação prevista para clientes com mais de uma instalação.

- **Exemplo de resposta (201):**

```json
{
  "id": "rsg_5e02a7cc",
  "beneficio_id": "ben_inter_cashback",
  "resgatado_em": "2026-08-23T14:31:12-03:00",
  "situacao": "confirmado",
  "instrucoes": "Abra o app do Inter e finalize a abertura da conta em até 7 dias para garantir o cashback.",
  "codigo": "BULBE-INTER-8F2K",
  "url_acesso": "https://parceiros.bulbe.com.br/inter/redirecionamento?rsg=rsg_5e02a7cc",
  "expira_em": "2026-08-30T23:59:59-03:00"
}
```

- **Revalidação no momento da confirmação:** os critérios de aceite 2 e 3 da US-04 exigem que validade e elegibilidade sejam checadas de novo no ato do resgate, e não apenas na listagem. Um benefício de uso único já resgatado responde `409`; um benefício que expirou entre a exibição da lista e a confirmação responde `410`, e o cliente deve recarregar a lista; um cliente que não atende às condições responde `422` com o motivo em `erro.mensagem`
- **Atomicidade:** o critério de aceite 4 da US-04 determina que uma falha no registro não contabilize uso algum. O registro do resgate e o incremento do contador de uso ocorrem na mesma transação, e a chave de idempotência garante que a nova tentativa do cliente não gere resgate duplicado
- **Status codes:** `201` resgate registrado, `400` cabeçalho `Idempotency-Key` ausente, `401` não autenticado, `404` benefício inexistente, `409` benefício de uso único já resgatado, `410` benefício expirado entre a listagem e a confirmação, `422` cliente não elegível

### GET /api/v1/resgates

- **Descrição:** lista os resgates já realizados pelo cliente autenticado. Permite ao frontend marcar na lista de benefícios o que já foi utilizado e exibir novamente o código de um resgate anterior, sem tentar um novo resgate que retornaria `409`.
- **Requisito de origem:** RF-03, US-04
- **Autenticação:** obrigatória. O recurso está na raiz e é sempre escopado ao cliente do token, seguindo a mesma regra de `GET /pedidos`: o identificador do cliente nunca aparece na URL
- **Parâmetros de query:** `pagina`, `limite`
- **Exemplo de resposta (200):**

```json
{
  "dados": [
    {
      "id": "rsg_5e02a7cc",
      "beneficio_id": "ben_inter_cashback",
      "beneficio_titulo": "Até 77% de cashback!",
      "parceiro_nome": "Inter",
      "resgatado_em": "2026-08-23T14:31:12-03:00",
      "situacao": "confirmado",
      "codigo": "BULBE-INTER-8F2K",
      "expira_em": "2026-08-30T23:59:59-03:00"
    }
  ],
  "pagina": 1,
  "limite": 20,
  "total": 1
}
```

- **Status codes:** `200` sucesso, `401` não autenticado

### GET /api/v1/ajuda/dicas

- **Descrição:** retorna os textos de ajuda contextual do Bulbinho associados a uma tela. Substitui as imagens `Camada Bulbinho.png` e `Camada Bulbinho2.png` que o `components.js` hoje abre em modal, e que carregam texto rasterizado.
- **Requisito de origem:** RF-04, US-05
- **Autenticação:** **não exigida**, porque a dica do simulador aparece em `simular-desconto-nao-logado.html`, tela acessível a visitante
- **Parâmetros de query:** `tela`, obrigatório, chave da tela. `elemento`, opcional, chave do campo ou componente específico. Quando `elemento` é omitido, a resposta traz todas as dicas da tela, permitindo que o cliente faça uma única requisição por tela
- **Chave de associação:** o par `tela` e `elemento` é o contrato entre frontend e backend. As chaves de `tela` correspondem às telas existentes: `simular-desconto`, `status-pedido`, `beneficios`, `impulsione-fatura`, `faturas`, `adesao`, `indique-ganhe`. As chaves de `elemento` são definidas pelo squad de frontend e registradas neste documento quando novas telas ganharem ajuda contextual
- **Exemplo de requisição:** `GET /api/v1/ajuda/dicas?tela=status-pedido`
- **Exemplo de resposta (200):**

```json
{
  "tela": "status-pedido",
  "atualizado_em": "2026-08-20T11:00:00-03:00",
  "dicas": [
    {
      "elemento": "titulo-status",
      "titulo": "Como funciona o acompanhamento",
      "rotulo_acessivel": "Entender as etapas do pedido",
      "blocos": [
        {
          "tipo": "paragrafo",
          "texto": "Seu pedido passa por 4 etapas até a liberação dos benefícios Bulbe."
        },
        {
          "tipo": "lista",
          "itens": [
            {
              "titulo": "Em análise pela Bulbe",
              "texto": "Nossa equipe confere os dados enviados e verifica se está tudo certo com o pedido."
            },
            {
              "titulo": "Enviado para a Cemig",
              "texto": "Depois da primeira análise, o pedido é enviado para a Cemig."
            },
            {
              "titulo": "Em análise pela Cemig",
              "texto": "A Cemig avalia e aprova o processo."
            },
            {
              "titulo": "Aprovado",
              "texto": "Após a aprovação, os benefícios ficam disponíveis no ecossistema Bulbe."
            }
          ]
        }
      ]
    }
  ]
}
```

- **Nota sobre o payload estruturado:** a resposta usa blocos tipados em vez de uma única string. A decisão vem do conteúdo real do protótipo em `simulador de economia - Tooltip Bulbinho/index.html`, que já combina um parágrafo de introdução com uma lista de quatro etapas, cada uma com título em negrito e descrição. Uma string simples obrigaria o frontend a interpretar HTML vindo da API, o que criaria risco de injeção e quebraria a semântica exigida pelo RNF-01
- **Ausência de conteúdo:** o critério de aceite 3 da US-05 determina que o ícone de ajuda não seja exibido quando não há conteúdo cadastrado. A resposta é `200` com `dicas` vazio, e o frontend usa a lista vazia como sinal para não renderizar o botão `.title__help`. A escolha de `200` em vez de `404` é deliberada: ausência de dica é um estado normal, não um erro
- **Atualização sem novo release:** o RF-04 exige que a equipe possa alterar o texto sem publicar nova versão do aplicativo. O campo `atualizado_em` permite ao cliente aplicar cache com revalidação, e a resposta deve trazer `Cache-Control` com janela curta para que a atualização chegue na próxima abertura do app, como pede o critério de aceite 2 da US-05
- **Status codes:** `200` sucesso, incluindo lista vazia, `400` parâmetro `tela` ausente ou desconhecido

---

# Bloco 2, Endpoints exigidos pela integração sem requisito de origem

Os endpoints desta seção **não possuem RF correspondente** no Documento de Requisitos Técnicos da Sprint 1. Eles foram identificados ao percorrer o frontend e constatar que existem telas, componentes e fluxos já construídos que nenhum requisito atual sustenta. A seção amplia a tabela "Lacunas identificadas, candidatas à Sprint 2" do documento de user stories, que já havia registrado duas dessas lacunas.

O registro é necessário porque **o frontend não integra apenas com o Bloco 1**. Sem autenticação, em particular, nenhum dos endpoints protegidos do Bloco 1 pode ser exercitado, o que torna o grupo 2.1 abaixo uma dependência técnica da própria Sprint 1.

## Visão geral dos endpoints, Bloco 2

| Método | Recurso (URI) | Descrição | Lacuna | Prioridade sugerida |
|---|---|---|---|---|
| POST | `/api/v1/sessoes` | Autentica o cliente e emite o par de tokens | 2.1 Autenticação | Alta, bloqueante |
| POST | `/api/v1/sessoes/renovacao` | Renova o token de acesso a partir do token de renovação | 2.1 Autenticação | Alta, bloqueante |
| DELETE | `/api/v1/sessoes` | Encerra a sessão e invalida o token de renovação | 2.1 Autenticação | Alta, bloqueante |
| GET | `/api/v1/perfil` | Retorna o perfil do cliente autenticado e suas instalações | 2.1 Autenticação | Alta, bloqueante |
| POST | `/api/v1/interessados` | Registra o interessado na etapa de contato | 2.2 Adesão | Alta |
| POST | `/api/v1/adesoes` | Abre um processo de adesão | 2.2 Adesão | Alta |
| PATCH | `/api/v1/adesoes/{id}` | Salva o progresso de uma etapa da adesão | 2.2 Adesão | Alta |
| POST | `/api/v1/adesoes/{id}/anexos` | Recebe o upload do arquivo da fatura de energia | 2.2 Adesão | Alta |
| POST | `/api/v1/adesoes/{id}/aceites` | Registra o aceite dos termos e da política de privacidade | 2.2 Adesão | Alta |
| POST | `/api/v1/adesoes/{id}/submissao` | Submete a adesão e origina o pedido de homologação | 2.2 Adesão | Alta |
| GET | `/api/v1/indicacoes` | Retorna código, indicações e progresso de recompensas | 2.3 Indique e ganhe | Média |
| POST | `/api/v1/indicacoes` | Registra uma nova indicação | 2.3 Indique e ganhe | Média |
| GET | `/api/v1/faturas` | Lista as faturas Bulbe do cliente | 2.4 Faturas e consumo | Média |
| GET | `/api/v1/faturas/{id}` | Retorna uma fatura com linha digitável e PDF | 2.4 Faturas e consumo | Média |
| GET | `/api/v1/consumo` | Retorna a série histórica de consumo e economia | 2.4 Faturas e consumo | Média |
| GET | `/api/v1/notificacoes` | Lista as notificações do cliente | 2.5 Notificações | Baixa |
| PATCH | `/api/v1/notificacoes/{id}` | Marca uma notificação como lida | 2.5 Notificações | Baixa |
| GET | `/api/v1/conteudos/boas-vindas` | Retorna o conteúdo das telas de onboarding didático | 2.6 Boas-vindas | Baixa |

## 2.1 Autenticação, dependência bloqueante da Sprint 1

**Lacuna:** o RF-01 e o RF-03 pressupõem "cliente autenticado", e o RNF-03 exige JWT nas rotas protegidas, mas **nenhum requisito descreve o endpoint que emite esse token**. No frontend, o estado de autenticação é simulado: o botão "Já possui conta? Entre aqui" de `index.html` apenas grava `sessionStorage.setItem('bulbe.logado', '1')` e navega para `status-pedido.html`, sem qualquer verificação de credencial.

**Encaminhamento sugerido:** elicitar o requisito antes de iniciar o RF-01, já que os testes de integração do Bloco 1 dependem da emissão de token.

**Nota sobre a modelagem:** o recurso foi nomeado `sessoes` em vez de `login` e `logout`, que são verbos e anglicismos. Criar uma sessão é `POST`, encerrar é `DELETE`, o que respeita a convenção de não usar verbo na URL.

### POST /api/v1/sessoes

- **Descrição:** autentica o cliente e cria uma sessão.
- **Autenticação:** público
- **Corpo da requisição:**

```json
{
  "identificador": "cliente@exemplo.com.br",
  "senha": "********"
}
```

`identificador` aceita e-mail ou CPF, porque a etapa 4 do fluxo de adesão em `adesao.html` menciona "senha de acesso" sem definir o par de login.

- **Exemplo de resposta (201):**

```json
{
  "token_acesso": "eyJhbGciOiJIUzI1NiIs...",
  "tipo_token": "Bearer",
  "expira_em_segundos": 900,
  "token_renovacao": "trn_9d21ba0c7e...",
  "cliente": {
    "id": "cli_3f81aa02",
    "nome": "Maria Souza",
    "possui_pedido_em_andamento": true,
    "possui_fatura_emitida": false
  }
}
```

- **Nota de desenho:** os campos `possui_pedido_em_andamento` e `possui_fatura_emitida` evitam que o cliente precise chamar três endpoints logo após a autenticação apenas para decidir qual tela abrir. Hoje o frontend resolve isso com a flag `bulbe.logado`, que também controla se o accordion de simulações e o CTA "Comece agora" são exibidos
- **Nota sobre os nomes dos campos:** `token_acesso` e `token_renovacao` são a tradução de `access_token` e `refresh_token`. Se a equipe decidir adotar OAuth 2.0 formalmente em vez de um fluxo próprio, os nomes padronizados pela RFC 6749 passam a ser obrigatórios e esta tradução deve ser revertida apenas neste endpoint
- **Segurança:** mensagem de erro genérica em credencial inválida, sem distinguir usuário inexistente de senha incorreta, e limite de tentativas por identificador e por IP
- **Status codes:** `201` sessão criada, `400` corpo malformado, `401` credenciais inválidas, `429` tentativas excedidas

### POST /api/v1/sessoes/renovacao

- **Descrição:** renova o token de acesso expirado.
- **Autenticação:** público, autorizado pelo próprio token de renovação no corpo
- **Corpo da requisição:** `{ "token_renovacao": "trn_9d21ba0c7e..." }`
- **Exemplo de resposta (201):** mesmo formato de `POST /sessoes`, com o token de renovação rotacionado
- **Status codes:** `201` renovado, `401` token de renovação inválido, expirado ou já utilizado

### DELETE /api/v1/sessoes

- **Descrição:** encerra a sessão do cliente e invalida o token de renovação.
- **Autenticação:** obrigatória
- **Corpo da requisição:** `{ "token_renovacao": "trn_9d21ba0c7e..." }`
- **Status codes:** `204` sessão encerrada, `401` não autenticado

### GET /api/v1/perfil

- **Descrição:** retorna o perfil do cliente autenticado e as instalações associadas, alimentando o avatar do header `variant="app"` e o seletor de instalação.
- **Autenticação:** obrigatória
- **Exemplo de resposta (200):**

```json
{
  "id": "cli_3f81aa02",
  "nome": "Maria Souza",
  "email": "cliente@exemplo.com.br",
  "telefone": "+5531999998888",
  "instalacoes": [
    { "numero": "3013588579", "distribuidora": "CEMIG", "pedido_id": "ped_7f3a9c21", "principal": true }
  ]
}
```

- **Status codes:** `200` sucesso, `401` não autenticado

## 2.2 Adesão e envio de fatura

**Lacuna:** já registrada no documento de user stories. Não existe RF descrevendo o upload, a validação e o armazenamento do arquivo de fatura, embora o RNF-03 preveja a proteção desses documentos. A tela `adesao.html` é hoje um placeholder que declara as quatro etapas do fluxo: Contato, com nome, e-mail e WhatsApp; Negócio, com dados da conta de luz; Termos, com política de privacidade e termo de adesão; e Confirmação, com compartilhamento e senha de acesso.

**Encaminhamento sugerido:** elicitar o requisito na Sprint 2 e derivar a user story correspondente, com atenção especial ao tratamento do arquivo de fatura sob a LGPD.

### POST /api/v1/interessados

- **Descrição:** registra o interessado na etapa 1 do fluxo, permitindo retomada posterior e não perdendo o contato caso o fluxo seja abandonado nas etapas seguintes. O nome do recurso segue a persona P-01 do documento de user stories, "Lead / Interessado".
- **Autenticação:** público
- **Corpo da requisição:**

```json
{
  "nome": "Maria Souza",
  "email": "cliente@exemplo.com.br",
  "whatsapp": "+5531999998888",
  "simulacao_id": "sim_2c81b40e",
  "aceite_comunicacoes": true
}
```

`simulacao_id` vincula o interessado à simulação que o motivou, fechando o ciclo entre o RF-02 e a adesão. `aceite_comunicacoes` é o consentimento explícito exigido pela LGPD para contato de marketing, e precisa ser distinto do aceite dos termos de adesão.

- **Exemplo de resposta (201):**

```json
{
  "id": "int_18c4a70b",
  "situacao": "novo",
  "token_fluxo": "tfl_c93b21ee...",
  "expira_em": "2026-08-24T14:30:00-03:00"
}
```

- **Nota de desenho:** `token_fluxo` autoriza as etapas seguintes da adesão sem exigir que o interessado crie senha antes de concluir o cadastro. A senha só é definida na etapa 4, conforme o placeholder do frontend
- **Status codes:** `201` interessado registrado, `400` dados inválidos, `409` interessado já existente para o e-mail informado

### POST /api/v1/adesoes

- **Descrição:** abre um processo de adesão a partir de um interessado, retornando o identificador usado nas etapas seguintes.
- **Autenticação:** público, autorizado pelo `token_fluxo` devolvido no registro do interessado
- **Corpo da requisição:** `{ "interessado_id": "int_18c4a70b" }`
- **Exemplo de resposta (201):**

```json
{
  "id": "ade_6b2f9013",
  "situacao": "em_preenchimento",
  "etapa_atual": "contato",
  "etapas_concluidas": ["contato"],
  "etapas_pendentes": ["negocio", "termos", "confirmacao"]
}
```

- **Status codes:** `201` adesão aberta, `400` dados inválidos, `404` interessado inexistente

### PATCH /api/v1/adesoes/{id}

- **Descrição:** salva o progresso de uma etapa. O método parcial foi escolhido para que o cliente possa preencher o formulário em mais de uma sessão sem perder dados, cenário provável dado o público de baixa familiaridade digital descrito na persona P-04.
- **Corpo da requisição, etapa Negócio:**

```json
{
  "etapa": "negocio",
  "dados": {
    "numero_instalacao": "3013588579",
    "distribuidora": "CEMIG",
    "titular_nome": "Maria Souza",
    "titular_documento": "00000000000",
    "cep": "30140071",
    "classe_consumo": "residencial"
  }
}
```

- **Status codes:** `200` progresso salvo, `400` etapa desconhecida, `404` adesão inexistente, `409` adesão já submetida, `422` dado inconsistente com a distribuidora informada

### POST /api/v1/adesoes/{id}/anexos

- **Descrição:** recebe o arquivo da fatura de energia do interessado. É o endpoint mais sensível de toda a API, por manipular documento que contém nome, endereço e número de instalação do titular.
- **Nota sobre a rota:** o recurso é `anexos`, e não `faturas`, para não colidir semanticamente com `GET /faturas`, que lista as **faturas Bulbe emitidas ao cliente**. Aqui trata-se do documento da distribuidora enviado pelo interessado. O campo `tipo` diferencia os anexos e, no escopo atual, aceita apenas `fatura_energia`, ficando extensível a outros documentos que a Bulbe venha a solicitar
- **Content-Type:** `multipart/form-data`, campos `arquivo` e `tipo`
- **Restrições:** formatos aceitos PDF, JPG e PNG; tamanho máximo 10 MB; validação do tipo real do arquivo pelo conteúdo, e não pela extensão
- **Exemplo de resposta (201):**

```json
{
  "id": "anx_4a71cc80",
  "tipo": "fatura_energia",
  "nome_arquivo": "fatura-junho.pdf",
  "tamanho_bytes": 284193,
  "situacao": "recebido",
  "recebido_em": "2026-08-23T14:35:00-03:00",
  "dados_extraidos": {
    "numero_instalacao": "3013588579",
    "valor_centavos": 35000,
    "consumo_kwh": 249,
    "confianca": 0.92
  }
}
```

- **Nota de desenho:** `dados_extraidos` é opcional e traz o resultado de leitura automática da fatura, com um índice de confiança. Quando a confiança é baixa, o frontend confirma os campos com o usuário em vez de assumi-los. O objetivo é reduzir digitação para a persona P-04, sem transformar um erro de leitura em erro de cadastro
- **Requisitos de LGPD (RNF-03):** armazenamento criptografado em repouso; URLs de acesso assinadas e de validade curta, nunca públicas; registro em log de todo acesso ao arquivo, com identificação de quem acessou; política de retenção definida, com descarte após o prazo; e o arquivo nunca trafega em resposta de listagem, apenas sob solicitação explícita
- **Status codes:** `201` arquivo recebido, `400` arquivo ausente, `404` adesão inexistente, `409` adesão já submetida, `413` arquivo acima do limite, `415` formato não suportado, `422` arquivo ilegível

### POST /api/v1/adesoes/{id}/aceites

- **Descrição:** registra o aceite da política de privacidade e do termo de adesão, etapa 3 do fluxo.
- **Corpo da requisição:**

```json
{
  "aceite_termo_adesao": true,
  "aceite_politica_privacidade": true,
  "versao_documentos": "2026-07-01",
  "aceito_em": "2026-08-23T14:36:00-03:00"
}
```

- **Nota de conformidade:** `versao_documentos` é obrigatório. Sem registrar qual versão foi aceita, o consentimento não é auditável, o que compromete a demonstração de conformidade com a LGPD exigida pelo RNF-03. O endereço IP e o user agent da requisição devem ser persistidos junto ao aceite
- **Status codes:** `201` aceite registrado, `400` aceite incompleto, `404` adesão inexistente, `409` já registrado, `422` versão de documento desatualizada

### POST /api/v1/adesoes/{id}/submissao

- **Descrição:** submete a adesão, valida que todas as etapas foram concluídas, cria as credenciais de acesso do cliente e **origina o pedido de homologação** que passa a ser consultável pelo `GET /pedidos/{id}/status` do RF-01.
- **Corpo da requisição:**

```json
{
  "senha": "********",
  "aceite_compartilhamento_dados": true
}
```

Os dois campos correspondem à etapa 4 declarada no placeholder do frontend, "Confirmação, compartilhamento e senha de acesso".

- **Exemplo de resposta (201):**

```json
{
  "adesao_id": "ade_6b2f9013",
  "cliente_id": "cli_3f81aa02",
  "pedido_id": "ped_7f3a9c21",
  "situacao": "submetida",
  "prazo_estimado_dias": { "minimo": 90, "maximo": 120 },
  "mensagem": "Recebemos sua adesão. A homologação junto à Cemig leva de 90 a 120 dias e você pode acompanhar cada etapa pelo app."
}
```

- **Nota de negócio:** o campo `mensagem` e o `prazo_estimado_dias` respondem diretamente à demanda D01 registrada em `docs/demandas.md` do frontend, segundo a qual o aviso do prazo de 90 dias só é dado após a adesão e está associado à inadimplência da primeira fatura. Devolver o prazo na resposta da submissão torna a expectativa explícita no momento em que ela se forma
- **Status codes:** `201` adesão submetida, `404` adesão inexistente, `409` já submetida, `422` etapas obrigatórias pendentes

## 2.3 Indique e ganhe

**Lacuna:** a tela `indique-ganhe.html` é um placeholder que declara quatro estados progressivos, e o componente `<bulbe-banner>` está presente em **todas** as doze telas com o rótulo acessível "Indique e ganhe R$50 mais prêmios especiais". Não existe requisito descrevendo a origem do código de indicação, a contagem, nem a regra de recompensa. A funcionalidade também atende à demanda D05, construção de confiança, segundo a qual "a confiança só aumenta quando é por indicação de amigos ou de empresa".

### GET /api/v1/indicacoes

- **Autenticação:** obrigatória
- **Exemplo de resposta (200):**

```json
{
  "codigo": "MARIA50",
  "url_compartilhamento": "https://bulbe.com.br/indique/MARIA50",
  "recompensa_por_indicacao_centavos": 5000,
  "total_indicacoes": 3,
  "indicacoes_convertidas": 2,
  "credito_acumulado_centavos": 10000,
  "faixa_atual": {
    "chave": "economia_com_indicacoes",
    "nome": "Economia + indicações",
    "proxima_faixa": "top_indicador",
    "indicacoes_para_proxima_faixa": 7
  },
  "indicacoes": [
    { "id": "ind_a10", "nome_ofuscado": "Jo** S****", "situacao": "convertida", "indicada_em": "2026-07-02" },
    { "id": "ind_a11", "nome_ofuscado": "Ca**** L***", "situacao": "pendente", "indicada_em": "2026-08-11" }
  ]
}
```

- **Nota de desenho:** `faixa_atual` reproduz os quatro estados declarados no placeholder do frontend, incluindo a faixa "TOP indicador" a partir de dez indicações. `nome_ofuscado` existe porque o indicado é titular de dados pessoais próprios e não consentiu em ter o nome completo exibido a quem o indicou
- **Status codes:** `200` sucesso, `401` não autenticado

### POST /api/v1/indicacoes

- **Corpo da requisição:** `{ "nome": "João Silva", "whatsapp": "+5531988887777" }`
- **Status codes:** `201` indicação registrada, `400` dados inválidos, `401` não autenticado, `409` contato já indicado ou já cliente, `422` limite de indicações pendentes atingido

## 2.4 Faturas e consumo

**Lacuna:** três telas do frontend, `faturas.html`, `pre-fatura.html` e `pre-grafico.html`, existem exclusivamente para exibir **estados vazios**. As mensagens são fixas no HTML: "Seus gráficos aparecerão em breve..." e "Oops... Não encontrei nenhuma fatura. Verifique se seu pedido já foi aprovado, e então tente novamente." Nenhum requisito atual permite ao backend informar qual estado vazio corresponde à situação real do cliente, nem servir os dados quando eles passarem a existir. A lacuna também alcança a demanda D02, falta de transparência com dados de consumo e economia.

### GET /api/v1/faturas

- **Descrição:** lista as faturas Bulbe emitidas ao cliente autenticado.
- **Autenticação:** obrigatória
- **Parâmetros de query:** `situacao`, `pagina`, `limite`
- **Exemplo de resposta com dados (200):**

```json
{
  "dados": [
    {
      "id": "fat_08a2ce31",
      "competencia": "2026-08",
      "vencimento": "2026-09-10",
      "valor_centavos": 29750,
      "economia_centavos": 5250,
      "situacao": "aberta",
      "linha_digitavel": "00190000090123456789012345678901234567890123",
      "url_pdf": "https://api.bulbe.com.br/api/v1/faturas/fat_08a2ce31/pdf"
    }
  ],
  "pagina": 1,
  "limite": 20,
  "total": 1,
  "estado_vazio": null
}
```

- **Exemplo de resposta em estado vazio (200):**

```json
{
  "dados": [],
  "pagina": 1,
  "limite": 20,
  "total": 0,
  "estado_vazio": {
    "chave": "aguardando_homologacao",
    "titulo": "Oops... Não encontrei nenhuma fatura.",
    "mensagem": "Seu pedido ainda está em análise pela Cemig. A primeira fatura chega depois da aprovação.",
    "acao_sugerida": { "rotulo": "Ver status do pedido", "destino": "status-pedido" }
  }
}
```

- **Nota de desenho:** o objeto `estado_vazio` é a peça que faltava. Hoje o frontend só sabe dizer "verifique se seu pedido já foi aprovado", porque não tem como saber em qual situação o cliente está. Com a chave vinda do backend, a tela passa a distinguir aguardando homologação, homologado sem fatura emitida e cliente sem instalação vinculada, e a sugerir a ação correta em cada caso
- **Status codes:** `200` sucesso, incluindo estado vazio, `401` não autenticado

### GET /api/v1/faturas/{id}

- **Descrição:** retorna uma fatura específica, incluindo linha digitável e URL assinada do PDF.
- **Status codes:** `200` sucesso, `401` não autenticado, `404` fatura inexistente ou de outro cliente

### GET /api/v1/consumo

- **Descrição:** série histórica de consumo e economia, alimentando os gráficos previstos em `pre-grafico.html`.
- **Parâmetros de query:** `instalacao` (opcional), `de` e `ate` no formato `YYYY-MM`, `granularidade` com valores `mensal` ou `anual`
- **Exemplo de resposta (200):**

```json
{
  "instalacao": "3013588579",
  "granularidade": "mensal",
  "serie": [
    { "competencia": "2026-07", "consumo_kwh": 241, "valor_pago_centavos": 28800, "economia_centavos": 5080 },
    { "competencia": "2026-08", "consumo_kwh": 249, "valor_pago_centavos": 29750, "economia_centavos": 5250 }
  ],
  "totais": { "economia_acumulada_centavos": 10330, "consumo_medio_kwh": 245 },
  "estado_vazio": null
}
```

- **Nota de acessibilidade (RNF-01):** o objeto `totais` existe para que a informação central do gráfico esteja disponível em texto. O critério de aceite 4 da US-06 exige alternativa textual para elemento visual que transmite informação, e um gráfico sem resumo numérico acessível não atende a esse critério
- **Status codes:** `200` sucesso, `401` não autenticado, `400` intervalo de datas inválido

## 2.5 Notificações

**Lacuna:** o header `variant="app"`, definido em `components.js` e usado em `status-pedido.html`, `faturas.html` e `impulsione-fatura.html`, renderiza um sino com `<span class="topbar__sino-badge">`, ou seja, um indicador de não lido. Nenhum requisito descreve a origem dessas notificações. Considerando a demanda D01, a notificação de mudança de etapa da homologação é justamente o mecanismo que reduz a ansiedade durante os 90 a 120 dias de espera.

### GET /api/v1/notificacoes

- **Parâmetros de query:** `apenas_nao_lidas` (booleano), `pagina`, `limite`
- **Exemplo de resposta (200):**

```json
{
  "dados": [
    {
      "id": "not_c410aa7b",
      "tipo": "mudanca_etapa_pedido",
      "titulo": "Seu pedido avançou de etapa",
      "mensagem": "Seu pedido foi enviado para a Cemig.",
      "lida": false,
      "criada_em": "2026-08-22T09:00:00-03:00",
      "referencia": { "tipo": "pedido", "id": "ped_7f3a9c21" }
    }
  ],
  "nao_lidas": 1,
  "pagina": 1,
  "limite": 20,
  "total": 1
}
```

- **Nota de desenho:** o contador `nao_lidas` vem no corpo, e não apenas derivado da lista, porque o badge do sino precisa do total sem paginar
- **Status codes:** `200` sucesso, `401` não autenticado

### PATCH /api/v1/notificacoes/{id}

- **Corpo da requisição:** `{ "lida": true }`
- **Status codes:** `200` atualizada, `401` não autenticado, `404` notificação inexistente

## 2.6 Conteúdo de boas-vindas

**Lacuna:** já registrada no documento de user stories, que pergunta se o conteúdo é estático no aplicativo ou servido pela API. Hoje o conteúdo dos três passos de `index.html` está **rasterizado dentro das imagens** `como-funciona-1.png`, `como-funciona-2.png` e `como-funciona-3.png`, com o texto disponível apenas nos atributos `alt`. Isso significa que qualquer ajuste de copy exige nova versão do aplicativo e que o texto não é selecionável nem redimensionável, o que conflita com o RNF-01.

**Nota sobre o nome do recurso:** o documento de requisitos chama a tela de "Onboarding Didático". O recurso foi nomeado `conteudos/boas-vindas` para manter a convenção de português nas rotas, e refere-se à mesma tela.

### GET /api/v1/conteudos/boas-vindas

- **Autenticação:** público
- **Exemplo de resposta (200):**

```json
{
  "versao": "2026-08-01",
  "titulo": "Como funciona",
  "passos": [
    {
      "ordem": 1,
      "titulo": "Energia solar que gera economia",
      "texto": "Nossas fazendas solares produzem energia limpa e renovável.",
      "url_ilustracao": "https://cdn.bulbe.com.br/boas-vindas/passo-1.svg",
      "texto_alternativo": "Painéis solares em uma fazenda solar"
    },
    {
      "ordem": 2,
      "titulo": "Energia que chega até você",
      "texto": "Essa energia solar é enviada para a rede de distribuição da CEMIG.",
      "url_ilustracao": "https://cdn.bulbe.com.br/boas-vindas/passo-2.svg",
      "texto_alternativo": "Linhas de transmissão levando energia à rede da distribuidora"
    },
    {
      "ordem": 3,
      "titulo": "Créditos que viram desconto na sua conta de luz",
      "texto": "A energia chega em forma de créditos que se transformam em desconto.",
      "url_ilustracao": "https://cdn.bulbe.com.br/boas-vindas/passo-3.svg",
      "texto_alternativo": "Fatura de energia com valor reduzido pelo desconto"
    }
  ]
}
```

- **Nota de desenho:** separar `titulo` e `texto` da ilustração resolve simultaneamente as duas questões levantadas na lacuna. O conteúdo passa a ser atualizável pela API, e o texto deixa de estar preso a um bitmap, ficando selecionável, redimensionável e legível por leitor de tela, com a ilustração reduzida ao papel decorativo que já tem
- **Status codes:** `200` sucesso

---

# Entidades do domínio implícitas neste contrato

Consolidação das entidades que os payloads acima pressupõem. Serve de entrada para a modelagem de dados a ser feita em `docs/banco-de-dados/`.

| Entidade | Origem | Principais atributos | Relacionamentos |
|---|---|---|---|
| Cliente | RF-01, RF-03 | nome, email, telefone, senha | possui N Instalações, N Simulações, N Resgates, N Indicações |
| Instalação | RF-01 | numero, distribuidora, classe_consumo | pertence a 1 Cliente, possui 1 Pedido |
| Pedido | RF-01 | situacao, criado_em, previsao_proxima_atualizacao | pertence a 1 Instalação, possui N Etapas de Pedido |
| Etapa de Pedido | RF-01 | ordem, chave, nome, descricao, situacao, concluida_em | pertence a 1 Pedido |
| Simulação | RF-02 | valor_fatura_centavos, percentual_desconto, economia_mensal_centavos | pertence a 0 ou 1 Cliente, possui 1 Memória de Cálculo |
| Memória de Cálculo | RF-02 | consumo_total_kwh, subtotal | pertence a 1 Simulação, possui N Linhas de Cálculo |
| Linha de Cálculo | RF-02 | fonte, consumo_kwh, valor_centavos, valor_com_desconto_centavos | pertence a 1 Memória de Cálculo |
| Trilha | RF-03 | chave, nome, descricao, cor_tema, regra_desbloqueio | possui N Benefícios |
| Parceiro | RF-03 | nome, url_logo, cor_marca | possui N Benefícios |
| Benefício | RF-03 | titulo, descricao, regras_de_uso, tipo, validade | pertence a 1 Trilha e 1 Parceiro, possui N Resgates |
| Resgate | RF-03 | codigo, resgatado_em, situacao, expira_em | pertence a 1 Cliente e 1 Benefício |
| Dica | RF-04 | tela, elemento, titulo, blocos, atualizado_em | independente |
| Interessado | Lacuna 2.2 | nome, email, whatsapp, aceite_comunicacoes | referencia 0 ou 1 Simulação, origina 0 ou 1 Adesão |
| Adesão | Lacuna 2.2 | situacao, etapa_atual, dados por etapa | pertence a 1 Interessado, possui N Anexos e 1 Aceite |
| Anexo | Lacuna 2.2 | tipo, nome_arquivo, tamanho_bytes, dados_extraidos | pertence a 1 Adesão |
| Aceite | Lacuna 2.2 | versao_documentos, aceito_em, ip, user_agent | pertence a 1 Adesão |
| Fatura | Lacuna 2.4 | competencia, vencimento, valor_centavos, economia_centavos | pertence a 1 Instalação |
| Indicação | Lacuna 2.3 | nome, whatsapp, situacao, indicada_em | pertence a 1 Cliente indicador |
| Notificação | Lacuna 2.5 | tipo, titulo, mensagem, lida, referencia | pertence a 1 Cliente |

---

# Observações

Premissas assumidas pela equipe e pontos que dependem de validação com o professor ou com a empresa parceira.

## Pontos a validar com a Bulbe Energia

1. **Entrada do simulador, valor da fatura ou consumo em kWh.** A dúvida já estava registrada na US-02. O frontend hoje coleta **apenas o valor em reais**, no campo rotulado "Valor da sua fatura atual". Por isso, `valor_fatura_centavos` foi modelado como obrigatório e `consumo_kwh` como opcional. Se a Bulbe confirmar que o cálculo correto exige o consumo em kWh, o campo passa a obrigatório e o formulário do frontend precisa de um segundo input, o que impacta também a US-06.

2. **A alíquota de 15% e a faixa de consumo aceita.** O `script.js` usa `DISCOUNT_RATE = 0.15` como constante fixa, mas a demanda D02 do documento do frontend registra a fala "nossa taxa de economia é de até 15%, devido ao frete". O "até" indica que o percentual **varia**, provavelmente por distribuidora ou região. O campo `percentual_desconto` foi incluído na resposta da simulação justamente para que a regra viva no backend, mas a fórmula precisa ser confirmada. A faixa de R$ 50,00 a R$ 5.000,00 é uma estimativa da equipe e precisa de validação.

3. **A memória de cálculo do protótipo.** Os valores de `linhas` e `subtotal` foram extraídos literalmente do HTML de `resultado.html`: CEMIG com 50 kWh a R$ 51,18 e Bulbe Energia com 199 kWh a R$ 199,13, com desconto para R$ 169,26. Não sabemos se o rateio entre distribuidora e Bulbe segue uma regra fixa, se depende da faixa de consumo, ou se aqueles números eram apenas ilustrativos no protótipo. A estrutura do payload suporta N linhas, mas a regra de composição é uma incógnita.

4. **Comportamento na indisponibilidade da CEMIG.** A US-01 já registrava a necessidade de validar isso. Este documento assume devolver o último dado conhecido com `dado_desatualizado: true`, reservando o `503` para quando não há histórico algum. Falta confirmar se existe integração automatizada com a CEMIG ou se a atualização de etapa é manual, feita pela equipe da Bulbe, o que mudaria completamente a natureza do fallback.

5. **Regras de elegibilidade e de uso único dos benefícios.** O campo `condicoes_resgate.tipo` prevê `uso_unico` e `recorrente`, e `exige_pedido_aprovado` reproduz o cadeado das trilhas Movement e Experience. As condições reais de desbloqueio de cada trilha não constam de nenhum documento e foram inferidas dos textos dos cards.

6. **Recompensa do "Indique e ganhe".** O banner promete "R$50 mais prêmios especiais", mas não há definição de quando o crédito é concedido, se na adesão ou no pagamento da primeira fatura do indicado, nem quais são os prêmios das faixas superiores.

## Decisões técnicas da equipe

7. **Convenção de URL base.** Este documento adota `/api/v1`, o que **sobrescreve** a convenção `/v1` declarada no template `modelo-lista-endpoints.md`. A escolha preserva a rastreabilidade, já que `/api/v1` é o prefixo escrito no Documento de Requisitos Técnicos e repetido nas tarefas técnicas de todas as user stories. Ponto a alinhar com o professor.

8. **Rotas, recursos e campos em português.** O Documento de Requisitos Técnicos e as user stories nomearam os endpoints em inglês. Este documento padroniza o português em toda a superfície da API, e a tabela "Mapeamento das rotas citadas nos documentos anteriores" preserva a correspondência. **Consequência prática:** `docs/requisitos.md` e `docs/user-stories.md` citam rotas que não existem mais com aquele nome, e precisam ser atualizados ou passar a referenciar a tabela de mapeamento. Permanecem em inglês apenas nomes padronizados pelo protocolo HTTP, como os cabeçalhos `Authorization` e `Idempotency-Key`, e nomes de marca, como as chaves de trilha `connect`, `movement` e `experience`.

9. **Remoção de verbos das URLs.** Três rotas foram remodeladas para cumprir a convenção de não usar verbo na URL, que o template exige: `simulator/calculate` passou a `POST /simulacoes`, `auth/login` e `auth/logout` passaram a `POST /sessoes` e `DELETE /sessoes`, e `enrollments/{id}/submit` passou a `POST /adesoes/{id}/submissao`. Em todos os casos a ação passou a ser expressa pelo método HTTP ou por um substantivo.

10. **Valores monetários em centavos.** Todo campo monetário é inteiro, em centavos, com sufixo `_centavos`. Evita erro de ponto flutuante e alinha com a função `parseCurrency` do frontend, que já converte a entrada do usuário para centavos antes de dividir por 100.

11. **Textos de interface vindos do backend.** Vários payloads carregam texto pronto para exibição: `rotulos` na simulação, `motivo_bloqueio` nas trilhas, `estado_vazio` nas listagens, `mensagem` no envelope de erro. A decisão atende a dois requisitos ao mesmo tempo. Ao RF-04, porque permite corrigir texto sem novo release, e ao RNF-01, porque garante que o rótulo anunciado pelo leitor de tela seja o mesmo que o backend considera correto para aquele estado. O custo é o acoplamento do backend ao vocabulário da interface, aceito de forma consciente.

12. **Duas rotas para benefícios.** `GET /beneficios` e `GET /trilhas` foram separados porque as duas telas existentes consomem formatos diferentes. `impulsione-fatura.html` renderiza cards de oferta de parceiro, com logo, cor de marca e CTA. `beneficios.html` renderiza cards de trilha, com estado de bloqueio e parceiros em miniatura. Unificar em um único endpoint obrigaria uma das telas a descartar metade do payload.

13. **`anexos` em vez de `faturas` na adesão.** O upload da conta de luz ficou em `POST /adesoes/{id}/anexos` para não colidir com `GET /faturas`, que trata das faturas Bulbe emitidas ao cliente. São dois documentos diferentes, de emissores diferentes, em momentos diferentes da jornada, e usar o mesmo substantivo para os dois seria fonte de erro na implementação.

14. **`estado_vazio` como parte do contrato.** Listagens que alimentam telas com estado vazio dedicado devolvem `200` com `dados` vazio e um objeto `estado_vazio`, nunca `404`. Lista vazia é um estado normal do domínio, não um erro, e essa é a única forma de o frontend distinguir "ainda não homologado" de "homologado sem fatura".

15. **Recursos escopados pelo token, não pela URL.** `GET /pedidos`, `GET /simulacoes`, `GET /resgates`, `GET /faturas`, `GET /indicacoes` e `GET /notificacoes` são sempre filtrados pelo cliente do JWT. Nenhum identificador de cliente aparece em path ou query, o que elimina por construção a classe de falha em que um cliente altera o identificador na URL para ler dados de outro.

## Limitações conhecidas deste documento

16. **Integração com a CEMIG não especificada.** O `GET /pedidos/{id}/status` descreve o contrato exposto ao aplicativo, não a integração que alimenta esse dado. Se a consulta à CEMIG for síncrona, o RNF-02, de resposta abaixo de 400ms, é improvável de ser cumprido, e será necessário um mecanismo de sincronização assíncrona com cache. Esse desenho pertence ao documento de arquitetura, ainda a ser escrito em `docs/arquitetura/`.

17. **Modelo de dados não incluído.** Este documento define o contrato da API, não o esquema do banco. A seção "Entidades do domínio implícitas neste contrato" lista as 19 entidades pressupostas pelos payloads, mas a modelagem lógica e física, com tipos, chaves e índices, pertence a `docs/banco-de-dados/`.

18. **Versionamento e paginação das dicas.** O `GET /ajuda/dicas` não é paginado, sob a premissa de que o volume de dicas por tela é pequeno. Se a ajuda contextual crescer para dezenas de itens por tela, a decisão precisa ser revista.

19. **O RNF-01 não gera endpoint.** A US-06 é uma enabler story e permanece sem endpoint próprio. Sua contribuição a este documento está distribuída nos campos de rótulo e descrição textual dos payloads, listados na tabela de rastreabilidade.

# Próximos passos

1. **Validar as pendências desta seção com a Bulbe Energia**, priorizando os itens 1, 2 e 3, que bloqueiam a implementação do RF-02, e o item 4, que define a arquitetura do RF-01.

2. **Atualizar `docs/requisitos.md` e `docs/user-stories.md`** com os nomes de rota definitivos, ou inserir nos dois arquivos uma referência à tabela de mapeamento desta especificação. Sem isso, a rastreabilidade entre os documentos fica quebrada no nível textual.

3. **Elicitar o requisito de autenticação.** O grupo 2.1 é dependência técnica da própria Sprint 1: sem emissão de JWT, os endpoints protegidos do RF-01 e do RF-03 não podem ser testados de ponta a ponta. Recomenda-se abrir um RF-05 antes do início do desenvolvimento, e não na Sprint 2.

4. **Formalizar este contrato em OpenAPI 3.1**, no arquivo `docs/api/openapi.yaml`, promovendo os objetos recorrentes a schemas reutilizáveis: `Erro`, `Paginacao`, `EstadoVazio`, `MemoriaCalculo`, `EtapaPedido`, `Beneficio`, `Trilha` e `Dica`.

5. **Modelar os casos de uso da API** a partir dos endpoints do Bloco 1, na Modelagem Comportamental prevista na Aula 06.

6. **Definir o modelo de dados** em `docs/banco-de-dados/`, a partir da tabela de entidades deste documento.

7. **Alinhar com o squad de frontend as chaves de `tela` e `elemento`** do `GET /ajuda/dicas`, e registrar a tabela de chaves acordada neste documento. É o único ponto do contrato em que uma string precisa coincidir exatamente entre os dois repositórios.

8. **Priorizar os grupos do Bloco 2 no backlog da Sprint 2**, seguindo a ordem sugerida na coluna de prioridade: autenticação primeiro, por ser bloqueante, depois adesão com envio de fatura, que fecha a jornada do interessado até o pedido.

# Glossário

- **Endpoint:** combinação de método HTTP e caminho que expõe uma operação da API.
- **Idempotência:** propriedade de uma operação que, repetida com a mesma entrada, produz o mesmo resultado sem efeito colateral adicional. Aplicada ao resgate de benefício via cabeçalho `Idempotency-Key`.
- **Memória de cálculo:** detalhamento dos valores intermediários que justificam o resultado da simulação, exigido pelo critério de aceite 1 da US-02.
- **Estado vazio:** resposta bem-sucedida que informa a ausência de dados junto com o motivo e a ação sugerida, em vez de devolver erro ou lista sem contexto.
- **Enabler story:** história derivada de requisito não funcional, que condiciona a aceitação das demais sem entregar funcionalidade própria.
- **Dica contextual:** texto de ajuda associado a uma tela ou campo, apresentado pelo mascote Bulbinho. Corresponde ao que os documentos anteriores chamavam de *tooltip*.
- **Trilha:** agrupamento de benefícios do clube, com regra própria de desbloqueio. Bulbe Connect, Bulbe Movement e Bulbe Experience.
- **JWT (JSON Web Token):** formato de token assinado usado para autenticar requisições, exigido pelo RNF-03.
- **LGPD:** Lei Geral de Proteção de Dados, Lei 13.709/2018, que rege o tratamento dos dados pessoais e das faturas manipulados por esta API.
