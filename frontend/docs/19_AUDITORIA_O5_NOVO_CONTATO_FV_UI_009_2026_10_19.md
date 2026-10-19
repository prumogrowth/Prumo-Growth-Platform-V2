# FV-UI-009 — O5, continuidade humana pós-marco bancário | 19/10/2026

**Frente:** frontend visual (branch `feat/frontend-plataforma-visual`). **Objetivo:** implementar, apenas em experiência sintética, a jornada O5 do caderno de telas doc.24 e FV-01: **novo contato humano após `cadastro enviado ao banco` ou `vendido`, preservando o caso e a evidência históricos, sem reativar a IA Vendedora**.

## Entregas verificadas

- Novo módulo `frontend/visual/postmark-view.mjs` representa vínculo entre **caso de origem** e **novo ciclo humano independente** já criados/projetados ficticiamente pela S0. Exige associação recíproca, IDs de casos, mesma concessionária, fonte `bank_submitted` ou `sold`, versão do vínculo, projeção `linkedByS0` e IA Vendedora silenciada.
- Aba **Novo contato** no painel do caso: mostra a relação e permite **navegar entre dois casos pré-existentes**, preservando status comercial de origem. Botão **não cria contato**, não altera status e não aciona Meta, OpenAI ou Banco.
- Fixtures: **A-105 → A-114** (pós-remessa), **A-115 → A-116** (pós-venda). A-105 mantém `cadastro enviado ao banco`; A-115 mantém `vendido` e histórico; A-114/A-116 têm `em atendimento pelo operador` como **outros casos**. Todos usam mensagens fictícias, sem PII, prova bancária ou mídia real.
- O novo ciclo só aceita ação local simulada de humano caso o contexto de **loja, ator designado, vínculo confirmado, janela Meta aberta e `allowed_actions`** permaneça coerente. Gestor sem atribuição vê D2 no escopo, mas não ganha capacidade de responder.
- Vínculo unilateral, versão divergente, alteração de origem, revogação, loja distinta ou caso fora da carteira não revela o identificador relacionado nem abre conversa alheia. Histórico anterior continua disponível para quem possui acesso.
- Lista e contadores sintéticos atualizados para incluir os casos novos. A aba usa rolagem horizontal existente no painel de detalhes; nenhuma decisão de aparência foi solicitada.

## Verificação efetuada sobre os arquivos da branch

Fontes, testes e CSS foram recuperados diretamente do GitHub e executados em **harness JavaScript V8** após os commits. Imports e asserções dos testes Node foram adaptados para o harness; **não** é execução nativa da suíte Node.

- **59/59** testes de domínio, incluindo **13 novos O5**, passaram.
- **25/25** testes de interação DOM sintético, incluindo **4 novos O5** (três desktop/genéricos e um mobile), passaram.
- **12/12** inspeções estáticas de HTML/CSS/JS e roteiro Chromium, incluindo **2 novas O5**, passaram.
- **96/96 verificações sintéticas PASS** e sintaxe dos módulos JS examinados sem falhas.

**Limitação:** ainda não foi executado Node `--test` literal, Playwright/Chromium da revisão atual, teste de leitor de tela, acessibilidade física ou integração S0/Meta. O roteiro Chromium foi **atualizado**, não executado. A simulação não comprova autorização, persistência, cálculo de janela real, criação C14 ou entrega de mensagem.

## Próximas dependências/gates

1. **S0/S1-002:** contrato físico UQ05/C14 e projeção de novo ciclo pós-marco, concessão e roteamento/atribuição humana sem autoatribuição pelo browser.
2. **Meta/Banco/OpenAI:** provas, políticas do canal, LGPD, decisão humana sobre eventos de banco, e ausência definitiva de nova atuação da IA Vendedora após handoff.
3. **Frontend:** executar checkout completo com Node e Chromium, ensaios de acessibilidade e completar jornadas sintéticas **G2–G4** mantendo separação de autoridade. Sem disponibilizar ao responsável uma versão para revisão estética prematura.
4. **Governança:** sem merge, deploy, alteração S0/Supabase ou índice auditado 19F (continua **69/100**).

**Veredito:** O5 representado em frontend sintético com invariantes testados; integração e produção não homologadas.
