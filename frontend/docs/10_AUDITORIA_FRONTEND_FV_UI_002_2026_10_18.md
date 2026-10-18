# FV-UI-002 — Auditoria da interface e testes sintéticos | 18/10/2026

**Escopo:** somente `frontend/visual/`, branch `feat/frontend-plataforma-visual`. **Natureza:** demonstração offline. Não comprova autenticação, S0, OpenAI, Meta, Banco, LGPD ou produção.

## Incrementos de apresentação

1. **Fila e filtros:** indicadores sintéticos do escopo, não lidas, casos humanos e filtro pelos oito estados comerciais.
2. **Painel com quatro abas:** Resumo, Histórico, Notas e Extração.
3. **Notas internas:** criação apenas em memória para profissional atualmente atribuído no cenário; gestor supervisor sem editor por mera supervisão.
4. **Equipe Prumo:** quadro gestorial fictício com profissionais e contagens de casos, sem remanejamento real.
5. **FV-02:** solicitação, resultado parcial, falha técnica e versão obsoleta — todos explicitamente simulados e jamais persistidos, sem transição comercial.
6. **Acessibilidade inicial:** abas com setas, Ctrl/Cmd+K para busca, Escape em navegação móvel e estados anunciados por texto.

## Evidências realizadas

| Teste | Evidência | Resultado |
| --- | --- | --- |
| Node e projeções puras | `node --test frontend/visual/tests/*.test.mjs` | **12/12 PASS** |
| Sintaxe JavaScript | `node --check` nos três módulos | PASS |
| Navegação Chromium sintética | 1440×900, 900×780, 390×844, 320×640 | PASS nos quatro tamanhos, sem erros JS nem overflow horizontal |
| Fluxo humano UI | Conversa → detalhes → nota → histórico → conclusão → parcial → histórico | PASS nos quatro tamanhos |
| Gestor e escopo | Visão equipe, duas concessionárias, filtro comercial, operador sem acesso ao quadro gestorial | PASS |

**Condição do teste de navegador:** o sandbox bloqueia HTTP loopback para Chromium. O teste injeta HTML/CSS/JS locais em Chromium headless; portanto, não comprova a carga via servidor HTTP, aplicativos reais, APIs ou autenticação. O arquivo opcional `frontend/visual/tests/browser.smoke.py` reproduz esse ensaio em ambiente Python com Playwright e Chromium instalados. Sem novo workflow de CI habilitado.

## Fronteiras e riscos

- Interface deliberadamente sem backend, banco, tokens, credenciais, OpenAI, Meta, instituição financeira, chamadas externas, domínio, hospedagem ou dados reais.
- S0 mantém regras de autorização, atribuições, idempotência, histórico durável e banco. Frontend apenas demonstra uma projeção de dados artificiais; **filtro JS não é controle de segurança**.
- Não se alterou `frontend/s1/` nem a branch `feat/s1-002-equipe-prumo` da S0.
- O operador **não preenche normalmente campos cadastrais**; os nomes de campos ilustrativos não definem cadastro mestre.
- Concluir atendimento não implica remessa, venda, perda, nono status ou reativação da IA Vendedora.
- Não foram concluídos: acessibilidade por leitor de tela, aparelhos físicos, revisão de privacidade, performance, revisão assinada S0/OpenAI ou testes com APIs homologadas.

## Portões

**FV-UI-002 — implementado e ensaiado somente com dados sintéticos.** A experiência visual ainda é candidata [P]. A integração S0/OpenAI segue pendente em [Issue #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4). Nenhum incremento automático no controle de progresso 19F/69%.
