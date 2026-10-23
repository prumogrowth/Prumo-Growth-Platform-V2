# S1-002 — matriz de aderência documental, precedência e gates
**Base: 22/10/2026; A2 atualizada em 23/10/2026 (I51) | Escopo: revisão da própria frente S1-002; documentação, sem alteração funcional.** Ler com [contrato vigente](S1_002_01_CONTRATO_FUNCIONAL_VIGENTE_2026_10_22.md). "Coberto no contrato" significa apenas **escrito corretamente na S1**, não implementado.

## A. Rastreabilidade das decisões

| ID | Decisão/contrato | Fonte de decisão | Registro na S1 | Situação documental e risco técnico |
| --- | --- | --- | --- | --- |
| S1-D01 | **Produto bancário Libera Credi ≠ plataforma**, aplicação ainda sem nome | Responsável 22/10; WDC-01; AL-IA-00 | 01 §1; doc nomenclatura | **Coberto [D]**; não chamar o sistema de LiberaCred |
| S1-D02 | Diretor / Gestor / Consultor; competências não mudam pela troca de nome | Responsável 21/10; WA-21; S0-045; D-NOM-01 | 01 §§1–2; nomenclatura | **Coberto [D]**; código/DB legado permanece |
| S1-D03 | Diretoria administra contas/grants; Gestor coordena equipe, não lojas como cargo | Issue #10; I11 ratificado | 01 §2 | **Coberto [D]**; matrícula/grants físicos em evolução |
| S1-D04 | **Um gestor principal ativo por Consultor** | Decisão direta D1 da conversa S1 | 01 §2 | **Coberto [D]**; I11 antigo ainda etiquetava hipótese [P] |
| S1-D05 | Gestor vê casos/histórico/cargas da equipe, não envia enquanto outro é titular; não vê outros times | Decisão direta C3, S1 | 01 §§2,7 | **Coberto [D]**; implementar RLS D2, evitar extrapolação D3/D4 |
| S1-D06 | Pausa intake global ao Consultor sem suspender conta, sem justificativa, sem revogar grants/acesso | Issue #10; S0-043; FV D-AL-01 | 01 §3 | **Coberto [D]**; I11/migration 048 e seus testes são históricos |
| S1-D07 | **Novos leads cross-team**, com concessão e disponibilidade | FV D-AL-05; S0-044 | 01 §4 | **Coberto [DN]**; não aplicar filtro same-team ao fluxo regular |
| S1-D08 | Lead novo sem elegível = **fila sem titular** visível a Gestores autorizados à loja; assunção exclusiva | FV D-AL-06; S0-044 | 01 §4 | **Coberto [DN]**; APIs/RLS/concorrência [R/T] |
| S1-D09 | Retorno de elegível volta a distribuir **somente leads ainda sem titular** | FV D-AL-07; S0-044 | 01 §4 | **Coberto [DN]**; CAS e lock [R/T] |
| S1-D10 | Caso já atribuído a pausado sem contato humano: redistribuir **mesma equipe com grant**; sem destino mantém titular | Issue #10; I54; FV D-AL-02 | 01 §4 | **Coberto [D]**; I54 simulado, não integração real |
| S1-D11 | Contato humano inicia com interação de humano confirmada; não pela IA/abertura; não aceitar ligação manual como prova | FV D-AL-04; S0-044 | 01 §5 | **Coberto [DN]**; produtor/critério físico pendentes |
| S1-D12 | Manual dentro da equipe sem grant da loja exige exceção revogável **por caso** | Issue #10; FV D-AL-03; I35 | 01 §5 | **Coberto [D]**; caso especial, anexos e GoTrue não homologados |
| S1-D13 | Exceção encerra na troca de titular, saída/bloqueio, revogação emergencial; conclusão isolada não corta leitura enquanto autorizado | B1 aprovada na conversa S1 | 01 §5 | **Coberto [D]**; recuperação pós-revogação e prazo físico [R] |
| S1-D14 | **A2**: **proibido** transferir ou atribuir novo lead/atendimento a Consultor com intake pausado, em qualquer caminho | Decisão direta do responsável 23/10/2026 (I51) | 01 §§3–5,11 | **[D] FECHADA**; I35 já negava experimentalmente, testar normal/excepcional, concorrência e S0 real [R/T] |
| S1-D15 | Indicador único COUNT/DOT/NONE; leitura individual por novo titular e gestor independente | C1, C2; Issue #10; I36 | 01 §6 | **Coberto [D]**; I36 antiga ainda não modela regra inteira |
| S1-D16 | **Template sistêmico NÃO limpa** o alerta; novo inbound acumula; saída iniciada pelo Consultor (inclusive template), **entregue**, encerra pendência | Correção direta do responsável na conversa S1, 21/10 | 01 §6 | **Coberto [D]**; conflito com I36 que usa saída humana sintética |
| S1-D17 | Encerramento humano confirmado reseta atenção do segmento; retorno inicia acompanhamento novo, histórico intocado | Correção direta do responsável na conversa S1 | 01 §§6,8 | **Coberto [D]**; evento/segmentação S0↔S1 [R/T] |
| S1-D18 | Consultor titular lê histórico **completo do mesmo contato/loja**, mesmo antigo, sem carteira alheia | Correção direta do responsável S1; AL-IA-01 §4 | 01 §7 | **Coberto [D]**; I35 prova apenas acesso por caso, gap RLS |
| S1-D19 | Gestor vê dados da equipe; fila compartilhada por loja não libera casos de outras equipes | Decisão S1 C3 + FV D-AL-06 | 01 §§2,4,7 | **Coberto [D/DN]**; cruzamento de escopos S0/RLS [R] |
| S1-D20 | F01 não sabe escala/grants, roteamento pertence ao núcleo | FV D-AL-08; S0-044; AL-IA-01 | 01 §4 | **Coberto [DN]**; controle de dados de prompts depende S0/OpenAI |
| S1-D21 | Conclusão explícita aciona F03; janela Meta, ciclo comercial e fechamento são coisas distintas | AL-IA-01 §§4,6; S0/CFI-01 | 01 §8 | **Coberto [DN]**; gateway e evento físico ainda não integrados |
| S1-D22 | Consultor não edita diretamente ficha; F03/S0 administram atualização | AL-IA-01; AL-IA-04 DEL-01 | 01 §8 | **Coberto [DN]**, mas contratos S0/D41 antigos divergem; harmonização física [R] |
| S1-D23 | Pendência F03 volta ao Consultor original, senão seu Gestor; pausa intake não o torna indisponível para casos próprios | AL-IA-01 §4 | 01 §8 | **Coberto [DN]**; roteamento de tarefa e permissão [R] |
| S1-D24 | Venda requer decisão humana e prova Banco; perda contextual F03 sob guardas S0; ficha contínua e remessas históricas | AL-IA-01 §§4–6 | 01 §8 | **Coberto [DN/E]**, transições físicas S0 e Banco [R/V] |
| S1-D25 | WhatsApp: assinatura humana visível papel+nome, IA sem assinatura, template sem prefixo arbitrário | Meta WA-21/WDC-21 | 01 §9 | **Coberto [D]**; autoria/S0/Meta futura |
| S1-D26 | Estado SENT ≠ DELIVERED; sent que reinicia contador técnico WA-18C não apaga bolinha operacional | Meta WDC-13/20; correção S1 | 01 §§6,9 | **Coberto [D]**; correlação real de entrega [R] |
| S1-D27 | Diretor MCP requer dupla confirmação, não altera software nem audit log protegido | AL-IA-03; WA WDC-05 | 01 §§2,10 | **Coberto apenas como limite de RBAC [DN]**, implementação outra frente |
| S1-D28 | 8 estados comerciais e isolamento por loja; sem acesso cruzado de clientes | S0 D-ORG-01; AL-IA-01; Meta DEC-WA-05 | 01 §§1,7–9 | **Coberto [E]**, RLS/provas ainda futuros |

