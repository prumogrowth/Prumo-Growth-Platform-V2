# FV-AUD-05 — Auditoria retrospectiva de FV-UI-004 a FV-UI-009

**Data:** 19/10/2026  
**Escopo:** branch `feat/frontend-plataforma-visual`, somente `frontend/`.  
**Base de comparação:** mapa de jornadas doc.24 via `frontend/docs/02_MAPA_DE_TELAS_E_JORNADAS.md`, FV-01, FV-02, FV-03/CF-OP-02, decisões D41, documentação de O3/O4/O5 e testes dos módulos atuais.  
**Conclusão:** a direção funcional da simulação permanece alinhada, **mas a auditoria identificou três classes de falhas**, corrigidas e verificadas no harness. Sem GO de produção.

## Falhas concretas e reparos

| ID | Severidade | Constatação | Reparação |
| --- | --- | --- | --- |
| AUD5-01 | Alta — escopo de acesso | `registrationProjectionFor` (O3) e `bankProjectionFor` (O4) devolviam resumo operacional ao **operador não atribuído** de uma loja concedida, embora `visibleConversations` não autorizasse aquele operador a ver o caso. A UI principal filtrava casos, porém o módulo de projeção não negava diretamente. | As duas funções agora devolvem `visibility=forbidden` para operadores sem atribuição. Mantido o resumo D2 ao gestor ativo da loja e os detalhes somente ao profissional atribuído. Testes adicionados para perfil Bianca acessando caso de Rafael. |
| AUD5-02 | Alta — continuidade pós-marco | O O5 confundia permissão para **operar o novo caso** com permissão para **abrir o caso anterior**. Um novo operador designado poderia ficar bloqueado se o histórico original pertencesse a outra carteira. | Introduzido `mayMockOperateContinuation`: novo caso exige própria atribuição e projeção confirmada do S0, respeita loja e sinal de IA silenciada, e rejeita vínculo incoerente detectável. Navegação ao histórico continua restrita a quem pode ver ambas as pontas; novo operador sem essa permissão segue atendendo o novo caso sem descobrir o anterior. Ações de recontato permanecem bloqueadas se o vínculo do novo caso não for válido. |
| AUD5-03 | Alta — integridade de fixtures | `copyCFDemoFixtures` copiava superficialmente `postmarkProjection`, `registrationProjection` e suas listas. Alterar uma fixture durante teste poderia **contaminar os resets e testes seguintes**. | Cópia independente de `postmarkProjection`, `bankProjection`, campos, ausências e conflitos da ficha e das tentativas de recontato. Teste de reset comprova que mutações não atravessam instâncias. |

## Invariantes novamente conferidos

- Exatamente oito estados comerciais canônicos; frontend não inventa transições para venda, perda, remessa ou negativa bancária.
- Conclusão humana solicitada ≠ confirmada; dados propostos pela IA ≠ ficha persistida. O3 só rotula persistência confirmada com versão.
- O4 só demonstra remessa/retorno com projeção fictícia de prova e registro humano, sem expor detalhes D4 por mera supervisão.
- Janelas Meta, C09 e envio final não são decididos por relógio do browser; `queued/requested` ≠ `sent` verificado.
- O5 tem ciclos **separados**: caso anterior preservado, novo humano independente, IA Vendedora silenciada, atendimento dentro da própria atribuição, sem expor histórico de outro operador.
- S0/S1-002 continuam autoridade real de identidade, concessão, atribuição, consentimento, provas, persistência, comandos e mudanças comerciais. Estas verificações são apenas de frontend **sintético**, não de segurança real.

## Evidência realmente executada

Após todos os reparos, arquivos foram recuperados da **branch remota GitHub**, e os testes escritos para Node foram avaliados com imports/asserções adaptados a um **harness JavaScript V8**:

- **65/65** testes de regras/projeções passaram, incluindo as novas regressões de acesso, continuidade e isolamento de fixtures.
- **25/25** testes de interação com DOM sintético passaram (incluindo mobile).
- **15/15** verificações estáticas de HTML/CSS/JS passaram.
- **Total 105/105 verificações sintéticas PASS**, sem falha de sintaxe nos módulos inspecionados.

**Não comprovado:** execução nativa `node --test`, Playwright/Chromium do código remoto mais recente, responsividade renderizada, leitor de tela, autenticação, isolamento S0/RLS, integrações, prova da instituição financeira ou funcionamento operacional real. O GitHub não apresentou status checks de CI associados à branch na verificação desta auditoria; testes simulados não substituem CI nem homologação. Não afirmar “sem problemas restantes” ou “pronto para produção”.

## Pendências e liberação de continuidade

1. **Pode prosseguir com desenvolvimento sintético** de G2–G4 no mesmo ramo, sem alterar domínio nem APIs de outras equipes.
2. **Antes de avaliação visual final:** obter checkout atual autorizado em ambiente de testes e executar Node literal, Chromium/Playwright em múltiplos tamanhos, acessibilidade e correções decorrentes.
3. **Antes de operação:** acordos físicos FV↔S0/S1/OpenAI/Meta/Banco, projeções minimizadas no servidor, testes reais de revogação e autorização e revisão de LGPD.
4. **Sem merge/deploy/alteração de infraestrutura** nem revisão automática do indicador auditado 19F (mantido em 69/100).

**Veredito:** falhas descobertas, reparadas e regressão sintética aprovada. O rumo é adequado **para continuar o protótipo**, mas não autoriza homologação funcional.
