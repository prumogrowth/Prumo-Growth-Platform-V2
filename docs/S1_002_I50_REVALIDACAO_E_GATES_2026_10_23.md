# S1-002 / I50 — CAS, revogação em voo e mapa de encerramento

**Atualização vinculante pós-I50, 23/10/2026:** A2 foi fechada [D]: transferência/atribuição nova para Consultor com intake pausado é proibida, inclusive manual ou por exceção. Ver [I51](S1_002_I51_DECISAO_A2_TRANSFERENCIA_2026_10_23.md). A referência histórica a A2 [R] neste documento registra somente o estado anterior à decisão.

**Data:** 23/10/2026. **Classificação:** laboratório [T/P], decisões de negócio [D]/[DN], integrações e aceites externos [R]/[V]. Não utilizar como migration operacional. Branch `feat/s1-002-equipe-prumo`, PR #5 Draft.

## I50: questão técnica

I49 comprovou, somente na fixture postgres, primeiro commit vencedor para dois Gestores autorizados. I50 aumenta a força desse ensaio: uma transação de assunção **já iniciada, mas aguardando o lock do lead**, precisa rever o grant de concessionária e o estado ativo da equipe **após adquirir o lock**. Uma concessão revogada enquanto a chamada aguarda não deve virar novo direito por snapshot anterior. A autorização de uma consulta de fila não vale como autorização automática de assunção.

A função privada `prumo_s1_i50_test.assumir_versao_mock` em `supabase/tests/s1_073_fila_cas_revalidacao_local_only.sql` é um espelho experimental S0, **não** RPC do produto. Exige papel do executor postgres, lock `FOR UPDATE` no lead, rechecagem de loja e Gestor, marcador explícito em estado pendente, versão esperada e inexistência de caso anterior. Insere caso/atribuição e marca resolvido em uma única transação; mensagens e históricos não são liberados. Os clientes não têm EXECUTE nessa função.

`scripts/test_s1_002_i50_fila_revalidacao.py` emprega a stack GoTrue da I44–I49, duas conexões postgres para controlar a espera e duas competidoras independentes para a disputa. O teste verifica no catálogo `pg_stat_activity` que a chamada ficou bloqueada **antes** de revogar autorização numa terceira transação.

### Critérios I50 — somente laboratório
1. Versão CAS desatualizada e lead sem marcador explícito falham fechados, sem caso/atribuição.
2. Grant da loja revogado enquanto a chamada está bloqueada: rechecagem após liberação do lock rejeita, preserva pendência e não cria caso.
3. Ator S1 suspenso enquanto a chamada está bloqueada: o mesmo comportamento, com JWT da sessão inalterado.
4. Fila noutra concessionária não concede direito de assumi-la sem grant próprio.
5. Dois Gestores ainda autorizados concorrem com mesma versão: exatamente um `APPLIED`, outro `ALREADY_CLAIMED`, sem segunda titularidade; retry vencido rejeitado.
6. Marcador resolvido some da projeção, mas isso não desbloqueia leitura de mensagens, D2/D3/D4 ou função privada de assunção.

## O que falta para efetivamente encerrar S1-002

**Base de referência:** contrato funcional S1 de 22/10/2026 e matriz de aderência (28 decisões documentadas, cujo status **não significa implementação**). Os incrementos I44–I50 demonstram permissões e cenários em bancadas locais; CI verde **não** comprova que a S1 se integrou à operação.

