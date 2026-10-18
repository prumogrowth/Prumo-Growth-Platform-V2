# Frente de desenvolvimento visual — Plataforma Prumo (nome técnico provisório)

**Situação:** área de trabalho preparada em 18/10/2026. **Branch:** `feat/frontend-plataforma-visual`, criada a partir de `main` no repositório privado `prumogrowth/Prumo-Growth---Platform`.

Esta branch reserva o trabalho de **frontend, experiência de uso, navegação, visualização de dados autorizados, acessibilidade e componentes de interface** da plataforma de operação comercial do produto **LiberaCred, da instituição financeira**. **Prumo Growth** é identificação técnica; o **nome comercial da plataforma ainda não foi definido**.

## Estado desta entrega

- [x] Branch independente criada no repositório existente.
- [x] Mapa de escopo, responsabilidades e limites registrado em `docs/01_ESCOPO_E_FRONTEIRAS.md`.
- [x] Inventário inicial de telas e fluxos registrado em `docs/02_MAPA_DE_TELAS_E_JORNADAS.md`.
- [x] Materiais-base, precedência normativa e critérios de continuidade reunidos em `docs/03_MATERIAIS_E_PREPARACAO.md`.
- [x] Área `design/` reservada a materiais visuais.
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
