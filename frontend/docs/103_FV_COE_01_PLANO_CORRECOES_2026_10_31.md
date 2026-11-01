# FV-COE-01 — Coerência operacional do Frontend — decisões e reparos

**Data de referência:** 31/10/2026. **Repositório:** `prumogrowth/Prumo-Growth-Platform-V2`.
**Base:** FV-COR-08 `59481887cec5af02f1243b83652865cdd6ad3a25`; branch de trabalho `fix/fv-coe-01-coerencia-20261031`.

## Regra de produto confirmada pelo proprietário — COE-01

**Abrir conversa equivale à leitura operacional**, inclusive se o Consultor fechar imediatamente, sem rolar nem permanecer na tela. A confirmação não pretende medir percepção humana. A mensagem permanece **lida e sem resposta** até haver resposta humana efetivamente confirmada; envio local e ACK técnico não a encerram. Uma mensagem recebida posterior reabre a pendência de leitura. Gestor apenas supervisor não registra leitura de outro titular; Gestor titular segue a mesma regra de abertura.

Esta decisão substitui a hipótese da auditoria COE-01 que exigiria distinguir abertura e leitura perceptual. **Não criar cronômetro, evento de rolagem ou telemetria de atenção**. A implementação real depende de reconhecimento S0 durável e versionado, não de persistência no navegador.

## Lote técnico 0 — FV-COR-08

O gate oficial do primeiro commit FV-COR-08 falhou em allowlist de `frontend/preview/build_preview.py`. Atualização isolada da allowlist feita na branch `fix/fv-cor-08-unicode-20261031`. A CI deve comprovar se o gate integral passa. **Não confundir testes Node com aceite integral.**

## Lote 1 — Ajustes determinísticos de coerência visual

| ID | Tratamento | Condição de aceite |
| --- | --- | --- |
| COE-02 | Preservar indicação de mensagem aberta sem resposta no histórico, rotulando **histórico/somente leitura** sem inventar ação possível | Evento de abertura reconhecido; não afirmar que histórico permite responder |
| COE-03 | Usar a mesma projeção de não lidas nas conversas e no resumo de equipe, minimizando conteúdo para Gestor | Inbound invisível não infla indicador gerencial |
| COE-04 | Prévia do card prioriza mensagens conversacionais; evento técnico permanece no histórico | Mensagem cliente não some atrás de evento `system` |
| COE-06 | Em remessa confirmada + retorno pendente, destacar o **retorno pendente** e preservar prova de remessa | Sem inferir aprovação/recusa |
| COE-07 | Renomear contador de status para **Na etapa humana**, sem prometer trabalho ativo | Contagem segue estágio comercial, não capacidade de envio |
| COE-08 | `pending` significa **não agendada**, distinto de `scheduled` | Sem promessa implícita de envio ou horário |
| COE-09 | Traduzir apresentação de F03 e estado bancário, preservando códigos e versões em evidência técnica | Não inventar dado ou resultado ausente |
| COE-11 | Não apresentar número de ordem causal ou referência de corte como horário de ocorrência | Contexto técnico permanece verificável e horário desconhecido é explícito |

**Status:** correções candidatas, exigem CI e revisão independente. A apresentação continua inteiramente sintética. Nenhum contrato da S0, S1, Meta ou OpenAI é alterado por esses rótulos.

## Lote 2 — Dependências e decisões de experiência

**COE-05 — Ordenação da fila:** a UI não deve inferir cronologia a partir de `Hoje`, `Ontem`, `Arquivo` ou IDs. Requer projeção autorizada S0 com `last_activity_at`/corte e critério de desempate. Até ratificação, manter ordem estável sem alegar prioridade temporal.

**COE-10 — Banco/Gestão em modais:** a auditoria apontou **risco de usabilidade, não defeito reproduzido**. Testar navegação de módulo dedicado versus diálogo, incluindo desktop/móvel, retorno ao caso, filtros e preservação de rascunhos. Não executar uma reestruturação transversal sem protótipo e aceite de fluxo.

**Integração futura:** alinhar com S0/S1 a projeção autoritativa de leitura/atendimento e a ordenação; Meta fornece evidência de transporte, nunca leitura operacional do Consultor.

## Regra de validação

1. Testes regressivos específicos por COE, incluindo abertura imediata, Gestor supervisor, conteúdo invisível, caso histórico, recência desconhecida e prova bancária.
2. `FULL LOCAL ACCEPTANCE: PASS` no SHA final, com Python, Node, Chromium e exportação de HTML.
3. Nova auditoria independente da semântica, não apenas dos gates.
4. Sem merge, deploy, dados reais ou homologação produtiva nesta branch.
