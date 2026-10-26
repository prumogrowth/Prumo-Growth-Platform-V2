# FVB-PREVIEW-01 — Pacote de avaliação da interface via Google Sites

> **SUPERADO EM 26/10/2026 — CORREÇÃO DE DESTINO DE PUBLICAÇÃO:** o responsável esclareceu que se referia ao **ChatGPT Sites (OpenAI)**, não ao Google Sites. O fluxo Google Sites + Cloudflare abaixo é apenas uma **alternativa técnica histórica não executada**. **Diretriz vigente:** preparar o projeto visual para o **ChatGPT Work/Codex → ChatGPT Sites**, sem publicação automática e sem acesso a dados reais. Consultar [FVB-SITES-02](./91_FVB_SITES_02_CHATGPT_SITES_DESTINO_VIGENTE_2026_10_26.md) antes de qualquer deploy. O ZIP previamente certificado continua válido como artefato estático opcional, mas não é requisito para ChatGPT Sites e não foi publicado.


**Data:** 26/10/2026. **Responsável pela frente:** Frontend visual, sem modificações em S0. **Objetivo:** permitir que avaliadores externos abram a versão interativa sintética em celular e computador, sem apresentar o protótipo como aplicativo operacional e **sem publicar o repositório privado**.

## Decisão técnica — Google Sites é a entrada; a aplicação é um embed externo

