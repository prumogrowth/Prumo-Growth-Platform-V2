# FV-UI-013 — Continuidade de cobertura Chromium mobile | 19/10/2026

Branch exclusiva: `feat/frontend-plataforma-visual`; base `cb53fcaa6ce35dcba46ddab3cb103e00edbe06f8`.

## Alterações desta execução
- `9133c396`: roteiro `browser.smoke.py` agora navega em G3 e G4 no celular (390x844), verifica painéis, ausência de dados da equipe Daniel na tela de Marina e overflow horizontal.
- `6526a737`: `source-module-graph.test.mjs` passa a exigir estaticamente os marcadores do cenário mobile, incluindo isolamento de G3/G4.

## Evidência efetiva e limites
- Arquivos e alterações recuperados da branch remota pelo conector autenticado GitHub.
- Oito marcadores da nova cobertura conferidos no bloco mobile real do script: 8/8 presentes. Fragmento de Python acrescentado aprovado em análise sintática local AST.
- O clone privado em ambiente local continua bloqueado por DNS de `github.com`.
- Nesta continuidade, **nenhum teste Node integral nem Playwright/Chromium da aplicação completa foi executado**. Os números históricos 23/23 Node parcial e 180/180 V8 adaptado não foram reexecutados e não representam homologação do novo smoke.

**Veredito:** cobertura preparada e versionada, execução nativa pendente. FV-UI-013 não homologada. Sem merge, deploy, integração, outras branches ou alterações fora de `frontend/`. Índice 19F preservado em **69/100**.

## Teste negativo da nova guarda
O teste estático novo foi executado isoladamente em V8 com o arquivo real do GitHub: PASS. Ao trocar deliberadamente a verificação de exclusão de L-G4-03, o mesmo teste falhou como esperado. Este é teste do **roteiro estático**, não execução Chromium.


## Terceira rodada — duas larguras gerenciais e isolamento de perfis

Commits:
- `4bb03f9c`: `browser.smoke.py` repete G2/G3/G4 no Chromium em **390x844 e 320x640**, além da varredura principal de quatro viewports.
- `7e8e68ed`: nova regra em `source-module-graph.test.mjs` exige as duas larguras e interações G3/G4.
- `031cafb6`: `app.mobile.dom.test.mjs` ganhou ensaio que alterna Marina -> Daniel -> perfil suspenso enquanto G3/G4 estão ativos, exigindo esvaziamento dos painéis anteriores.

**Ensaios executados nesta rodada:** fonte integral dos 11 módulos e mock DOM original recuperados do GitHub para o HEAD `031cafb6`. No harness V8 adaptado, `app.mobile.dom.test.mjs` passou **10/10**; a verificação estática adicional passou **1/1**. Duas mutações negativas no smoke (remover 320px e remover clique em G3) foram detectadas pelo novo teste estático (**2/2 falhas esperadas**). Nenhum desses números é execução nativa Node/Chromium.

**Pendente:** checkout privado completo, execução oficial `node --test`, Py/Playwright/Chromium real e capturas/evidências de layout nos quatro tamanhos. Não inferir homologação pela passagem V8. Sem alterações fora de `frontend/`; sem deploy, APIs de negócio, autenticação ou remessa. 19F **69/100** e FV-UI-013 **NÃO HOMOLOGADA**.


## FV-UI-013 — prova combinatória do isolamento entre gestores

