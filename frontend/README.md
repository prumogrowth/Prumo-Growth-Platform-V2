# Frente de desenvolvimento visual — Plataforma Prumo (nome técnico provisório)

**Situação:** área de trabalho preparada em 18/10/2026. **Branch:** `feat/frontend-plataforma-visual`, criada a partir de `main` no repositório privado `prumogrowth/Prumo-Growth---Platform`.

Esta branch reserva o trabalho de **frontend, experiência de uso, navegação, visualização de dados autorizados, acessibilidade e componentes de interface** da plataforma de operação comercial do produto **LiberaCred, da instituição financeira**. **Prumo Growth** é identificação técnica; o **nome comercial da plataforma ainda não foi definido**.

## Estado desta entrega

- [x] Branch independente criada no repositório existente.
- [x] Mapa de escopo, responsabilidades e limites registrado em `docs/01_ESCOPO_E_FRONTEIRAS.md`.
- [x] Inventário inicial de telas e fluxos registrado em `docs/02_MAPA_DE_TELAS_E_JORNADAS.md`.
- [x] Materiais-base, precedência normativa e critérios de continuidade reunidos em `docs/03_MATERIAIS_E_PREPARACAO.md`.
- [x] Área `design/` reservada a materiais visuais.
- [x] Contratos técnicos FV-01 e FV-02 redigidos e auditoria documental FV registrada; **homologação S0/OpenAI pendente**.
- [ ] Interface final, componentes e fluxos codificados.
- [ ] Testes visuais/responsivos e acessibilidade executados.
- [ ] Integração autenticada com backend.

**Nenhuma hospedagem, domínio, serviço externo, conexão com banco, credencial ou ambiente Supabase foi criado ou alterado por esta frente.** Dados reais de clientes não podem ser inseridos em mocks, fixtures, imagens ou commits.

## Importante: já existe uma S1 sintética

A branch `feat/s0-fundacao-prumo` já contém `frontend/s1/`, um **protótipo visual local**, com regras/testes sintéticos em desenvolvimento pela frente de fundação. **Não copiar, reescrever, mover, mesclar ou editar esses arquivos a partir desta branch sem revisão e coordenação com sua frente responsável.** Nossa branch parte de `main` para preservar independência. Sua integração ou eventual reaproveitamento da S1 requer comparação de escopo e revisão via PR, sem sobrepor trabalhos.

As branches `feat/s2-openai-adapter-sintetico` (provedor OpenAI) e `docs/whatsapp-meta-concessionária de demonstração-poc-20261017` (Meta/WhatsApp) também permanecem sob suas respectivas frentes.

## Antes de escrever o primeiro componente

1. Seguir as decisões aprovadas D41-01..06, a regra organizacional D-ORG-01 de 18/10 e os oito estados comerciais canônicos.
2. Examinar o caderno de telas (doc. 24) e o comportamento já demonstrado em `frontend/s1/`, **sem inferir que são código ou layout aprovados para produção**.
3. Separar visualização/protótipo de autorização real: permissões, transições e auditoria efetivas são responsabilidade do backend.
4. Definir a abordagem de interface com atenção à integração futura; não escolher hospedagem, domínio ou integração real nesta etapa.
5. Usar **somente conteúdo sintético** e submeter a revisão qualquer interface com ações sensíveis.

Nenhuma mudança nesta branch equivale a aceite de implementação, aprovação de MVP global, autorização externa ou incremento automático na régua de planejamento.

## Contratos técnicos e nova regra de extração pós-humana (18/10/2026)

A partir da decisão funcional mais recente, **operadores não preenchem rotineiramente os campos do cadastro**. O fluxo normal é **conversa humana → ação “Concluir atendimento” (rótulo provisório) → processamento OpenAI de retaguarda → validação/persistência pela S0 → ficha consultável com pendências**. A interface não chama a OpenAI diretamente nem modifica dados no banco. Concluir não envia ao banco, não marca vendido/perdido e não reativa a IA Vendedora.

- [FV-01 — contrato visual ↔ S0](docs/04_CONTRATO_FV01_UI_BACKEND_v0_1.md) — responsabilidades, leitura/escrita, permissões e telas.
- [FV-02 — conclusão de conversa e extração](docs/05_CONTRATO_FV02_CONCLUSAO_EXTRAÇÃO_POS_HUMANA_v0_1.md) — ação, feedback, idempotência, falhas e compatibilidade.
- [Auditoria dos contratos](docs/06_AUDITORIA_CONTRATOS_FV_2026_10_18.md) — achados, limites e pendências.

**Importante:** docs 23 e 41 continuam autorizando **correção humana excepcional** da ficha versionada; isto não significa voltar ao preenchimento manual rotina. O contrato interno OpenAI OAI-05/E01 está em outra branch e permanece sob responsabilidade da sua equipe. FV-01/FV-02 são [P/R] e não foram implementados nem aprovados entre frentes.

## Conciliação contratual S0/OpenAI — 18/10/2026

- [CFI-01 — relatório de conciliação interfrentes](docs/07_CONCILIACAO_INTERFRENTES_FV_S0_OAI_v0_1.md): mapeia FV-01/FV-02, contratos S0 (docs 26/40) e OAI-05/E01, divergências dos envelopes e critérios de decisão.
- [MAT-CFI-01 — 36 cenários de aceite contratual](docs/08_MATRIZ_ACEITE_CONTRATUAL_FV_S0_OAI_v0_1.md): **especificados, não executados**.

A OpenAI padronizou o nome candidato `human_close_extract` nos documentos OAI-05/E01. **Ainda há divergências nas estruturas de request/response**, cuja resolução pertence às frentes S0 e OpenAI. A operação browser→S0 permanece sem nome físico; o navegador **nunca** envia diretamente à OpenAI. Nenhuma revisão por proprietários S0/OpenAI, teste integrado ou deploy foi concluído nesta frente.
