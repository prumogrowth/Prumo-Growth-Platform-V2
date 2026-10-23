# S1-002 / I49 — fila sem titular, projeção mínima e disputa entre Gestores

**Data:** 23/10/2026. **Categoria:** decisão funcional vigente [D/DN] aplicada a fixtures [T], projeção/claim técnico [P], integração S0 [R]. **NÃO** é autorização para implantar RPC, migrations ou operações S0. PR #5 continua Draft.

## Decisão funcional preservada

Conforme contrato S1-002 de 22/10/2026 §§2–5: lead novo sem destinatário elegível entra em fila **sem titular humano**, visível a TODOS os Gestores especificamente autorizados à concessionária, inclusive de equipes diferentes. Gestor sem concessão específica não pode ver a fila. Essa exceção **não** concede leitura de casos atribuídos a outras equipes. Ao assumir, somente um titular pode vencer uma disputa; o primeiro commit válido deve impedir o segundo. Lead já atribuído a Consultor pausado não vira automaticamente fila compartilhada. Consultores comuns não exploram essa fila sem alçada.

O evento confiável de **ingresso na fila** é responsabilidade da S0. **Não se pode deduzir fila** exclusivamente de `leads_loja` sem `casos_humanos`, de `mensagens.caso_id IS NULL`, de status comercial ou de concessão de loja. O protótipo I49 cria marcador fictício emitido por S0 e concede APENAS uma projeção mínima com IDs opacos, sem telefone, corpo da conversa, documentos, histórico de caso ou direito de enviar.

## Desenho exclusivamente no banco local descartável

- `supabase/tests/s1_072_fila_minima_local_only.sql`: esquema privado `prumo_s1_i49_test` com `s0_fila_sem_titular_mock` (loja, lead, ciclo, estado e versão) representando **somente um evento fictício** de S0. A função `public.s1_i49_fila_resumo_mock(loja)` é **SECURITY DEFINER apenas no laboratório**, com `search_path=''`, EXECUTE concedido só ao papel `authenticated`, controle explícito de `auth.uid()`, equipe S1 ativa, grant `gestor` vigente da loja, concessionária ativa, marcador pendente e inexistência de caso associado ao lead. Retorna SOMENTE `concessionaria_id, lead_id, ciclo_id`. Não retorna PII nem permite escrever. A função em `public` é uma ferramenta do teste PostgREST, **não um endpoint aprovado**, e requer revisão de S0 e Security para qualquer equivalente real.
- No mesmo SQL, `prumo_s1_i49_test.assumir_mock` simula, como **postgres apenas**, um núcleo S0 que bloqueia o lead `FOR UPDATE`, revalida marcador, loja, ator e ausência de caso; cria caso e atribuição numa transação, resolve o marcador e incrementa versão. É `SECURITY INVOKER`, não exposta no PostgREST, com EXECUTE revogado a `authenticated`/anon/PUBLIC. **Não é uma API S1 de transferência/assunção**, e não substitui a função S0 canônica, nem prova sua proteção real contra interleavings de outros escritores.
- `scripts/test_s1_002_i49_fila_concorrencia.py`: reusa seis identidades com JWT real GoTrue e a stack I44–I48, mais duas sessões PostgreSQL independentes para disputar o mesmo item fictício.

## Critérios verificáveis I49

1. **I49-01 — marcador explícito obrigatório**: dois Gestores autorizados à loja LA veem somente fila fictícia LA (L4/CY5); outro lead sem caso, mas sem marcador, NÃO aparece. Fonte da carteira completa `leads_loja` permanece fechada pelo I45.
2. **I49-02 — alçada**: Consultores, outsider, anon e Gestor não autorizado à loja LB não visualizam a fila.
3. **I49-03 — concessão**: revogar grant LA corta acesso com o mesmo JWT; reautorizar restabelece somente a fila daquela loja, sem conceder acesso a casos alheios.
4. **I49-04 — suspensão e multiloja**: suspender Gestor S1 corta a fila; concessão LB não concede LA e vice-versa.
5. **I49-05 — concorrência**: duas sessões transacionais disputam mesmo marcador; uma obtém APPLIED, outra ALREADY_CLAIMED, sem segunda atribuição/caso no fixture. Marcador resolvido impede a fila reaparecer depois do commit; retry não assume de novo.
6. **I49-06 — não escalar D2/D3/D4**: mensagens sem caso_id continuam fechadas, cliente não cria caso pelo REST, e função privada de claim não é executável pelo cliente.

## Dependências S0/S1 ainda abertas [R]

O S0 deve comprovar: evento real e durável de entrada/saída da fila, estágio correto do lead novo (que pode já ter caso sem titular), elegibilidade cross-team, prova CAS/versão confiável, ordem de locks, auditoria do Gestor autenticado e bloqueio de criação de casos/atribuições por caminhos alternativos. A fila compartilhada deve ter apresentação útil sem divulgar dados de outras equipes, e o retorno de Consultor elegível só pode redistribuir itens **ainda sem titular**. Projeção/ação contextual devem ser separadas: enxergar identificador não é permissão de ler conteúdo, enviar, assumir ou alterar concessão.

**Limite de cobertura:** a fixture I44 carrega S0/001–005 e protótipos I41–I48, não executa um endpoint S0 real de fila. O mock de concorrência é uma demonstração **positiva** de bloqueio por lead no executor postgres, não teste de corrida contra o núcleo produtivo nem validação completa dos contratos D3/D4, entrega Meta, LGPD ou F03. A2 (movimentação manual para Consultor com intake pausado) permanece [R].

## Evidências

Verificar logs e SHA de Actions antes de atribuir PASS; registrar no encerramento.
