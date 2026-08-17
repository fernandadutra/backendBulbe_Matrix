\# Documento de User Stories, \[Bulbe Matrix]

&#x20;

\## Identificação

&#x20;

\- \*\*Projeto:\*\* \[Bulbe Evolution]

\- \*\*Empresa parceira:\*\* \[Bulbe Energia]

\- \*\*Equipe:\*\* \[Squad Matrix]

\- \*\*Integrantes:\*\* \[Augusto Gama], \[Felipe Lara], \[Fernanda Dutra], \[Leandro Dias], \[Mariana Maia] e \[Rafael Bentes]

\- \*\*Data:\*\* \[\_\_/\_\_/2026]

\- \*\*Sprint / Etapa:\*\* \[Sprint 1, Elicitação]

\- \*\*Documento de origem:\*\* Documento de Requisitos Técnicos, Bulbe Matrix

\## Como este documento foi construído

&#x20;

As user stories abaixo foram derivadas dos requisitos funcionais e não funcionais levantados no Documento de Requisitos Técnicos.

Cada requisito técnico foi reescrito sob a perspectiva do usuário final, explicitando a persona envolvida, a ação desejada e o valor gerado, de forma que as tarefas de backend passem a ser rastreáveis a partir de uma necessidade concreta de negócio.

\[Complementar com o critério que a equipe adotou para quebrar ou agrupar histórias.]

&#x20;

\## Personas

&#x20;

| ID | Persona | Descrição | Principais necessidades |

|---|---|---|---|

| P-01 | \[Lead / Interessado] | \[Ainda não aderiu; está avaliando a proposta de valor] | \[Simular economia, entender o processo, se cadastrar] |

| P-02 | \[Cliente aderido] | \[Já enviou fatura e assinou; aguarda ou já usa o serviço] | \[Acompanhar homologação, usar benefícios] |

| P-03 | \[Usuário com deficiência visual] | \[Navega por leitor de tela] | \[Percorrer todas as jornadas sem depender de visão] |

| P-04 | \[ ] | \[ ] | \[ ] |

&#x20;

\## Índice de rastreabilidade

&#x20;

| User Story | Requisito(s) de origem | Persona | Prioridade | Estimativa |

|---|---|---|---|---|

| US-01 | RF-01 | P-02 | Alta | \[ ] |

| US-02 | RF-02 | \[P-01] | \[Alta] | \[ ] |

| US-03 | RF-03 | \[P-02] | \[Média] | \[ ] |

| US-04 | RF-03 | \[P-02] | \[Média] | \[ ] |

| US-05 | RF-04 | \[ ] | \[Média] | \[ ] |

| US-06 | RNF-01 | \[P-03] | \[Alta] | \[ ] |

| US-07 | \[ ] | \[ ] | \[ ] | \[ ] |

&#x20;

\---

&#x20;

\## US-01, Acompanhar status da homologação

&#x20;

\*\*Requisito de origem:\*\* RF-01

\*\*Persona:\*\* P-02, Cliente aderido

\*\*Prioridade:\*\* Alta

\*\*Estimativa:\*\* \[ ]

&#x20;

> Como \*\*cliente que já aderiu ao plano\*\*, quero \*\*visualizar em que etapa está minha homologação na CEMIG\*\*, para que \*\*eu saiba quanto falta e não precise acionar o suporte durante os 90 a 120 dias de espera\*\*.

&#x20;

\*\*Critérios de aceite\*\*

&#x20;

1\. \*\*Dado\*\* que sou um cliente autenticado com pedido em andamento, \*\*quando\*\* abro a tela de acompanhamento, \*\*então\*\* visualizo a etapa atual destacada, as etapas já concluídas e a previsão da próxima atualização.

2\. \*\*Dado\*\* que meu pedido está em análise, \*\*quando\*\* a tela carrega, \*\*então\*\* a resposta é retornada em menos de 400ms.

3\. \*\*Dado\*\* que o serviço externo está indisponível, \*\*quando\*\* consulto o status, \*\*então\*\* recebo a última informação conhecida acompanhada da data da consulta, em vez de uma tela de erro.

4\. \*\*Dado\*\* que navego por leitor de tela, \*\*quando\*\* percorro a linha do tempo, \*\*então\*\* cada etapa é anunciada com seu nome e situação.

\*\*Tarefas técnicas\*\*

&#x20;

\- \[ ] Implementar `GET /api/v1/orders/{id}/status`

