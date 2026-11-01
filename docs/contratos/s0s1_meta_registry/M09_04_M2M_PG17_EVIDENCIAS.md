# M09-04 — assinatura M2M Ed25519 e proteção contra replay no PG17 descartável

**Data da implementação:** 31/10/2026 (America/Recife). **Estado:** `S0S1_M09_M2M_PG17_LAB_ONLY`. Issue canônica: https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8.

## Base e escopo congelados

- Base M09-03 `67324a229e044a190549e9cd137b0410b4e85ceb`; fonte S0 Meta Ingress PG17 **independente pinada** `01ffdb093013664b73b18d23f92aac2202578210`. A implementação não altera S0 Meta Ingress, OPS-03, Meta, backend, Supabase nem `main`.
- Nova branch `exp/s0s1-m09-m2m-read-20261031`. Novos arquivos: `integration/s0s1_m09_registry/pg17_m2m_journal.sql`, `pg17_m2m.py`, `test_pg17_m2m.py`, workflow `.github/workflows/exp-s0s1-m09-m2m.yml` e este relatório.
- A tabela `s0_m09_lab.read_nonces` só é criada quando PG17, `s0_meta_ingress_lab`, usuário de instalação `postgres`, `s0_meta.disposable=YES`, `s0_m09.install=M2M_CANDIDATE_ONLY` e schemas anteriores existem. Runtime pode **inserir** nonce, mas não ler, alterar ou excluir o jornal; constraint única `(key_id,nonce)`.
- O setup utiliza exclusivamente VM/Docker PG17 descartável e prova SHA de checkout separado da fonte original. Remoção e auditoria de catálogo ocorrem na limpeza do laboratório M09-03 reutilizado.

## Fronteira criptográfica e transacional implementada

O candidato `prumo.s0.meta.registry.m2m-pg17/0.1-candidate` recebe bytes JSON canônicos e assinatura Ed25519 destacada. O domínio de assinatura `PRUMO.S0.M09.REGISTRY.READ/0.1\0` é distinto dos contratos de ingresso/recibo Meta. Campos estritamente tipados: versão, `key_id`, issuer, revisão de chave, `audience=LAB_S0_M09`, `purpose=REGISTRY_READ`, nonce, janela de validade de até 120 segundos, `host_ref`, `route_ref` e `app_ref`. JSON duplicado, com campos extras, não canônico, expirado ou assinatura adulterada é recusado.

O escopo de host provém exclusivamente do resolver **injetado pelo ensaio** (não do payload). Na **mesma transação** PG17: trava rota e principal na ordem original; revalida chave pública, issuer, grant/canal, validade usando relógio do banco; verifica assinatura Ed25519; insere nonce único; invoca a leitura completa M09-03 do mesmo `connection` para checar App/grant/tenant/loja/binding, cinco revisões e digest. Só devolve `AUTHENTICATED_READ_LAB_ONLY` depois de commit sem erro. Um mesmo nonce assinado não pode obter dois resultados de sucesso, inclusive em conexões concorrentes.

Replay exato ou divergente, assinatura trocada, rotação de chave, outra loja, host inexistente, grant revogado após assinatura, expiração e versões stale levam a resposta negativa. A negativa não expõe texto SQL, chave, segredo, slot ou dados sensíveis de principal; nenhuma saída concede Graph, ACK, envio ou operação comercial.

## Evidências de teste

- [CI funcional M09-04](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41263750605) no SHA `c3b540fd04ae3ff7eec6fa7748157feff759fc90`: verificação de delta isolado e regressão offline concluídas; **16/16 novos testes físicos PG17 PASS**, **13/13 testes PG17 M09-03 PASS** e **11/11 PG17 M09-02 PASS**. A suíte herdada M09-01 com **32 casos distintos** passou (reexecutada em modo otimizado).
- Total comprovado das quatro suítes sem duplicar repetições: **72 casos distintos** (32 sintéticos + 11 físicos M09-02 + 13 físicos M09-03 + 16 físicos M09-04).
- Testes novos incluem nonce e assinatura incorretos, replay exato e replay divergente, concorrência duas threads, revisão/rotação de chave, negação de escopo e propósito, expiração, RLS de nonces, integridade da consulta e incapacidade de autorização comercial. Essas provas são somente do **laboratório** e não de tráfego Meta real.
- Este relatório adiciona um commit novo ao funcional. A evidência de CI final no SHA documental será registrada na própria Issue #8; não confundir com a CI do SHA funcional.

## Limitações que NÃO podem ser inferidas como resolvidas

1. O par de chaves Ed25519 é gerado no próprio teste descartável; isto **não** é identidade M2M operacional, trust anchor ratificado, custódia em KMS, rotação coordenada ou principal habilitado em produção. A resolução da rota/host é fixture explícita; não houve prova de autorização de Infra.
2. Embora nonce e leitura sejam transacionais no banco de laboratório, o snapshot é apenas prova técnica de consulta e **não** autorização de despacho, ACK HTTP ou uso futuro. Recheck de consentimento/template no instante de envio pertence à #10; ingresso/recibo e decisão de HTTP à #2.
3. O catálogo App/grant foi persistido somente em uma extensão PG17 descartável; não foi criada migration hospedada. Titularidade/delegação dos ativos Meta continua `UNVERIFIED`, sem validação Graph nem secrets reais.
4. O adaptador Meta `credential-routing.ts` e o inventário WA09 ainda não consomem esta resposta por contrato homologado; a frente Meta precisa revisar tipagem, mecanismo de host confiável e fronteira do serviço.
5. Não há garantia de alta disponibilidade, recovery cross-region, retenção/purge dos nonces, escala multi-instância do serviço real ou política hospedada de criação/rotação de principal. Nenhum merge ou deploy foi autorizado.

**Próximo incremento:** interface typed/adapter Meta offline e auditoria de confiança do host; depois, decisões de Infra/Proprietário e homologação da fonte S0 persistente. Não ativar operação real por silêncio.
