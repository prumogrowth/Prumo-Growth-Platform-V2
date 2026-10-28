# I86 — relatório de desenvolvimento isolado e governança candidata

28/10/2026, America/Sao_Paulo. Resultado: I86_LAB_CONDITIONAL. Provas técnicas autorizadas concluídas; operação de governança depende de decisões externas ainda não ratificadas. Nenhum ato organizacional foi ratificado.

## Estado recuperado

Base compartilhada exata 3cab3d57619cc1157698a08ac26f34e0c363f6dd, tree09e597b763bd6026fe6fb9686e3471e42f87bd3a; I85 código062c90ffbe2b223c1d6bb08f614e7a1b6a898201, PR42 Draft, CI40680048140 SUCCESS/seis jobs. A branch I86 não existia antes desta execução e foi criada desse commit, sem force. Não foi derivada de main, Meta ou novo HEAD não auditado.

Branch exclusiva exp/s1-i86-governanca-autoridade-20261028; [PR Draft49](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/49), base I85 congelada. Worktree de edição próprio; nenhum Docker/Supabase foi iniciado no ambiente compartilhado do Codex.

O inventário remoto de branches/PRs e a busca no repositório não localizaram contrato oficial I86. Os contratos I79–I85 e implementações canônicas foram recuperados; esta entrega propõe contrato candidato, sem ratificação unilateral.

## Diagnóstico e decisões

Identidade Auth, classificação de equipe, competência global, administração ordinária e capacidade técnica do instalador são coisas distintas. O UUID vem do GoTrue e é o mesmo em auth.users/public.atores. auth.sessions comprova sessão viva; equipe Diretor/ativo exige ainda competência global ativa para I79/I80. Service_role e postgres não são Diretores humanos. Metadados/claims isolados não autorizam promoção.

I85 continua bootstrap único sintético; não é nomeação repetível. Sua retirada conserva classificação histórica, desativa competência e retira sessões. Novo login não é recuperação de autoridade. A política para nomear, substituir, aprovar, recuperar ou revogar organizacionalmente não foi definida pelos contratos atuais. D01–D05 estão em DECISOES.json, com encaminhamento à orquestração e responsável organizacional a designar. Não foi inventado quórum, prazo de mandato, sucessor ou poder do Diretor atual.

## Implementação efetiva e seus limites

- integration/i86/authority.py reutiliza SupabaseGoTrueVerifier, Bootstrap.owned e a barreira cfi01_session_valid_local. A ferramenta do instalador observa apenas o sujeito autenticado, com revalidação SQL após locks e snapshot/hash gerados no servidor.
- integration/i86/observation.sql cria somente duas tabelas privadas de evidência/auditoria no schema prumo_i86_lab. RLS/FORCE RLS, sem grants aos clientes ou Edge, função INVOKER imutável. Nenhuma função de nomeação, owner operacional, novo login, membership ou grant herdado.
- Observação e auditoria têm COMMIT conjunto, CAS de snapshot e idempotência por ator/sessão/chave. Replay revalida estado, não devolve permissão positiva revogada. O digest xmin é técnico e conservador, não versão de mandato ou contrato comercial.
- governance_gate mantém APPOINT_DIRECTOR, REPLACE_DIRECTOR, REACTIVATE_AUTHORITY e REVOKE_ORGANIZATIONAL_AUTHORITY como PENDING_DECISION, operationally_enabled=false. OBSERVED não aprova nenhuma dessas operações.
- scope.py verifica base/tree, cada commit e diff acumulado, remoções/renomes, modos perigosos e estado local staged/unstaged/untracked/ignored; FAIL/exit1 bloqueia a CI. Até edição depois revertida é detectada.
- sandbox.py exporta o HEAD Git verificado para RUNNER_TEMP em VM GitHub-hosted exclusiva. CLI escreve seus caches nessa cópia, sem sujar fontes herdadas. Fonte S1 fixada em8780b576aa18bd3983c063339e2e42d2452af22c. O mesmo número de porta/nome herdado em VMs distintas não representa compartilhamento físico.
- cleanup.py só chama retirada negativa existente e destruição do próprio laboratório. Não apaga incerteza; abandono após destruição exige a prova/opt-in I85. Hash da identidade física permite distinguir os dois laboratórios sem divulgar credenciais.

A conexão postgres dessa observação é ferramenta de ensaio do instalador, nunca API ou autorização de negócio. Transformá-la em serviço exigirá contrato organizacional e owner/login mínimos em incremento aprovado; esta execução não faz esse provisionamento. HMAC/nonce continuam nas portas I79/I80, não são substituídos pela evidência I86.

