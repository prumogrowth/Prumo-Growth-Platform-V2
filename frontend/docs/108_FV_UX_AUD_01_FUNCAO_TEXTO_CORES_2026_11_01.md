# FV-UX-AUD-01 — Auditoria orientada a funcionamento, concisão e cores

**Data:** 2026-11-01. **Base validada previamente:** `feat/fv-modulos-telas-proprias-20261101` em `7708d0d203efa4332771928c2c37b28be7d75242`, CI 41345326606 `success`. **Branch isolada desta auditoria:** `fix/fv-ux-aud-01-functional-minimal-color-20261101`.

## Prioridade aprovada pelo responsável

1. **Funcionalidade antes de decoração.** Todo controle visível deve ter ação coerente, observável e permitida; estados desabilitados não devem fingir integração.
2. **Pouquíssimo texto em tela.** Rótulos autoexplicativos (“Claro”, “Escuro”, “Banco”, “Gestão”), dados e mensagens de estado curtas. Detalhes técnicos importantes ficam recolhidos sob demanda, não removidos do sistema. Preservar descrições acessíveis para leitores de tela.
3. **Claro e escuro são os temas-base, não uma proibição de cores.** Cores podem destacar estados: número verde para mensagens não lidas e ponto laranja para lidas aguardando resposta humana; não depender exclusivamente de matiz.

## Achados sobre a versão de partida

- **AUD-FUN-01 (PASS automatizado da base, não prova operação real):** CI 41345326606 concluiu 466 testes Node, gate Chromium, 56 cenários FV-COR-07, provas offline e capturas sintéticas. Banco/Gestão/Conversas eram interativos no protótipo.
- **AUD-TXT-01 (ajustado):** Banco mostrava aviso longo, e ficha pronta chamava `renderRegistration` (painel diagnóstico F03 com parágrafos sobre regras e versões). Nesta branch, Banco exibe só nome, campos confirmados e o bloco “Versão e origens” recolhido. Diagnósticos F03 continuam no Resumo das Conversas.
- **AUD-TXT-02 (ajustado):** Gestão duplicava texto de alcance e explicação, inclusive introdução longa e descrições repetidas em cada Consultor. A introdução e os cartões agora mostram somente situação da conta, recebimento de leads, casos e lojas. O detalhamento das consequências de pausa/retomada permanece recolhido em “Entenda o alcance e os limites”, sem minimizar as restrições S0.
- **AUD-COR-01 (já implementado na base):** badges de não lidas verdes e pontos de lidas sem resposta laranja, inclusive em modo escuro. Foram **preservados**, não reinventados. Número vs ponto e `aria-label` permitem reconhecimento sem depender da cor.
- **AUD-FUN-02 (limite vigente):** botões das simulações abrem painéis/alteram estados locais e são cobertos por testes; **não** enviam mensagem real, não registram remessa bancária, não fazem alterações produtivas de atribuição/permissão. Contratos físicos S0, Meta e Banco não homologados. A instrução de “cada botão funcionar” significa fazer exatamente o que o botão informa — não simular sucesso externo.
- **AUD-ACC-01 (pendente para homologação):** Banco/Gestão usam elementos `dialog.show()` estilizados como áreas internas, sem top-layer. Requer auditoria semântica com leitor de tela real e validação de landmarks antes de rotular experiência como homologada.

## Alterações e critérios

- Banco: `bank-guidance` breve (“Somente leitura · sem envio real.”); estado vazio “Nenhum cadastro apto no momento.”; lista apenas nomes aptos e ficha só de dados confirmados; proveniência dentro de `details`.
- Gestão: título “Gestão”, introdução “Ações de exemplo · sem alterações reais.”; controles existentes preservados. As justificativas normativas permanecem consultáveis, mas não ocupam espaço inicial.
- Sem editar elegibilidade, escopo por ator/loja, cursor de leitura, texto das mensagens, temas-base, permissão, ações bancárias ou contratos de produção.
- Testes acrescentados para concisão da ficha, cores claras/escuras, preservação de `aria-label` e interações de temas, Banco e abas de Gestão.

## Gate e aceite

O resultado da CI no **HEAD desta branch** deverá ser anotado após execução. Mesmo com CI verde, aceite final ainda exige revisão visual independente de foco, leitura de tela, contraste e compreensão de estados em desktop e celular; publicação/produtivo fora do escopo. Não usar `success` da branch-base como aprovação das alterações deste documento.
