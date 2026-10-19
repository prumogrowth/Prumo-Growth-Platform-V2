# WA-06D/B — PostgreSQL 17 efêmero + leitura pós-COMMIT em nova conexão

**18/10/2026 — [P], pronto para execução, NÃO executado em PostgreSQL.**

> **Precedência: [AUD2](wa06d-aud2-auditoria-aderencia-execucao-v0_1.md).** O ensaio B **não integra o caminho de ingresso WA-06D/A nem S0**: seus inserts usam tabelas e fixture separadas, logo um futuro PASS aqui provará apenas semântica ACID/visibilidade numa conexão nova em PostgreSQL fictício. O recibo de exemplo agora se chama `FIXTURE_COMMITTED_NOT_ACK`, não `IN_TX_ONLY`. Nenhuma evidência de autorização para responder HTTP 200. Novos resultados realmente executados: **7/7 testes do executor com Postgres falso PASS** e `bash -n` PASS, root real negado (exit 77); **0/20 testes SQL PostgreSQL**. Os quatro blobs anteriores nesta seção são **históricos**; atuais: runner `3057062b31d1e7c63f8c26a9bac9c4508ce71890`, testes `1c8e49fbbb6d1fe88e5da9173fc0464c002c7af5`, setup `dc159fc4c00ee6f4708fa563d74f189ea5ce098c`, verify `ecb690e78647bf209cc17b32ed53cfc4ad152472`. Quando falhar ao desligar cluster, o runner preserva os arquivos e indica falha, em vez de prometer limpeza.** Complementa WA-06D/A3; não modifica esquema S0, Supabase hospedado ou webhook Meta. **Nenhuma decisão comercial nova.**

## O que foi implementado

1. `integrations/whatsapp-meta/lab/run-wa06d-ephemeral.sh` cria um **cluster PostgreSQL 17 próprio e descartável** via `initdb`, acessível **somente por socket Unix em diretório privado**, `listen_addresses=''` (sem TCP), com banco `wa06d_test_ephemeral`. Rejeita execução como root, opções de conexão de usuário, PG diferente da versão 17 e binários faltantes. Ignora ambiente `PGHOSTADDR/PGSERVICE/PGOPTIONS`. Ao sair, tenta desligar o cluster e apaga o diretório efêmero. Nunca conecta a banco já existente. Requer PostgreSQL 17 local instalado e usuário não-root.
2. Executa **em três conexões separadas** `wa06d_pg17_atomicity.sql` (14 casos candidatos, todos encerrados em `ROLLBACK`), `wa06d_pg17_postcommit_setup.sql` (cria dados sintéticos em schema isolado no banco descartável e faz `COMMIT`) e `wa06d_pg17_postcommit_verify.sql` (verifica estado persistido em outra conexão, colisões e falhas). O schema é destruído **com o próprio cluster**.
3. `integrations/whatsapp-meta/lab/test_wa06d_ephemeral_runner.py` testa a proteção do executor com binários PostgreSQL **fictícios**. Nenhum socket ou conexão real é usado nesses testes.

## Matriz pós-COMMIT candidata (ainda 0/6 executados)

| Caso | O que deve demonstrar **quando executado** |
|---|---|
| WA06D-B01 | lote, corpo, nonce, 2 ocorrências, 2 tarefas e marcador de recibo sobrevivem ao COMMIT e são legíveis por outra conexão |
| WA06D-B02 | IDs de mensagem repetidos preservados quando posições Meta diferem |
| WA06D-B03 | consulta do próprio `request_ref` recupera a mesma impressão digital do lote/corpo |
| WA06D-B04 | solicitação repetida com `request_ref` e lote diferentes é rejeitada por unicidade |
| WA06D-B05 | falha injetada na gravação cancela mudanças parciais na subtransação |
| WA06D-B06 | registro de recibo é consultável, **mas não autoriza HTTP ACK** |

A fixture é deliberadamente **autoritativa apenas dentro do banco de laboratório**: `fake_principal` e `app_a` são strings fictícias e **NÃO** identidade de workload, autenticação Meta, prova MAC, cadastro real do canal ou ACL comercial. O texto `IN_TX_ONLY` continua significando que o objeto, mesmo após persistido, **não representa autorização de protocolo de ACK**. O teste B demonstra sobrevivência a **uma nova conexão após COMMIT**, **não** prova fsync em falha de energia, restauração de backup, queda/crash real, `COMMIT_UNKNOWN` causado por desconexão na janela crítica, RLS e revogação concorrente.

## Evidência efetivamente executada nesta etapa

- **5/5 testes Python do executor efêmero PASS**, todos com ferramentas Postgres simuladas: recusa de URL/argumentos extras, ausência dos binários, versão incompatível, ordem de 3 conexões separadas com desligamento e isolamento de variáveis de ambiente remotas. `bash -n` passou. O teste de root real recusou iniciar.
- Conferidos por leitura após publicação os **4 blobs Git idênticos** aos arquivos locais verificados:
  - `run-wa06d-ephemeral.sh`: `afa91da5be864ca9b560b211bef26ba37d236ddd`.
  - `test_wa06d_ephemeral_runner.py`: `59bc4133ebed007f941652c87d10b18115df28bc`.
  - `wa06d_pg17_postcommit_setup.sql`: `b9f3e3d846cfdb9dec67ad27eedf9a6f823b8a9e`.
  - `wa06d_pg17_postcommit_verify.sql`: `1aac81e1e3b6cfe37d937b44673aaf130bbd850c`.
- **0/14 WA06D-A e 0/6 WA06D-B executados em PostgreSQL = 0/20 testes SQL.** Não havia `psql`, `postgres`, `initdb`, `pg_ctl` local; tentativa de obter pacotes via gerenciador não teve sucesso. SQL ainda pode exigir reparos após primeira execução; não atribuir GO de atomicidade ou atualizar progresso operacional.

**Comando recomendado, exclusivamente em computador não-root que disponha de PostgreSQL 17 local:**

```bash
bash integrations/whatsapp-meta/lab/run-wa06d-ephemeral.sh
```

**Próxima etapa [R S0]:** executar esse runner em ambiente de laboratório e revisar logs; depois ensaiar duas sessões realmente concorrentes, fonte autenticada de identidade e escopo revogável, autenticação de App/WABA/emissor, chave HMAC/nonce transacionais, payload protegido e recibo **pós-commit autoritativo**, com tratamento de `COMMIT_UNKNOWN`. Continuam pendentes DEC-WA-04/06 e homologação operacional. Nenhuma Graph API, POC concessionária de demonstração, plano pago, deploy ou merge executados.