\- \[ ] Modelar payload de etapas (concluídas, em andamento, previsão)

\- \[ ] Persistir e retornar última consulta bem-sucedida como fallback

\- \[ ] Validar autorização por JWT

\*\*RNFs aplicáveis:\*\* RNF-01, RNF-02, RNF-03

\*\*Dependências:\*\* \[ ]

\*\*Observações:\*\* \[ ]

&#x20;

\---

&#x20;

\## US-02, \[Título curto da história]

&#x20;

\*\*Requisito de origem:\*\* RF-02

\*\*Persona:\*\* \[ ]

\*\*Prioridade:\*\* \[ ]

\*\*Estimativa:\*\* \[ ]

&#x20;

> Como \*\*\[persona]\*\*, quero \*\*\[ação]\*\*, para que \*\*\[benefício]\*\*.

&#x20;

\*\*Critérios de aceite\*\*

&#x20;

1\. \*\*Dado\*\* \[contexto inicial], \*\*quando\*\* \[ação do usuário], \*\*então\*\* \[resultado observável].

2\. \*\*Dado\*\* \[ ], \*\*quando\*\* \[ ], \*\*então\*\* \[ ].

3\. \*\*Dado\*\* \[caminho infeliz: dado inválido, ausente ou fora da faixa esperada], \*\*quando\*\* \[ ], \*\*então\*\* \[ ].

4\. \*\*Dado\*\* \[critério derivado de RNF, se aplicável], \*\*quando\*\* \[ ], \*\*então\*\* \[ ].

\*\*Tarefas técnicas\*\*

&#x20;

\- \[ ] \[ ]

\- \[ ] \[ ]

\- \[ ] \[ ]

\*\*RNFs aplicáveis:\*\* \[ ]

\*\*Dependências:\*\* \[ ]

\*\*Observações:\*\* \[ ]

&#x20;

\---

&#x20;

\## US-03, \[Título curto da história]

&#x20;

\*\*Requisito de origem:\*\* RF-03

\*\*Persona:\*\* \[ ]

\*\*Prioridade:\*\* \[ ]

\*\*Estimativa:\*\* \[ ]

&#x20;

> Como \*\*\[persona]\*\*, quero \*\*\[ação]\*\*, para que \*\*\[benefício]\*\*.

&#x20;

\*\*Critérios de aceite\*\*

&#x20;

1\. \*\*Dado\*\* \[ ], \*\*quando\*\* \[ ], \*\*então\*\* \[ ].

2\. \*\*Dado\*\* \[ ], \*\*quando\*\* \[ ], \*\*então\*\* \[ ].

3\. \*\*Dado\*\* \[caminho infeliz], \*\*quando\*\* \[ ], \*\*então\*\* \[ ].

\*\*Tarefas técnicas\*\*

&#x20;

\- \[ ] \[ ]

\- \[ ] \[ ]

\*\*RNFs aplicáveis:\*\* \[ ]

\*\*Dependências:\*\* \[ ]

\*\*Observações:\*\* \[ ]

&#x20;

\---

&#x20;

\## US-04, \[Título curto da história]

&#x20;

\*\*Requisito de origem:\*\* RF-03

\*\*Persona:\*\* \[ ]

\*\*Prioridade:\*\* \[ ]

\*\*Estimativa:\*\* \[ ]

&#x20;

> Como \*\*\[persona]\*\*, quero \*\*\[ação]\*\*, para que \*\*\[benefício]\*\*.

&#x20;

\*\*Critérios de aceite\*\*

&#x20;

1\. \*\*Dado\*\* \[ ], \*\*quando\*\* \[ ], \*\*então\*\* \[ ].

2\. \*\*Dado\*\* \[ ], \*\*quando\*\* \[ ], \*\*então\*\* \[ ].

3\. \*\*Dado\*\* \[caminho infeliz], \*\*quando\*\* \[ ], \*\*então\*\* \[ ].

\*\*Tarefas técnicas\*\*

&#x20;

\- \[ ] \[ ]

\- \[ ] \[ ]

\*\*RNFs aplicáveis:\*\* \[ ]

\*\*Dependências:\*\* \[ ]

\*\*Observações:\*\* \[ ]

&#x20;

\---

&#x20;

\## US-05, \[Título curto da história]

&#x20;

\*\*Requisito de origem:\*\* RF-04

\*\*Persona:\*\* \[ ]

