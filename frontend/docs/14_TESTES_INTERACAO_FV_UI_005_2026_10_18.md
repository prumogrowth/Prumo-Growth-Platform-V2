# FV-UI-005 — Testes de interação e proteção de foco | 18/10/2026

**Escopo:** `frontend/visual/`, exclusivamente na branch visual. **Condição:** testes sintéticos, sem integração externa ou dados reais.

## Entregas

- `tests/dom-fixture.mjs`: DOM mínimo sem dependências, somente para testar o JavaScript da interface em Node (não renderiza CSS e não simula navegador completo).
- `tests/app.dom.test.mjs`: oito cenários de interface (fila, janela Meta expirada, escolha elegível de template, histórico, equipe de gestor, suspensão, conclusão humana e foco de modal).
- `tests/app.mobile.dom.test.mjs`: quatro cenários de navegação móvel (lista/conversa/detalhes, gestor mobile, histórico, ações com janela Meta vencida).
- `app.mjs`: correção adicional para ignorar atalhos globais enquanto há `dialog[open]`, mantendo foco dentro do modal. Nada chama API.
- A simulação preserva as projeções `allowedActionsProjection`, `metaWindowProjection` e `eligibleTemplatesProjection` sob fonte S0 **fictícia**, não inventa autorização real.

## Evidência realmente executada

Em 18/10/2026, foram lidos **diretamente** da branch GitHub os módulos `fixtures.mjs`, `view-model.mjs`, `cf-op-02.mjs`, `app.mjs` e os testes. Com `import/export` adaptados ao **harness V8 de avaliação**:

- **24/24 testes de domínio/projeção PASS.**
- **12/12 testes de interação com DOM simulado PASS** (oito desktop/genéricos e quatro mobile).
- **Total: 36 testes sintéticos PASS**, zero falhas no harness.

A suíte `node --test frontend/visual/tests/*.test.mjs` foi deixada executável no repositório e inclui seis checagens estáticas adicionais de fonte, **mas não foi executada diretamente com Node nesta rodada**. Portanto, não somar essas checagens ao total de 36. A suíte de Playwright/Chromium após FV-03/FV-UI-005 **não foi executada**, e os testes com DOM simulado não comprovam layout, responsividade real, leitor de tela ou transporte HTTP.

## Limites e próximos gates

1. **Frontend:** executar em ambiente apto o Node direto e o Playwright/Chromium nos tamanhos desktop/tablet/mobile, tratar eventuais divergências de renderização/rolagem/foco, e depois revisar acessibilidade.
2. **S0, S1-002, OpenAI e Meta:** homologação de contratos físicos e permissão em tempo de execução; nenhum cenário de mock significa serviço real aprovado.
3. **Governo e fornecedores:** LGPD, banco, canal Meta, custos, templates reais e produção permanecem fora da branch.
4. **Responsável:** avaliação de aparência/posicionamento só quando navegação e funcionalidades previstas estiverem substancialmente consolidadas.

**Não alterar o controle de planejamento doc.19F sem critério concluído e evidência (permanece 69%).** Não houve merge, deploy, hospedagem, alteração de infraestrutura ou Supabase.
