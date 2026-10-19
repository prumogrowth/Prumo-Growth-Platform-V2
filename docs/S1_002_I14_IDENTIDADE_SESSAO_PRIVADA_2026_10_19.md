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


**Reforço de privilégio I14 [segurança]:** após revisão, as três interfaces foram colocadas no novo schema `prumo_s1_interface`, nunca em `prumo_private`. Essa separação evita conceder USAGE em toda a área que contém funções privadas legadas, algumas das quais podem herdar permissões padrão. Teste `S1S-02B` verifica USAGE apenas do schema de interface para authenticated e ausência de USAGE para anon/service_role. O schema de interface continua **não exposto** na Data API; nenhum teste de token real foi executado.


## Resultado CI verificado — identidade simulada, não Auth real

**[GitHub Actions #39301242451 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39301242451)**, commit testado `3ebb0af704ec677aeca00a6a5c363507d0d530cc`, job `118226683757`, logs inspecionados: **S1S-01..14 + S1S-02B = 15/15 PASS**. Provas: sessão ausente/sem usuário negada; gestor de outra equipe e metadados forjados negados; autoria extraída de `auth.uid()` em movimento e pausa/retorno; grants de A/B preservados; `anon`/`service_role` não executam; `authenticated` não obtém EXECUTE dos comandos internos; schema `prumo_s1_interface` recebe USAGE sem conceder USAGE a `prumo_private`; nenhum RPC de gestão foi criado em `public`. Regresso PG17: S1AG 5/5, S1MR 4/4, S1M 12/12 duas vezes, S1T 14/14, S1A 9/9, S1H 8/8, S1R 9/9 em três passagens, AUD1 7/7 e AUD2 5/5, além dos testes I1–I7 do runner.

O primeiro ensaio [#39300916154 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39300916154) havia passado 14/14 mas concedia USAGE amplo em `prumo_private`; **foi corrigido antes do aceite** com a criação do schema dedicado, conforme #39301242451. O teste é **fake-auth** em PostgreSQL local descartável: os GUC `request.jwt.claim.*` são controláveis pelo fixture e NÃO há assinatura de JWT, GoTrue, PostgREST, teste HTTP ou revogação de sessão. As fachadas ainda NÃO podem ser expostas na Data API. Sem merge, deploy, dados reais, chamadas de terceiros ou alteração no percentual global.