Commit [`414e825f`](https://github.com/prumogrowth/Prumo-Growth---Platform/commit/414e825f2273ac80153458c37fc632fa5fb3d7a8): incremento de `frontend/visual/tests/fixtures.test.mjs`, **sem mudar o comportamento de produção**. Acrescentada matriz determinística de 512 registros com os oito estados comerciais, atribuições a seis atores, nulo ou desconhecido, vinculação de gestão Marina/Daniel/nula/desconhecida e duas lojas fictícias. Cruzamento com seis perfis e usuário ausente em duas lojas: **7.168 asserções de visibilidade esperada**.

**Execução comprovada desta rodada:** fontes literais `fixtures.mjs` (Git blob `22264f84947c5f8ea4a1a52adf038dcd1ac27d4b`) e nova suíte (Git blob `9547b1dfd1cf9107a897eb85f3d4cecddc3d900d`) recuperadas da branch. Harness **V8 adaptado**, não Node nativo: **7/7 testes passaram**, inclusive o novo teste combinatório. Mutação proposital da regra de gestor para aceitar qualquer atribuição dentro da loja levou a **5/7 PASS e 2 falhas esperadas**, demonstrando que a nova matriz rejeita a ampliação indevida do acesso.

**Limites:** essa asserção exercita exclusivamente o filtro da demonstração e **não é prova de autorização do S0, RLS ou integração**. O teste adicionado ainda requer reexecução com `node --test` sobre o checkout privado integral e Chromium real. Git HTTPS local permanece bloqueado por ausência de resolução DNS. FV-UI-013 **não homologada**; indicador 19F **69/100**.


## Bloqueio explicado e caminho alternativo de execução (19/10/2026)

**O checkout não depende do Supabase.** Checkout significa obter no computador/ambiente de testes uma cópia integral da branch GitHub, com arquivos e metadados de revisão. O bloqueio visto no terminal é de **resolução DNS de `github.com`**, enquanto a integração autenticada GitHub consegue ler e editar arquivos. Node v22 e Chromium já estão instalados; nenhum backend, banco Supabase, RLS ou endpoint Meta é exigido para estes testes exclusivamente fictícios.

**Nova ferramenta de desbloqueio:** [`frontend/visual/tests/verify_offline_export.py`](../visual/tests/verify_offline_export.py), criada em `f6037291`. Ela aceita um ZIP padrão da branch baixado no GitHub e verifica, em memória e por SHA-1 Git Blob + tamanho, **31 arquivos obrigatórios** de `frontend/visual/` correspondentes ao commit base `50cc951e52c5ac5ca125e93416b2cad45f416ee9`. Esses arquivos não foram modificados no commit que adicionou a ferramenta. Arquivo ausente, duplicado, alterado ou com caminho inseguro é reprovado antes de executar qualquer teste. Caso aprovada a integridade, `--run-native` executa todas as suítes `node --test` e o roteiro real Playwright/Chromium sobre os bytes verificados, gravando evidências JSON.

### Como executar com o ZIP autorizado

1. Baixar do próprio GitHub o **ZIP da branch** `feat/frontend-plataforma-visual` (idealmente fixado no commit `50cc951e52c5ac5ca125e93416b2cad45f416ee9`, ou revisão posterior que preserve os mesmos 31 blobs). Não colocar token, arquivo `.env`, segredo ou dados reais no ZIP; é apenas fonte fictícia.
2. Com a ferramenta e o ZIP em mãos, executar `python3 verify_offline_export.py --archive /caminho/branch.zip --run-native --json-report /caminho/evidencia.json`.
3. Inspecionar os passos `node` e `chromium` no JSON. A ferramenta fixa `full_acceptance=false` e `git_checkout_verified=false` porque ZIP íntegro **não é o mesmo que checkout Git**. Resultados só devem ser relatados se realmente executados.
4. Para o gate **formal original** (`run_acceptance.py --expected-head SHA`), ainda é necessário um checkout Git completo, com branch, HEAD e árvore de trabalho verificados. A ferramenta ZIP viabiliza o diagnóstico nativo sem liberar homologação indevida.

**Ensaios efetivos desta rodada:** o verificador local equivalente foi compilado por Python e exercitado com ZIP sintético íntegro (aceito), arquivo adulterado (rejeitado) e erro de manifesto (rejeitado). A versão GitHub teve a consistência de seu manifesto de 31 arquivos e do commit-base conferida pela leitura autenticada. **Nenhum ZIP integral real do frontend foi fornecido nesta rodada; Node/Chromium integrais ainda não foram executados**. Sem Supabase, integração, merge ou produção. FV-UI-013 segue **NÃO HOMOLOGADA**; 19F **69/100**.
