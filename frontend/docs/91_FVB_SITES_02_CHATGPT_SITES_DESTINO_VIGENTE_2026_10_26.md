# FVB-SITES-02 — ChatGPT Sites como destino de prévia interativa (diretriz vigente)

**26/10/2026 · Frente visual da plataforma Prumo · branch `feat/frontend-plataforma-visual`.**

## Correção de entendimento e precedência

O responsável esclareceu que seu objetivo é **ChatGPT Sites**, integrado ao ambiente **ChatGPT Work/Codex**, **não Google Sites nem um endereço permanente da aplicação**. A prévia deve ser navegável por colaboradores em celular e desktop, permitir cliques e avaliação de UX, e permanecer desligada de serviços reais.

Este documento **substitui a recomendação de hospedagem principal** do documento `90_FVB_PREVIEW_01_GOOGLE_SITES_GUIA_DEPLOY_ISOLADO_2026_10_26.md`. O ZIP verificado [run 40310945219](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40310945219) é um **artefato opcional válido**, mas não precisa ser enviado ao Cloudflare nem incorporado ao Google Sites. Nenhuma dessas publicações externas foi feita.

## Produto confirmado (fontes oficiais OpenAI em 26/10/2026)

- ChatGPT Sites cria, pré-visualiza, hospeda, publica e compartilha sites interativos e apps leves, a partir de descrição ou **projeto existente compatível**.
- A criação está disponível via **ChatGPT Work no navegador** ou **Work/Codex no aplicativo desktop**, incluindo o invocador `@Sites`; os acessos dependem do plano/permissões.
- Antes de publicar: revisar a prévia privada, testar comportamento e escolher o público em **Compartilhar**. Os Sites criados são privados inicialmente.
- Nas contas Plus/Pro elegíveis, a hospedagem do Sites está incluída no plano durante a disponibilidade atual, sujeita aos limites de uso; criação e edição consomem uso do Codex.
- Referências: https://help.openai.com/pt-br/articles/20001339-creating-and-using-chatgpt-sites e https://learn.chatgpt.com/pt-BR/docs/sites .
- **Compatibilidade de importação não pressuposta:** Work/Codex deve inspecionar o projeto e verificar suporte à estrutura HTML/CSS/ESM, adaptando uma cópia do frontend visual se necessário. A simples conexão GitHub não é prova de implantação pronta.

## Fluxo aprovado de preparação, sem autorização para publicação imediata

1. Prosseguir normalmente com as verificações FVA/FVB e fechar a versão visual demonstrativa; preservar `main` e S0 sob responsabilidade do Codex. A última auditoria FVA-01 aprovada está em [run 40300012152](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40300012152).
2. Entregar ao Work **a branch `feat/frontend-plataforma-visual`**, diretório `frontend/visual/`, os contratos visuais atuais e a certificação GitHub Actions. Aguardar que Work inspecione compatibilidade com ChatGPT Sites antes de alterar o projeto.
3. Pedir a criação de **prévia privada no ChatGPT Sites**, a partir do frontend existente, **sem redesenhar do zero nem inventar integrações**. O resultado deve preservar todas as jornadas e dados 100% sintéticos, sem backend operacional, sem credenciais ou comunicação com Meta, banco, OpenAI operacional ou Supabase.
4. Conferir em navegador desktop e celular: toque/click, lista, busca, filtros, conversas, equipe, etapas, modais, tema claro/escuro, histórico e estados de simulação. Identificar eventuais limitações da experiência mobile ou incompatibilidade do Site antes de publicar.
5. Somente após aprovação do responsável, **implantar o Site** e definir quem pode acessá-lo; compartilhar URL temporária com colaboradores escolhidos. A implantação gera uma URL real da prévia, mas não é a implantação oficial da plataforma Prumo.
6. Coletar feedback por ferramenta própria ou formulário separado autorizado; registrar dispositivo, navegador, módulo visitado, dificuldade, proposta e evidência visual, **sem solicitar dados de clientes reais**.

## Prompt de handoff para ChatGPT Work / @Sites quando a frente visual estiver pronta

> Crie uma **prévia interativa de avaliação** no **ChatGPT Sites** aproveitando o projeto existente no repositório privado `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`, branch `feat/frontend-plataforma-visual`, diretório `frontend/visual/`. Primeiro verifique a disponibilidade desse repositório e a compatibilidade do projeto com o ChatGPT Sites. Utilize os arquivos e contratos atuais da frente visual, preservando layout, responsividade, interações, módulos e **somente dados sintéticos**. Não reconstrua a interface por suposição, não conecte S0/S1/WhatsApp/OpenAI/Banco/Supabase, não use dados reais, não altere branches oficiais nem publique automaticamente. Mostre primeiro uma prévia privada navegável em desktop/mobile e relate adaptações necessárias. Depois de minha aprovação, publique como versão **temporária de avaliação** com controles de acesso apropriados e forneça o link para compartilhar com os avaliadores. Se alguma dependência bloquear a publicação, documente sem contornar permissões.

## Fronteiras e estado

- O **responsável S0 é o Codex**; qualquer proposta que afete o núcleo fica isolada com arquivos/contratos/dependências, sem merge sem coordenação.
- A preview **não** implementa backend real, segurança autenticada, salvamento de leads ou autorização produtiva. Os seletores de ator/loja são **fictícios**.
- O desenvolvimento do frontend pode continuar até o aceite de UX, sem confundir esta escolha de hospedagem com encerramento do projeto.
- **Ainda não criado nem publicado um ChatGPT Site.** Esta rodada documenta a diretriz corrigida e prepara o handoff, não executa a implantação.
