# S0/CF-OP-02 — Matriz conservadora de elegibilidade, recontato e C09 | v0.1

**19/10/2026. [P/R] Contrato de decisão S0 em revisão, NÃO implementação, SQL, tabela, enum ou homologação.**
**Missão de desbloqueio limitado:** distinguir o que pode ser especificado agora para a frente OpenAI do que **não deve ser assumido** até aceite por status/fase. A frente WhatsApp/Meta também recebeu autorização do responsável para **seus próprios ajustes S0**; esta proposta não modifica nem substitui a autenticação de provedor, C07/WA-01, canal, migrations 040, IDs Meta nem prova durável de envio.

**Referências:** docs 03 ATD-01B, 21–23, 26 C04/C05/C08/C09/C10, CF-OP-02 PR #7, issue #6, S0 `docs/CF_OP_02_CONTRATO_NUCLEO_RECONTATO_HUMANO_v0_1.md`, OpenAI OAI-08, S1-002 I6–I9 e novo [S0/CFI-01](S0_CFI_01_PONTE_CONTRATO_FECHAMENTO_OPENAI_v0_1.md).

## 1. Decisões seguras de fase/estado para C09 por silêncio

**Princípio:** S0 só poderá declarar `perdido` por silêncio pós-template final em estado/fase **explicitamente permitido por matriz homologada**. Em toda fase sem decisão (inclusive pré-banco com humano), **DENY/BLOCKED** no comportamento físico; não converter uma regra de negócio desejada em código de autorização antes da ratificação.

| Contexto real de domínio, determinado pela S0 | Estado proposto do gate C09 no escopo pós-humano | Explicação |
|---|---|---|
| Ciclo sob IA Vendedora e ainda elegível, sem handoff | **EXISTENTE CONDICIONAL**, sob regras vigentes C05–C09 e guarda efetiva | Não flexibilizar nem alterar a regra original `sob IA`; execução real só conforme gates e status existentes |
| `em atendimento pelo operador`, com caso humano ainda elegível pré-banco | **CANDIDATO [R], não ALLOW** | Direção CF-OP-02 admite extensão pós-humana, mas matriz técnica de status ainda requer aceite; negar C09 automático no interim |
| `cadastro enviado ao operador` | **DENY ATÉ DECISÃO EXPLÍCITA [R]** | Dados preparados e responsabilidade de remessa não equivalem a elegibilidade de perda por silêncio; política em aberto |
| `cadastro enviado ao banco` | **DENY** | Negativa definitiva do Banco exige prova e lançamento humano; não usar silêncio como resposta bancária |
| `vendido` | **DENY** | Venda preservada; retorno pós-venda é novo caso humano, não reinício de ciclo vendido |
| `perdido` histórico | **DENY** | Reabrir ou alterar ciclo perdido requer decisão de negócio própria, não reusar C09 |
| Demais fases sem categoria aprovada para silêncio | **DENY** | Nega por padrão; não inventar enum nem completar oito status pela intuição |

**Nota:** esta matriz é uma proposta de **comportamento conservador de implementação futura**, não ratificação da extensão humana, não enum oficial e não autorização de produção. O S0 e a coordenação precisam fixar em contrato e evidenciar as fases elegíveis.

## 2. Sequência de atendimento e três relógios (+ um agendamento)

- **T-META:** prazo para mensagens livres da Meta = **último inbound autêntico do CLIENTE +24h**. `sent` outbound/template não abre janela; inbound novo renova o prazo. O S0 recebe evento correlacionado/autenticado do canal via fronteira Meta.
- **T-HUMANO:** clique técnico `concluir atendimento` do operador Prumo autorizado inicia F03 interna. A conversa concluída permanece visível enquanto a janela operacional ligada ao inbound estiver aberta; se o humano NUNCA concluiu, vencimento T-META não conclui caso nem apaga inbox.
- **T-FINAL-PREVISTO:** após 2–5 tentativas regulares para cliente já atendido e silencioso (e sem inbound), planejar **template final SEPARADO aproximadamente 24h após a última tentativa regular**, dentro da política e sem prometer entrega.
- **T-C09:** somente a prova de **`sent` EFETIVO do template FINAL** correlacionado/autenticado inicia **OUTRAS 24h sem inbound**. `queued`, `accepted`, `uncertain`, chamada Graph aceita ou agendamento não bastam. S0 revalida caso/fase, opt-out, envio final, versão do plano e provas de inbound sob controle de concorrência antes de qualquer ato comercial.

**Regra de falhas:** após **duas falhas consecutivas de envio qualificadas** nas tentativas de uma cadeia, S0 deve cancelar próximas tentativas sem apagar histórico. Definir com Meta quais eventos contam como `failed`, repetição, ordenação/reconciliação e atraso dos callbacks; não tratar ausência de confirmação, `uncertain` ou `accepted` como prova de falha.