## B. Mapa de fontes e condições de precedência

| Documento S1 existente | Leitura segura a partir de 22/10/2026 |
| --- | --- |
| I10 — matriz de autoridades por loja (19/10) | Histórico parcialmente superado por I11/Issue #10 e pelo contrato 01: gestor por equipe, não por loja; nomenclatura nova |
| I11 — pausa global 048 (19/10) | **Não** aplicar descrição de conta suspensa, redistribuição de TODOS os casos ou perda de leitura à pausa intake. Migração/testes antigos seguem evidência histórica |
| I12 — transferência comum 049/050 (19/10) | Exigência de grant geral vale para via **normal**; via excepcional por caso exige gate e isolamento específicos. Exceção I35 apenas sandbox; destino pausado sempre inelegível [D/A2] |
| I35 — exceção RLS por caso | Prova exclusivamente do **caso atribuído**; não prova autorização de ler todo o histórico do **mesmo contato**. A2 fechada [D] proibindo destino pausado; revogação e visibilidade pós-fecho exigem contratos |
| I36 — indicador único | **Regra antiga**: DOT some com saída humana inserida em fixture; agora **origem humana efetiva + entrega**, nenhuma mensagem sistêmica resolve, segmento encerrado reseta, novo titular tem leitura própria |
| I37 — gateway intake assinado | Apenas novo comando intake na instância de teste e CAS/GoTrue local; não demonstra fila cross-team, contato Meta real, recontato, F03 nem produto implantado |
| Testes/S1_ACEITE.md | Registra ensaios e SHAs; **não** serve para revogar decisão de negócio posterior nem comprovar funções externas ou produção |
| Marco de pausa 20/10 | Tem perguntas A1, C1, C2 e D1 **históricas**; foram respondidas depois. A2 foi fechada por decisão direta posterior em 23/10 (I51); usar o índice 00 e contrato 01 para saber estado atual |
| Auditoria cruzada 22/10 | É **inventário de origem**; seus alertas agora estão preservados em contrato normativo S1 e esta matriz. Não declara validação das outras frentes |

