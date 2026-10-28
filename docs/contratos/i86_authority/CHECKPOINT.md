> Continuidade manual: a política D01–D05 deste registro histórico foi atualizada pela instrução expressa do responsável. Consulte [contrato manual revisão 2](manual/CONTRATO_MANUAL_V2.md) e [checkpoint manual](manual/CHECKPOINT.md). Os resultados técnicos históricos abaixo permanecem limitados à sua revisão original.

# I86 — checkpoint de desenvolvimento e evidências

28/10/2026, America/Sao_Paulo. **I86_LAB_CONDITIONAL**: provas técnicas concluídas, decisões organizacionais D01–D05 pendentes. Não é autorização operacional.

Base imutável: 3cab3d57619cc1157698a08ac26f34e0c363f6dd, tree09e597b763bd6026fe6fb9686e3471e42f87bd3a. Branch exclusiva: exp/s1-i86-governanca-autoridade-20261028. [PR Draft49](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/49), base I85 histórica intacta.

Código testado: **c1b66cb009a56e2049148f118395ab5cb98dc4ea**, tree ea02668e7034394ba12d0bc79e1693fb5ed42a93. [CI40731718955 SUCCESS/três jobs](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40731718955). Commit inicial a6ceacb639b08603edd1488a2b7942bb50042301/CI40731027793 falhou na preparação por import path do preflight:0/22 físicos; correção somente nos chamadores I86, sem editar herdados.

Implementado: checker de escopo obrigatório; observação transacional de identidade/sessão/cargo/competência, CAS e idempotência; duas tabelas privadas de evidência/auditoria do instalador; gates fixos PENDING_DECISION; sandbox de fonte exata e retirada negativa com prova física. Não há endpoint, nova nomeação, novo login/grant herdado ou rebootstrap.

Resultados: **22/22 reais**, zero ignorados, 189,986s; jornada I85 original **um teste/13 pontos**, seis comandos I79/I80, 25,915s; 11 testes Git adversariais + cinco DTO/modelo normais e Python -O; 288 unidades backend. Escopo PASS antes/depois em todos os jobs. Catálogo herdado igual, credenciais do instalador ausentes na Edge, zero material detectado nos logs e dois laboratórios com identidades físicas distintas completamente descartados. Artefatos12836100118,12835745913,12834664649, hashes e casos na matriz.

As suítes históricas completas não reexecutadas estão identificadas como BASELINE_ONLY na matriz, com fonte imutável CI40680048140; não são novos PASS desta I86. A compatibilidade nova é provada por escopo, catálogo, jornada real e concorrência do observador.

Documentação posterior é somente documental, [skip ci], sem alterar os11 arquivos de código/workflow testados. SHA documental no histórico e PR49. Arquivos novos somente nas três áreas autorizadas; I85, Meta, Frontend, F02, backend e migrations permanecem intactos.

Leia [RELATORIO.md](RELATORIO.md), [CONTRATO_CANDIDATO_V1.md](CONTRATO_CANDIDATO_V1.md), [DECISOES.json](DECISOES.json), [MATRIZ_VALIDACAO.json](MATRIZ_VALIDACAO.json), [MANIFESTO.json](MANIFESTO.json) e [DIAGNOSTICO_E_INTERFACES.md](DIAGNOSTICO_E_INTERFACES.md).

Próxima ação: revisão da orquestração e decisão organizacional D01–D05; nenhuma transição será habilitada por este checkpoint. Sem merge, deploy, usuário real, Supabase hospedado ou integração Meta.