## 3. Concorrência template individual vs cadeia IA pós-humana

1. **Operador humano ainda não concluiu e janela Meta expirou:** pode pedir template aprovado INDIVIDUAL (sem F02) ou pedir NOVA cadeia contextual C05/F02. Só S0 valida concessão, caso, fase, allowlist, versão, opt-out/custos e decisão de concorrência.
2. **Candidata guard determinística [R]:** para mesmo caso/ciclo/finalidade, não autorizar simultaneamente template individual e cadeia incompatível. Identificar pedido opaco e versão para detectar corrida; conflito gera decisão segura `CONFLICT/PENDING_REVIEW`, **não dois envios**. Escolher política transacional, cancelamento e precedência com donos S0/Meta.
3. **Após handoff:** planos da IA Vendedora antes de handoff cancelados C08/C10 não são reativados. F02 pós-humana cria novo identificador e só por solicitação S0 autenticada. Resposta do cliente segue operador atual autorizado, eventualmente redistribuído pela S1.
4. **Fila protegida/operador revogado:** não gerar intenção de resposta humana, plano, disparo nem retorno à IA Vendedora enquanto titularidade não for revalidada; a S1 administra redistribuição segura.
5. **Pós-venda:** caso novo de suporte humano nunca usa `vendido` histórico como gatilho de recontato comercial. Novo ciclo/objetivo e elegibilidade requerem decisão S0 expressa.

## 4. Propostas de ensaios S0 offline — zero executados neste trabalho

| Ref | Entrada fictícia | Oráculo de decisão (não prova real) |
|---|---|---|
| **S0O-01** | caso humano em `em atendimento pelo operador`, final `sent` fictício e 24h silêncio, porém C09 humano não ratificado | `BLOCKED_POLICY_PENDING`, nunca `perdido` |
| **S0O-02** | `cadastro enviado ao operador` com todos os timers concluídos | `DENY` até decisão própria; não confundir com regra IA |
| **S0O-03** | `cadastro enviado ao banco`, `vendido`, `perdido` | `DENY`, sem transição automática |
| **S0O-04** | final `accepted` ou `queued` sem `sent` confiável | `NOT_READY`, C09 não inicia |
| **S0O-05** | final `sent` autenticado mas há inbound antes de +24h | `CANCEL_NO_LOSS`; cliente vai ao humano autorizado se houve handoff |
| **S0O-06** | duas falhas de entrega qualificadas consecutivas + tentativa futura planejada | próximas tentativas canceladas; `uncertain` entre falhas exige regra de qualificação/ordenação [R] |
| **S0O-07** | template individual e cadeia F02 solicitados simultaneamente | no máximo uma intenção válida por política S0 após transação; nenhum duplo `sent` |
| **S0O-08** | alteração de operador e chegada de cliente concorrem com recomendação antiga F03/F02 | rejeitar versão/titularidade obsoleta; manter atendimento humano |
| **S0O-09** | histórico `vendido` recebe retorno de suporte | novo caso humano, `vendido` anterior inalterado, nenhuma F02 comercial automática |
| **S0O-10** | tentativa de usar evento `sent` de outra concessionária/número emissor/caso | `DENY`; proveniência/identidade Meta é fornecida e autenticada pela própria integração responsável, não IA/frontend |

**Não são fixtures, implementações, testes PASS ou homologação.** Resultados positivos C09 pós-humano intencionalmente ausentes até matriz ratificada. Regras de execução devem ser revistas antes de escrever SQL/workers.

## 5. Fronteiras e próximos aceites

- **S0 / issue #6:** ratificar matriz C09 por status/ciclo (inclusive se `cadastro enviado ao operador` pode ou não sofrer perda por silêncio) e precedência de template individual versus cadeia, idempotência e critérios de fase.
- **Meta / issue #6:** definir prova de `sent` final correlacionada a emissor exclusivo da concessionária e caso, `provider_timestamp` x tempo confiável do servidor, falha qualificada e callback fora de ordem. Não mexer em C07/WA ou migrations 040 por este trabalho.
- **OpenAI:** só sugestões F02/F03; nunca C09, valor bancário, operador, emissão Meta ou parametrização autônoma.
- **S1/Frontend:** gestão segura de operador revogado, fila protegida e projeção da conversa; nenhuma volta à Vendedora.
- **Usuário/coordenação:** decisão de negócio se a matriz não puder ser inferida dos documentos, principalmente `cadastro enviado ao operador`; consultar antes de marcar regra autorizada.
- **Não permitido nesta etapa:** API OpenAI/chave/billing (decisão de adiar), webhook Meta, Supabase hospedado, SQL de produção, n8n, deploy, merge. Esta é uma **ponte de contratos S0** compatível com a autorização específica do responsável.
