# S1-002/I14 — Identidade da sessão em interface de gestão privada (19/10/2026)

**Fronteira:** esta implementação é somente para PostgreSQL 17 descartável. O projeto Prumo / LiberaCred exige que gestor coordene sua **equipe de operadores**; somente responsáveis autorizam concessionárias A/B/C e admitem/removem definitivamente profissionais. Pausa temporária é global, enquanto movimentações de casos preservam concessionária de origem e alçada do gestor sobre origem/destino.

## Fragilidade mitigada

Até I13, os comandos internos recebiam `p_solicitante` como UUID fornecido pela chamada. Não podem ser disponibilizados para clientes dessa forma. A migration `051` acrescenta **três interfaces de protótipo no schema privado** `prumo_private`: `s1_mover_atendimento_sessao(loja,caso,atribuicao_esperada,destino)`, `s1_pausar_operador_sessao(operador,motivo_codigo)` e `s1_reativar_operador_sessao(operador)`. **Nenhuma recebe identidade do autor como parâmetro**.

As três usam `auth.uid()` do contexto de sessão + conferência do papel de sessão `authenticated` e da existência do ator. Executam operações transacionais testadas I11/I13 internamente como `SECURITY DEFINER`, `search_path=''`, usando nomes qualificados. A autorização material continua em tabelas privadas de responsáveis/equipes e valida os casos e grants. `anon`, `service_role` e `PUBLIC` não possuem EXECUTE, e as interfaces ficam no schema **não exposto** `prumo_private` (não há RPC pública no `public`). Somente a role `authenticated` recebe `EXECUTE` nas três interfaces de protótipo + USAGE do schema; não recebe DML ou EXECUTE das funções internas com `p_solicitante`.

O controle de JWT é **provisório e não criptográfico** neste sandbox. O fake-auth fornece `auth.uid()` via `request.jwt.claim.sub` setável por SQL local. Somente um gateway real que valide assinatura JWT, sessão, revogação e as configurações de PostgREST pode garantir que esse contexto não seja adulterado. Consequentemente: **PROIBIDO considerar I14 homologação GoTrue/REST ou expor `prumo_private` na Data API**. O desenho segue os princípios da [documentação de funções Supabase](https://supabase.com/docs/guides/database/functions) sobre SECURITY DEFINER, `search_path` e privilégios explícitos, mas permanece candidato [P/V].

## Ensaios

`S1S-01..14`: fixture G1/G2, operadores O3/O4/O5 nas lojas A/B; papel ausente e `auth.uid` ausente falham; operador ou gestor alheio sem alçada falham; gestor G1 transfere A para O4 com autoria gerada da sessão; metadata de usuário com papel falsificado não amplia alçada; G1 pausa O3 globalmente em A/B, os grants permanecem, G2 não reativa O3; G1 reativa sem retornar casos antigos; anon/service_role não executam; `authenticated` não executa comandos internos com identidade parametrizada; interfaces não aparecem no schema public. **Até obter logs PG17 os marcadores são proposta de teste.**

## Gates remanescentes

- Teste real GoTrue/PostgREST com JWT assinado e revogado, claims `session_id` e políticas de sessão, incluindo falsificação de sessão e replay HTTP.
- Revisar privilégio EXECUTE dos comandos de protótipo depois do gateway real; enquanto `prumo_private` não estiver exposto, não há chamada REST; jamais disponibilizar automaticamente.
- Homologar status concluído/aberto do `CASO_HUMANO` no S0 antes de expor movimentação humana; sincronizar o novo titular para inbound e UI, sem envio/Meta automático.
- Definir política responsável→gestor, transferência de equipe, escala e plantão, experiência de afastamento sem registrar atestado nem diagnóstico.
- Sem merge, deploy, dados reais, Supabase hospedado, credenciais ou alteração no percentual global.

**Nenhuma mudança foi feita nas branches S0, OAI, Meta ou frontend.**
