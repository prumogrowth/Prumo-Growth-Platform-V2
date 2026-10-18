# 01 — Escopo e fronteiras da frente visual

**Natureza:** organização de trabalho [P] informada pela instrução do responsável em 18/10/2026; não modifica as decisões comerciais e de autorização já aprovadas. **Objetivo:** desenvolver a experiência visual da plataforma e versionar o trabalho exclusivamente no GitHub.

## A frente visual faz

- Estrutura de navegação, aparência, componentes, tipografia, estados de tela, responsividade, acessibilidade e experiência de operação.
- Telas para **operador da Prumo**, **gestor da Prumo** e visualizações administrativas cuja experiência visual venha a ser autorizada.
- Representações **fiéis** dos dados que um backend autorizado forneceria: estado comercial, fila/atribuição, conversas, históricos, cadastros permitidos, remessa e resultado; transparência quanto a carregamento, falha, permissão e informação ainda não confirmada.
- Protótipos **sem dados reais**, fluxos de navegação, testes de interface e documentação de decisões de design.
- Contrato de apresentação do gatilho de **conclusão da conversa humana** e retorno de **extração cadastral pós-humana**, sem tocar em APIs/credenciais da OpenAI ou em persistência S0.

## Responsabilidades que NÃO migram para a frente visual

| Frente / autoridade | Responsabilidade própria | Limite desta branch |
| --- | --- | --- |
| Fundação / S0 / backend / Supabase | Identidade autenticada, autorização, RLS/grants, separação por concessionária e caso, modelos persistidos, transições válidas, auditoria e consistência | Front não concede acesso, não cria migrations, não altera regras de negócio nem Supabase |
| WhatsApp / Meta | Webhooks, canais, titularidade App/WABA, envio, templates, status técnicos e processamento de mensagens | Front apenas **exibe** informação já validada; não chama Graph nem dispara comunicação |
| OpenAI / IA | Adaptadores, prompts, modelos, custos de inferência, decisão de chamada e processamento autorizado | Front pode representar estados e mensagens fornecidos pelo backend; não executa modelos nem controla IA por conta própria |
| Gestão por ChatGPT / MCP | Comandos administrativos permitidos, confirmação autenticada especial e trilha própria | Front não implementa comandos MCP nem substitui o procedimento administrativo aprovado |
| instituição financeira / humano autorizado | Prova de remessa e de resultado real, parâmetros e autorização bancária | Front não infere remessa, venda ou recusa por simulação, clique ou retorno incerto |
| Produto / responsável | Aprovação de escopo e de decisões pendentes; autorização de publicação/uso real | Wireframe, protótipo e sugestão são [P], não decisão [D] |

## Regras já aprovadas que a UI deve respeitar

1. Existem **exatamente oito status comerciais**, com estes nomes: `aguardando primeiro disparo`; `primeiro disparo enviado`; `em atendimento pela IA`; `em atendimento pelo operador`; `cadastro enviado ao operador`; `cadastro enviado ao banco`; `vendido`; `perdido`. Fila, atribuição, espera, mensagem lida, callback ou processamento são informações técnicas **separadas**, não novos status comerciais.
2. **Handoff humano definitivo no caso**: a UI não oferece retorno livre à IA; atribuição e primeira resposta do operador são eventos diferentes.
3. `cadastro enviado ao banco` requer envio real confirmado por operador; `vendido` requer venda efetivamente confirmada pelo banco e registro humano. Recusa definitiva comprovada, após remessa, é registrada manualmente como `perdido`, preservando evidência e histórico. Silêncio do banco não é recusa.
4. Após `cadastro enviado ao banco` ou `vendido`, novo contato do cliente volta a humano da concessionária pertinente, sem reativar a IA nem sobrescrever o ciclo anterior.
5. **D41-01..06:** gestor pode ler conversas completas D2 das concessionárias sob sua gestão e autoatribuir caso; em modo de supervisão não obtém automaticamente ficha D3 ou provas brutas D4. Ações de operador exigem atribuição válida, inclusive se o ator for gestor. Operadores acessam somente os casos designados e seus escopos concedidos.
6. **D-ORG-01 (18/10/2026):** operadores e gestores são profissionais **da Prumo**, não empregados das concessionárias, ainda que dedicados a uma loja. Identidade, papel, concessões de loja, atribuição a caso e escala são dimensões diferentes. Suporte a várias lojas não significa acesso irrestrito.
7. Texto de conversas D2 pode conter informação financeira fornecida espontaneamente. Não assumir que omitir painéis D3/D4 resolve, por si só, a exposição de dados sensíveis. Em protótipos utilizar somente dados sintéticos.
8. A interface não torna verdadeiras autorizações de banco, Meta, LGPD nem capacidades de integrações ainda não homologadas.

## Fronteiras de branch e convivência

- Esta branch deriva de **`main`**, para não absorver migrations, testes ou interfaces em curso no PR S0 e não invadir a frente Meta ou OpenAI.
- Diretório de trabalho reservado: `frontend/` e sua documentação. **Não alterar** `supabase/`, `backend/`, `integrations/`, workflows de outras frentes, seus documentos de auditoria nem a branch `main`.
- A S1-001 de `feat/s0-fundacao-prumo` é uma **referência existente**, não código desta branch. Qualquer reaproveitamento dependerá de revisão coordenada, evitando duas implementações concorrentes da mesma tela.
- Antes de integrar código, verificar contratos técnicos vigentes e alterações recentes de D-ORG-01, sem transformar propostas em regras aprovadas.

## Emenda FV-2026-10-18 — cadastro extraído automaticamente, não digitado rotineiramente

**[D-direção atual]** O operador conversa com o cliente e conclui sua etapa. A plataforma solicita ao backend S0 processamento de extração pela OpenAI; o S0 valida e grava automaticamente os campos elegíveis na base, com origem e versão rastreáveis. **Nenhum campo de cadastro é digitado rotineiramente pelo operador no frontend.**

**[P/R]** O botão, contrato de solicitação, tela de andamento/pendência e opção de conferência são definidos por [FV-01](04_CONTRATO_FV01_UI_BACKEND_v0_1.md) e [FV-02](05_CONTRATO_FV02_CONCLUSAO_EXTRAÇÃO_POS_HUMANA_v0_1.md). A frente OpenAI já dispõe de OAI-05/E01 e mantém total titularidade de extração/adaptador; S0 continua dono de evento, identidade, catálogo, validação, escrita e auditoria.

**[D preservada]** Correção humana individual excepcional doc.23/C13/D41-04 não foi expressamente revogada; não criar formulário regular de digitação. Encerramento da conversa é evento técnico, não remessa, venda, recusa, status comercial novo ou reativação da IA Vendedora.

**Auditoria:** [06_AUDITORIA_CONTRATOS_FV_2026_10_18.md](06_AUDITORIA_CONTRATOS_FV_2026_10_18.md); sem testes de contrato/aceite interfrentes.