## Testes, falhas e correções

Local: 11 testes adversariais de escopo, cinco DTO/modelo, ambos também Python -O, e288 testes backend PASS. O parser PostgreSQL aceitou a fixture, o que não equivale a execução SQL.

Primeiro código a6ceacb639b08603edd1488a2b7942bb50042301, CI40731027793: FAIL. Gate de escopo/modelo PASS; os dois jobs físicos pararam antes dos testes no preflight herdado, chamado como caminho de script na cópia isolada. Causa comprovada no log E2E: ModuleNotFoundError: integration. Artefato12834957631 registra0/22 executados,22 NOT_TESTED; ambos os laboratórios foram descartados e escopo final PASS. Essa rodada não é evidência de integração.

Correção c1b66cb009a56e2049148f118395ab5cb98dc4ea: mesma ferramenta herdada chamada por python -m, sem editar I83. Hash usa sha256 nativo PG17 para não pressupor schema de pgcrypto; limpeza registra hash físico e trata estado parcial conservadoramente.

[CI candidata40731718955](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40731718955) **SUCCESS, três jobs**, concluída em 28/10/2026 14:05:42 BRT (17:05:42 UTC). Código testado exato c1b66cb009a56e2049148f118395ab5cb98dc4ea, tree ea02668e7034394ba12d0bc79e1693fb5ed42a93. Foram executados **22/22 casos reais**, zero skips e zero NOT_TESTED entre os casos planejados, em189,986s, além da jornada I85 original de **um teste/13 pontos**, em25,915s. Os artefatos foram baixados e inspecionados; a CI não foi usada isoladamente como prova. Wrappers de falha apenas agendam SIGKILL de processos com Auth/SQL reais; não simulam resultados como único critério.


### Jobs e artefatos inspecionados

| Job | ID | Resultado |
| --- | --- | --- |
| scope-and-model | [122969498982](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40731718955/job/122969498982) | SUCCESS |
| i86-real-authority | [122969729921](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40731718955/job/122969729921) | SUCCESS |
| inherited-i85-e2e | [122969730081](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40731718955/job/122969730081) | SUCCESS |

| Artefato | ID | SHA256 ZIP |
| --- | --- | --- |
| Escopo/modelo | 12836100118 | ccb30eff4f0a9746f3d8b9683c7e885aa6a1c6714632ac70f5076776f4530d98 |
| Jornada herdada I85 | 12835745913 | 370e0e887e658737f8923afcac862735debc7ba51450aadc4b7dc0fe46aec0fc |
| Provas reais I86 | 12834664649 | 543eb2cf1ef5ad24df19ff4d4675ae2128317607c4e64edad8dc964be2087969 |

SHA256 do JSON real: dc49fe86a39a13b7d6a9582eb80a6349f33728d33d7e582ad0ee41682e39ac09.
MATRIZ_VALIDACAO.json preserva cada caso, camada, resultado, limite, flags de limpeza e hashes dos membros; os artefatos originais têm retenção de14 dias. Não foram versionados dumps, journals privados, tokens, senhas ou logs brutos.

Comprovado: identidade/sessão canônica; classificação sem competência; metadata e service_role sem promoção; CAS obsoleto; replay e concorrência; logout/expiração, inclusive durante espera; SIGKILL pré-COMMIT com rollback e pós-COMMIT com reconciliação; falha de constraint diferida sem sucesso falso; ACLs privados; negação de SET ROLE; evidência imutável; rotação do perfil restrito; revogação que drena leitura anterior e recusa solicitação cuja identidade fora verificada antes do corte. Novo login após retirada continua sem competência; cargo/estado históricos conservados e rebootstrap recusado.

Não comprovado como operação: corrida entre duas nomeações organizacionais aprovadas, quórum de aprovação, substituição real, recuperação da última autoridade e revogação humana ordinária. Essas funcionalidades são PENDING_DECISION; o caso11 mede apenas duas observações concorrentes e não as certifica.

Ambos os laboratórios terminaram resources_absent=true, private_material_removed=true, physical_identity_complete=true e sem evidência incerta abandonada. Hashes físicos distintos:

- E2E herdado: 0d9cb8791fb6f61f116a7bd930069722e021a1386b860d264cb3515ec2a74172.
- I86 real: 4671dc5847014e0e41247e3982dc641b5de94d15fc1aea95d4216fdea16f1e9c.