O Google Sites permite incorporar o URL de outra página como uma seção ou como **página inteira** (Ajuda Google: https://support.google.com/sites/answer/90569?hl=pt-br). Porém os módulos JavaScript `type="module"` da interface exigem uma origem HTTPS que sirva arquivos reais (`index.html`, `styles.css`, `*.mjs`). Para evitar copiar centenas de KB de código para um bloco do Sites, o pipeline prepara um **ZIP estático** que pode ser hospedado por exemplo no **Cloudflare Pages Direct Upload** (documentação: https://developers.cloudflare.com/pages/get-started/direct-upload/).

O Google Sites fornece o **link que será compartilhado com a equipe**. A URL auxiliar `*.pages.dev` fica como hospedagem técnica da interface e poderá ser aberta diretamente no celular caso o embed do Google Sites tenha recorte de altura/scroll.

### O que o pacote contém e não contém

Apenas os arquivos da raiz `frontend/visual/` necessários ao navegador: `index.html`, `styles.css`, módulos `*.mjs` com **fixtures fictícias**, além de um manifesto de integridade, `robots.txt` e headers para *não indexação*. Exclui `frontend/docs`, `frontend/visual/tests`, `.github`, documentação do núcleo, credenciais, variáveis de ambiente, backend, Supabase, Meta e OpenAI. O ZIP é gerado **sem alterar o código visual já certificado**; preserva byte a byte os assets pinados no manifesto auditado.

**Não indexação não é proteção de acesso.** Um link estático de Cloudflare Pages pode ser visto por qualquer pessoa que o obtenha; o uso público só é defensável porque **os dados são 100% sintéticos e não há operações reais**. Não colocar dados reais, tokens, credenciais ou integrações nesta versão. Permissões de visualização do Google Sites **não protegem automaticamente** a URL direta de hospedagem.

## Procedimento de distribuição — sem publicar a `main`

1. Conferir o último workflow `frontend-visual-validation` na branch `feat/frontend-plataforma-visual`, exigindo **`FULL LOCAL ACCEPTANCE: PASS`** antes do ZIP. O workflow produz o artefato `prumo-demo-visual-zip` somente quando Python, Node e Chromium passam.
2. Em **GitHub > Actions > execução aprovada > Artifacts**, baixar `prumo-demo-visual-zip`. O download do GitHub é um contêiner de artefato, dentro do qual está **`prumo-demo-visual.zip`**; se necessário, extrair o ZIP externo primeiro.
3. Abrir **Cloudflare > Workers & Pages > Create application > Drag and drop**; enviar o arquivo `prumo-demo-visual.zip` (ZIP interno que contém `index.html` na raiz), sem conectar o repositório e sem implementar backend. Confirmar após o deploy que `https://<projeto>.pages.dev/` mostra conversas fictícias e navegação desktop/mobile. **Esse passo exige ação explícita na conta do responsável**; não foi executado por este desenvolvimento.
4. Abrir https://sites.google.com/new no computador, criar um site provisório de avaliação. Incluir contexto claro e botão para abrir a versão em tela cheia.
5. Em **Páginas > Nova página > Incorporação de página inteira**, inserir a URL HTTPS do Pages. Alternativamente, em **Inserir > Incorporar**, incorporar a mesma URL dentro de uma página explicativa. Conferir os limites do quadro no celular, e oferecer **link direto** para `pages.dev` quando for mais fácil avaliar toque/rolagem.
6. Publicar o Google Sites apenas para os avaliadores escolhidos, verificando quem pode visualizar; não confundir essa permissão com segredo da página Cloudflare. Distribuir o **link do Google Sites** à equipe junto com orientação de avaliação.
7. Coletar feedback por Google Forms separado (sem pedir nome do cliente nem documentos bancários) ou outro canal autorizado; registrar data, dispositivo, navegador, tela e observação. Consolidar antes de corrigir a interface.

## Texto recomendado para a página inicial do Sites

**Título:** Prévia interativa — Central de Atendimento Prumo (versão de avaliação)

**Aviso:** Esta é uma prévia de design e navegação. Os nomes, clientes, conversas, decisões de banco e telas são **simulações fictícias**. Nenhuma mensagem é enviada e nenhum cadastro real é processado. O nome definitivo da plataforma ainda não foi definido. LiberaCred é o produto financeiro da instituição financeira, não o nome deste site.

**Instruções:** Experimente no celular e no computador. Use o seletor de **perfil fictício** para comparar Consultor e Gestor; teste fila, histórico, conversa, detalhes, tema claro/escuro e estados de confirmação. Ao terminar, informe o que ficou confuso, o que precisa melhorar e em qual aparelho/navegador ocorreu.

**Botão recomendado:** Abrir demonstração em tela cheia → URL técnica `https://<projeto>.pages.dev/`.

**Coleta recomendada:** Google Forms com: dispositivo; navegador; tela/perfil avaliado; nota de 1 a 5 para clareza e navegação; dificuldade encontrada; sugestão; opcional captura de tela **sem dados pessoais**.

## Critérios de conferência antes do compartilhamento

- A versão pública abre via HTTPS com `index.html` na raiz; módulos ES carregam sem erros nem 404.
- Testar 320px/390px mobile e desktop (>=900px), claro/escuro, abertura/volta de conversa, filtro/busca, histórico, aba equipe do Gestor.
- Testar a incorporação Google Sites **e o botão direto** em celular real; evitar duas barras de rolagem ao avaliar responsividade.
- Confirmar que cabeçalhos/avisos dizem demonstração fictícia; não expor `README`, testes, documentação interna nem arquivos de S0.
- A publicação externa é um **ato separado** do build e deve ser aprovada/realizada pelo responsável. Nenhuma ferramenta desta frente habilita publicação automática, Google Sites, Cloudflare ou conexão com o núcleo.

## Impacto nos contratos e S0

Arquivos adicionados: `frontend/preview/build_preview.py`, `frontend/preview/test_build_preview.py`, este documento. Arquivo modificado: `.github/workflows/frontend-visual-validation.yml`. Nenhum arquivo sob `frontend/visual/`, `frontend/s1/`, S0, API, migrations ou `main` foi alterado. Continua preservado todo o trabalho e PRs anteriores.

## Empacotamento rápido usando o snapshot FVA-01 já certificado

O build geral da interface continua testando Chromium para alterações reais de frontend. Para permitir distribuição do mesmo runtime sem qualquer nova modificação visual, foi adicionada uma rotina **separada** `.github/workflows/frontend-preview-package.yml` com verificação *fail-closed*: o Git tree inteiro de `frontend/visual` precisa ser **idêntico** ao já aprovado `c9e7dd75f3a50dd0727eaeac808c412e26de9258` ([run PASS 40300012152](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40300012152)). A rotina executa os testes do ZIP e compara cada asset aos hashes do manifesto antes de disponibilizar artefato, **sem modificar a `main` e sem publicar nada**. Não substitui Chromium quando o runtime visual mudar; basta um arquivo alterado nessa árvore para o empacotamento rápido bloquear até haver nova certificação e repin do baseline. O artefato pode ser baixado de qualquer execução **PASS** da rotina rápida ou do workflow nativo completo.

## Certificação de distribuição do ZIP — 26/10/2026

A geração **não depende** da instalação de Chromium da nova execução de validação, pois exige que a árvore inteira de `frontend/visual` seja idêntica à árvore aprovada FVA-01 (`c9e7dd75f3a50dd0727eaeac808c412e26de9258`, [run PASS 40300012152](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40300012152)). Se o runtime mudar um byte, a rotina rápida bloqueia até nova certificação, sem produzir pacote indevido.

- **Commit da rotina e da documentação pré-certificação:** `92c9cdead85bdf2f40b7a933359bfacc640033fb`.
- **Run de empacotamento:** [40310945219](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40310945219), `completed / success`.
- **Arquivo disponível no GitHub:** [artefato prumo-demo-visual-zip](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40310945219/artifacts/12645156168), identificação `12645156168`, cerca de 76 KB, retenção de **30 dias** configurada no workflow. Contém `prumo-demo-visual.zip` para upload estático.
- **Prova no log:** `Runtime idêntico ao SHA certificado ... — PASS`; Python **2/2 testes do empacotador PASS**; **22 arquivos de runtime pinados** e copiados byte a byte; `Preview ZIP prepared: out/prumo-demo-visual.zip`; upload do artefato `success`.
- O pacote ainda **NÃO** foi enviado ao Cloudflare Pages ou Google Sites, não há URL pública e nenhum usuário externo obteve acesso por esta execução. A publicação requer ação do responsável em suas contas.
- **Run adicional da suíte completa:** [40309322594](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40309322594) foi iniciado para o commit anterior da preparação; seu estado não é usado para afirmar aprovação do ZIP, pois a rotina rápida já foi aprovada contra o runtime FVA-01 certificado. Consultar o resultado desse run separadamente antes de inferir nova aprovação.
