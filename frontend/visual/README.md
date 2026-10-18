# FV-UI-001 — Central de Atendimento, estrutura visual responsiva

**Branch proprietária:** `feat/frontend-plataforma-visual`. **Referência visual:** organização de mensageiro familiar ao WhatsApp, sem copiar sua identidade, marca ou recursos. **Situação:** demonstração local com dados 100% sintéticos; não é portal operacional.

## Abrir localmente

Na raiz do repositório:

```bash
python3 -m http.server 4174 --directory frontend/visual --bind 127.0.0.1
```

Abra `http://127.0.0.1:4174` no navegador. Não publicar na internet nem expor o servidor de demonstração na rede. Não há instalação de dependências. O carregamento de módulos ES exige HTTP local, e não `file://`.

## Testar fixtures e sintaxe

```bash
node --check frontend/visual/fixtures.mjs
node --check frontend/visual/app.mjs
node --test frontend/visual/tests/*.test.mjs
```

Os seis testes de regras artificiais foram executados localmente, com resultado PASS. A inspeção visual e navegação em Chromium headless foi realizada nos tamanhos 1440, 900, 390 e 320 px, sem erro de script nem overflow horizontal. Por restrições do ambiente, o navegador de testes recebeu HTML/CSS/JS localmente e não acessou a URL via rede; a carga HTTP direta ainda precisa de verificação em ambiente permitido.

## Experiência demonstrada

- **Desktop:** barra lateral fina, lista de conversas e filtros, conversa aberta e painel de detalhes.
- **Celular:** lista → conversa em tela cheia → detalhes; botões para voltar.
- **Perfis fictícios:** operadores Rafael, Bianca e Lia e gestora Marina (equipe Prumo). A gestora visualiza lojas concedidas e pode agir apenas num caso de exemplo autoatribuído. **Esse seletor não autentica ninguém.**
- **Conversa:** mensagens sintéticas podem ser acrescentadas só na memória do navegador. Nada é transmitido.
- **Conclusão FV-02:** botão em caso humano atribuído abre confirmação e mostra solicitação fictícia; detalhe pode demonstrar resultado parcial fictício. Não chama OpenAI nem grava cadastro.
- **Cadastro:** não há formulário de preenchimento manual habitual. Catálogo definitivo de campos, correções excepcionais C13 e processamento real pertencem às frentes responsáveis.
- **Estados comerciais:** somente os oito aprovados. Conclusão/extração são eventos técnicos, não marcos de venda ou remessa.

## Limites críticos

O código **não possui** autenticação, RLS, backend, Supabase, OpenAI, Meta/WhatsApp, instituição financeira, gravação persistente, API, chamadas de rede, cookies, localStorage, segredos nem dados reais. Filtrar dados no JavaScript de uma demonstração não protege informações; em implantação o S0 deve filtrar no servidor.

Esta área `frontend/visual/` é **separada** de `frontend/s1/` e da branch `feat/s1-002-equipe-prumo` (frente S0). Não reutilizar a demonstração como regras de negócio. A integração depende dos contratos FV-01/FV-02 e da revisão S0/OpenAI [Issue #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4), ainda pendente.

**Identidade:** Prumo é referência técnica e organizacional, não nome comercial aprovado da plataforma. LiberaCred é produto da instituição financeira.

## Critérios de continuidade

Revisar estética/responsividade com responsável; testar navegação por teclado e tecnologia assistiva; obter revisão S0/OpenAI antes de consumir serviços reais. Não configurar domínio, hospedagem ou migrações.

## FV-UI-002 — Incremento funcional de interface, 18/10/2026

Sem alterar a identidade do protótipo, foram acrescentados filtro por status comercial (apenas os oito valores canônicos), indicadores sintéticos da fila, quatro abas de detalhe (**Resumo, Histórico, Notas e Extração**), notas internas demonstrativas, visão de equipe apenas para o perfil fictício de gestor e três cenários de retorno da extração (parcial, falha, versão obsoleta), além do pedido aceito. Nenhum cenário persiste a ficha, envia mensagem ou modifica estado comercial.

Teclas adicionais: **Ctrl/Cmd+K** busca, setas direita/esquerda para abas e Escape para voltar em telas pequenas fora de formulários/dialogs.

**Teste Node executado:** `node --test frontend/visual/tests/*.test.mjs` → **12/12 PASS**. **Teste Chromium headless executado:** quatro larguras (1440, 900, 390, 320) e fluxo de gestor/duas lojas, sem erro JS nem overflow. O ensaio Chromium foi feito por injeção local de HTML/CSS/JS pois o ambiente bloqueia HTTP loopback; ele não valida serviço HTTP ou autenticação. Roteiro opcional reproduzível (com Playwright + Chromium já instalados): `python frontend/visual/tests/browser.smoke.py`.

[Auditoria FV-UI-002](../docs/10_AUDITORIA_FRONTEND_FV_UI_002_2026_10_18.md). Falta aprovação visual futura, acessibilidade aprofundada e homologação de integração; **não é aplicação de produção**.
