# FV-UX-AUD-02 — Auditoria funcional e simplificação visual

**Data:** 01/11/2026. **Base aprovada:** `feat/fv-modulos-telas-proprias-20261101` @ `7708d0d203efa4332771928c2c37b28be7d75242`, CI [41345326606](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41345326606) `success` (466 Node PASS, testes Chromium e exportação nativa PASS, conjunto FV-COR-07 PASS). **Branch de alterações:** `audit/fv-ux-funcional-enxuta-20261101`; seu aceite exige CI no SHA final. Não houve merge/deploy.

## Critérios expressos do responsável

1. **Funcionalidade primeiro:** cada controle precisa fazer o que sua identificação sugere e respeitar identidade, foco, dados, ausência de privilégios e estados vazios. Não substituir operações reais por simulações que parecem reais.
2. **Texto mínimo e útil:** preferir títulos, nomes e ações curtas. Explicações longas não devem se repetir na interface. Avisos essenciais de confirmação/segurança permanecem; acessibilidade mantém rótulos para tecnologias assistivas, mesmo quando não visíveis.
3. **Tema claro / escuro são os sistemas visuais predominantes**, não uma obrigação de monocromia absoluta. Acentos semânticos moderados: **verde para número de mensagens não lidas**, **laranja para ponto de conversa lida sem resposta humana**, mantendo forma/contagem, título e aria-label independentes da cor.

## Inspeção do estado anterior à correção

| Código | Natureza | Evidência/parecer | Tratamento |
| --- | --- | --- | --- |
| UX-01 | Excesso de texto | Banco repetia demonstrativo, prontidão e inexistência de envio; Gestão exibia intro longa e ajuda extensa. | Simplificar títulos, ajuda colapsada e nota de envio sem omitir o caráter de simulação. |
| UX-02 | Identificação visual | Indicadores de não lida e lida sem resposta apareciam em cinzas próximos. | Introduzir verde/laranja contrastantes por tema, preservando número versus ponto. |
| UX-03 | Interação de Banco | O cadastro pronto era escolhido via `select`, não numa lista de nomes clicáveis conforme decisão do proprietário. | Criar lista visível somente com nomes e botões, ficha autorizada ao lado; manter seletor antigo apenas como adaptador oculto do protótipo. Validação e recheck de permissão antes de abrir detalhe. |
| UX-04 | Fluxos operacionais | A prévia está coberta por diversas suítes Node/Chromium e teve sucesso, mas a confirmação de atendimento, o envio de mensagens, a distribuição e o registro bancário são simulações. | **Não** declarar funções produtivas ou bancos/Meta/S0 reais em operação. S0/S1 mantém autoridade dos comandos. |
| UX-05 | Estrutura | Banco e Gestão usam `dialog.show()` não modal, embora posicionados como páginas no workspace. | Navegação in-flow funcionou na CI da base. Revisão semântica de landmarks/leitor de tela continua item técnico de auditoria antes de produção; não mascarar como página nativa completa. |
| UX-06 | Listagem sem aptos | As fixtures principais não oferecem uma nova remessa confirmadamente elegível por prudência da S0; a fila fica vazia. | Não inserir clientes pendentes/fictícios apenas para preencher UI. Testar positivamente com fixture isolada sintética e negativamente após iniciar remessa. |

## Cobertura funcional auditada

- **Fonte estática:** em `index.html`, 26 botões com `id` foram inspecionados; 21 têm referência direta no controlador principal e os 5 controles de áudio/emoji são delegados ao componente `communication-composer.mjs`. Esse inventário não equivale à execução manual individual, nem alcança todos os botões dinâmicos.
- **Evidência anterior:** CI completa no commit base passou 466 testes Node, navegação Chromium e cenários responsivos/temas. São cenários de protótipo offline, não homologação hospedada.
- **Evidência a obter nesta branch:** auditoria de textos e sinais cromáticos, lista Banco clicável (positiva com cenário sintético autorizado + negativa por remessa), seleção sem exposição de CPF/status no item, navegação Gestor/Consultor, teclas, foco, light/dark, nenhuma escrita real. Rodar gate integral e capturas finais.
- **Segurança funcional:** estados desconhecidos, remessas iniciadas, casos históricos e fichas incompletas não entram na lista Banco; abertura da página não marca conversa lida, consulta de ficha revalida autorização; histórico F03 pertence ao Resumo.

## Limites e aceite

**Não afirmar que 'todos os botões funcionam em produção'.** Neste estágio são controles de protótipo; os comandos externos S0/S1, Meta, OpenAI e Banco exigem integração e autoridade próprias. Todas as alterações desta branch são visuais ou de navegação sintética.

Aceite somente depois da CI final e revisão funcional independente, com prova de ausência de regressão; continuar usando o protocolo de comunicação [#4](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/4) e a dependência bancária [#15](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/15).