\*\*Prioridade:\*\* \[ ]

\*\*Estimativa:\*\* \[ ]

&#x20;

> Como \*\*\[persona]\*\*, quero \*\*\[ação]\*\*, para que \*\*\[benefício]\*\*.

&#x20;

\*\*Critérios de aceite\*\*

&#x20;

1\. \*\*Dado\*\* \[ ], \*\*quando\*\* \[ ], \*\*então\*\* \[ ].

2\. \*\*Dado\*\* \[ ], \*\*quando\*\* \[ ], \*\*então\*\* \[ ].

3\. \*\*Dado\*\* \[caminho infeliz], \*\*quando\*\* \[ ], \*\*então\*\* \[ ].

\*\*Tarefas técnicas\*\*

&#x20;

\- \[ ] \[ ]

\- \[ ] \[ ]

\*\*RNFs aplicáveis:\*\* \[ ]

\*\*Dependências:\*\* \[ ]

\*\*Observações:\*\* \[ ]

&#x20;

\---

&#x20;

\## US-06, \[Enabler story, derivada de RNF]

&#x20;

\*\*Requisito de origem:\*\* RNF-\[ ]

\*\*Persona:\*\* \[ ]

\*\*Prioridade:\*\* \[ ]

\*\*Estimativa:\*\* \[ ]

&#x20;

> Como \*\*\[persona]\*\*, quero \*\*\[característica de qualidade percebida pelo usuário]\*\*, para que \*\*\[benefício]\*\*.

&#x20;

\*\*Critérios de aceite\*\*

&#x20;

1\. \*\*Dado\*\* \[ ], \*\*quando\*\* \[ ], \*\*então\*\* \[ ].

2\. \*\*Dado\*\* \[ ], \*\*quando\*\* \[ ], \*\*então\*\* \[ ].

\*\*Tarefas técnicas\*\*

&#x20;

\- \[ ] \[ ]

\- \[ ] \[ ]

\*\*Dependências:\*\* \[ ]

\*\*Observações:\*\* \[ ]

&#x20;

\---

&#x20;

\## Definition of Done do Squad

&#x20;

Critérios transversais que se aplicam a \*\*todas\*\* as histórias e não precisam ser repetidos individualmente:

&#x20;

\- \[ ] Endpoint documentado na especificação OpenAPI/Swagger

\- \[ ] Tráfego exclusivamente via HTTPS/TLS (RNF-03)

\- \[ ] Rotas protegidas exigem token JWT válido (RNF-03)

\- \[ ] Dados pessoais e faturas tratados conforme a LGPD (RNF-03)

\- \[ ] Componentes de interface aderentes às diretrizes WCAG (RNF-01)

\- \[ ] Tempo de resposta abaixo de 400ms nas consultas de status e simulação (RNF-02)

\- \[ ] Testes automatizados cobrindo caminho feliz e caminho infeliz

\- \[ ] Revisão de código aprovada por ao menos um integrante do squad

\## Checklist INVEST

&#x20;

Aplicar a cada história antes de fechar a sprint de elicitação:

&#x20;

| Critério | Verificação |

|---|---|

| \*\*I\*\*ndependent | A história pode ser desenvolvida sem depender da conclusão de outra? |

| \*\*N\*\*egotiable | O texto descreve a necessidade, e não uma solução técnica fechada? |

| \*\*V\*\*aluable | Existe um "para que" que faz sentido para o usuário ou para o negócio? |

| \*\*E\*\*stimable | A equipe tem informação suficiente para estimar o esforço? |

| \*\*S\*\*mall | A história cabe em uma sprint? Se não, quebrar. |

| \*\*T\*\*estable | Os critérios de aceite permitem dizer objetivamente se está pronto? |

&#x20;

\## Glossário

&#x20;

\- \*\*User Story:\*\* descrição curta de uma funcionalidade sob a perspectiva de quem recebe o valor, no formato "Como... quero... para que...".

\- \*\*Critério de aceite:\*\* condição verificável que define quando a história pode ser considerada concluída.

\- \*\*Enabler story:\*\* história derivada de requisito não funcional ou de trabalho técnico habilitador, sem entrega direta de funcionalidade nova.

\- \*\*Caminho infeliz:\*\* cenário de exceção (erro, dado inválido, indisponibilidade) que a história também precisa tratar.

\- \*\*Definition of Done:\*\* conjunto de critérios que toda entrega do squad precisa cumprir, independentemente da história.

