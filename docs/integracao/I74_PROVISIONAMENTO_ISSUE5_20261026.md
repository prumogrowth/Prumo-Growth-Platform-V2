# Issue #5 — provisionamento I74 em Supabase descartável

26/10/2026. Branch experimental `exp/s0-i74-provisionamento-20261026`.
Base S1 verificada antes da implementação:
`01f7ba1a3c46100e023ce88a91a7bcc97d638a6c`.
S0/PR #4 preservada em `060b472b03e9e7b89f5b3d7e19b72b98836f106d`, com
CFI-01 real aprovado nos runs #40298770078 e #40298769996. Seu worktree e os
relatórios locais pendentes foram preservados, sem nova escrita na branch S0.

## Causas confirmadas

1. O instalador I74 executava `SET ROLE prumo_s1_export_executor` sem provisionar
   `SET` ao `postgres` não superusuário da stack Supabase. O ensaio PostgreSQL
   puro, com instalador superusuário, não reproduzia essa restrição. O caso foi
   observado no run original #40294183275 e novamente comprovado pelo probe
   `I74-PROV-01` (antes de qualquer grant temporário).
2. Depois de resolver o primeiro bloqueio, o run experimental #40301912378
   chegou a I74-E2E-02 e falhou em `permission denied for table chaves_i74`,
   no `SELECT ... FOR SHARE`. PostgreSQL exige UPDATE ACL e política UPDATE
   de visibilidade para esse lock; SELECT isolado não basta. Esse segundo
   problema não tinha sido exercitado pelos seis testes SQL anteriores.

A primeira tentativa não é certificação E2E; o instalador e o rollback forçado
passaram, mas a chamada assinada ainda estava bloqueada. A correção seguinte
preserva integralmente o corpo HMAC/nonce/sessão/exportação da função.
SHA-256 do trecho `$body$`: `ab537e63f06e2f8c12feb5874132637e0b2fcfa7715076105d8e1ad0e709cde9`.

## Solução mínima e segregação

`supabase/tests/s1_108_export_signed_executor_local_only.sql`:

- Todo o provisionamento está em **um DO atômico**, sem COMMIT interno. Funciona
  tanto em autocommit quanto dentro do ROLLBACK da suíte PG17. Um erro desfaz
  objetos, grants, mudança de papel e revogação do acesso antigo.
- Reutiliza o padrão CFI-01: CREATE no schema e associação SET ao instalador são
  transitórios. O grant de instalação usa `INHERIT false, SET true`.
- Guarda/restaura as opções ADMIN/INHERIT/SET do grant pré-existente emitido por
  `postgres`, sem tocar grants de outros emissores. Se não havia grant próprio,
  remove-o. Confere igualdade do catálogo antes/depois para o instalador.
  Não remove cegamente uma associação administrativa que já existia, nem deixa
  um SET novo instalado. O administrador continua autoridade de instalação;
  não se promete impedir um administrador legítimo de reprovisionar.
- O owner continua `prumo_s1_export_executor`, NOLOGIN, sem SUPERUSER/BYPASSRLS/
  CREATEROLE; função privada SECURITY DEFINER com search_path vazio.
- O login assinado e o antigo login de gateway não recebem associação ao
  executor. Apenas o login assinado recebe EXECUTE na porta assinada.
- O owner recebe **somente UPDATE(id)** na tabela de chaves para o lock, sem
  UPDATE(secret/active/validade). Política UPDATE específica permite visibilidade
  para lock e tem **WITH CHECK false**: nenhuma linha pode ser modificada.
  RLS segue habilitada; não se adiciona política de DML permissivo.
- Mantém grants separados: instalador provisiona; executor usa a porta fechada;
  custódia administra a chave fora do login da aplicação; signer independente
  autentica GoTrue antes de produzir a prova. Nenhuma chave sai para o gateway.
- Não muda a RPC I71 invocadora, assinatura, nonce, janela temporal, sessão,
  RLS comercial S0, política de quota ou algoritmo de exportação.

