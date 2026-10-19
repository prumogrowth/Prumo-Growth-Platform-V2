# FV-AUD-04 — Revisão dos incrementos recentes FV-UI-004 a 007 | 18/10/2026

**Solicitação:** auditar as últimas implementações e corrigir o que estiver incompatível com o objetivo final antes de continuar. **Escopo:** branch `feat/frontend-plataforma-visual`, principalmente `frontend/visual/` e contratos FV-01/FV-02/FV-03; comparação normativa com documento 24 (O1–O5 / G1–G4) e decisões D41. **Resultado:** divergências detectadas e reparadas na simulação; integração funcional, browser real e produção **não homologados**.

## Objetivo e limites da frente

A plataforma operacional ainda não recebeu nome comercial. LiberaCred é o produto da instituição financeira, Prumo é a equipe profissional. Interface responsiva inspirada na organização do WhatsApp (sem cópia de marca), atendimentos isolados por concessionária, oito estados comerciais, IA Vendedora definitivamente silenciada após handoff, operadores designados, gestores leitores D2 mas não D3/D4 brutos em supervisão. S0 permanece autoridade exclusiva de permissões, status, evidência bancária, janela Meta, comandos, versão, extração persistida e recontatos; S1-002 revoga/remaneja, OpenAI propõe, Meta transporta. A UI não possui nem reivindica APIs reais.

## Achados e reparos nesta auditoria

| ID | Problema | Reparação feita |
| --- | --- | --- |
| AUD4-01 (alta) | `mayMockFreeText` podia permitir resposta livre no **mesmo ciclo já enviado ao banco, vendido ou perdido** se chegassem `allowedActionsProjection` e janela aberta inconsistentes. `projectedFollowupActions` também podia expor pedido de template/cadeia a esse ciclo. Isso contrariava a preservação dos marcos e a separação do novo contato humano. | Novo `isPriorCycleLocked` nega ambas as ações quando status é `cadastro enviado ao banco`, `vendido` ou `perdido`. Nenhuma transição comercial foi acrescentada. Teste específico com permissões residuais simuladas. |
| AUD4-02 (alta) | O3 podia mostrar **ausências e contradições** da projeção de extração com estado `failed`, `stale` ou `processing` como se fossem pendências atuais validadas. | Somente projeção `persisted/partial` com `confirmedPersisted=true` e referência de versão não vazia exibe pendências/conflitos; sem confirmação, arrays ficam vazios. |
| AUD4-03 (alta) | A cópia da interface de O3 exibia título “**Versão persistida**” a partir apenas do valor `state=persisted/partial`, mesmo quando faltava confirmação válida da versão. | `registrationStateCopy` retorna “**Persistência não confirmada**” sem comprovação de nova versão, jamais título de sucesso; testes para `persisted` e `partial` sem versão. |
| AUD4-04 (média) | Referência de versão com somente espaços poderia ser tratada como válida. | Versão exigida como string não vazia após `trim`; sem versão válida, não mostrar dados aplicados como confirmados. |

## Revisão dos últimos incrementos

- **FV-UI-004/005:** equipes e perfis, atalhos/modais, navegação mobile e histórico mantidos; event handlers por DOM simulado cobrem seleção de template, conclusão e perfil suspenso. Nenhuma autoridade server-side inferida.
- **FV-UI-006:** a distinção “conclusão solicitada” vs “conclusão confirmada” e a proteção contra diálogo/formulário de caso anterior foram preservadas nos testes.
- **FV-UI-007:** versão fictícia, origem, valor aplicado, ausências/conflitos e a ocultação de detalhes D3 para gestor apenas supervisor permanecem. Novos reparos evitam promoção de dados e mensagens de sucesso sem versão válida.
- **Contrato FV-03:** o navegador não calcula janelas Meta nem perda C09; “queued/accepted” não são prova “sent”; `cadastro enviado ao banco` e `vendido` não sofrem perda por silêncio; ciclos antigos não são reativados por ações residuais. Handoff não reativa a IA Vendedora.

## Evidências executadas (arquivos recentes recuperados do GitHub)

Com a branch já atualizada, fontes e testes foram avaliados num **harness JavaScript V8** com imports/asserções adaptados:

- **37/37** testes de domínio e projeção sintéticos **PASS** (incluem os novos cenários bancários e de persistência).
- **19/19** testes de interação com DOM sintético (desktop/móvel) **PASS**.
- **8/8** verificações estáticas de HTML/CSS/JS e roteiro de teste **PASS**.
- **Total 64/64** verificações sintéticas, sem falha nesse harness; sintaxe JavaScript dos módulos examinados aprovada.

**Ressalva obrigatória:** isso NÃO comprova execução literal dos testes com `node --test` ou Playwright/Chromium na versão atual da branch. O Chromium e o Playwright estão disponíveis localmente, mas não foi possível obter na sessão uma cópia íntegra dos arquivos mais recentes do repositório privado para execução direta no navegador. Não se deve reivindicar prova de UI renderizada, acessibilidade, perfis reais, dados reais, segurança backend ou conclusão técnica de integrações. Roteiro `frontend/visual/tests/browser.smoke.py` permanece candidato para executar em ambiente com checkout autorizado.

## Cobertura contra destino final

| Percurso | O que há hoje | O que falta para declarar “funcional” |
| --- | --- | --- |
| O1/O2 | Conversas, pesquisa, estados comerciais, mensagens, notas e handoff humano em fixtures | Autenticação e projeções S0, C12, inbound Meta, testes reais |
| O3 | Ficha fictícia versionada, valores aplicados, origem e pendências com restrições de visualização | Catálogo real aprovado, UQ03, confirmação de gravação S0, LGPD e leitura D3 autorizada |
| FV-02/FV-03 | Pedir conclusão, template único, cadeia, estados técnicos e janela Meta projetada | Comandos físicos, idempotência e retorno S0/OAI/Meta, `sent` confiável, concorrência |
| O4/O5 | Apenas contexto e proteção de marcos; NÃO implementação de remessa/recusa/novo ciclo real | Fluxo e prova bancária humana e pós-marco em interface, autorização S0, regras e evidências |
| G1–G4 | Fila gestorial, perfis fictícios e contagens simples | Atribuição/autoatribuição autorizada, monitor completo, importação/lotes e S1-002 reais |

**Decisão:** avanços sintéticos coerentes após correções, mas **NÃO pronto para a revisão visual final nem para produção**. Priorizar testagem real com checkout, O4/O5/G2–G4 sintéticos e acordos interfrentes. Não transferir pendências a um pedido de avaliação estética prematuro.

**Escopo dos commits:** somente `frontend/` na branch proprietária; sem tocar backend, Supabase, canal Meta, APIs pagas, hospedagem, domínio ou `main`. **Controle de progresso documental 19F: 69/100, sem alteração automática.**
