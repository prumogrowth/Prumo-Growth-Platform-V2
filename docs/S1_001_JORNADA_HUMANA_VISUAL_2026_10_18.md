# S1-001 — Primeira jornada operacional visual com gestores e operadores

**Data:** 18/10/2026. **Branch:** `feat/s0-fundacao-prumo`, PR #1 Draft. **Natureza:** demonstração local, inteiramente sintética, sem autenticação ou backend real. **Estado inicial:** implementação proposta, aceite condicionado ao workflow S1.

## Objetivo

Sair de uma fundação S0 predominantemente SQL e auditoria para uma **primeira interface navegável** em que seja possível acompanhar a jornada de um lead fictício desde a importação/primeiro disparo simulado até o atendimento humano, uma remessa bancária simulada e o registro manual de encerramento. Isso **não inicia** integrações Meta, Banco, OpenAI ou Supabase hospedado; também não transforma S0 em produção. A S1-001 é o primeiro incremento visual, não a entrega total da fase S1.

Arquivos implementados: `frontend/s1/index.html`, `styles.css`, `app.mjs`, `domain.mjs`, `tests/domain.test.mjs`, `README.md`; workflow isolado `.github/workflows/s1-synthetic-ui.yml`. Sem bibliotecas, pacotes, credenciais ou execução de API remota. O modelo de estado permanece em **memória de página**; atualizar ou restaurar desfaz a demonstração.

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

**Automação S1:** `node --check` nos módulos, `node --test frontend/s1/tests/domain.test.mjs` (18 cenários) e verificações de arquivos HTML/CSS no workflow específico S1. Cobertura: exatos oito status, telefone repetido A/B, isolamento por loja, operador designado, atribuição e suspensão da IA, transições de status, evidência manual de venda, perda, prevenção de replay por versão, notas, re-atribuição e ausência de rede/armazenamento persistente.

**Antes de chamar de S1 integrada:** autenticação GoTrue, backend com auditoria persistente, integração de atribuição real com `casos_humanos` e `atribuicoes_humanas`, permissões D2 versus D3/D4, jornada de cadastro conforme normas 00A/13A/21–23/41, testes de acessibilidade e aplicação visual conectada em ambiente *local* de homologação. Isso exigirá revisão explícita de segurança e decisões de produto. A S1-001 não publica interface como portal real.

**Ambiente:** PRs #1/#2 Draft, sem merge; sem migrations hospedadas, RPC pública, recursos pagos, Meta/Graph/Banco real, frontend em domínio público ou produção. DEC-WA-04/06 e identidade de ocorrência do C07 continuam pendentes.

**Evidência definitiva:** preencher apenas após inspecionar o workflow S1 relativo ao SHA do código testado; até então este documento é especificação de protótipo.