O grant técnico UPDATE(id) não foi presumido seguro: primeiro foi reproduzido
em PG17 local com tabela fictícia, depois é testado sob o próprio executor
no ambiente GoTrue. O teste tenta UPDATE em id/secret/active e exige negação.
O probe temporário do administrador termina em ROLLBACK, inclusive de seu grant.

## Arquivos alterados

### Solução e testes que a S1 deve revisar

1. `supabase/tests/s1_108_export_signed_executor_local_only.sql` — instalação
   atômica, restauração do instalador e privilégio mínimo de lock sob RLS.
2. `scripts/test_s1_002_i74_signed_export_e2e.py` — somente dois pontos de chamada
   dos probes adicionais; os oito cenários e marcadores originais são mantidos.
3. `scripts/test_s0_i74_provisioning.py` — causa inicial sob não superusuário,
   foto de catálogo e falha deliberada depois do grant, em autocommit; exige
   rollback completo e retorno ao papel postgres.
4. `scripts/test_s0_i74_security_e2e.py` — negativas adicionais de SET ROLE,
   EXECUTE por anon/authenticated/service_role, DML de chaves, concessão da loja,
   sessão GoTrue após MAC válido e revogação da chave no banco.

### Apenas bancada experimental/evidências

- `.github/workflows/exp-s0-i74-pg17.yml`: jobs e passos originais da regressão
  S1 PostgreSQL, com gatilho e grupo de concorrência restritos à branch própria.
- `.github/workflows/exp-s0-i74-gotrue.yml`: jobs unitários e E2E originais I37,
  sem omitir regressões I53+, com gatilho e concorrência experimentais.
- Este relatório e `I74_EVIDENCIAS_ISSUE5_20261026.json`.

Migrations, código backend do signer/gateway, os seis testes SQL I74 e os
workflows oficiais não foram modificados. Não se publicou código nas branches
S0, S1 ou main. Não houve merge, deploy ou acesso a banco hospedado.

## Aceite verificável

Dados finais dos runs, jobs, SHA e marcadores: `I74_EVIDENCIAS_ISSUE5_20261026.json`.
Os resultados finais são registrados abaixo após leitura do CI; não inferir
certificação a partir da existência do commit.

Provas exigidas:

- I74-01..06: ownership, grants, segredo/nonce, RLS, RPC invocadora e scanner I65.
- I74-E2E-01..08: GoTrue/signer independente, MAC, escopo, replay simples e
  concorrente, alteração de parâmetros, expiração e revogação do signer.
- I74-PROV-01..04: instalador restrito, rollback em autocommit, SET ROLE/EXECUTE
  efetivamente negados e DML de chaves negado ao owner.
- I74-SEC-01..03: concessão revogada sem dados/quota; MAC válido depois de logout
  real negado com rollback de nonce/quota; chave revogada no banco nega prova
  previamente emitida, também sem nonce/quota.
- Regressão integral I37/I53+ e unitários do workflow original, sem dano às
  sessões compartilhadas: o logout adicional usa uma identidade nova exclusiva.

## Instruções objetivas para S1-002

1. Revisar o diff experimental contra `01f7ba1`; transportar em proposta própria
   os **quatro arquivos de solução/teste** listados acima. Não promover os
   workflows experimentais nem copiar uma linha isolada de GRANT sem o bloco
   de restauração/atomicidade e o grant/policy de lock.
2. Manter ordem I72 → I73 → I74. A fixture I74 é para instalação **uma vez** em
   stack descartável nova; não é migration hospedada nem instalador idempotente
   para uma base já inicializada. Não limpar/recriar chaves automaticamente.
3. Acrescentar os dois helpers `scripts/test_s0_i74_*` aos filtros de paths dos
   workflows da própria S1 quando adotar, preservando os checks oficiais.
   A edição desses workflows oficiais é da S1 e não foi feita nesta bancada.
