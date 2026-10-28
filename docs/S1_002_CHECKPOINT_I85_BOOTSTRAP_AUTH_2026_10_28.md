# S0/S1 — checkpoint I85 — auditoria independente do bootstrap Auth

28/10/2026, America/Sao_Paulo. **I85_LAB_CLOSED — recomendação técnica limitada ao laboratório**, submetida à avaliação final da orquestração.
Não iniciar I86. Nenhuma autorização de produção ou nomeação real.

## Fonte vigente e histórico

- Branch: `exp/s0-s1-i85-bootstrap-auth-diretor-20261028`.
- [PR Draft #42](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/42), base experimental I84, sem merge.
- HEAD encontrado: `0d3beb4f9e0ee32ce088c591125b9d61ef43173f`; código anterior `840b2db7299d024c03ced2e5120b241a23046a0e`; CI40664481472 SUCCESS, cinco jobs. Esse resultado histórico provava uma jornada encadeada com 13 pontos; não demonstrava resistência independente, exclusividade entre candidatos distintos ou ausência de credenciais no runtime.
- [Checkpoint anterior preservado no commit original](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/0d3beb4f9e0ee32ce088c591125b9d61ef43173f/docs/S1_002_CHECKPOINT_I85_BOOTSTRAP_AUTH_2026_10_28.md). Sua recomendação de avançar para I86 e a afirmação de ausência de service_role na Edge ficam substituídas pela auditoria atual.
- Base I84 preservada: código `6852a4f509df8466e35da46ba995a4ac2ed5e1f7`, checkpoint `3bf948fe67d439d93f6c848300ea2e5e053311ed`, PR40/CI40622136488.
- S1 fixada em `8780b576aa18bd3983c063339e2e42d2452af22c`.

## Correções atuais

Journal interno v2 com escrita durável, recuperação explícita e retenção de resíduos; custódia única/trava nas interfaces CLI e Python; binding físico estável; aprovação recuperada exige ratificação; UUID canônico GoTrue/SQL; grant inicial serializado; revogação com ordem de locks compatível e retomada exclusivamente negativa; status/descarte com prova SQL; init/dispose retomáveis após SIGKILL; parser sem eco.

O perfil restrito I85 usa o mesmo Runtime oficial e o TypeScript I82 sem mudanças, mas retira service_role, URL postgres do instalador e segredo JWT desde a criação do container. Bootstrap recusa worker legado, e marcador da stack impede fallback ao perfil anterior. Hook limitado em `local_admin/worker.py` somente nesta branch; a branch I84 histórica permanece intacta. Nenhuma alteração de SQL comercial, grants, owners, HTTP candidato, F02 ou Frontend.

Cargo Diretor/estado ativo permanecem como classificação histórica após revogação, conforme I79; a competência global inativa impede administração. Conta Auth não é banida por inferência: novo login pode funcionar, mas não restaura autoridade. Bootstrap não é substituição ordinária de Diretor e permanece único por laboratório, inclusive após revogação.

## Evidências vigentes

Código certificado neste escopo laboratorial: `062c90ffbe2b223c1d6bb08f614e7a1b6a898201`.
[CI final 40680048140](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40680048140), **SUCCESS, seis jobs concluídos e artefatos inspecionados**.
A primeira rodada independente 40675928138 ficou FAIL: 26/27 provas reais; uma contenção instrumentada na tabela errada foi corrigida sem flexibilizar a invariante. Não foi tratada como fechamento.

Resultados finais: resistência **29/29**, zero skips, 29 descartes comprovados e catálogos iguais; filesystem **7/7** e I84 boundary **9/9**, normal e Python -O; jornada I85 **um teste/13 pontos**; I84 **um teste/16 pontos**; backend288, Deno14, I79/G1 62, I80 33, I81 14, I82 HTTP20 e I83 35 preservados. Refresh revogado REJECTED; novo login Auth sem competência administrativa. Artefato de resistência12813622741, SHA256 ZIP `809c56d574c8a398138cc381b34e24e0b4263e0bd9f4564954b701c297c97858`.

A matriz completa, resultados/jobs/artefatos e classificação final ficam em:

- [Relatório A–H](contratos/i85_auth/RELATORIO_AUDITORIA_INDEPENDENTE.md).
- [Matriz estruturada](contratos/i85_auth/MATRIZ_AUDITORIA.json).
- [Contrato local v1 revisado](contratos/i85_auth/BOOTSTRAP_E_RECONCILIACAO_V1.md).
- [Runbook de bootstrap, recuperação, revogação e descarte](contratos/i85_auth/RUNBOOK_AUDITADO.md).
- [Impacto herdado registrado antes da mudança](contratos/i85_auth/IMPACTO_DA_AUDITORIA_EM_COMPONENTES_ANTERIORES.md).

## Próxima ação segura

Encaminhar o relatório e a matriz à auditoria final da orquestração; as provas de descarte foram verificadas. Nenhuma nova rodada corretiva é necessária para os requisitos laboratoriais testados. Não iniciar I86 nesta execução. Produção, nomeação de Diretor real, governança organizacional, TLS/custódia hospedada, revisão Frontend, homologação e rollout continuam gates próprios. F02 G01–G06 parciais/G07 pendente, sem mudança comercial. Sem merge, deploy ou Supabase hospedado.

Este checkpoint documental é posterior ao código testado. Seus commits exatos são registrados no relatório/PR; commits somente documentais usam `[skip ci]`, sem alterar o tree de código certificado nem atribuir CI a código não executado.
