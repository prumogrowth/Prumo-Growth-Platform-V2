# WA-40 — Handoff Meta → S0 com HMAC, nonce e registro atômico (laboratório PG17)

**23/10/2026 · Candidata aditiva no [PR S0/Meta #17](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/17), baseado no [PR S0 #1 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/1). Não é migração aprovada para Supabase hospedado nem autenticação produtiva.**

## Por que esta etapa existe

WA-39 fez uma ponte física dos status Meta para o **binding real da S0**, aproveitando migrations S0/029, S0/040, S0/041, S0/042, sem duplicar cadastros. Seu arquivo de evidências aceitava argumentos técnicos de um processo SQL fictício `postgres`, **sem validação criptográfica do chamador**.

WA-40 complementa esse laboratório com uma **assinatura interna distinta do App Secret da Meta**, verificação HMAC-SHA256 executada no PostgreSQL, janela temporal curta (30 segundos anteriores, 5 segundos de tolerância no futuro), nonce globalmente único e registro de status WA-39 **na mesma transação**. Não cria rota web, worker HTTP, Graph sender, login permanente nem utiliza os tokens da primeira concessionária.

## Arquivos e responsabilidades

- `supabase/migrations/202610230044_s0_meta_handoff_assinado_fixture.sql`: cria papel `prumo_s0_meta_ingress_lab` **NOLOGIN/NOINHERIT/NOBYPASSRLS**, sem filiação fora dos administradores locais, mais duas tabelas privadas `meta_servico_chaves_fixture_s0` e `meta_servico_nonces_fixture_s0`. RLS habilitada e todas as permissões das tabelas revogadas aos papéis externos, inclusive ao ingressor fictício. **Nenhum segredo é preenchido pela migration.**
- A função `meta_material_handoff_fixture_s0` fixa finalidade `FORENSIC_APPEND_ONLY`, versão e codificação canônica dos campos: ID de chave, App/WABA/Phone técnicos, canal, intenção, tentativa, correlação, destinatário, wamid, evento, status, SHA-256 do corpo, emissão e nonce. Todos os campos textuais aceitos são validados para não conter separadores ambíguos. **Não é o mesmo formato do pacote TypeScript WA34**, que permanece proposta e deverá ser versionado em coordenação com Meta.
- A única entrada `meta_arquivar_handoff_assinado_fixture_s0` exige **papel de laboratório + HMAC interna válida**, chave fictícia ativa e limitada ao App, tempo correto e nonce não consumido; invoca `archivar_status_meta_tecnico_fixture_s0` da WA39 após o consumo do nonce. Erro de escopo ou qualquer exceção desfaz **tanto nonce quanto eventual observação**. Devolve exclusivamente estados `LAB_*` e flags falsas para ACK, Graph, reenvio, entrega confirmada e movimentação comercial.
- `supabase/tests/s0_wa_044_meta_handoff_setup.sql`: duas concessionárias e um `wamid` fictício repetido entre elas, duas chaves de bytes artificiais e bindings S0 preexistentes; carrega apenas no banco descartável do CI.
- `supabase/tests/s0_wa_044_assert_meta_handoff_pg17.py`: cenários de MAC válida/adulterada, relógio, replay, nonce, escopo por loja e canal, destinatário, chave de outro App, cancelamento, variantes de corpo, duas sessões concorrentes, rollback, revogação, ACL de `anon`/`authenticated`/`service_role`/papéis internos e ausência de autorização de envio.
- `scripts/run-s0-local.sh` e `.github/workflows/wa39-s0-meta-offline.yml`: adicionam a migration e os testes ao **ciclo completo de regressões S0** no PostgreSQL 17 local, sem usar Supabase real. A prova anterior WA39 18/18 deve continuar verde.

## Limites explícitos e lacunas operacionais

**Esta não é a identidade real do serviço Meta.** O papel NOLOGIN é selecionado pelo administrador do PostgreSQL de teste com `SET ROLE`; não existe um cliente que se autentique realmente como essa máquina. A função de laboratório usa `SECURITY DEFINER` proprietário `postgres` porque os procedimentos S0-041/043 exigem `current_user='postgres'`. Isso **não é menor privilégio de ponta a ponta**. O chamador real precisará ter credenciais de serviço gerenciadas pela frente de infraestrutura e uma função receptora com proprietário reduzido, sem superusuário ou `service_role` genérico. Não instalar um login artificial ou estender grants no Supabase hospedado.

A assinatura interna **não prova** que o ingressor verificou o HMAC do webhook da Meta sobre os bytes originais, pois um processo que possua a chave interna de laboratório pode assinar um pacote fabricado. O campo `body_sha256` é apenas alegado pelo fixture. A integração real precisa de credenciais distintas/isoladas, testemunho auditável da origem Meta e verificação da identidade do processo. O nonce não substitui a autorização comercial, nem a regra real de idempotência e de lotes de callbacks.

A migração 044 é **aditiva**, não altera nomes ou contratos existentes de S0/S1, não modifica permissões humanas, não implementa endpoint público, não autoriza envio, template, IA, campanha ou resposta HTTP ACK. O número comercial da concessionária 01 não é incluído. O próximo passo produtivo dependerá de ratificação das equipes Meta, S0/infra e de implantação específica pela frente Supabase.

## Aceite do laboratório

Critério automático: regressão histórica da S0 sem quebras, 18 verificações WA39 intactas, 25 verificações WA40, todas em PostgreSQL 17 descartável, com confirmação dos resultados no HEAD do PR. **A validação de produção permanece bloqueada mesmo quando o laboratório for aprovado.**
