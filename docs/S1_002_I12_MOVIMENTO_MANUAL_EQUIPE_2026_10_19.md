# S1-002/I12 — Movimentação manual de atendimento na equipe

> **AVISO DE PRECEDÊNCIA — 22/10/2026:** **Retificação:** transferência normal pode exigir concessão geral, mas a via aprovada excepcional é **por caso**, sem grant de loja, com direito contextual ao histórico do mesmo contato na concessionária. O destino já pausado permanece [R], e a escrita deve permanecer vinculada à titularidade atual. [Contrato funcional S1 vigente (22/10/2026)](S1_002_01_CONTRATO_FUNCIONAL_VIGENTE_2026_10_22.md) · [matriz de aderência](S1_002_02_MATRIZ_ADERENCIA_E_PENDENCIAS_2026_10_22.md).


**Status:** prova técnica em PostgreSQL 17 descartável, sem endpoint, sem GoTrue/REST real e sem merge.

**Regra [D]:** gestores administram OPERADORES supervisionados, independentemente das concessionárias. Somente os responsáveis concedem A/B/C a cada operador; o gestor não modifica essas concessões. O destino de uma movimentação precisa ser operador ativo, com autorização vigente para a concessionária do atendimento. **Hipótese prudente [P]:** o gestor só pode movimentar entre dois operadores da própria equipe; transferência entre equipes depende de contrato próprio.

Migration 049 adiciona função privada s1_mover_atendimento_da_equipe(solicitante,loja,caso,atribuicao_esperada,destino). A função confere alçada em origem e destino, trava registros de equipe em ordem e caso/ciclo, exige o ID exato da atribuição ativa para rejeitar replay, encerra atribuição antiga e cria a nova na MESMA loja. Cria histórico append-only de quem moveu, origem, destino, caso e IDs das atribuições. Ciclo vendido/perdido original sem novo caso humano é bloqueado; retorno humano pós-venda é permitido sem alterar vendido. Nenhum envio, status, grant ou composição da equipe é alterado.

O código aceita executor somente postgres no **sandbox**; não aceita chamada de authenticated/anon/service_role. Em produção será obrigatório extrair identidade validada da sessão pelo gateway e auditar autorização com requisitos do S0, incluindo caso já concluído. Testes S1M-01..12 verificam A/B sem grant para gestor, destino com/sem grant, pessoas de outras equipes, caso terminal versus retorno, repetição, isolamento por loja, trilha e negação da API. Testes concorrentes intersessões ainda pendentes.

**Limites:** não implementa agendamento, mutação RH real, controle de turnos, bulk manual, integração Meta, reabertura de caso, auth real nem alteração de S0.


## Evidências verificadas do incremento I12 (19/10/2026)

[GitHub Actions PG17 #39251996100 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39251996100), commit `d525148242e2d645a6f139af612b8b48dbd99cd2`, job `118057803139`: **S1M-01..12 = 12/12 PASS**, abrangendo gestão por equipe, duas lojas A/B sem grant próprio do gestor, origem/destino dentro da mesma equipe, destino ativo autorizado na loja do caso, venda histórica sem reabertura, replay negado, trilha append-only e sem EXECUTE via authenticated. O primeiro ensaio #39251784096 falhou por expressão SQL qualificada como `pg_catalog.greatest` que não existe; corrigida e retestada, sem deploy.

[GitHub Actions PG17 #39252443273 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39252443273), commit `571df70e44ed9d3ff69c7aa45f72b8aa6217fbde`, job `118059321243`: regressão **S1M 12/12**, mais **S1MR-01..04 = 4/4 PASS**. Duas conexões tentando mudar a mesma atribuição: uma transferência aceita e outra rejeitada sem duplicidade; pausa global simultânea vence comando manual obsoleto sem dois titulares. Suites legadas de I1–I11, inclusive S1T 14/14, S1A 9/9, S1H 8/8, AUD1 7/7 e AUD2 5/5, passaram no mesmo job. Nenhum deadlock SQL inesperado nos marcadores conferidos.

**Conclusão restrita:** funcionamento sintético demonstrado, mas nenhum login Supabase GoTrue, JWT assinado, endpoint REST, serviço bancário, Meta real, status de conclusão humana definitivo, autorização administrativa real ou merge/deploy. O algoritmo automático I2 ainda pode escolher operador de outra equipe elegível na mesma loja; política definitiva desse caso permanece [R], sem presumir decisão do usuário.

---

## Retificação de contrato — issue #10 (20/10/2026)

**A exigência atual de concessão geral à loja permanece válida apenas para o fluxo manual comum.** A nova decisão [D] autoriza que um gestor transfira individualmente um atendimento a integrante de sua equipe mesmo sem grant geral da concessionária, **somente se existir autorização excepcional revogável e auditável restrita àquele caso**. Não é permitido editar concessões de loja, transferir outra equipe nem dar leitura a outros casos/documentos da concessionária.

As migrations 049/050 ainda aplicam o contrato legado, com obrigatoriedade de grant de loja; **a exceção não foi implementada como operação**. A tabela privada `s1_excecoes_caso_preparacao_10` da fixture ISSUE10 representa apenas modelagem sem permissões RLS/SELECT nem autorização real. A efetivação depende do S0 certificar quais tabelas, visões, anexos, mensagens e projeções precisam ser isolados por caso, e do núcleo oferecer um evento versionado de início de atendimento humano. Nunca contornar o guard de atribuição com concessão geral, login fingido ou flag do navegador.

[Plano técnico e dependências S0](S1_002_ISSUE10_CORRECAO_PAUSA_INTAKE_2026_10_20.md). A regressão histórica I12 continua evidência do fluxo normal **pré-exceção**, não da nova capacidade. **NO-GO produção/merge/deploy.**
