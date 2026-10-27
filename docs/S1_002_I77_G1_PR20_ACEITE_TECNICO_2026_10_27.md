# S1-002 / I77 — Aceite técnico experimental da G1 manual (PR Draft #20)

**Data da revisão:** 27/10/2026. **Branch única de escrita:** `feat/s1-002-equipe-prumo`. **Código verificado:** `de15329dae304583c269b8516b997e4ccdee5a4c`. **Âmbito:** testes descartáveis no GitHub Actions, NÃO homologação de produto, deploy ou migração hospedada.

## Proveniência e decisão de incorporação

Fonte proprietária S0: [PR Draft #20](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/20), código certificado `d53c40a6ef55e82d2282c482b299cff1dbf990bd` e documentação posterior `4775091ac6207e1593daf1d8fb3b3b3f414224de`; [contrato G1](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/4775091ac6207e1593daf1d8fb3b3b3f414224de/docs/contratos/g1_issue17/CONTRATO_G1_MANUAL_V1.md) e [relatório de reprodução](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/4775091ac6207e1593daf1d8fb3b3b3f414224de/docs/contratos/g1_issue17/RELATORIO_E_REPRODUCAO.md). Baseline S1 antes da I77: `b71ebf4479c9a0a3527519471cca04ec7e178e18`.

**Escolha segura de integração experimental:** o adaptador G1 do PR #20 importa o executor `backend.s0_cfi01_atomic_commands_local` e funções internas CFI/F02/S0 não presentes na branch S1. Uma importação seletiva de `backend/s0_g1_manual_queue_local.py` e do SQL seria um candidato quebrado. Em vez disso, a S1 adicionou:

1. `scripts/test_s1_002_i77_g1_pr20_compatibility.py` — verifica SHA completo `d53c40a`, compara **34 SHA-256** de arquivos S1 do manifesto G1 contra o **HEAD atual da S1** e falha fechada se houver drift. Exige contrato `ENCAMINHADO`, preservação do check de eventos legados e reuso de I61. Somente no checkout efêmero do PR #20, após todas as comparações, troca o `ref` do manifesto para o SHA verificado da S1; **não altera bytes dos 34 fontes nem escreve nas branches externas**. Gera JSON de evidência.
2. `.github/workflows/s1-002-postgres.yml` — conserva job oficial PostgreSQL `s1-002-equipe` e acrescenta job isolado `g1-pr20-compatibility` com checkout PINADO do executável S0 `d53c40a` e checkout S1 do SHA da execução. Reproduz, sem portar o workflow experimental S0, a preparação GoTrue, CFI, F02, I63, instalação G1 e as provas originais I54/I56/I57/I58/I61, seguidas dos 36 cenários reais G1. Sem dados pessoais, sem Meta/Banco, sem credenciais hospedadas. `supabase stop --no-backup` executa na limpeza condicional.

Nenhum arquivo de negócio, migration ou rotina de privilégios da S0 foi copiado para a branch S1. O SHA fixado evita absorção silenciosa de novos commits do PR #20.

## Contrato ENCAMINHADO e garantias verificadas

**Três operações diferentes:** `s0_fila_distribuir` (automaticamente Consultor elegível), `s0_fila_assumir`/I55 (Gestor assume pessoalmente) e G1 manual (Gestor autorizado encaminha lead **sem titular** a Consultor da **própria equipe**). A versão CAS de fila não é a versão de caso/ciclo. Fonte funcional vinculante: `docs/S1_002_01_CONTRATO_FUNCIONAL_VIGENTE_2026_10_22.md` §§4–5 e A2/I51.

O delta [`supabase/tests/s0_g1_manual_queue_local_only.sql` do PR #20](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/d53c40a6ef55e82d2282c482b299cff1dbf990bd/supabase/tests/s0_g1_manual_queue_local_only.sql), **somente laboratório**, exige exatamente os valores legados `PENDENTE, ASSUMIDO, DISTRIBUIDO, RECONCILIADO` na constraint `s0_fila_evento_i56` e acrescenta **`ENCAMINHADO`** ao mesmo ledger, sem nova tabela paralela de fila. O evento insere `gestor` solicitante, Consultor destino, caso, atribuição, versão anterior/nova e identidade loja/ciclo/lead na mesma transação; a idempotência conserva recibo/auditoria privados e evita novo evento em replay.

G1 valida Bearer/sessão GoTrue e HMAC+nonce; rejeita ator/role/session fornecidos no payload, destino fora da equipe, Consultor pausado (A2), grant ou vínculo revogado depois de locks, CAS stale, mesmo contato já com caso, e requisições concorrentes. Para destinatário sem grant geral, cria somente exceção **por caso/atribuição** I61, sem inserir `vinculos_papel_escopo`; o acesso indevido em outra loja/equipe é recusado. Provas de rollback incluem falha em exceção/atribuição/auditoria/constraint adiada e validação da resposta antes do COMMIT. Erro de confirmação desconhecida retorna indisponibilidade, não falso sucesso ou rollback garantido.

**Risco remanescente explicitamente aceito somente em laboratório:** a ponte privada de negócio usa `SECURITY DEFINER` owned por `postgres` porque triggers/guards canônicos I57/I61 exigem `current_user='postgres'`. A entrada assinada pertence a role `NOLOGIN` restrita; o login de aplicação não acessa ponte/ledgers diretamente. Essa solução **não aprova owner produtivo**, isolamento completo do provisionamento ou configuração de borda em serviço hospedado.

## Evidência oficial reexecutada na própria S1

Primeira tentativa [#40471191964](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40471191964) não executou G1: workflow escapou incorretamente `${{ github.sha }}`, produzindo refspec inválido; limpeza inicial sem checkout falhou. Corrigido **somente no workflow**, commit `de15329dae304583c269b8516b997e4ccdee5a4c`. Não considerar a tentativa como aceite.

**[Workflow oficial S1 #40471384039](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40471384039)** — conclusão **SUCCESS**, HEAD executado `de15329dae304583c269b8516b997e4ccdee5a4c`; jobs `122079118585` (S1 PG17) e `122079118758` (G1 pinned GoTrue), ambos **SUCCESS**. Logs conferidos:

| Evidência | Resultado |
|---|---|
| `PASS I77-01` e `PASS I77-02` | PR20 pinado + 34/34 SHA-256 S1, contrato do evento, manifesto efêmero reconciliado sem alterar fontes |
| Unitários do checkout S0/F02/G1 | **272/272** PASS, incluindo 8 novos G1 do PR #20 |
| Históricos `S0` e `I63` | **19/19 + 19/19** real GoTrue |
| Compatibilidade CFI/F02 | **56/56** reais |
| SQL S1 originais I54/I56/I57/I58/I61 | **8+6+5+6+9 = 34/34** |
| Testes G1 GoTrue/PostgreSQL/PostgREST `integration/g1/test_manual_handoff.py` | **36/36** PASS, incluindo disputa com I54/I55, sessão revogada, ida/volta de locks, exceção I61/I62, idempotência e rollback |
| Regressão PostgreSQL original da S1 | **SUCCESS**, inventários I75B/I75C, demais aceites PG17 preservados |

Artifact `s1-002-i77-pr20-pinned-compatibility` (ID `12718975482`) arquivado junto aos inventários do job S1. Todos os atores e contatos em testes são sintéticos; job G1 executado em stack própria e descartada.

## Aceite e pendências reais

**ACEITE TÉCNICO: APROVADO PARA COMPOSIÇÃO EXPERIMENTAL NA FRENTE S1.** I77 fecha a **lacuna de prova de compatibilidade técnica do encaminhamento manual G1**, não o gate operacional G1 completo. A [Issue #17](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/issues/17) deve continuar **aberta** até o contrato e provisionamento da ponte privilegiada em S0 e o aceite de integração final. O reportado pela S0 em PR #20 foi **independentemente reproduzido**, não apenas herdado como alegação.

Bloqueios ainda existentes:
- **Provisionamento operacional/ownership** da ponte, serviços com autenticação real na borda e revisão da autoridade `postgres`.
- Integração verdadeira S0/S1/Meta do produtor de sinal humano e primeiro contato comprovado; reconciliação e concorrência com escritores externos além dos exercitados.
- API/DTO/UI do Gestor para encaminhamento e UX de conflitos, idempotência, progresso e revogação, ainda não homologados.
- G2: Diretor, chefia principal única e gestão de equipe ponta a ponta; G3: políticas operacionais de histórico, D3/D4, arquivos e retenção; G4: primeiro contato/indicadores; G5: conclusão/F03; G6: homologação multi-loja/externa.
- Não há evidência que autorize merge, deploy, aplicação de SQL de laboratório no Supabase hospedado ou percentual total de conclusão da S1.

**Próximo incremento independente recomendado: I78/G2** — auditar o modelo vigente de Diretor/Gestor/Consultor e a unicidade da chefia ativa em objetos S1 reais; aproveitar testes existentes e acrescentar apenas negativos ausentes sem tocar S0. Eventual necessidade de API administrativa oficial deve ser coordenada com o Codex.
