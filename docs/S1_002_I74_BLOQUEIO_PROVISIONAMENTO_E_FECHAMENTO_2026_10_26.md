# S1-002 — I74: bloqueio de provisionamento e critérios de conclusão

**Data:** 26/10/2026. **Responsabilidade:** S1-002 na branch de laboratório; núcleo S0 oficial coordenado pelo Codex.  
**Natureza:** evidência e contrato de coordenação, não migration nem autorização para implantar.

## Estado certificado

- **I73 permanece o último incremento integralmente certificado**: PG17 6/6 e GoTrue/PostgREST real descartável 8/8.
- **I74 está implementada na branch, porém NÃO certificada.** O ensaio PostgreSQL 17 da I74 passou 6/6 em [run 40294183203](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40294183203), com regressões e rollback.
- Os testes unitários e regressões do assinador I25–I31 passaram na revisão candidata `87f0778d10311aff7f0c5be1d06d1b0373ed8275`.
- A execução GoTrue/PostgREST [run 40294183275](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40294183275), job `121476111391`, **falhou na preparação** da fixture `s1_108_export_signed_executor_local_only.sql`, na transição para o proprietário restrito da função SQL: `permission denied to set role "prumo_s1_export_executor"`.
- **Nenhum** dos 8 testes E2E específicos da I74 foi validado nessa execução. Não confundir unitários verdes nem PG17 com homologação real.

## Descrição reproduzível da dependência

A I74 exige que `prumo_export_auth.exportar_assinado_i74` pertença ao papel `prumo_s1_export_executor`, com `SECURITY DEFINER` privado e limitado. A API assinada apenas executa essa função. A rotina mantém o contexto invocador de `public.s1_71_exportar_resumo`, que depende do RBAC/RLS comercial S0.

Na stack Supabase local, o papel `postgres` utilizado pelo instalador não dispõe da capacidade de assumir o novo executor. No PG17 sintético puro a operação funcionou. **Não resolver criando a função como proprietário superprivilegiado permanente** nem dando `SET ROLE` ao login de aplicação, pois isso enfraquece a fronteira que a I74 existe para proteger.

## Contrato para S0/Codex revisar

1. Validar, em ambiente descartável, método de instalação auditável e estritamente transitório para definir o proprietário restrito. O privilégio de instalação deve desaparecer após a criação da função.
2. Confirmar que `authenticated`, `anon`, `service_role`, e o login SQL assinado não assumem o executor, não acessam os segredos/ledger e não chamam a RPC I71 sem prova.
3. Verificar propriedade real da função e `SECURITY DEFINER` privado; executar inspeção de RLS e catálogo ACL antes e depois da instalação.
4. Executar 8/8 testes I74 com GoTrue real, incluindo assinatura independente, nonce concorrente/replay, adulteração de parâmetros, revogação de chave e de sessão, além da regressão inteira I53 em diante.
5. Registrar compatibilidade com evolução da S0 pelo Codex, contratos afetados, processo de rollback, retenção/LGPD, administração de chaves, roteamento e limites na borda, **sem merge/deploy automáticos**.

### Arquivos estritamente S1 impactados

- `supabase/tests/s1_108_export_signed_executor_local_only.sql` — fixture de instalação atualmente bloqueada no ambiente GoTrue/Supabase descartável.
- `supabase/tests/s1_109_export_signed_executor_aceite.sql` — seis provas de PostgreSQL 17.
- `backend/s1_gateway_export_signed_local.py`, `backend/s1_signer_process_local.py`.
- `scripts/test_s1_002_i74_signed_export_e2e.py`, `tests/test_s1_002_i74_export_signed.py`.
- Runner S1 `scripts/test_s1_002_i73_export_executor_e2e.py`, workflow `.github/workflows/s1-002-i37-intake-signed-local.yml`, fixture `s1_090_s0_indirect_read_boundary_aceite.sql`.

**Nenhum arquivo pertencente ao núcleo S0, migration hospedada, `main` ou produção deve ser alterado nesta proposta.**

## Distinção entre finalizar a I74 e encerrar a S1-002

O mapa formal de encerramento está em `docs/S1_002_I50_REVALIDACAO_E_GATES_2026_10_23.md`: seis gates G1–G6 (fila/distribuição; RBAC e equipe; histórico/exceções; primeiro contato/indicador; conclusão/F03; homologação). Os incrementos I51–I74 acrescentaram implementação e provas relevantes depois daquele mapa, mas **não existe auditoria conclusiva de G1–G6** que permita afirmar percentual de frente pronta.

Para evitar crescimento indefinido por número de incrementos, avaliar o fechamento por **aceites observáveis**: integrar contratos reais S0/S1, manter RLS/segregação multi-loja, consumir eventos e serviços verdadeiros, homologar fluxos UI e casos negativos, realizar gates de dados/LGPD e aprovar no processo de integração S0/Codex.

**Estado atual:** I74 candidata sem E2E integrado; S1-002 em desenvolvimento, não pronta para operação. PRs existentes em outras branches continuam preservados.
