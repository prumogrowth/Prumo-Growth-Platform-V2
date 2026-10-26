# S1-002 / I76 — dois Gestores de equipes distintas na mesma fila sem titular

**Data:** 26/10/2026. **Branch:** `feat/s1-002-equipe-prumo`. **Natureza:** integração de teste sobre S0 canônica, com GoTrue/PostgREST reais descartáveis, gateway de fila assinado I55 e nenhum dado comercial real.

## Motivação e decisão funcional

Conforme `docs/S1_002_01_CONTRATO_FUNCIONAL_VIGENTE_2026_10_22.md`, seção 4, fila de lead **sem titular** é visível aos Gestores **especificamente autorizados à concessionária**, inclusive de equipes diferentes; isso não torna a carteira de casos ativos de outra equipe visível nem transfere Consultores entre equipes. A decisão A2 da I51 mantém destino com intake pausado inelegível. I54 já possuía sinal S0, distribuição automática e assunção pelo Gestor; I55–I58 já testavam gateway real, autorização e revogação para **um** Gestor.

**Lacuna endereçada:** dois Gestores com equipes separadas e autorização temporária válida à mesma loja devem obter a projeção mínima da mesma pendência, disputar a assunção com CAS, não produzir dois casos nem deixar uma concessão revogada continuar operando.

## Implementação S1 (sem mudanças S0)

1. `scripts/test_s1_002_i76_two_managers_queue_e2e.py`: sete cenários GoTrue reais sobre `s0_fila_humana` e os comandos `/s1/fila`, `/s1/assumir_fila` existentes.
2. `scripts/test_s1_002_i55_signed_queue_e2e.py`: executa I76 no final da suíte I55, antes de encerrar a instância do gateway assinado.
3. `.github/workflows/s1-002-i37-intake-signed-local.yml`: adiciona o novo caminho ao filtro de alterações da CI oficial. Nenhum workflow novo ou migration criada.

Dois leads, ciclos e telefones exclusivamente sintéticos; um Gestor de outra equipe inicialmente **sem** grant da loja, com grant explicitamente instalado e depois eliminado na stack descartável; assinatura, identidade e chave continuam sob o gateway e signer I55/I37 já certificados.

## Evidências reais e negativas

| Marcador | Prova certificada |
|---|---|
| I76-G1-01 | Times distintos sem Consultor compartilhado e Gestor sem grant da loja recusado |
| I76-G1-02 | Duas pendências surgem **somente** após sinal comercial canônico explícito |
| I76-G1-03 | Gestores de equipes diferentes com grant próprio à loja veem a **mesma fila sem titular**, quatro campos por item, nenhum payload PII |
| I76-G1-04 | Gestor da outra equipe assume com GoTrue/HMAC/CAS; outro Gestor recebe conflito; um caso, titular e evento |
| I76-G1-05 | Item assumido some da listagem; outro item não assumido permanece disponível |
| I76-G1-06 | Excluir grant temporário bloqueia lista e assunção no **mesmo JWT**, sem consumir a pendência |
| I76-G1-07 | Gestor original assume a segunda pendência; exatamente dois casos com titulares separados, dois eventos, nenhum grant temporário permanece |

**Execução oficial da S1:** código `781fc839165ae3e420ff6b435f3e1f95b3f2db5a`, [Actions #40413807995](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40413807995), jobs `121890912677` GoTrue/PostgREST e `121890913191` unitários, ambos **SUCCESS**. Logs verificados para **`PASS I76-G1-01..07` (7/7)**, `I76 7/7`, `PASS I75D-E2E-01..07`, `PASS I74-E2E-08`, `S1INTAKE-148`, fechamento I37 histórico e **179 testes unitários**. Sem relaxar controles SQL, assinatura, privilégio, política de exceção ou regras RLS.

**O que NÃO foi provado:** envio de mensagem, primeiro contato humano, Redis/Graph/Meta, distribuição por rede produtiva, UI do Gestor, revogação da sessão aplicada ao SELECT histórico de produção, endereçamento manual a **Consultor** específico a partir da fila, nem compatibilidade completa com todas as branches S0. A autorização multi-equipe deste teste vale só para a **fila sem titular**, não para carteira de outra equipe.

## Dependência de integração real identificada

[Issue #17 — G1/S0: encaminhamento manual da fila sem titular para Consultor da equipe](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/issues/17).

As rotinas S0 `s0_fila_distribuir` (destinatário automático entre equipes) e `s0_fila_assumir` (Gestor assume pessoalmente) **não implementam** o terceiro caso da seção 4: Gestor manda manualmente lead sem titular a Consultor de sua **própria equipe**, que pode precisar de exceção I61 por caso em vez de concessão global de loja. O contrato precisa considerar A2/pausa, loja, equipe, versões CAS, concorrência com distribuição e assunção, criação única de caso+atribuição+exceção e rollback. **Propriedade da S0/Codex**, não implementar em duplicidade na S1.

O S0 PR Draft #16 trata revogação de sessão em leitura de histórico e permanece isolado do incremento I76. G1 avança em laboratório, mas **não está homologado operacionalmente**; G2–G6 continuam abertos. Nenhum merge, deploy ou intervenção em `main`, S0 oficial, Meta ou banco hospedado.
