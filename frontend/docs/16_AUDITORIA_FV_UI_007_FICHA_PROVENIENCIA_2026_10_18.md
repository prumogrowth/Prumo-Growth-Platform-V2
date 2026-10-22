> **EMENDA SUPERVENIENTE — 22/10/2026 [D/E]:** para a **frente Frontend** prevalece o [FV-DOC-03 — contrato funcional vigente](./38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md). **A plataforma da Prumo ainda não tem nome; LiberaCred é o produto da instituição financeira.** Papéis visíveis: **Diretor / Gestor / Consultor**. A ficha cadastral do **Consultor é integralmente não editável**, inclusive sem correção excepcional C13 na UI; pendências são esclarecidas por atendimento, e atualização autorizada é confirmada pelo S0. **F01** atende, **F02** planeja templates, **F03** extrai após conclusão humana explícita; a troca de siglas em fala recente está marcada [R-SIGLA-01]. Assinatura de mensagem humana livre deve ser `Cargo Nome:\nMensagem` com validação pelo serviço. IA de melhoria fora da primeira versão. **Descrições anteriores incompatíveis abaixo são históricas e não critérios vigentes de aceite de UI.** Nenhuma alteração de código ou das outras frentes decorre desta emenda.

# FV-UI-007 — Ficha extraída, origem, pendências e restrição D3 | 18/10/2026

**Escopo:** incremento de experiência operacional **O3** na branch visual; todos os dados são sintéticos e sem informação pessoal, dados financeiros ou provas bancárias. Sem backend, rede, supabase, integração OpenAI ou domínio.

## Objetivo normativo

Conforme FV-01/FV-02, doc.24 O3 e D41-01..06:
- **Conclusão solicitada não significa extração concluída**; saída da IA sem validação e versão S0 não é ficha preenchida.
- O operador **não preenche normalmente** campos do cadastro. Corrigir campo C13 é exceção humana versionada e depende de contrato S0, não de formulário genérico.
- Mostrar apenas campos elegíveis **persistidos/confirmados pelo S0**, com versão e fonte permitida, além de ausências e contradições.
- O gestor supervisor tem acesso D2 às conversas de sua concessionária, **não** aos detalhes cadastrais D3/D4, exceto como operador autorizado e autoatribuído ao caso ativo.

## Implementação na demonstração

1. `frontend/visual/registration-view.mjs` apresenta projeção de ficha somente quando estado/versão indicam confirmação; filtra campos que não foram aplicados ou não têm fonte.
2. Um cenário completamente fictício `A-108` representa ficha **parcial e confirmada na fixture**, campo aplicado, campo meramente proposto oculto, uma lacuna e uma contradição. **Não define catálogo cadastral real, campo obrigatório nem validade externa.**
3. Aba **Extração** passa a mostrar: estado/versão da projeção, campo ilustrativo aplicado, valor fictício, referência de mensagem, ausências e conflitos. A supervisora que não está designada só vê um resumo sem nomes de campos, valores, fonte, versão ou lista de pendências.
4. Se o estado não tiver versão persistida ou for desconhecido, não apresentar campo como confirmado. Os estados `processing/failed/stale` não equivalem a sucesso.
5. Proteção de valores no JavaScript é SOMENTE uma simulação. A consulta **real** do S0 precisará devolver projeção de dados já minimizada e autorizada; nunca transmitir D3 bruto ao navegador de gestor supervisor.

## Evidências executadas

Arquivos lidos **diretamente da branch GitHub após os commits** e verificados em harness JavaScript V8 de asserções equivalentes, com imports adaptados:

- **33/33** testes de domínio/projeção: PASS (25 anteriores + 8 específicos O3).
- **19/19** testes de interação de DOM sintético: PASS (17 anteriores + 2 de privacidade/visualização O3).
- **8/8** testes de inspeção estática de fonte: PASS (6 anteriores + 2 O3).
- **60/60** verificações sintéticas sem falhas no harness. Sintaxe das fontes MJS examinadas: aprovada.

**Não afirmar** que foi executada a suíte Node direta, um navegador Chromium da versão atual, screenshot atual, teste de leitor de tela ou prova de integração. O roteiro opcional `frontend/visual/tests/browser.smoke.py` foi adaptado para incluir `registration-view.mjs` e cenários O3, mas **não foi executado nesta etapa**.

## Gates ainda abertos

- S0: schema canônico de projeções UQ03/versionamento/`allowed_actions`, proveniência e persistência backend.
- D3/D4: políticas de leitura por atribuição e concessão aprovadas, validação de LGPD, prova bancária e restrições do Banco.
- Frontend: execução Node e Chromium reais da branch, testes de acessibilidade e expansão das telas O4/O5/G2/G3/G4 em modo sintético.
- Sem merge, deploy, alterações em branches alheias ou mudança automática do índice do planejamento auditado (**69%**).

**Estado deste incremento: O3 representado e coberto por testes sintéticos; sem autorização para dados reais nem GO de produção.**
