# S1-001 — Primeira jornada operacional visual com gestores e operadores

**Data:** 18/10/2026. **Branch:** `feat/s0-fundacao-prumo`, PR #1 Draft. **Natureza:** demonstração local, inteiramente sintética, sem autenticação ou backend real. **Estado final:** protótipo local S1-001 testado automaticamente, **não** homologado em navegador real/produção.

## Objetivo

Sair de uma fundação S0 predominantemente SQL e auditoria para uma **primeira interface navegável** em que seja possível acompanhar a jornada de um lead fictício desde a importação/primeiro disparo simulado até o atendimento humano, uma remessa bancária simulada e o registro manual de encerramento. Isso **não inicia** integrações Meta, Banco, OpenAI ou Supabase hospedado; também não transforma S0 em produção. A S1-001 é o primeiro incremento visual, não a entrega total da fase S1.

Arquivos implementados: `frontend/s1/index.html`, `styles.css`, `app.mjs`, `domain.mjs`, `tests/domain.test.mjs`, `tests/app.smoke.test.mjs`, `README.md`; workflow isolado `.github/workflows/s1-synthetic-ui.yml`. Sem bibliotecas, pacotes, credenciais ou execução de API remota. O modelo de estado permanece em **memória de página**; atualizar ou restaurar desfaz a demonstração.

## Jornada do demonstrador

1. Perfil de gestor **Marina Costa, Concessionária Aurora**: vê apenas casos Aurora, indicadores e status. Outro gestor da **Concessionária Horizonte** tem escopo distinto; o mesmo telefone fictício aparece em ambas sem compartilhar históricos nem casos.
2. Um lead inicial sob triagem IA simulada é **atribuído a um operador da mesma loja**. A atribuição cria caso fictício e suspende a IA automática; a interface não oferece ação de retomar IA depois do handoff.
3. Perfil de operador: vê apenas os casos **atualmente atribuídos a ele**, nunca o catálogo da loja inteira; pode assumir atendimento humano, criar nota interna e simular o envio do cadastro ao banco. A revogação/re-atribuição remove imediatamente o caso de sua visão.
4. O gestor pode simular primeiro disparo e triagem IA somente antes da transferência humana, encaminhar cadastro ao operador designado e registrar manualmente a venda **com evidência fictícia** ou uma perda com motivo. O estado `cadastro enviado ao banco` **não é vendido**.
5. O histórico contém eventos com autor e versão; versão esperada evita aplicar comando desatualizado dentro do próprio reducer. Mensagens exemplificativas são `origem: fictícia`, não chat conectado, e notas internas não saem ao cliente.

## Modelo de visibilidade e operações

| Função | Gestor da mesma loja | Operador designado | Operador sem atribuição / outra loja |
| --- | --- | --- | --- |
| Listar leads, abrir histórico D2 sintético e notas | Sim, apenas própria loja | Sim, apenas caso designado | Não |
| Atribuir/re-atribuir caso | Sim, operador da própria loja | Não | Não |
| Simular primeiro disparo ou triagem IA | Sim, apenas etapa permitida e sem handoff | Não | Não |
| Encaminhar cadastro ao operador | Sim, depois de atribuir | Não | Não |
| Assumir atendimento humano | Não; exige operador designado | Sim, em etapa permitida | Não |
| Criar nota interna | Sim | Sim | Não |
| Simular cadastro enviado ao banco | Não; exige operador designado | Sim | Não |
| Registrar manualmente venda/perda | Sim, com evidência/motivo e etapa correta | Não | Não |

Os **oito estados comerciais** permanecem exatamente: `aguardando primeiro disparo`, `primeiro disparo enviado`, `em atendimento pela IA`, `em atendimento pelo operador`, `cadastro enviado ao operador`, `cadastro enviado ao banco`, `vendido`, `perdido`. Não existem novos estados comerciais de tarefa, webhook, agendamento ou callback. A interface não altera status automaticamente por callback simulado.

## Segurança: fronteira estritamente educativa

**Trocar o perfil via `select` não é autenticação**. Os filtros de escopo no JavaScript e as versões no reducer são **somente comportamentos de protótipo**. Em uma futura aplicação conectada, as autorizações terão de ser verificadas em backend autenticado, GoTrue/RLS por loja e caso designado, com locks, versionamento e auditoria transacional, conforme S0. A role `SECURITY DEFINER postgres` das duas wrappers comerciais legadas continua pendente de redesenho. Não usar HTML/app como API ou controle de acesso real.

A demonstração não coleta CPF, documentos, valor financiado, provas bancárias reais nem dados pessoais de clientes. Não usa `fetch`, `XMLHttpRequest`, `WebSocket`, `localStorage`, `sessionStorage`, cookies nem tokens; os textos renderizados dinamicamente usam `textContent` para não tratar notas como HTML ativo. Não representa D3/D4 bancários. Não contém endereço Meta real, URL Graph, canal ou chave; não há login verdadeiro nem deploy.

## Portões de aceite

**Automação S1:** `node --check` nos módulos e `node --test frontend/s1/tests/*.test.mjs` (27 cenários após auditoria: 21 de domínio e 6 smoke tests de DOM simulado), além de verificações de HTML/CSS no workflow S1. Cobertura: exatos oito status, telefone repetido A/B, isolamento por loja, operador designado, atribuição e suspensão da IA, transições de status, evidência manual de venda, perda, prevenção de replay por versão, notas, re-atribuição e ausência de rede/armazenamento persistente.