| Gate / frente | Estado observado | Entrega ainda necessária |
| --- | --- | --- |
| **G1 Distribuição/fila** | Regras [D/DN]; I49 e I50 mocks, CAS/concorrência locais [T] | S0 produzir evento real de pendência por caso/lead, versões e locks oficiais, distribuir lead novo entre equipes, assunção manual e retorno de elegibilidade, sem tocar casos já atribuídos |
| **G2 RBAC/equipe/intake** | SQL e GoTrue de teste para equipe, concessões, revogação e intake histórico [T] | Unificar autoridade do Diretor, vínculo de chefia única, tela/serviços reais de pausa, retomada, transferência e supervisão; manter conta/casos operantes durante pausa |
| **G3 Exceção/histórico** | RLS por caso e contato sintéticos [T]; I45–I48 superfície de leads/eventos investigada | RLS e consultas definitivas do histórico completo do mesmo contato na mesma loja; revogação em voo e após perda do caso, mídias/anexos e permissões D2 versus D3/D4; integrar entitlement à S0 |
| **G4 Primeiro contato e indicador** | I36 histórico, regra COUNT/DOT/NONE revisada [D] | Produtor real do primeiro ato humano e entrega, estados SENT versus DELIVERED, segmento atual, leitura própria após transferência, saída humana versus sistema, reset por conclusão e concorrência |
| **G5 Conclusão/F03** | Contratos e experimentos CFI/S0 [T/R] | Serviço real de conclusão, cutoff, versões e ordem de locks S1→S0, F03 autorizada por caso, tarefa de pendência/retorno ao Consultor ou Gestor, controles de ficha e provas Banco |
| **G6 Homologação** | CI PG17 e GoTrue locais; PR Draft | Consolidação com S0, testes integrados positivos/negativos multi-loja e cenários de falha/retry, UI/UX, segurança, segregação de dados, operação e validação Meta/Banco/LGPD aplicáveis |

**A2 [R]** — transferência manual para Consultor com intake pausado — continua a única decisão funcional expressamente em aberto no mapa, sem presumir que uma recusa conservadora do protótipo seja regra definitiva.

**Leitura gerencial para planejamento:** os contratos centrais estão detalhados e existem vários controles locais bem testados. Entretanto **ainda falta trabalho relevante de integração e validação** nos seis gates. Não há base confiável para afirmar um percentual de produto pronto, nem para chamar a S1 de quase pronta apenas por ter dezenas de ensaios verdes. Um fechamento restrito de escopo do *laboratório S1* é diferente de um fechamento operacional da *frente S1-002*.

## Segurança e limites

Estas provas não aplicam migrations operacionais S0, não usam autenticação de usuários reais/Meta/Banco, não aprovam upload/anexos nem expõem uma API real de fila. `pg_stat_activity` confirma concorrência somente entre sessões controladas na topologia descartável, não cobre todos os escritores S0, alterações Meta ou atrasos de rede. Requer homologação do produtor real de evento/versão e de lock compartilhado no núcleo S0 antes de proposta de merge.

## Evidências

**CI conferido em 23/10/2026.** Código em `287792e8cba15b2aa7378e4e686ada58c28f306e`:

- [GoTrue/PostgREST real local, run #39942963303](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39942963303), job `120379274711`: **SUCCESS**. Logs abertos e conferidos: **`PASS I50-01` até `PASS I50-06` (6/6)**; também `PASS I49-01..06` na mesma execução. A confirmação de espera no lock e a revogação concorrente são duas provas de bancada, não certificação do serviço produtivo.
- [Regressão completa PG17 S0/S1, run #39942925177](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39942925177): **SUCCESS** em `61a2f7f948ad9f98f62ca210d398ba0d94eb7547` (commit com os arquivos base I50, **anterior** à ligação I50 no runner GoTrue). A validação **específica I50** vem do run GoTrue acima; o PG17 isoladamente não executa a nova rotina de teste.
- [Run #39942943913](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39942943913) cancelado pela concorrência do workflow após o commit mais recente; não contabilizado como falha nem aceite.
- PR #5 preservado **Draft**, sem merge, deploy ou mudança nas migrations S0. É necessário consolidar com o owner S0 e homologar contratos D3/D4, F03 e evidências externas quando pertinentes.

**Próxima etapa possível:** pactuar o produtor verdadeiro de evento de fila com a S0 e validar o contrato de CAS/revogação em serviço integrado, não aumentar indefinidamente os mocks. O checklist de G1–G6 acima é a referência para declarar a frente concluída.
