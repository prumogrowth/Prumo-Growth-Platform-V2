# Decisão de escopo — integração técnica entre frentes (01/11/2026)

**Estado:** AUTORIZADO_DESENVOLVIMENTO_ISOLADO; PRODUCAO_NAO_AUTORIZADA.

Registro da orientação expressa do proprietário, nesta data: S0/S1 pode prosseguir com **desenvolvimento e testes de integração que sejam úteis**, sem aguardar nova anuência para cada incremento técnico. Dependências pertencentes a outra frente devem ser documentadas na Issue existente e devolvidas ao responsável para execução/aceite. Não é autorização irrestrita para ambientes reais.

## Autoridade e limites

**Permitido neste escopo:** contratos candidatos versionados, leitura de código e documentação, adapters e testes entre frentes em **branches isoladas**, CI, bases PG17/Docker descartáveis, dados e chaves sintéticos, auditorias e comentários de coordenação. Pode cruzar artefatos de outras frentes por **checkout SHA-pinned de somente leitura**, preservando propriedade da fonte; qualquer edição nela requer coordenação com sua frente responsável.

**Não autorizado por esta decisão:** merge na main, deploy, alteração de Supabase/banco hospedado, migrations/ACL reais, uso de credenciais Meta/Graph/KMS, configuração de provedores/contas reais, escrita em dados de cliente, HTTP ACK produtivo, mensagem real, operação bancária/comercial, mudanças de regra de negócio, acesso não consentido a dados sensíveis ou designação/alteração de autoridade humana. Esses atos requerem provas e aprovação específica, mesmo com todos os testes verdes. Não se deve inventar posse de ativos ou substituir assinaturas de responsabilidade técnica por uma autorização genérica.

**Critério de aceite técnico:** entrega com escopo exato, versão, SHA, testes reproduzíveis, negativas de segurança, autenticação e versão de origem comprovadas no ambiente pertinente e revisão expressa da frente consumidora. `ENTREGUE` ou `CI_SUCCESS` nunca equivalem a `ACEITA` ou `PRODUCAO_AUTORIZADA`.

## Matriz de encaminhamento — quem tem de entregar o quê

| Issue | Responsabilidade de S0/S1 | Entrega de outra frente e aceite necessário |
| --- | --- | --- |
| [#8 M09](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8) | Fonte autoritativa de App/loja/WABA/número/canal, grants, cinco revisões, revogação, host/M2M, recheck; M09-08 segue somente em PG17 descartável | **Meta:** revisar e aceitar/rejeitar contrato `scoped/purpose-specific` sem três slots juntos e consumer WA04A/WA09. **Infra/Proprietário:** inventário e prova de titularidade/delegação de Business/App/WABA/número, confiança de serviço, custódia/rotação de chaves e slots |
| [#2 Ingresso](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2) | Proposta de persistência, atomicidade de lote, readback/recovery e recibo técnico S0 | **Meta:** política de borda GET/POST, HMAC por App, código HTTP/ACK e interpretação de retries. **Infra/Proprietário:** gateway, rede, identidade, segredos, disponibilidade, observabilidade e autorização específica para teste E2E hospedado |
| [#10 PRE_DISPATCH](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10) | Fonte/contrato de consentimento por finalidade, opt-out, template/versão e recheck transacional da tentativa com CAS | **Meta:** especificar quais provas de aprovação/media/revisão precisam ser verificadas e aceitar interface de execução; **Infra/Proprietário:** habilitar só após controle de custódia/política. M09-08 não concede envio |
| [#7 F02](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7) | Pedido S0 explícito, catálogo elegível e aliases, versões de plano, guarda de consentimento e continuidade | **OpenAI:** revisar shape de consumidor F02, obedecer aliases opacos e não converter preview M15 em autorização; **Meta:** revisão do catálogo interno e das provas M13/M15/M16 |
| [#5/#6 F03](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/5) | Manifesto multicases com cutoff/completude e aplicação somente S0, com recheck semântico e CAS | **OpenAI:** consumir metadados minimizados, preservar conflitos/proveniência e nunca aplicar fichas diretamente; **Privacidade/Proprietário:** política de acesso a conteúdo/mídia |
| [#11/#12 F01](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/11) | Posse IA, handoff humano definitivo, guardas de publicação e fatos comerciais versionados/vigentes por loja | **OpenAI:** adequar consumidor, não publicar após handoff nem criar oferta a partir de fonte vencida; **Comercial/Proprietário:** fonte e aprovação de ofertas/preços |
| [#14 Frontend](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/14) | Leitura do titular ao abrir, pendência de resposta, timestamp/ordenação, versões/escopo e concorrência | **Frontend:** integrar UI somente à projeção S0 ratificada; gestor supervisor não marca leitura do Consultor titular |
| [#9 WA39 outbound](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9) | Correlacionar tentativa/recibo/evento e publicar estado autenticado para consumidor F02 | **Meta:** contrato tipado de sent/falha definitiva, ordem, dedupe e provas de transporte; **OpenAI:** não tratar API_ACCEPTED como sent |
| [#13 Resumo](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/13) | Futuro contrato de histórico resumido minimizado | **OpenAI/Frontend:** resumos pequenos de F01/F02/F03 na aba Resumo; não antecipar a implementação |

## Sequência de trabalho e handoff

1. **S0/S1 não repassa responsabilidades próprias**: pode continuar contrato técnico, testes, segurança, CAS e leitura de fonte em isolamento enquanto espera consumo Meta.
2. **Meta** recebe na #8 decisão pontual: interface `scoped/purpose-specific` versus API antiga de três slots; na #2 e #10 informa requisitos e revisa negativa/autoridade. **OpenAI e Frontend** recebem em suas Issues o contrato que precisam revisar quando houver candidato S0.
3. **Infra/Proprietário** responde sobre recursos reais, identidade/segredos, titularidade/delegação, ambientes e política de produção por uma aprovação própria. A autorização atual cobre somente desenvolvimento isolado, não essas operações.
4. Não abrir Issues duplicadas. Pela [#4, protocolo](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/4), cada frente revisa e comenta na Issue existente; **silêncio não equivale a aceite**.

**Checkpoint atual:** M09-08 SHA `0925aa46df6fcafd6ac7551fe2f33a35691b2622`, [CI 41296781187](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41296781187): 18 casos novos físicos, 16 físicos herdados, 32 sintéticos; todos PASS, somente laboratório. Sem merge, deploy ou credenciais de produção.
