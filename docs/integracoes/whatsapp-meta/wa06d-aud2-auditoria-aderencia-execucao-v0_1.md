# WA-06D-AUD2 — auditoria independente das últimas entregas Meta/S0

**Data:** 18/10/2026. **Natureza:** revisão de execução, evidência, segurança e alinhamento com a plataforma de atendimento comercial. **Estado final:** dois reparos aplicados, um descompasso de teste explicitado; nenhuma homologação do ingresso.

## Resultado da auditoria e medidas concretas

| Severidade | Achado demonstrável | Ação / situação |
|---|---|---|
| Alta — cobertura funcional | `wa06d_pg17_postcommit_setup.sql` insere manualmente em **tabelas novas** `wa06d_postcommit.*`. Os seis casos B01–B06 verificam essas inserções, **não invocam** `pg_temp.wa06d_accept` de WA-06D/A, tampouco a rota S0-029/032/033. Portanto, mesmo com 20/20 verdes no futuro, **não haveria prova de integração do ingresso real**, autenticação ou decisão sobre HTTP ACK. | **Corrigida a classificação da evidência**, não o contrato operacional: WA-06D/B é somente experimento independente de semântica PostgreSQL após COMMIT. Integração com fonte S0 real fica como próximo gate, não uma implementação silenciosa. |
| Alta — limpeza segura | Runner anterior ativava `started=true` **somente após** `pg_ctl start` retornar sucesso; se start falhasse após gerar processo, o `trap` não tentava desligá-lo e podia apagar os diretórios de cluster/socket em uso. Também ignorava uma falha de desligamento no fluxo normal. | **Reparado** no `run-wa06d-ephemeral.sh`: marca tentativa antes do start, sempre tenta stop depois de tentativa, verifica `pg_ctl status`, **preserva diretório e falha com código 70** se servidor continuar ativo; não afirma destruição sem confirmação. Mensagem final revisada para anunciar verificação de desligamento pendente, sem prometer exclusão antecipada. |
| Média — recibo ambíguo | O exemplo persistido em WA-06D/B tinha `state='IN_TX_ONLY'` mesmo após `COMMIT`. Esse rótulo confundia artefato durável fictício com resposta de transação/ACK. | **Reparado** nos SQL `wa06d_pg17_postcommit_setup.sql` e `wa06d_pg17_postcommit_verify.sql`: estado explícito `FIXTURE_COMMITTED_NOT_ACK`, com assertiva do valor após o COMMIT. Continua sem autorização para ACK. |
| Gestão — repetição de preparação | WA-06D/A, A2, A3 e B acumularam artefatos e verificações estáticas, porém **nenhum cenário real em PostgreSQL** foi executado. O avanço apresentado poderia sugerir maturidade maior que a comprovada. | **Congelar novas expansões artificiais da matriz** até PG17 descartável executar a suíte atual. Prioridade após execução: integração na API/transaction S0, concorrência e identidade real; não aumentar porcentagem do planejamento. |

## Evidência verificada nesta auditoria

- O ambiente de execução dispõe de `pg_config` da biblioteca libpq 17.11, mas **não** de binários `postgres`, `psql`, `initdb`, `pg_ctl`; não foi iniciada nenhuma sessão PostgreSQL.
- Executei `python -m unittest -v test_wa06d_ephemeral_runner.py` numa cópia local **byte a byte idêntica** ao arquivo Git publicado: **7/7 testes Python PASS**, incluindo falha simulada na inicialização e desligamento não confirmado. `bash -n run-wa06d-ephemeral.sh` PASS. Hashes Git de código ensaiado e publicado: runner `3057062b31d1e7c63f8c26a9bac9c4508ce71890`; teste `1c8e49fbbb6d1fe88e5da9173fc0464c002c7af5`.
- O próprio runner, invocado como root real e sem binários PostgreSQL, **recusou com exit 77**, antes de acesso a qualquer banco.
- SQL pós-COMMIT atualizado: setup blob `dc159fc4c00ee6f4708fa563d74f189ea5ce098c`, verificação blob `ecb690e78647bf209cc17b32ed53cfc4ad152472`, leitura no GitHub após atualização. Eles **não** foram executados em PG, nem validados por CI.
- **0/14 WA-06D/A + 0/6 WA-06D/B = 0/20 testes PostgreSQL**; não existe prova de persistência, recuperação real, crash/COMMIT_UNKNOWN, ACK, assinatura, RLS, atendimento humano/IA ou Meta comercial nesta etapa.

## Aderência ao objetivo final e limites

O trabalho Meta contribui ao requisito estrutural de **atendimento comercial por IA com transferência definitiva para operador humano**, múltiplas concessionárias isoladas, autorização de janela/templates pela Meta, histórico recuperável e envio ao banco somente pelo operador no fluxo permitido. **LiberaCred é o produto da instituição financeira, não o nome da plataforma**.

Porém, a documentação normativa separa *prontidão documental do planejamento* de *progresso de implementação*; seus pontos não podem subir por testes fictícios. O pacote documental de 17/10 registra **69/100 para planejamento** no documento 19F, não 69% de código entregue. Nenhuma atualização dessa régua é reivindicada aqui. S0/Meta/OpenAI/CF-OP-02 têm frentes e decisões pendentes que não se tornam homologadas por este ensaio.

**Direção corrigida:** parar de produzir variantes do mesmo experimento em memória/TEMP; priorizar (1) **execução real da suíte existente em PG17 descartável e logs por SHA**; (2) demonstração **integrada** com tabelas/funções S0, não inserções paralelas; (3) duas sessões concorrentes, isolamento App/WABA/emissor→loja, serviço autenticado, nonce/revogação e recibo autoritativo `COMMIT_UNKNOWN`; (4) avaliação de cada gate sem inferir autorização Meta/Banco/LGPD. No atual ambiente (sem PG17), o bloqueio técnico continua transparente e **não exige nova decisão de negócio**.

**Restrições respeitadas:** apenas arquivos de branch GitHub e cópia local de teste; PRs Draft, sem merge; sem acesso a Supabase hospedado, POC concessionária de demonstração, Meta Graph, instituição financeira, mensagens reais, custos ou provisionamento em produção.
