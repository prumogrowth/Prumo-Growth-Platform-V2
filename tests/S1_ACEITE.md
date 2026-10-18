# S1 — Registro de aceite e limites

## S1-001 — Central de operações humana sintética (18/10/2026 UTC)

**Resultado:** [GitHub Actions S1 #39133454184 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39133454184). Commit testado `6bd187148da74da6906493b0e2a97d817ffe84ba`, workflow `.github/workflows/s1-synthetic-ui.yml`. Foram executados `node --check`, **24 testes Node 22 (18 de domínio, 6 de montagem fake-DOM), 24 PASS e 0 FAIL**, e verificações de arquivos HTML/CSS/README. Antes dos smoke tests, [#39133175311 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39133175311) passou nos 18 primeiros testes. O workflow foi restringido a PR/manual para evitar duas rodadas por commit.

**Código:** `frontend/s1/index.html`, `styles.css`, `app.mjs`, `domain.mjs`, `tests/domain.test.mjs`, `tests/app.smoke.test.mjs`, `README.md`. Primeira UI de gestor e operador em memória de navegador, sem pacotes terceiros ou solicitações externas. O HTML referencia apenas CSS e módulos locais. A app renderiza conteúdo dinâmico via `textContent`. Não há tokens, dados pessoais verdadeiros, login, cookies, `fetch`, `localStorage`, Supabase ou Graph.

**Aceites específicos:** mesma identidade telefônica fictícia A/B sem cruzamento de leads; gestor vê apenas concessionária própria; operador vê somente os próprios casos com atribuição vigente; atribuição exclusiva para operador da mesma loja; handoff humano suspende IA; versão otimista bloqueia comando stale; notas internas não se tornam outbound; primeiro disparo/triagem IA/remessa ao banco são explícitas simulações; venda somente após estado cadastrado no banco e evidência manual fictícia; perda com motivo humano; exatamente oito estados comerciais.

**Limitações:** teste de fake DOM não é teste em navegador nem screenshot; nenhuma homologação visual, mobile, WCAG, foco de teclado, sessão GoTrue, RLS, acesso D2 real, D3/D4, banco, n8n, Meta, OpenAI API, worker ou persistência. As duas wrappers comerciais legadas da S0 continuam `SECURITY DEFINER postgres`. S1-001 não significa fase S1 completa. Em especial, alternar perfil com um `select` é somente encenação e **não autentica ninguém**.

**Documentos:** `docs/S1_001_JORNADA_HUMANA_VISUAL_2026_10_18.md`, `docs/MAPA_MENTAL.md`, este arquivo de aceite e `frontend/s1/README.md`.

**Governança:** PR #1/#2 Draft, sem merge. Não houve migrations no Supabase hospedado, instalação de frontend público, chave real, tráfego Meta/Banco ou operação produtiva. **GO para revisar visualmente a demo local e planejar S1-002 com backend autenticado; NO-GO para publicação/uso com clientes reais.**


## Auditoria retroativa S1-001 — handoff antes do primeiro disparo

[**GitHub Actions Node 22 #39134672559 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39134672559), SHA `360b1a8d2c5bbfa6ae239344ee5d011583c815a4`: **27 testes PASS, 0 FAIL** (21 domínio, seis DOM simulado). **AUD-S1-01:** a atribuição de caso ainda aguardando primeiro disparo gerava suspensão de IA e um caminho humano inacessível; no protótipo, essa atribuição agora é negada até projeto de handoff inicial real. **AUD-S1-02:** o primeiro disparo não pode ocorrer se a IA estiver suspensa. **AUD-S1-03:** perfil inválido, loja errada e versão obsoleta não alteram estado. A S1 ainda carrega todas as fixtures fictícias no navegador: filtro visual **não é confidencialidade**. Não houve browser/screenshot real, login, RLS ou backend persistente. Ver `docs/AUDITORIA_S0_037EF_S1_001_2026_10_18.md`. **GO para desenho controlado S1-002; NO-GO para uso com clientes reais.**


## D-ORG-01 — governança organizacional do demonstrador

**Alinhamento organizacional D-ORG-01 (18/10/2026):** gestores e operadores são profissionais **da Prumo**, inclusive quando dedicados exclusivamente a uma concessionária. Loja é escopo de atendimento, não vínculo empregatício. Uma pessoa pode ter múltiplas lojas por concessão explícita; gestor pode autoatribuir caso segundo D41-04. Ver `docs/D_ORG_01_EQUIPE_PRUMO_2026_10_18.md`. A demo ainda não implementa múltiplas concessões por usuário nem gestor atuando como operador autoatribuído, funcionalidades aprovadas/necessárias para futura S1-002. Não interpretar os perfis exclusivos dos testes como funcionários das lojas. Validar o próximo commit S1 antes de acrescentar números de aceite.
