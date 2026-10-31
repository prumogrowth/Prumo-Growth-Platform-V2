# Checklist de conclusão — Frente WhatsApp/Meta

**Plataforma:** Prumo Growth Platform V2 (software sem marca própria; LiberaCred é produto da instituição financeira).  
**Atualização inicial:** 31/10/2026. **Proprietário da lista:** coordenação Meta.  
**Branch de trabalho:** `feat/meta-s0-physical-interop-ack-guard-20261031`. **Não representa merge, deploy nem autorização produtiva.**

## Como acompanhar

- `[x]`: marco **específico** concluído com evidência; marcos marcados como *offline/lab* NÃO significam operação real.
- `[ ]`: pendente (pode haver código preliminar ou testes parciais).
- Só marcar um item depois de satisfazer seu critério de aceite e anexar commit/teste ou ratificação correspondente.
- Este arquivo é a lista canônica para atualizações, sem porcentagem. Dependências alheias permanecem atribuídas aos seus donos.

## A. Base técnica e testes

- [x] **M01 — Decisões vigentes consolidadas:** WDC-01 a WDC-22, especificação e precedência disponíveis. Evidência: `00-decisoes-vigentes-precedencia-documental-2026-10-21.md` + `01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md`.
- [x] **M02 — Entrada Cloud offline:** HMAC, GET, roteamento App/WABA/phone e leitores de eventos com testes sintéticos. Evidência: `integrations/whatsapp-meta/` + CI 1183; **sem webhook real**.
- [x] **M03 — Saída Cloud offline:** construtores de texto, templates, mídia/interações e observação técnica sintéticos. Evidência: `graph-outbound.ts`, `graph-template.ts`, demais módulos + CI 1183; **sem Graph real**.
- [x] **M04 — Verificação de recibo Ed25519 sintético:** consumidor Meta com chave pública confiada separadamente e regressões negativas. Evidência: `cloud-s0-ed25519-receipt-interop.ts` e 36 testes; **não é recibo do PG17**.
- [x] **M05 — CI offline integral rastreável ao SHA:** 1.183/1.183, zero falhas/skips; checkout/GITHUB_SHA conferidos no job. Evidência: [run 41187216781](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41187216781), SHA `a91b0dac2c332ef5ebbe07fb7884ed5137d60484`.
- [ ] **M06 — Interoperabilidade física S0→Meta:** gerar recibo no runtime S0/PG17 descartável e consumi-lo no verificador Meta com âncora confiada fora do recibo; positivos, negativos, cleanup e logs no SHA final.
- [ ] **M07 — Proteção completa contra ACK sintético:** scanner, testes negativos e política de runtime/HTTP ratificada; nenhuma alegação estrutural pode emitir 200.
- [ ] **M08 — Escopo de lote multicanais/ACK ratificado:** contrato S0/Meta/Infra para unidade física, rejeição integral, retry e replay; prova cruzada sem ACK parcial.

## B. Patrimônio Meta e fronteira operacional

- [ ] **M09 — Cadastro e onboarding por concessionária:** comprovar App/WABA/número/templates próprios e delegação à Prumo, sem compartilhamento entre lojas.
- [ ] **M10 — Credenciais e identidade de serviço:** custódia, âncoras Ed25519, HMAC, rotação/revogação, menores privilégios e M2M homologados por S0/Infra.
- [ ] **M11 — Webhook GET/POST operacional:** endpoint autorizado, assinatura sobre bytes originais, limites, registro durável e retorno HTTP conforme contrato S0/Infra.
- [ ] **M12 — Ingresso durável integrado:** idempotência, concorrência, readback/recuperação e segregação por canal/tenant comprovados no serviço autorizado, não apenas PG17 lab.
- [ ] **M13 — Catálogo de assets e templates confiável:** fonte vigente com estados/aprovações/versões e sincronização com Meta, S0 e tenant.

## C. Envio e política comercial

- [ ] **M14 — Elegibilidade e opt-out:** consentimento, finalidades múltiplas, grants, supressão por concessionária e revisão no instante do envio com fonte S0 real.
- [ ] **M15 — Contrato F02 de planejamento:** fornecer somente templates ativos/autorizados; F02 não dispara nem inventa template e mantém contexto de campanha verificável.
- [ ] **M16 — Preparação segura de templates:** conteúdo, botões, mídia, variáveis congeladas por versão, snapshot auditável e integração de administração com frente MCP autorizada.
- [ ] **M17 — Assinatura de mensagem humana:** `Consultor/Gestor/Diretor Nome:\nMensagem` por autor autenticado na S0, somente texto livre permitido; prova de envio separada da assinatura.
- [ ] **M18 — Despacho Graph API homologado:** operação real somente com autorização específica, política de janela, revalidação, idempotência, rate limit e condição de recuperação.
- [ ] **M19 — Status e evidências reais reconciliados:** wamid/tentativa/tenant, callbacks duplicados e fora de ordem, estados incertos, leitura e entrega sem inferência comercial.
- [ ] **M20 — Regra WDC-13 integrada à S0:** evidência de `sent` e falha definitiva, reset e duas consecutivas processados pela autoridade S0 sem confundir timeout/ACK com envio.
- [ ] **M21 — Handoff humano e integração F01/F03:** impedir retomada F01 após handoff definitivo, preservar cutoff F03 e não conceder transições comerciais à Meta.

## D. Robustez, privacidade e controle

- [ ] **M22 — Logs/auditoria/observabilidade:** rastros sem PII/segredos, métricas por canal, status de saúde e alarmes operacionais.
- [ ] **M23 — Segurança e LGPD:** retenção, minimização, acesso, exclusão, mídias e tratamento de dados financeiros homologados com os donos.
- [ ] **M24 — Falhas externas e escala:** throughput, backpressure, redelivery, quarentena, recuperação pós-restart, timeouts e limites da Meta testados.
- [ ] **M25 — Política externa vigente da Meta:** validar janela de atendimento, templates/categorias, mídia, regras aplicáveis a crédito e consentimento antes de ativação.
- [ ] **M26 — Fluxos administrativos com S1/MCP e frontend:** capacidades e auditoria autorizadas, sem promover IA/MCP a administrador de Diretores.

## E. Homologação e conclusão real

- [ ] **M27 — Contratos interfrentes ratificados:** decisões WA-36/WA-37 atualizadas com aceite expresso S0/S1/Meta/Infra em suas competências e testes cruzados.
- [ ] **M28 — E2E autorizado em homologação:** webhook real, fluxo de cliente de teste, template aprovado, Graph, persistência S0, reconciliação, handoff e casos negativos documentados.
- [ ] **M29 — Segurança operacional final:** revisão de privilégios, casos adversariais, runbooks, rollback, incidentes e evidências de recuperação.
- [ ] **M30 — Liberação de produção:** merge/deploy explicitamente autorizados, ativos e credenciais reais homologados, monitoramento e aceite final dos responsáveis.

## Próximo marco

**M06**, com a implementação no laboratório físico da S0 **somente leitura da fonte**. O laboratório S0 por si já tem 49 testes PG17 declarados/certificados em seu checkpoint, mas isso não marca M06, M08, M11 ou M12 como concluídos.

## Limites permanentes

Nenhum sucesso offline autoriza HTTP 200, Graph real, envio, S0 write, privilégio humano, transição de venda, merge ou produção. S0/S1 não podem ser alteradas unilateralmente. Decisions WDC são preservadas. Os itens pendentes que exigem aceite humano serão destacados quando chegarem à etapa correspondente.
