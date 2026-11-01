# S0/S1 — M09-07, integridade de origem e recheck assinado no laboratório

**Data:** 01/11/2026. **Estado:** `S0S1_M09_07_SIGNED_ORIGIN_LAB_PARTIAL`. Issue canônica: https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8. Não homologado pela Meta ou Infra e **não** consumível operacionalmente.

## Proveniência e alterações

- Base M09-06: `b73ed2923c6422143889205a7727cebd8dffd1f4`; branch `exp/s0s1-m09-origin-recheck-20261101`. Fonte PG17 S0 Meta Ingress independente: `01ffdb093013664b73b18d23f92aac2202578210`. Meta WA04A/WA09 original, pinada: `745f54acd8255bea728c5ab7c87848d5018ad66b`.
- Adições exclusivas: `integration/s0s1_m09_registry/origin_recheck_consumer.ts`, `test_origin_recheck_consumer.mjs`, `emit_origin_recheck_evidence.py`, `.github/workflows/exp-s0s1-m09-origin-recheck.yml` e este relatório. O workflow recusa qualquer delta fora dos cinco arquivos. Não se modifica `integrations/whatsapp-meta/`, S0 Ingress, `backend/`, `supabase/` ou `main`.
- Evidência funcional inicial: [GitHub Actions 41295585791](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41295585791), em `b05bb90c166cbee238691c92d896fb2b7a394478`: dois jobs `success`. O SHA final incluindo este documento requer execução CI específica e comprovação em Issue #8.

## O que foi construído

- Verificador offline `inspectOriginRecheckLab` recebe **dois** envelopes assinados Ed25519 (origem `ORIGIN` e recheck `RECHECK`), escopo/revisões esperados **independentemente** e chave pública SPKI Ed25519 injetada por um host de testes. Verifica assinatura sobre JSON canônico e domínio próprio `PRUMO.S0.M09.ATTEST.RECHECK/0.1\0`, campos exatos sem getters, dois nonces diferentes vinculados por `parent_nonce`, até 15 segundos entre observações, expiração de 30 segundos, correspondência de loja/App/rota/canal/WABA/número, finalidade, cinco revisões e digest. Denega assinatura adulterada, chave diferente, replay de observação, parâmetros extras, getters, proxies, revisão stale e recheck ausente.
- Saída tipada `LAB_SIGNED_RECHECK_MATCHED_UNVERIFIED` **não** contém nome de slot, segredo, documento do cliente ou chaves. Todas as flags de autorização comercial, Graph, envio, ACK, escrita e resolução de credencial são **falsas**, inclusive `recheck_atomic_with_dispatch=false`. Sucesso comprova **apenas integridade de assinatura da fixture**, não identidade S0 real.
- Gerador `emit_origin_recheck_evidence.py` realiza **duas requisições M09-04 assinadas com nonces distintos** no PG17 descartável, obtém o único slot `POST_APP_SECRET` pelo instalador de teste, gera duas atestações assinadas com uma **nova chave Ed25519 efêmera de teste** e expõe apenas sua chave pública e dados sanitizados em arquivo temporário. **Após** as duas observações, revoga fisicamente `binding` e `grant` em transação e confirma que uma **terceira** leitura assinada M09-04 já não é aceita. Os testes Node verificam a correlação da fixture sem jamais utilizá-la para enviar/consultar Graph ou resolver vault.

## Resultados de CI, sem dupla contagem

- Workflow funcional: `completed/success`, ambos jobs aprovados. **29 casos distintos próprios da M09-07**, dos quais 28 PASS e 1 skip PG17 esperado no job offline, e **29/29 PASS sem skip** no job físico com evidência PG17 real descartável. Adicionalmente, 23 casos herdados M09-06 foram executados offline (22 PASS, 1 skip esperado), 63/63 regressões WA04A/WA09 originais PASS e 16/16 regressões físicas M09-04 Ed25519/antirreplay PASS.
- Os 29 casos M09-07 incluem chave injetada incorreta, payload adulterado, ausência de novo recheck, nonce de origem reciclado, janela expirada, revisão isolada divergente, mudança de escopo/slot, campo extra, getter malicioso, Proxy e **um ensaio negativo deliberado**: assinaturas ainda válidas matematicamente **mesmo após revogação física posterior**.
- Sem alteração nos repositórios/árvores pinados e sem persistência da evidência após término do job. Nenhuma chave privada, token ou segredo real foi exportado.

## Bloqueios que permanecem

1. **A chave pública do atestador é transportada no próprio artefato da fixture.** Para operacionalizar confiança, ela deverá ser obtida de **trust anchor independente provisionado por Infra/Proprietário**, sob política de rotação, revogação, prazo e credencial S0 autenticada. A assinatura desta fixture **não** prova origem de ambiente S0 real ou custódia; o parâmetro público injetado pode ser escolhido por qualquer teste.
2. **Duas observações assinadas não são recheck atômico com uso externo.** Uma revogação após o segundo read deixa os dois envelopes criptograficamente verificáveis por sua curta janela; o laboratório comprova expressamente a insuficiência. Para autorização real seria preciso recheck transacional/lease ou outro mecanismo ratificado vinculado à ação privilegiada **no ponto de uso**, sem janela TOCTOU; nenhuma credencial é resolvida por este candidato.
3. **Propósito do M09-04 ainda é `REGISTRY_READ`** e não uma autorização Meta GET/POST/Graph. O slot `POST_APP_SECRET` foi observado somente pelo instalador PG17 descartável. O consumidor WA04A/WA09 original não foi substituído nem recebeu contrato de finalidade única ratificado.
4. Titularidade e delegação de App/WABA/número, custódia de segredos, M2M/host operacionais, origem de catálogo Meta e decisão de ambiente hospedado permanecem com Infra/Proprietário/Meta; `UNVERIFIED`. Não houve Graph, HTTP ACK, banco hospedado, merge, deploy, envio ou ato comercial.

**Próxima ação S0/S1:** projeto e ensaio restrito de recheck transacional no ponto de uso, sem conceder autorização de envio; Meta deve revisar forma `scoped/purpose-specific` na Issue #8. #2, #7 e #10 são frentes independentes.
