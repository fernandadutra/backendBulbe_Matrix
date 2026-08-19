# Documento de User Stories, [Bulbe Matrix]

## Identificação

- **Projeto:** [Bulbe Evolution]
- **Empresa parceira:** [Bulbe Energia]
- **Equipe:** [Squad Matrix]
- **Integrantes:** [Augusto Gama], [Felipe Lara], [Fernanda Dutra], [Leandro Dias], [Mariana Maia] e [Rafael Bentes]
- **Data:** [__/__/2026]
- **Sprint / Etapa:** [Sprint 1, Elicitação]
- **Documento de origem:** Documento de Requisitos Técnicos, Bulbe Matrix

## Como este documento foi construído

As user stories abaixo foram derivadas dos requisitos funcionais e não funcionais levantados no Documento de Requisitos Técnicos.
Cada requisito técnico foi reescrito sob a perspectiva do usuário final, explicitando a persona envolvida, a ação desejada e o valor gerado, de forma que as tarefas de backend passem a ser rastreáveis a partir de uma necessidade concreta de negócio.
[Complementar com o critério que a equipe adotou para quebrar ou agrupar histórias.]

## Personas

| ID | Persona | Descrição | Principais necessidades |
|---|---|---|---|
| P-01 | [Lead / Interessado] | [Ainda não aderiu; está avaliando a proposta de valor] | [Simular economia, entender o processo, se cadastrar] |
| P-02 | [Cliente aderido] | [Já enviou fatura e assinou; aguarda ou já usa o serviço] | [Acompanhar homologação, usar benefícios] |
| P-03 | [Usuário com deficiência visual] | [Navega por leitor de tela] | [Percorrer todas as jornadas sem depender de visão] |
| P-04 | [Usuário com baixa familiaridade digital] | [Tem dúvidas sobre termos técnicos do setor elétrico e sobre o processo de adesão] | [Entender cada campo e etapa sem sair do app] |

## Índice de rastreabilidade

| User Story | Título | Requisito(s) de origem | Persona | Prioridade | Estimativa |
|---|---|---|---|---|---|
| US-01 | Acompanhar status da homologação | RF-01 | P-02 | Alta | [ ] |
| US-02 | Simular economia antes de aderir | RF-02 | P-01 | Alta | [ ] |
| US-03 | Consultar benefícios disponíveis | RF-03 | P-02 | Média | [ ] |
| US-04 | Resgatar um benefício | RF-03 | P-02 | Média | [ ] |
| US-05 | Receber ajuda contextual do Bulbinho | RF-04 | P-04 | Média | [ ] |
| US-06 | Navegar o app por leitor de tela e teclado | RNF-01 | P-03 | Alta | [ ] |

Os requisitos RNF-02 (tempo de resposta) e RNF-03 (segurança e LGPD) não geraram histórias próprias por serem critérios transversais; estão contemplados na Definition of Done e nos critérios de aceite das histórias afetadas.

---

## US-01, Acompanhar status da homologação

**Requisito de origem:** RF-01
**Persona:** P-02, Cliente aderido
**Prioridade:** Alta

> Como **cliente que já aderiu ao plano**, quero **visualizar em que etapa está minha homologação na CEMIG**, para que **eu saiba quanto falta e não precise acionar o suporte durante os 90 a 120 dias de espera**.

**Critérios de aceite**

1. **Dado** que sou um cliente autenticado com pedido em andamento, **quando** abro a tela de acompanhamento, **então** visualizo a etapa atual destacada, as etapas já concluídas e a previsão da próxima atualização.
2. **Dado** que meu pedido está em análise, **quando** a tela carrega, **então** a resposta é retornada em menos de 400ms.
3. **Dado** que o serviço externo está indisponível, **quando** consulto o status, **então** recebo a última informação conhecida acompanhada da data da consulta, em vez de uma tela de erro.
4. **Dado** que navego por leitor de tela, **quando** percorro a linha do tempo, **então** cada etapa é anunciada com seu nome e situação.

**Tarefas técnicas**

- [ ] Implementar `GET /api/v1/orders/{id}/status`
- [ ] Modelar payload de etapas (concluídas, em andamento, previsão)
- [ ] Persistir e retornar última consulta bem-sucedida como fallback
- [ ] Validar autorização por JWT

**RNFs aplicáveis:** RNF-01, RNF-02, RNF-03
**Dependências:** [ ]
**Observações:** [Validar com a Bulbe o comportamento esperado quando a consulta externa falha.]

---

## US-02, Simular economia antes de aderir

**Requisito de origem:** RF-02
**Persona:** P-01, Lead / Interessado
**Prioridade:** Alta

> Como **lead, que ainda não aderiu ao plano**, quero **informar o meu consumo mensal**, para que **eu receba uma estimativa de quanto eu economizaria com a Bulbe**.

**Critérios de aceite**