Catálogo I86: igualdade completa do catálogo herdado, normalizando apenas LOGIN temporário I83, e zero correspondências de material sensível nos logs. Jornada I85 acusa ausência física de credenciais do instalador no runtime e zero correspondências. Retirada não promete destruição forense de RAM/WAL/backups. Observação é histórica, não um bearer de autorização futura.

## Regressões e integridade

A matriz distingue unidade, modelo, SQL e E2E. O job herdado reexecuta a jornada I85 original, passando pelos seis comandos I79/I80 e recusas, HMAC/nonce, CAS, idempotência, ownership, sessão e perfil Edge restrito. O job I86 compara catálogo herdado completo antes/depois, normalizando somente o bit LOGIN temporário do executor I83. Não se normaliza nova policy, owner, grant, trigger, constraint ou função.

As suítes completas CFI, I79/G1 62, I80 33, I81 14, I82 20, I83 35 e I85 resistência29 têm baseline na CI40680048140 da fonte imutável. Não foram reexecutadas integralmente como suítes separadas nesta I86 e não são apresentadas como novos PASS. A prova nova necessária combina ausência de alteração de fontes, igualdade de catálogo, jornada real das seis portas e concorrência/revogação do novo observador.

Refs rechecadas ao final: main dace737ab7afb7ae3f5a3a6f5cb522e6def8b43a; I85 3cab3d57619cc1157698a08ac26f34e0c363f6dd; S1 8780b576aa18bd3983c063339e2e42d2452af22c. PR49 continua Draft, não merged, base exatamente3cab3d5. Verificador local após documentação inventariou18 arquivos autorizados e zero violações; os11 hashes de código/workflow coincidem com o SHA efetivamente testado. Nenhum arquivo herdado foi editado; allowlist fixa não foi ampliada. Código, SQL de fixture, ferramentas, testes, documentos e workflow novos estão somente nas três áreas autorizadas. I85 permanece histórica. Sem merge, deploy, main, usuário real, Supabase hospedado, Frontend, F02 ou chamadas comerciais.

O isolamento comprovado é físico (VM/engine/rede/custódia) e do material dedicado I83 e das senhas sintéticas geradas. Permanecem as chaves JWT de desenvolvimento herdadas do CLI, cujo valor padrão não é promessa de emissor criptograficamente exclusivo entre projetos — limite já registrado na auditoria I85. Não foram trocadas credenciais entre conversas, nem houve acesso a recursos da Meta. Homologar emissor/chaves produtivas ou mudar configuração herdada exigirá escopo próprio; esta I86 não o faz.

## Conflitos e interfaces futuras

Não houve necessidade de corrigir arquivo herdado nesta entrega. Se aparecer falha que exija isso, sua alteração fica fora desta I86 e deverá ser encaminhada à orquestração. Não há dependência da frente Meta: M2M, webhooks, persistência, ACK e recibos de ingestão não foram desenvolvidos/importados. Administração humana futura de canais é interface a decidir.

## Recomendação e encaminhamento

**I86_LAB_CONDITIONAL**: a implementação laboratorial permitida e suas provas foram concluídas, mas as decisões organizacionais D01–D05 impedem o funcionamento operacional das transições de governança. Não há falha técnica pendente nos casos executados; a condição é externa e não pode ser resolvida por inferência no código. D01–D05 continuam PENDING_DECISION, independentemente de testes de modelo passarem. O contrato é candidato. A orquestração deve avaliar as provas técnicas e definir os responsáveis pelas decisões organizacionais, sem autorização automática de nomeação, hospedagem ou integração com outra frente.

## Checkpoint e próxima ação segura

Código certificado nesta rodada laboratorial: c1b66cb009a56e2049148f118395ab5cb98dc4ea, CI40731718955. Documentação posterior altera somente docs/contratos/i86_authority e usa [skip ci]; o SHA documental exato fica no histórico/PR49. MANIFESTO.json fixa a base, os11 hashes de código/workflow e o inventário documental; os relatórios de escopo da CI inspecionam também todo o histórico e o estado local.

Próxima ação: auditoria independente da orquestração sobre PR49 e ratificação explícita, se desejada, de D01–D05. DECISOES.json oferece alternativas não aprovadas e recomendações técnicas de evidência, sem escolher órgão, pessoa, quórum ou prazo. Somente depois disso caberá uma nova execução para implementar a primeira transição autorizada e revisar seu owner/runtime. Esta entrega não fecha governança operacional, não integra Meta e não autoriza avanço automático, merge ou deploy.
