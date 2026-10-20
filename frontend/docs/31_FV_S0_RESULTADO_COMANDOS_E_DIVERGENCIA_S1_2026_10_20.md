# FV-S0-CMD-01 — resultados de comando S0 candidatos e alinhamento S1

Data: 20/10/2026. **Documento de coordenação**, não autorização de implantação. Nova orientação do responsável: S0 pode ser ajustada quando necessário; S1-002 possui frente proprietária própria, a ser notificada de conflitos. **Prioridade atual: funcionalidade, não design visual**.

## Evidência documental examinada

- **26_Contratos_Conceituais_Eventos_APIs_v0_1** (17/10): `APPLIED` (efeito persistido), `ALREADY_APPLIED` (idempotência), `ACCEPTED_FOR_PROCESSING` (aceito sem efeito comprovado), `PENDING_EXTERNAL`, `UNCERTAIN_EXTERNAL`, `REJECTED`. São códigos **conceituais [P]**, não contratos oficiais Meta/Banco.
- **40_Contratos_Interfaces_Campos_Operacionais_Rastreabilidade_v0_1** (17/10): C11 para atribuição, C12 mensagem humana, C13 correção, C15–C18 para remessa/retorno/venda/recusa sob titularidade humana autorizada. C14 de entrada pós-marco, comandos MCP administrativos e ações Meta não são expostos por este candidato.
- **S1 I10** foi expressamente superado por **S1 I11**. A frente atual `feat/s1-002-equipe-prumo` tem a migration 048 com equipe gestor→operador, grants por responsáveis e pausa global. **Isso já segue a orientação nova quanto à chefia**.
- **Divergência confirmada:** `s1_pausar_operador_da_equipe` executa `UPDATE equipe_prumo_s1 SET estado='suspenso'` e desencadeia restrição de leitura/redistribuição. A diretriz expressa em `frontend/docs/21_FV_G2_01_GESTAO_POR_OPERADORES_E_PAUSA_GLOBAL_2026_10_19.md` distingue **pausar novos leads** de suspender conta/acesso. A questão foi notificada à proprietária S1 na [issue #10](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/10); **não editar a branch S1 por esta frente**.

## Contrato candidato implementado

`frontend/visual/s0-command-result.mjs` oferece `stageCandidateCommandResult(response, expected)`, uma função pura para **classificar** uma resposta recebida pelo frontend futuramente. Não dispara C11–C18, não tem rede, banco ou transporte, não atualiza a UI existente e não confere autenticação real.

- O eco dos campos de contexto (`contract_id/version`, `request_id`, `correlation_id`, `actor_id`, `scope_ref`, `aggregate_ref`, `expected_version`) e a versão candidata são validados. São **campos de ensaio**, ainda sujeitos ao acordo final com a S0; não constituem prova de identidade.
- `APPLIED`/`ALREADY_APPLIED` exigem indicação estruturada de efeito persistido, identificador e versão; são classificados apenas como `claimed_applied`, com `hasVerifiedEffect:false`. **Somente S0 autenticada e auditada pode verificar o efeito verdadeiro.**
- `ACCEPTED_FOR_PROCESSING`, `PENDING_EXTERNAL` e `UNCERTAIN_EXTERNAL` sempre ficam em `pending` e nunca declaram remessa, envio, entrega, venda ou recusa confirmados.
- `REJECTED` precisa de motivo e não retorna conteúdo sensível da resposta. Respostas desconhecidas, misturadas entre atores/casos, fora de versão ou malformadas são rejeitadas sem mostrar dados brutos.
- O módulo não é mecanismo RLS, política de aprovação financeira ou validação de evidência do Banco.

## Provas realizadas

- Fonte local idêntica aos Git blobs de `s0-command-result.mjs` (`21e3006c0e6cf3403774400cb0ae1f7180ee6661`) e seu teste (`7b5c2a34c021ad7260540544fe27a1fb8567ecd6`), confirmados também no GitHub.
- **Node.js nativo**: 208/208 testes PASS, sem skips, usando cópia do frontend validada por hashes na rodada anterior mais os dois arquivos novos.
- **Chromium/Playwright real**: smoke PASS nas larguras 1440, 900, 390 e 320 px e em cenários existentes. O novo módulo não participa da UI em execução; isso prova ausência de regressão nos fluxos antigos, **não integração S0**.
- Teste negativo deliberado: ao suprimir a checagem de `confirmed_persisted`, a nova suíte recusou a mutação (**1 falha esperada**); original restaurado e 8/8 novos testes aprovados.

## Responsabilidades e pendências

**S0:** validar envelope, autenticação, autorização por equipe/loja/caso, idempotência, auditoria, provas e os códigos finais de erro; ajustar núcleo quando especificação estiver resolvida. Esta autorização não é permissão para deploy, alteração de Supabase hospedado ou remessa bancária real.

**S1:** corrigir/alinhavar a separação entre indisponibilidade de entrada e suspensão de conta, além da política de redistribuição. Issue #10 acompanha. Se regras ainda não implementadas, prosseguir apenas com contrato/prova offline, sem presumir efeito.

**Status:** FV-UI-013 continua **não homologada pelo gate Git**. 19F mantido em **69/100**. Sem merge, deploy, Meta, integração bancária ou dados reais.
