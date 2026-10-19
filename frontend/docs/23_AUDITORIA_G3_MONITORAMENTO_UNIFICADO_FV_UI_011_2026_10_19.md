# FV-UI-011 — Auditoria integrada G3: monitoramento por operadores e sinais operacionais

**Data:** 19/10/2026. **Ramo:** `feat/frontend-plataforma-visual`. **Escopo restrito:** `frontend/`, dados exclusivamente fictícios. Nenhuma consulta ou comando contra S0, S1, Meta, OpenAI, instituição financeira ou Supabase.

## Objetivo contrastado

Jornada **G3** do mapa visual `02_MAPA_DE_TELAS_E_JORNADAS.md`, emendada pela orientação do responsável de gestão **por operadores sob um gestor**, não por todos os atendimentos de cada concessionária. A visão deve separar os **oito estados comerciais canônicos** dos **indicadores técnicos**, tempos de espera e alertas operacionais **somente quando projetados pelo S0**. Não presumir SLA, cálculos Meta/C09, aprovação/recusa bancária, redistribuição ou produtividade.

## O que a frente visual agora demonstra

- `team-monitoring.mjs`: painel agregado da equipe com contagens de casos ativos/históricos, não lidos, janela Meta projetada como expirada, fila protegida, casos sem atribuição, retornos bancários pendentes e carteiras dos operadores; os **oito estados** aparecem em quadro separado. Não inclui nomes de clientes, mensagens, dados D3/D4 ou versões de provas.
- `team-monitor.mjs`: indicadores adicionais de pausa de novos leads, pedidos **somente locais ainda não aplicados** e sinais específicos `waiting_human`, `bank_pending`, `followup_scheduled`, `protected_queue`, `delivery_unverified`. Tempos apenas quando presentes e válidos na projeção `s0_fixture`; fonte, corte e minutos são **100% fictícios**.
- `app.mjs`: o gestor ativo pode alternar entre **Operadores** e **Monitoramento** no mesmo diálogo, tanto no desktop quanto no mobile. A aba reúne o resumo agregado anterior e os novos alertas. O filtro de concessionária do inbox **não redefine** a equipe do gestor. Na troca de perfil, o diálogo é fechado e o conteúdo de ambas as vistas é limpo.
- `cf-op-02.mjs`: fixtures novas de alertas G3 sempre projetadas, não calculadas com `Date.now`. Cada reset recebe cópias isoladas.
- `index.html` e `styles.css`: um único identificador `team-monitor`, navegação com botões `aria-pressed`, rolagem e indicadores responsivos.
- A gestão Marina→Rafael/Lia permanece isolada de Daniel→Bianca/Otávio, inclusive quando as equipes compartilham concessionárias. A S0 deverá realizar a minimização e autorização no **servidor**; filtros locais não provam segurança real.

## Problemas identificados e resolvidos durante a integração

1. **Edição simultânea** trouxe dois módulos G3 e renderizações concorrentes para o mesmo painel. Foram preservadas as duas linhas de funcionalidade e sua apresentação foi unificada; nenhuma delas foi silenciosamente descartada.
2. O HTML chegou a conter **dois elementos com o ID `team-monitor`**, gerando comportamento ambíguo de seletores. Foi removido o duplicado.
3. O roteiro `browser.smoke.py` omitia `team-monitor.mjs` da concatenação de módulos, que ocasionaria erro em navegador; a importação no roteiro foi atualizada.
4. O mesmo roteiro procurava texto com `.inner_text()` no monitoramento **antes** de ativar a aba oculta. Foi corrigido para abrir a aba, verificar os dois conjuntos de indicadores e retornar a **Operadores** antes de acionar a pausa fictícia.
5. Testes específicos de mudança de gestor cobrem limpeza dos nós antigos do DOM e a ausência de indicadores da outra equipe.

## Evidências executadas após conciliação

Fontes recuperadas diretamente da branch GitHub e exercitadas em um **harness JavaScript V8**, com imports/asserções adaptados e DOM sintético:

- **99/99** testes de regras/projeções, incluindo duas linhas complementares de G3.
- **41/41** testes de interação sintética desktop/mobile e regressões anteriores.
- **23/23** inspeções estáticas de código, marcação, isolamento e roteiro.
- **163/163 verificações sintéticas aprovadas**, sem falhas nas baterias executadas.

**Limitações explícitas:** as verificações **não são** execução nativa `node --test` nem Playwright/Chromium da versão atual do repositório privado. A existência e correção do roteiro Chromium não prova sua execução. Não há testes de acessibilidade com leitor de tela, prova de responsividade real, integração backend, autenticação, RLS, política Meta, SLA ou homologação de dados financeiros.

## Critérios ainda pendentes antes de avançar a operação

- Conciliação [S0/S1-002 issue #9](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/9): gestor vinculado a operadores, concessões de lojas decididas somente pelo responsável, pausa global do recebimento e redistribuição de leads no backend.
- Contratos físicos de projeção minimizada G3, autorização por equipe e tenant, sinais com observação e fonte auditável, atualização/revogação sem vazamento de cache e métricas de espera verificadas.
- Executar a suíte **Node e Chromium reais** em checkout autorizado da revisão consolidada, com cenários mobile e acessibilidade, **antes de avaliação visual final**.
- Próxima frente sintética: **G4 — importação/lotes**, sem envio de leads nem mudanças de concessões reais.
- Sem merge, deploy, supabase, edição de branches alheias ou ajuste arbitrário do progresso 19F (permanece **69/100**).

**Veredito:** G3 consistente e aprovado **somente como protótipo sintético**; integrações e homologação real permanecem bloqueadas pelos critérios acima.
