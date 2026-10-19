# S1-002/I18 — Operações reais de gestão com JWT GoTrue por HTTP (19/10/2026)

**Contrato e perímetro:** somente GitHub Actions com Supabase CLI/Docker efêmero, nunca Supabase hospedado. O I11 continua normativo: o gestor supervisiona **operadores da própria equipe** (não lojas), só responsáveis concedem concessionárias A/B/C. Pausa é global, redistribui atendimentos e preserva grants; retorno não traz carteira antiga.

## Objetivo e implementação

Reunir num mesmo PostgreSQL Supabase real:
1. GoTrue e PostgREST reais, com JWT e `auth.sessions` próprios da stack;
2. **todas as migrations S0/S1 efetivas** que o runner legado utiliza, sem `bootstrap_fake_auth.sql`, sem stubs I16 e sem alterar branches externas;
3. comandos reais I11/I12/I13 através das três fachadas I14/051 reforçadas pelo helper de sessão I15/052;
4. pontes HTTP no schema `public` **apenas para o banco de teste descartável**, nunca migrations nem gateway de produção.

O teste `scripts/test_s1_002_http_e2e.py` exige ambiente CI, marcador `PRUMO_S1_I18_EPHEMERAL=YES`, URLs loopback e banco local `/postgres`. Lê exclusivamente as migrations referenciadas pelos runners S0/S1 e aplica em ordem; falha fechado se não identificar a fundação/quantidade esperada. A fixture `supabase/tests/s1_018_bridge_http_local_only.sql` define três funções-canário `s1_i18_mover`, `s1_i18_pausar`, `s1_i18_reativar` em `public`, com `SECURITY DEFINER`, `search_path=''`, `EXECUTE` apenas `authenticated`, e **sem parâmetro `solicitante`**. Os canários são invocadores das fachadas privadas REAIS, não stubs. Ao encerrar o CI toda a stack e esses endpoints deixam de existir. `prumo_s1_interface` não entra na Data API, e os comandos de produção não são publicados.

## Cenários candidatos S1E2E-01..10

1. Migrations S0/S1 em banco GoTrue real descartável.
2. Cinco contas GoTrue reais sintéticas (gestores G1/G2, operadores O3/O4/O5), dois casos nas lojas A/B, concessões apenas de operadores, duas equipes independentes.
3. G2 não pausa operador de G1.
4. G1 move caso A entre O3 e O4 sem precisar possuir grant da loja.
5. Comando repetido com atribuição antiga falha.
6. G1 pausa O3 globalmente, B redistribuído a O4 e grants A/B intactos.
7. G2 não reativa O3.
8. Logout GoTrue invalida comando de G1 com JWT antigo.
9. Nova sessão real de G1 reativa O3 sem restituir carteira; autoria persistida.
10. Nenhuma fachada privada real em `public`; clientes permanecem sem `USAGE` de `prumo_private` ou `SELECT` em `auth.sessions`.

O teste é estritamente positivo/negativo em stack efêmera, não homologação de frontend, banco, Meta, OpenAI ou gestão de responsáveis. Não cria autorização RH/escala nem decide política automática entre equipes. **CI/evidência pendentes até conclusão e inspeção dos logs.**

**Riscos conhecidos:** pontes do teste são `SECURITY DEFINER` intencionalmente para o canário e seriam inaceitáveis como gateway público em produção; as migrações S0/S1 podem precisar de adaptação isolada para Supabase local real, nunca presumir sucesso sem logs. PR #5 Draft e sem merge/deploy/dados reais/progresso global.