1. **Dado** que informo meu consumo médio mensal, **quando** solicito a simulação, **então** visualizo a estimativa de economia mensal e anual acompanhada da memória de cálculo que justifica os valores.
2. **Dado** que informo um consumo fora da faixa aceita (zero, negativo ou acima do limite previsto), **quando** solicito a simulação, **então** recebo uma mensagem indicando o intervalo válido e o cálculo não é executado.
3. **Dado** que a simulação foi solicitada com dados válidos, **quando** o resultado é processado, **então** a resposta é retornada em menos de 400ms.
4. **Dado** que ainda não possuo cadastro, **quando** solicito a simulação, **então** consigo obter o resultado sem precisar criar conta.
5. **Dado** que navego por leitor de tela, **quando** o resultado é exibido, **então** cada valor é anunciado junto ao seu rótulo (economia mensal, economia anual).

**Tarefas técnicas**

- [ ] Implementar `POST /api/v1/simulator/calculate`
- [ ] Definir schema de entrada e validação da faixa de consumo aceita
- [ ] Estruturar payload da memória de cálculo para renderização no frontend
- [ ] [ ]

**RNFs aplicáveis:** RNF-01, RNF-02
**Dependências:** [ ]
**Observações:** [Confirmar com a Bulbe quais parâmetros de entrada o simulador recebe: kWh, valor da fatura, ou ambos.]

---

## US-03, Consultar benefícios disponíveis

**Requisito de origem:** RF-03
**Persona:** P-02, Cliente aderido
**Prioridade:** Média

> Como **cliente que já aderiu ao plano**, quero **consultar os benefícios disponiveis, com regras de uso, validade e condições de resgate**, para que **eu entenda qual são as vantagens de aderir à Bulbe**.

**Critérios de aceite**

1. **Dado** que sou um cliente autenticado, **quando** acesso o Clube de Benefícios, **então** visualizo as empresas parceiras com seus benefícios ativos, regras de uso, validade e condições de resgate.
2. **Dado** que um benefício está expirado ou foi desativado pelo parceiro, **quando** a lista é carregada, **então** ele não aparece entre os benefícios disponíveis.
3. **Dado** que não há nenhum benefício ativo no momento, **quando** acesso a área, **então** recebo uma mensagem de estado vazio explicando a situação, em vez de uma tela em branco.
4. **Dado** que navego por leitor de tela, **quando** percorro a lista, **então** cada item é anunciado com nome do parceiro, benefício e prazo de validade.

**Tarefas técnicas**

- [ ] Implementar `GET /api/v1/benefits`
- [ ] Modelar entidade de benefício (parceiro, regras, validade, condições de resgate)
- [ ] Filtrar benefícios inativos ou expirados na consulta
- [ ] [ ]

**RNFs aplicáveis:** RNF-01, RNF-03
**Dependências:** [ ]
**Observações:** [ ]

---

## US-04, Resgatar um benefício

**Requisito de origem:** RF-03
**Persona:** P-02, Cliente aderido
**Prioridade:** Média

> Como **cliente que já aderiu ao plano**, quero **resgatar um benefício**, para que **eu tenho acesso e coloque eu uso os benefícios disponíveis**.

**Critérios de aceite**

1. **Dado** que visualizo um benefício ativo e atendo às condições de resgate, **quando** confirmo a utilização, **então** o uso é registrado e recebo a confirmação com as instruções ou código necessários para usufruir.
2. **Dado** que já utilizei um benefício de uso único, **quando** tento resgatá-lo novamente, **então** a ação é bloqueada com uma mensagem explicando o motivo.
3. **Dado** que o benefício expirou entre a exibição da lista e a minha confirmação, **quando** confirmo o resgate, **então** a operação é recusada e a lista é atualizada.
4. **Dado** que ocorre uma falha no registro do resgate, **quando** confirmo a utilização, **então** nenhum uso é contabilizado e posso tentar novamente.

**Tarefas técnicas**

- [ ] Implementar endpoint de registro de utilização de benefício
- [ ] Garantir idempotência ou controle de uso único por cliente
- [ ] Revalidar validade e elegibilidade no momento da confirmação
- [ ] [ ]

**RNFs aplicáveis:** RNF-03
**Dependências:** US-03
**Observações:** [Separada da US-03 por se tratar de uma jornada distinta, com escrita de dados e regras próprias de elegibilidade.]

---

## US-05, Receber ajuda contextual do Bulbinho

**Requisito de origem:** RF-04
**Persona:** P-04, Usuário com baixa familiaridade digital
**Prioridade:** Média

> Como **usuário com baixa familiaridade digital**, quero **receber ajuda contextual do Bulbinho**, para que **eu possa entender bem quais são os termos e etapas do setor elétrico bem como usar o app da Bulbe, sem precisar sair do próprio app**.

**Critérios de aceite**

1. **Dado** que estou em uma tela com ajuda contextual disponível, **quando** aciono o Bulbinho, **então** visualizo o texto de ajuda correspondente àquela tela, campo ou funcionalidade.
2. **Dado** que a equipe atualiza o conteúdo de um tooltip, **quando** abro o aplicativo novamente, **então** visualizo o texto atualizado sem precisar instalar uma nova versão.
3. **Dado** que não existe conteúdo cadastrado para determinado campo, **quando** a tela é carregada, **então** o ícone de ajuda não é exibido, evitando um tooltip vazio.
4. **Dado** que navego por teclado ou leitor de tela, **quando** aciono a ajuda, **então** o conteúdo é alcançável e anunciado corretamente.

