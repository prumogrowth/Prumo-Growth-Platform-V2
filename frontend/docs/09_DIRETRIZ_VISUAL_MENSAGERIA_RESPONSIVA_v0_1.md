# FV-UI-001 — Diretriz visual responsiva de mensageria, v0.1

**18/10/2026. Origem:** nova orientação expressa do responsável: utilizar a estrutura geral do WhatsApp como **referência de disposição de conversas** em desktop e celular, sem cópia exata de aparência, marca ou funcionalidades. **[D-direção]** referência geral; **[P]** desenho, cores, componentes e divisão detalhada das telas. 

## Composição e comportamento

**Desktop:** `[barra lateral estreita] [lista de conversas, pesquisa, filtros e contexto de concessionária] [conversa principal e compositor fictício] [painel contextual com dados permitidos e processamento FV-02]`.

**Celular:** `[lista] → [conversa em tela inteira] → [detalhes]`, com botões Voltar e nenhuma dependência de hover.

**Gestor da Prumo:** no demonstrador vê conversas por concessionária de exemplo sob concessão; o seletor fictício não prova autenticação. O gestor pode solicitar conclusão somente em caso de exemplo autoatribuído, não por ser supervisor. Não expor D3/D4 brutos em modo de supervisão.

**Operador da Prumo:** lista de casos fictícios atribuídos, conversa e botão visual de conclusão quando a fixture mostra elegibilidade. Sem formulário habitual para digitar nome, e-mail ou demais campos do cadastro. O retorno da extração é representado por estados de exibição artificiais, não por resultado comprovado.

**Identidade:** paleta própria de azul-petróleo e verde suave, visual corporativo, sem logotipo WhatsApp. Prumo é indicação técnica da operação e não nome comercial decidido; LiberaCred pertence à instituição financeira.

## Limites de responsabilidade

A pasta `frontend/visual/` não invade `frontend/s1/` nem `feat/s1-002-equipe-prumo` da frente S0. Não implementa status, transições, autorização, C13, C15, banco ou adaptadores. OpenAI `human_close_extract` é uma operação candidata S0→OpenAI; a UI só simula o pedido FV-02, sem integração. Contratos FV-01/FV-02 e CFI-01 ainda aguardam validação interfrentes no [issue #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4).

## Evidências e próximos portões

- [x] Primeira versão HTML/CSS/JS, fixtures e testes preparados.
- [x] Seis testes Node de invariantes fictícios PASS.
- [x] Chromium headless: inspeção funcional e responsiva em 1440, 900, 390 e 320 px com injeção dos recursos locais; sem erro JS nem overflow horizontal.
- [ ] Servidor HTTP local testado diretamente no navegador de homologação (navegação bloqueada por política do ambiente onde o teste foi feito).
- [ ] Avaliação com o responsável e refinamento de interação/identidade.
- [ ] Auditoria completa de acessibilidade por teclado/leitor de tela, dispositivos físicos e validação com backend S0.
- [ ] Homologação de contratos e integrações S0/OpenAI, sem dados reais antes das aprovações externas.

Nenhuma hospedagem, domínio, banco, token, alteração de outra branch, migração Supabase ou serviço pago integra esta entrega. A pontuação do plano auditado 19F não é aumentada automaticamente por este incremento de UI.