## C. Gates mínimos para próxima auditoria TÉCNICA (nenhum homologado por esta matriz)

**G1 — Fluxos de atribuição:** normal cross-team para lead novo, fila sem titular por loja autorizada, assunção de Gestor com winner CAS, retorno de elegibilidade, contra fluxo same-team de caso já atribuído a pausado. Provas de titularidade única, locks, idempotência e RLS negativa interequipes.

**G2 — RBAC e escopos:** Diretor/Gestor/Consultor, uma chefia principal, supervisão de equipe, acesso restrito à fila compartilhada autorizada, no-op na visualização de Gestor, conta ativa com intake pausado, transferência para si como pré-condição de envio, bloqueios cross-store.

**G3 — Exceção e histórico:** autorização por caso para ESCRITA; leitura contextual do mesmo contato na mesma loja e ciclos históricos, inclusive sem grant geral, sem D3/D4 indiscriminado; revogação, read/write em voo, mudança de titular, saída de equipe/conta, mídias/anexos e histórico imutável.

**G4 — Contato e indicador:** prova humana/negativa S0, origem humana versus automação, delivery callback correlacionado, template manual permitido como saída, COUNT/ DOT /NONE, transferência de leitura individual, reset de segmento por conclusão, inbound tardio e concorrente; diferenciar status Meta e contador técnico de falha de template.

**G5 — Fechamento e F03:** evento técnico GoTrue/HMAC, cutoff idempotente, S1 lock antes de S0, rechecagem de atribuição e sessão, exceção I35 contemplada, ficha não editável pelo Consultor, tarefas de retorno e provas Banco externas.

**G6 — Comprovação e status:** não declarar versão I35/36/37 e S0 CFI-01 como migration, UI produtiva, Meta validada ou contrato comercial Banco homologado; todas as branches mantidas isoladas em Draft, sem merge/deploy/Supabase hospedado.

## D. Lacunas registradas [R] — sem novas decisões presumidas
- Implementar tecnicamente **A2 já decidida**: barrar nova atribuição e transferência, inclusive manual/por exceção, para Consultor pausado, com rechecagem sob lock da elegibilidade e integração S0. Manter leitura/resposta em casos previamente atribuídos.
- Confirmação física do primeiro contato humano; se o primeiro ato for template acionado pelo Consultor; fonte de prova negativa e bloqueio simultâneo.
- Formulação precisa de `DELIVERED` ou prova de entrega equivalente e política de status atrasado/incerto.
- Persistência do reset de segmento, titularidade pós-conclusão, novo inbound após fechamento e tela de acompanhamento.
- Abordagem física de identidade única do contato/loja e histórico de ciclos, privacidade e retenção de mídias/anexos.
- Exceção I35 integrada a CFI/F03, versão do caso versus ciclo, e revogação em voo.
- Permissões finas de D2/D3/D4 e projeção mínima para Gestor que ainda não assumiu item da fila.
- Fila: algoritmo de carga/prioridade, elegibilidade, alertas e concorrências; sem SLA/badge de tempo inventado.
- Implementação de assinatura humana do WhatsApp com retry/autoria imutável e ausência de prefixo não autorizado em template.
- Contratos externos Meta, instituição financeira, LGPD e operação real/segredos/DR.

**Decisões fechadas não precisam ser repetidas ao responsável por falta de implementação.** A auditoria técnica deve abrir tarefas para contratos, não para inventar comportamento alternativo.