**Antes de chamar de S1 integrada:** autenticação GoTrue, backend com auditoria persistente, integração de atribuição real com `casos_humanos` e `atribuicoes_humanas`, permissões D2 versus D3/D4, jornada de cadastro conforme normas 00A/13A/21–23/41, testes de acessibilidade e aplicação visual conectada em ambiente *local* de homologação. Isso exigirá revisão explícita de segurança e decisões de produto. A S1-001 não publica interface como portal real.

**Ambiente:** PRs #1/#2 Draft, sem merge; sem migrations hospedadas, RPC pública, recursos pagos, Meta/Graph/Banco real, frontend em domínio público ou produção. DEC-WA-04/06 e identidade de ocorrência do C07 continuam pendentes.

## Aceite técnico confirmado — 18/10/2026

**[Workflow GitHub Actions S1 #39133454184 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39133454184)**, commit de código e testes `6bd187148da74da6906493b0e2a97d817ffe84ba`. Node 22: `node --check` dos módulos e testes, **24 casos PASS, 0 FAIL**, verificação de `index.html`, `styles.css` e guia de execução. Sem `npm install`, dependências externas, migrações ou segredos.

- **S1-001..018:** regras puras da jornada humana, oito estados, escopos A/B, visibilidade de operador designado, atribuição, suspensão de IA, estados e motivos/evidência, notas, versão otimista e ausência de rede/persistência.
- **S1-UI-01..06:** smoke test de DOM **fictício** verifica IDs referenciados, montagem inicial, troca de perfil operador, troca de concessionária, pesquisa vazia e restauração do estado.
- A primeira execução do protótipo [#39133175311 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39133175311) também aprovou 18/18 testes de domínio. O workflow foi simplificado depois para evitar execuções duplicadas por push e PR. O aceite final considera o commit posterior com smoke tests incluídos.

**Não coberto:** nenhum navegador foi aberto pelo CI, nenhuma revisão visual manual, mobile real, leitor de tela, RLS/GoTrue, backend persistente, concorrência em múltiplas sessões, envio Meta, IA OpenAI, cadastro bancário ou resultado comercial real foi testado. Qualquer evolução para aplicação conectada requer novo gate de segurança/autorização/auditoria. O protótipo **não** deve ser usado com dados pessoais reais.


**Verificação visual adicional:** os seis smoke tests de interface usam DOM fictício em Node para conferir referências de IDs, montagem inicial, seleção de operador, troca de loja, filtro vazio e reset. Isso **não substitui testes de navegador, mobile, leitores de tela ou auditoria UX**. O workflow é acionado por PR e execução manual, evitando duas rodadas iguais de push + PR na mesma revisão.


## Auditoria retroativa — correção de handoff S1 (18/10/2026)

**Achado AUD-S1-01 — trajetória inconsistente na etapa inicial:** antes da revisão, o gestor podia atribuir o caso quando ainda estava em `aguardando primeiro disparo`. A atribuição suspendia a IA, mas `start_human` e `route_operator` não aceitavam essa etapa; o lead ficava sem caminho humano correto. Além disso, `simulate_first` não verificava `aiSuspended` diretamente. **Correção sintética:** bloquear a atribuição nessa etapa inicial, até que exista fluxo humano validado; exigir `!aiSuspended` para toda simulação de primeiro disparo; regressões AUD-S1-01..03. Isso **não** significa proibir atendimento humano antes de contato na plataforma real: a exceção deverá ser explicitamente especificada para S1-002 no backend e respeitar cancelamentos/opt-out.

**Gate de transparência:** toda a fixture de outras concessionárias continua no JavaScript da demo; o isolamento ocorre apenas na UI/reducer. Não há confidencialidade real de dados em um protótipo 100% client-side. **Não usar clientes reais nem levar essa técnica de permissão para o backend**.

**Resultado da regressão de auditoria:** [Workflow S1 #39134672559 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39134672559) no SHA `360b1a8d2c5bbfa6ae239344ee5d011583c815a4`, 27 PASS, 0 FAIL. Testes de DOM continuam fictícios; navegador real e acessibilidade pendentes.


## Alinhamento organizacional D-ORG-01 — equipe Prumo

**Alinhamento organizacional D-ORG-01 (18/10/2026):** gestores e operadores são profissionais **da Prumo**, inclusive quando dedicados exclusivamente a uma concessionária. Loja é escopo de atendimento, não vínculo empregatício. Uma pessoa pode ter múltiplas lojas por concessão explícita; gestor pode autoatribuir caso segundo D41-04. Ver `docs/D_ORG_01_EQUIPE_PRUMO_2026_10_18.md`. Na S1-001, `shopId` por ator é *uma única concessionária escolhida como cenário*, não empregador ou cardinalidade final. Na S1-002, representar equipe própria Prumo com múltiplos escopos autorizados e opção de dedicação exclusiva, sem acesso irrestrito; manter capacidade do gestor se autoatribuir casos D41-04. “Gestor da loja A” significa gestor da Prumo **com concessão vigente** para A. Não modificar os 27 testes aprovados retroativamente: qualquer nova verificação exigirá CI próprio.
