# Frente WhatsApp/Meta — adoção do protocolo interfrentes #4

**Data de triagem:** 31/10/2026. **Fila oficial:** [Issue #4](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/4), protocolo v1. **Escopo:** Prumo Growth Platform V2, frente Meta; LiberaCred é o produto de crédito, não a marca da plataforma.

**Estado desta triagem:** nenhuma solicitação constitui homologação, autorização produtiva ou permissão de escrita em S0/S1. Esta matriz é uma fotografia dos pedidos encontrados; **o estado operacional corrente é o último comentário `STATUS: ...` em cada Issue**, não esta tabela.

## Adoção da rotina obrigatória

1. Ao iniciar **cada novo ciclo de desenvolvimento**, consultar **todas as Issues abertas** de `prumogrowth/Prumo-Growth-Platform-V2`; filtrar pelo `Responsável` e títulos, incluindo pedidos `OpenAI→Meta`. Ler comentários recentes, código/commit e documentação. Não presumir comunicação automática entre conversas.
2. Antes de abrir dependência, procurar pelo tema na fila **aberta e encerrada** e nos documentos do projeto; **uma Issue por interface/decisão real**. Responder no mesmo pedido com o modelo `Tipo/Solicitante/Responsável/Estado/Prioridade` e critérios.
3. A frente Meta pode trabalhar **somente no próprio branch/código offline**. Ao entregar, registrar na Issue: **`STATUS: ENTREGUE_PARA_ACEITE`**, branch, SHA exato, CI/testes, lacunas e próximo responsável. **Não marcar `ACEITA` por conta própria** quando depender de S0/S1/Infra/Proprietário.
4. A resposta da frente destinatária deve ocorrer na mesma Issue; quem requer revisa/aceita com evidência. `ENTREGUE` não é `ACEITO`, e nenhum aceite técnico é, por si, autorização de Graph, Meta Business Manager, SQL produtivo, permissões S0/S1, deploy, merge ou produção.
5. O protocolo declara operação **sem bot** e acompanhamento **por consulta deliberada no início de cada ciclo**, não prometendo monitoramento contínuo. Codex só é acionado mediante missão explícita quando houver implementação necessária.

## Fila existente — sem novas duplicatas

| M Meta | Contrato ou decisão real | Origem → Responsável | Issue canônica | Situação na triagem |
|---|---|---|---|---|
| M07-D / M08-D / M10-D / M11–12 | Autoridade de recibo S0, POST físico indivisível, HMAC/M2M, key pin, rotação/revogação, recuperação, política HTTP/ACK | Meta → S0/S1; Infra/Proprietário em decisões reservadas | [#2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2) | **AGUARDANDO_DECISAO**. Além de M07/M08 e M10, M11-A/B/C têm preflight estrito **somente offline** (44 testes, [CI 41214703461](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41214703461)); M11-D requer endpoint/HTTP/ACK e integração S0 reais. [Matriz M11](M11_ENVELOPE_WEBHOOK_GET_POST_PREFLIGHT_OFFLINE_2026-10-31.md). O PG17 é lab; nenhuma resposta HTTP 200 real autorizada. |
| M08-D (duplicidade histórica) | Mesma unidade transacional, replay e ACK | Meta → S0/S1 | [#3](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/3) | Encerrada **como duplicata**, demandas preservadas na #2; isso **não é aceite**. |
| M09 / M10 / M12 | Fonte versionada de cadastro/rotas App-WABA-phone-channel, grants e revogação por loja, sem segredos | Meta → S0/S1; Infra para ativos/credenciais reais | [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8) | **EM_ANALISE**: S0/S1 respondeu com fronteira preliminar, sem homologação. M09-A/B/C têm validação sintética (38 testes, [CI 41209617874](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41209617874)); M09-D aguarda fonte persistente S0 e comprovação Meta real. Em M10-A/B/C, 39 testes de pin/serviço sintético passaram; M10-D aguarda custódia e identidade reais. [Matriz M09](M09_AUDITORIA_OFFLINE_ASSETS_ONBOARDING_2026-10-31.md), [M10](M10_TRUST_PINS_M2M_ROTACAO_REVOGACAO_2026-10-31.md). |
| M13 / M15 (F02) | Pedido expresso de planejamento F02, catálogo já filtrado de templates elegíveis, revisões e continuidade | OpenAI → S0/S1, Meta contribui com escopo de templates | [#7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7) | **AGUARDANDO_DECISAO**. Meta comentou WA-26 e referenciou #10, sem criar outra Issue de planejamento. |
| M14 / M18 | Recheck S0 autoritativo `PRE_DISPATCH` de consentimento/opt-out/loja/grants/template/versão/campanha antes de Graph | Meta → S0/S1 | [#10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10) | **AGUARDANDO_DECISAO**, distinta do pedido F02 da #7. |
| M19 / M20 / F02 | Contrato outbound: Graph API_ACCEPTED vs sent/failed confirmado, ligação wamid/intento/tentativa/loja/template final, 131049; WDC-13/C09 só S0 | OpenAI → **Meta** (com S0 como autoridade de efeitos) | [#9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9) | **EM_ANALISE** pela Meta; módulos offline existentes identificados, versão física pendente. |
| M21 / F03 | Identidade, manifesto histórico multicaso, cutoff/handoff humano e direitos de mídia | OpenAI → S0/S1; Meta oferece somente transporte técnico quando requisitada | [#5](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/5) | Solicitação existente; nenhuma Meta paralela e nenhum conteúdo de mídia real publicado. |
| M21 / F03 | Retorno de proposta F03, recheck e aplicação comercial atômica **exclusiva S0** | OpenAI → S0/S1 | [#6](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/6) | Solicitação existente; Meta não executa conclusão nem transição. |

## Dependências identificadas, ainda sem Issue nova

Estas são **fronteiras futuras reais**, mas ainda não exigem solicitação paralela imediata enquanto a definição do consumo estiver imatura. Conferir a fila novamente antes de abrir:

- **M17 — S1 identidade de autor humano:** assinatura `Consultor/Gestor/Diretor Nome:\nMensagem` derivada de identidade autenticada, não de texto/alegação do cliente. Futura interface S0/S1 para autoria/versão/permissão, distinta de Graph. Sem alterar S0/S1 por conta própria.
- **M19–M20 — aplicação S0 de evidência/status e regra WDC-13:** a #9 é contrato de evidência **Meta→S0** solicitado pela OpenAI; a aplicação transacional WDC-13, eventos concorrentes e C09 são S0. Não criar demanda adicional se o novo contrato da #9 e a futura resposta S0 cobrir o assunto.
- **M21 — Frontend/S1 e OpenAI F01/F03:** handoff humano, janela Meta 24h, cutoff F03 e UI de autoria/leitura, sem confundir relógios ou reabrir F01. As #5/#6 já cobrem parte do fluxo F03.
- **M26 — Frontend e S1/MCP:** administrador Diretor autenticado, permissões, confirmação dupla em mutações; ferramenta administrativa não concede novos privilégios ao modelo. Abrir interface apenas após inventário de operações específicas e buscas na fila.
- **M27/28/29/30 — Infra/Proprietário:** ratificação de contratos, segredos, operação/observabilidade, E2E com recursos reais, merge e deploy expressos. Nenhum laboratório equivale a aprovação.

## Evidências já disponíveis e limites

- [Checklist Meta M01–M30](CHECKLIST_CONCLUSAO_META.md).
- [Auditoria M07/M08](AUDITORIA_M07_M08_2026-10-31.md), CI [1.210 offline / 18 PG17](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41194019498), fonte Meta `dd27a01d6a44bd8496d52d9cc2455c8b5752f886`, S0 referência fixa `01ffdb093013664b73b18d23f92aac2202578210`.
- [WA-26 ponte S0/Meta para template](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/dd27a01d6a44bd8496d52d9cc2455c8b5752f886/integrations/whatsapp-meta/s0-template-purpose-bridge.ts), sem serviço S0 real.
- [WA-09 reconciliação status](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/dd27a01d6a44bd8496d52d9cc2455c8b5752f886/integrations/whatsapp-meta/technical-reconciliation.ts), in-memory, sem persistência, tentativa/sent reais ou autoridade S0.

**Próxima ação própria:** M11-A/B/C concluídos em laboratório com 44 novos testes e [1.331/1.331 Meta em CI](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41214703461), sem endpoint ou ACK externo; M11-D aguarda S0/Infra na #2, e fonte canônica de canal na #8. Próximo marco M12 pode avançar apenas com contratos e testes offline de ingresso durável, sem alterar S0/S1 nem executar commit real até ratificação. O [contrato candidato WA-39 outbound](WA39_CONTRATO_CANDIDATO_EVIDENCIA_OUTBOUND_F02_S0_v0_1.md) foi publicado e comentado na [#9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9), sob **EM_ANALISE**, sem status de entrega operacional ou homologação; nunca enviar Graph/ACK reais nem alterar outras frentes.
