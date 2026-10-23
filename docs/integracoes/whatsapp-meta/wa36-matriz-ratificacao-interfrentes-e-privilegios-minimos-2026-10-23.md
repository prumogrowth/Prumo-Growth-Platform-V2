# WA-36 — Matriz de ratificação interfrentes e privilégio mínimo (somente laboratório)

**23/10/2026 · Frente WhatsApp/Meta · [PR #2 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2).** Escopo: plataforma de atendimento comercial operada pela Prumo, cuja marca própria ainda não foi definida. **LiberaCred é o produto comercial da instituição financeira, não o nome da plataforma.**

## Parecer técnico desta etapa

**Não há autorização de produção nem ratificação S0/S1/infra.** As [WA-32](./wa32-webhook-assinado-escopo-s0-forense-offline-2026-10-22.md)–[WA-35](./wa35-ponte-hmac-meta-envelope-s0-pg17-offline-2026-10-23.md) comprovaram elementos isolados ou encadeados em laboratório, mas o runner ainda passa argumentos para um SQL privilegiado sem autenticar o **serviço invocador** perante uma API S0 real. Nenhum êxito de HMAC, replay, PG17 ou papel humano muda isso.

A análise das fontes atuais em branches independentes confirma:

- **S0/CFI-01, [PR #12 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/12):** há GoTrue/HMAC/nonce para **conclusão humana**, recibos/snapshots e uma ordem de bloqueios de equipe S1 → caso e concessões S0. **Não é uma porta Meta** nem autoriza reaproveitar a sessão de um humano para uma integração máquina→máquina. Ver [ordem de locks](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-cfi01-f03-auth-preflight-20261020/docs/S0_CFI01_S1_TRANSACAO_ORDEM_LOCKS_2026_10_21.md) e [recibo F03 de laboratório](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-cfi01-f03-auth-preflight-20261020/docs/S0_CFI01_F03_SNAPSHOT_METADATA_RATIFICATION_GATE_2026_10_21.md).
- **S1, [PR #5 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/5):** perfis de pessoas são **Diretor, Gestor e Consultor**; nomenclatura não acrescenta privilégios, perfis técnicos ou tokens Meta. [Fonte S1](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s1-002-equipe-prumo/docs/S1_002_DECISAO_NOMENCLATURA_PAPEIS_2026_10_21.md).
- **S0 fundação, [PR #1 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/1):** objetos, concessões e RLS de domínio não podem ser presumidos como interfaces de webhook prontas. Nenhuma alteração foi enviada para a branch-base S0 nesta etapa.
- O status externo **Meta** ainda exige rota confiável e HMAC dos bytes exatos do webhook; isso não autentica, por si só, o destino S0 nem a identidade da tentativa e não comprova entrega comercial. A chave HMAC interna de laboratório WA34 **não é** uma credencial de serviço operacional.

## Matriz de decisão — todas as 12 entradas SEM ratificação externa

Os códigos são preservados pelo contrato tipado de testes `wa36-ratification-gate.ts`. **Responsável indicado é frente a consultar, não aceitação assinada ou autorização concedida.**

| ID | Ponto de homologação obrigatório | Frente titular proposta | Evidência até aqui |
|---|---|---|---|
| WA36-M2M-IDENTITY | Identidade de processo e autenticação máquina→máquina, sem reutilizar GoTrue humano | S0 + Infra | WA35, apenas runner fictício |
| WA36-META-PROVENANCE | HMAC de bytes brutos, rota/App autenticados e prova de origem no canal interno | Meta + S0 | WA32 e WA35 offline |
| WA36-KEY-SEPARATION | Segredos separados, rotação, revogação e guarda de chave interna | Meta + Infra | WA34 com chave fictícia |
| WA36-SCOPE-BINDING | Vinculação durável por App/WABA/remetente/destinatário/loja/caso/tentativa e revisão | S0 + S1 | WA33, binding plantado |
| WA36-MACHINE-ROLE | Privilégios técnicos explícitos, sem perfis Diretor/Gestor/Consultor | S0 + S1 | S1 PR #5, regra humana |
| WA36-NONCE-ATOMICITY | MAC validado no receptor + nonce e evento na MESMA transação S0 | S0 | WA34, fragmentos de laboratório |
| WA36-LOCK-ORDER | Ordem real com concessões S1, opt-out e alteração de atribuição/caso | S0 + S1 | S0 PR #12 só para humano |
| WA36-RLS-MIN-PRIVILEGE | RLS por tenant, credencial mínima e proibição de escrita direta | S0 + S1 | WA36, ensaio negativo NOLOGIN |
| WA36-CALLBACK-DEDUPE | Semântica de ID de status, callback repetido/conflitante e atraso | Meta + S0 | WA35: hash sintético, não ID único Meta |
| WA36-ACK-RETRY | Resposta HTTP só após persistência autorizada; replay de entrada ≠ Graph resend | Meta + S0 + Infra | WA30–35, sem ACK real |
| WA36-RETENTION-LGPD | Minimização, retenção, acesso/auditoria, exclusão e finalidade forense | S0 + Jurídico/LGPD | WA31 forense fictícia |
| WA36-REVOCATION | Regra forense após revogação sem reabrir consentimento ou envio | S0 + S1 + Meta | WA29/31/33, fixtures |

**Ponto de aceite:** decisões escritas e versionadas pelos donos, contrato S0 real com privilégios mínimos, revisão conjunta de segurança e execução física independente. O documento de outra frente, por existir ou estar em Draft, não é uma assinatura de aceite. A matriz não presume que qualquer requisito foi ratificado.

## Testes executáveis da WA-36

- `integrations/whatsapp-meta/wa36-ratification-gate.ts` e `.test.ts`: inventário tipado dos 12 itens; **22 testes de manifesto/negação**. Uma matriz completa só retorna `LAB_REVIEW_PACKET_ONLY`, sem autorização; aprovações autodeclaradas, falso GoTrue, alegações de serviço, IDs adicionais, objetos com getters/proxy, segredos ou campos extras retornam `LAB_REJECTED_MANIFEST`. **Nem um pacote válido aprova produção.**
- `integrations/whatsapp-meta/lab/wa36_pg17_least_privilege.sql`: quatro papéis fictícios **NOLOGIN**, schema isolado `wa36_lab`, wrapper `SECURITY INVOKER`, tabela de revisão com `CHECK(NOT ...)` nas flags de operação. `GRANT EXECUTE` ao papel fictício sem `GRANT INSERT` significa que a função **não** consegue escrever como aquele papel. Nenhum papel recebe função de produção ou papéis humanos S1. **Não é migração S0 nem serviço real.**
- `integrations/whatsapp-meta/lab/wa36-assert-least-privilege-pg17.py`: **20 verificações pretendidas no PostgreSQL 17 descartável**, incluindo operações sem privilégio com SQLSTATE 42501, ausência de LOGIN/BYPASSRLS, negando acesso à fixture WA34, impedindo update/delete, CHECK de flags falsas e controle de escrita reservado ao próprio superusuário de teste. Recusa DSN fora de `postgresql://postgres@127.0.0.1:5432/prumo_s0_test_ci` e variações libpq por ambiente.
- `.github/workflows/whatsapp-meta-offline.yml`: gate WA36 depois de WA35, exigindo 20 marcadores distintos e regressão Node.

**Limite do ensaio de privilégios:** o superusuário do CI configura os papéis por `SET ROLE`; não há identidade humana ou máquina realmente autenticada. Permissões do wrapper fictício não substituem um serviço S0 responsável por validar assinatura/tenant/nonce/locks na gravação. A função WA34 usa argumentos de laboratório; seu consumo não deve ser exposto por meio de grants oportunistas na produção.

## Critério de parada e transferência

Nenhuma implantação, endpoint Meta publicado, migração S0/S1, uso de Graph, segredos, webhook real, ACK, automação de reenvio, alteração comercial, merge ou acessos cruzados foram autorizados. Até que **S0 + S1 + Meta + Infra** ratifiquem as interfaces, o próximo trabalho legítimo é revisão cruzada da matriz e testes negativos adicionais **na própria frente**, nunca adaptar a fixture como endpoint de produção.

**Estado:** PR #2 Draft e independente. Todos os sinalizadores de `production_authorized`, `send_authorized`, `ack_allowed`, `retry_external`, `s0_write_authorized` e `case_transition_authorized` permanecem falsos no contrato.