4. Rodar os workflows originais `s1-002-postgres.yml` e
   `s1-002-i37-intake-signed-local.yml` no SHA de adoção da S1. Exigir todos os
   marcadores acima e a conclusão das regressões depois de I74; unitário verde
   ou E2E parcial não bastam. Guardar os logs do mesmo SHA.
5. Conferir owner e search_path, RLS habilitada, igualdade dos grants do
   instalador, ausência de associação da aplicação ao executor e ausência de
   DML de segredos. Não tornar owner postgres, não usar BYPASSRLS e não dar
   SET ROLE permanente ao login de aplicação.
6. Somente depois desse aceite a S1 pode registrar I74 validada **no laboratório
   da sua própria revisão**. Isto não autoriza concluir G1–G6 da frente inteira,
   integrar produção, aplicar migrations hospedadas ou fazer merge/deploy.

## Riscos e limites remanescentes

- PostgreSQL 17 e a stack local pinada são o alvo testado; não há certificação
  de instalador de produção ou de outra versão. As fixtures de permissão
  continuam sendo laboratório, não catálogo normativo hospedado.
- O administrador de instalação e a custódia das chaves continuam confiáveis;
  o objetivo é isolar o login operacional, não resistir ao administrador do DB.
- O executor pode ler a chave dentro da função privada; o login não pode assumir
  esse papel nem ler a tabela. Compromisso do DB/custódia está fora da proteção
  de uma assinatura feita no mesmo domínio administrativo.
- Retenção/expurgo de nonces e reservas, quotas globais por loja, rate-limit,
  LGPD e avaliação de custo permanecem gates de operação. Não foram inventados
  parâmetros novos para resolver o erro de instalação.
- O contrato S0 de gestor/concessionária e a RPC invocadora foram preservados;
  revalidação de sessão, grants e isolamento por loja continua no caminho real.
  Isto não ratifica o contrato UI/F03 ainda pendente nem altera comercial.
- A Issue #5 pode receber os resultados experimentais sem fechar automaticamente
  a coordenação: a adoção pela S1 e eventual aprovação de produção são separadas.

## Resultado final certificado na bancada

Commit executável: **`ab38ebb3c5c8010857953383b665a52029be57f7`**.

| Execução | Resultado observado |
| --- | --- |
| [PG17 #40302989195](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40302989195), job `121505135657` | SUCCESS; I74 **6/6**, regressão S0/S1 e I52+ inteira; objetos experimentais revertidos no rollback de aceitação |
| [GoTrue #40302989277](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40302989277), job `121505135875` | SUCCESS; I74 **8/8 E2E**, **4/4 PROV**, **3/3 SEC**; regressões anteriores e posteriores à I74 preservadas |
| Mesmo run, job `121505136245` | SUCCESS; **179 unitários** no conjunto original, incluindo os quatro específicos I74 |

O job real chegou após I74 até `PASS S1INTAKE-147`, `PASS S1INTAKE-148` e o
marcador final `S1-002/I37: 132 older E2E and 16 new I37 gates PASS.`. Portanto
não se certificou apenas um trecho da cadeia antes de uma falha posterior.
Cleanup da stack descartável e pós-passos também terminaram SUCCESS.

A primeira revisão `57d711f` passou PG17, instalador/restauração e duas provas
E2E, mas falhou no lock da chave. Foi corrigida em `ab38ebb`; ambos os workflows
foram reexecutados no **mesmo SHA final**. Não houve retry oculto nem se reutilizou
resultado PG17 de outro commit como evidência do final. As suites são distintas;
não se soma 179 unitários com marcadores E2E como se fossem jornadas comerciais.

**Conclusão limitada:** bloqueios de provisionamento e de lock I74 resolvidos e
aceites solicitados comprovados no laboratório. A adoção na branch oficial S1
continua uma etapa própria, sem integração/merge automático, sem autorizar
produção e sem concluir os gates G1–G6 da frente inteira.
