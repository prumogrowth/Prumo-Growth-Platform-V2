# I86 manual — checkpoint de desenvolvimento bloqueado

28/10/2026, America/Sao_Paulo. **LAB_BLOCKED**: implementação preparada, sem certificação SQL/E2E desta continuidade.

Base exata dbf49ab19b73766d60678c4ce6f7dea56cd66c9b, tree9d2f54b8753d4afadf5175ee5b332510890f1772. Branch exclusiva exp/s1-i86-manual-director-20261028, [PR Draft51](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/51). A I86 histórica e I85 permanecem intactas.

**Código candidato, não certificado:96a7c5ff054ec3be9d15237803914ac247292e61**, treebd8379a5e708f15f89c951492a3c9299e2e6ddbb. [CI40774122852](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40774122852):FAIL em duas tentativas, sem runner atribuído e sem nenhum step. Os três jobs físicos ficaram SKIPPED,31 testes novos não executados, nenhum artifact. Logs do job indisponíveis/BlobNotFound. A causa subjacente do GitHub não pôde ser obtida pelo conector; não se atribui a billing/quota por inferência.

Implementado instrumento SQL INVOKER APPOINT/REVOKE/REACTIVATE, CAS, idempotência, evidência manual vinculada, auditoria atômica, confirmação por reconciliação MVCC posterior e retirada de sessões. Nenhum endpoint, CLI operacional, login ou grant comum novo. Vários Diretores são permitidos; substituição automática e conversão de cargos legados não foram criadas. A rotina não chama o bootstrap I85.

**Local PASS:**13 testes de escopo +5 contratos históricos +4 política manual, normais e -O;288 unidades backend; AST Python e parse YAML. Checker aplicado ao worktree:PASS, zero violações. Isso não substitui SQL real, RLS efetiva, concorrência, COMMIT, GoTrue/Edge ou presença humana. Parser/servidor PostgreSQL, psycopg e Supabase CLI não estão disponíveis localmente, e o proxy shell está inacessível. Nenhum recurso compartilhado foi usado.

D01–D05 reclassificadas segundo a política expressa do responsável: operação somente humana privilegiada; não se impõe quórum ou prazo. Identidade nominal, custódia/evidência operacionais e continuidade não decidida continuam pendentes. Não se alega que RLS distingue humano de IA com credencial postgres comprometida.

Próxima execução: orquestração investigar a falha de inicialização dos runners no GitHub e reexecutar o workflow exclusivo nesta branch; exigir os quatro jobs,31 casos novos,22 herdados e uma jornada I85, inspecionar logs/artifacts e comprovar descarte. Corrigir somente dentro da allowlist; se depender de compartilhado, encaminhar sem alterar. Até isso, não promover a LAB_CLOSED/CONDITIONAL por inferência.

Documentação posterior é somente documental; SHA exato no PR/histórico. Leia RELATORIO.md, CONTRATO_MANUAL_V2.md, RUNBOOK_RESTRITO.md, MANIFESTO.json, MATRIZ_VALIDACAO.json e EVIDENCIA_CI_BLOQUEADA.json. Sem merge, deploy, Supabase hospedado, usuários/Diretores reais, Frontend ou Meta.