**Tarefas técnicas**

- [ ] Implementar `GET /api/v1/help/tooltips`
- [ ] Definir chave de associação entre tooltip e tela/campo do frontend
- [ ] Permitir atualização de conteúdo sem novo release do aplicativo
- [ ] [ ]

**RNFs aplicáveis:** RNF-01
**Dependências:** [ ]
**Observações:** [ ]

---

## US-06, Navegar o app por leitor de tela e teclado

**Requisito de origem:** RNF-01
**Persona:** P-03, Usuário com deficiência visual
**Prioridade:** Alta

> Como **usuário com deficiência visual**, quero **percorrer todas as telas e concluir qualquer jornada usando apenas teclado e leitor de tela**, para que **eu possa acompanhar a minha homologação, simular minhas economias e resgatar meus benefícios sem depender de terceiros**.

**Critérios de aceite**

1. **Dado** que navego por teclado, **quando** percorro qualquer tela, **então** o foco é sempre visível e a ordem de tabulação segue a ordem lógica de leitura.
2. **Dado** que utilizo leitor de tela, **quando** alcanço um componente interativo, **então** ele é anunciado com um rótulo semântico que descreve sua função.
3. **Dado** que a interface é auditada, **quando** o contraste entre texto e fundo é medido, **então** atende à razão mínima exigida pela WCAG no nível adotado pela equipe.
4. **Dado** que existem imagens ou ícones que transmitem informação, **quando** a tela é lida, **então** cada um possui texto alternativo descritivo.

**Tarefas técnicas**

- [ ] Definir o nível WCAG adotado como meta pela equipe (A, AA ou AAA)
- [ ] Estabelecer checklist de acessibilidade na revisão de código
- [ ] [ ]

**Dependências:** [ ]
**Observações:** [Enabler story: não entrega funcionalidade nova, mas condiciona a aceitação de todas as demais.]

---

## Lacunas identificadas, candidatas à Sprint 2

Durante a redação das user stories, a equipe identificou que duas funcionalidades mapeadas no frontend do Projeto Ciência de Dados I não geraram requisitos técnicos correspondentes na Sprint 1. Como não há requisito de origem, essas histórias não foram escritas neste documento e ficam registradas como backlog para a próxima etapa.

| Funcionalidade do frontend | Lacuna | Encaminhamento sugerido |
|---|---|---|
| Formulário de Cadastro/Adesão com Envio de Faturas | Não existe RF descrevendo o upload, a validação e o armazenamento do arquivo de fatura, embora o RNF-03 já preveja a proteção desses documentos | Elicitar requisito na Sprint 2 e derivar a user story correspondente |
| Tela de Onboarding Didático | Não existe RF descrevendo a origem e a atualização do conteúdo das telas de onboarding | Avaliar se o conteúdo é estático no aplicativo ou servido pela API |

---

## Definition of Done do Squad

Critérios transversais que se aplicam a **todas** as histórias e não precisam ser repetidos individualmente:

- [ ] Endpoint documentado na especificação OpenAPI/Swagger
- [ ] Tráfego exclusivamente via HTTPS/TLS (RNF-03)
- [ ] Rotas protegidas exigem token JWT válido (RNF-03)
- [ ] Dados pessoais e faturas tratados conforme a LGPD (RNF-03)
- [ ] Componentes de interface aderentes às diretrizes WCAG (RNF-01)
- [ ] Tempo de resposta abaixo de 400ms nas consultas de status e simulação (RNF-02)
- [ ] Testes automatizados cobrindo caminho feliz e caminho infeliz
- [ ] Revisão de código aprovada por ao menos um integrante do squad

## Checklist INVEST

Aplicar a cada história antes de fechar a sprint de elicitação:

| Critério | Verificação |
|---|---|
| **I**ndependent | A história pode ser desenvolvida sem depender da conclusão de outra? |
| **N**egotiable | O texto descreve a necessidade, e não uma solução técnica fechada? |
| **V**aluable | Existe um "para que" que faz sentido para o usuário ou para o negócio? |
| **E**stimable | A equipe tem informação suficiente para estimar o esforço? |
| **S**mall | A história cabe em uma sprint? Se não, quebrar. |
| **T**estable | Os critérios de aceite permitem dizer objetivamente se está pronto? |

## Glossário

- **User Story:** descrição curta de uma funcionalidade sob a perspectiva de quem recebe o valor, no formato "Como... quero... para que...".
- **Critério de aceite:** condição verificável que define quando a história pode ser considerada concluída.
- **Enabler story:** história derivada de requisito não funcional ou de trabalho técnico habilitador, sem entrega direta de funcionalidade nova.
- **Caminho infeliz:** cenário de exceção (erro, dado inválido, indisponibilidade) que a história também precisa tratar.
- **Definition of Done:** conjunto de critérios que toda entrega do squad precisa cumprir, independentemente da história.