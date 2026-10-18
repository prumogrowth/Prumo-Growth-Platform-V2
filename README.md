# Prumo — plataforma comercial (nome provisório)

**Alinhamento organizacional D-ORG-01 (18/10/2026):** gestores e operadores são profissionais **da Prumo**, inclusive quando dedicados exclusivamente a uma concessionária. Loja é escopo de atendimento, não vínculo empregatício. Uma pessoa pode ter múltiplas lojas por concessão explícita; gestor pode autoatribuir caso segundo D41-04. Ver `docs/D_ORG_01_EQUIPE_PRUMO_2026_10_18.md`. 


Operação comercial do produto **LiberaCred**, da instituição financeira. As ideias iniciais foram superadas: implementar somente normas vigentes dos documentos **00A, 13A, 21–23 e 41**, com os projetos técnicos 25/26/30/38/39/42/43.

**S0 em desenvolvimento, dados exclusivamente sintéticos.** Nenhuma integração Meta, Banco, OpenAI ou n8n está conectada e não há liberação para produção.

Arquivos:
- `supabase/migrations/`: fundamento e RLS de leitura segura por concessionária.
- `supabase/tests/`: fixtures sintéticas, importação C01 e testes SQL de isolamento/transições.
- `supabase/migrations/202610170006_s0_transactional_simulation.sql`: serviços internos C01 e evento de inbound simulados; **não expostos à API**.
- `scripts/test_s0_concurrency.sh`: ensaio com duas conexões PostgreSQL concorrentes.
- `supabase/migrations/202610170009_s0_c02_inbound_synthetic.sql`: recebimento fictício de mensagens e roteamento pendente, **sem Meta**.
- `scripts/test_s0_c02_concurrency.sh`: duplicidade de webhook fictício e eventos paralelos.
- `docs/C02_RECEBIMENTO_SIMULADO_S0.md`: ingresso simulado e relação com cancelamento local.
- `docs/RECONTATOS_C05_C08_SIMULACAO_2026_10_17.md`: catálogo, planos, reservas, cancelamento e limites (sem transmissão Meta).
- `scripts/test_s0_recontato_race.sh`: concorrência entre inbound e reserva em duas conexões PostgreSQL.
- `scripts/run-s0-local.sh`: runner restrito a Postgres LOCAL e base descartável.
- `docs/MAPA_MENTAL.md`: mapa mental simples.
- `docs/DECISOES_E_GATES.md`: regras, custos e próximos portões.
- `supabase/config.toml`, `scripts/test_s0_auth_rest_local.py`, `.github/workflows/s0-auth-rest.yml`: testes locais de GoTrue e PostgREST com JWTs reais de sandbox, sem usar Supabase hospedado.
- `docs/AUTH_REST_S0_VALIDACAO_LOCAL.md`: evidências e limitações da integração de autenticação.
- `docs/C04_ELEGIBILIDADE_OPTOUT_SIMULADO_2026_10_17.md`: evidência fictícia, supressão por emissor/finalidade e bloqueios C05/C06.
- `docs/C07_CALLBACKS_SIMULADOS_2026_10_17.md`: eventos técnicos correlacionados, duplicados, tardios e pendências de reconciliação; sem prova externa.
- `docs/C07_RECONCILIACAO_FALHAS_SIMULADAS_2026_10_17.md`: pendências por evento, revisão humana com versão, histórico e bloqueio de retry cego.
- `docs/ESTADO_AMBIENTES_GITHUB_SUPABASE_2026_10_17.md`: diferença entre GitHub, Supabase descartável de testes e projeto hospedado (sem migrações comerciais).
- `backend/identity_boundary.py`, `backend/tests/test_identity_boundary.py`: protótipo **interno/local** que deriva ator do GoTrue autenticado, confirma sessão ativa e só permite dois comandos sintéticos via SQL parametrizado; não expõe API pública nem DSN remoto.
- `docs/BACKEND_IDENTIDADE_AUTENTICADA_S0_2026_10_17.md`: fronteira de confiança, limitações e gates antes de serviço operacional.
- `supabase/migrations/202610170023_s0_gateway_minimo_e_auditoria.sql`, `backend/identity_boundary.py`: papel técnico NOLOGIN, duas funções privadas autenticadas e trilha de auditoria transacional. Nenhuma API pública.
- `docs/GATEWAY_PRIVILEGIOS_MINIMOS_AUDITORIA_S0_2026_10_17.md`: limites do papel restrito, segredo apenas no teste descartável e gate de implantação.
- `docs/AUDITORIA_GATEWAY_S0_2026_10_17.md`: achados de segurança, migração 024, testes GW-06/07 e limites de credenciais/SECURITY DEFINER antes da operação.
- `docs/GATEWAY_PROVA_DUPLA_S0_2026_10_18.md`: migração 025, credencial SQL e HMAC separados, nonce anti-replay, janela temporal curta e limites antes de produção.
- `docs/SEGURANCA_ROTACAO_CHAVES_LOGS_S0_2026_10_17.md`: migração 026, ativação/revogação versionada de chaves, retenção segura dos nonces e negativas sanitizadas no backend.
- `docs/SEGURANCA_OWNER_HMAC_S0_2026_10_17.md`: migração 027, verificador HMAC com proprietário técnico NOLOGIN e ACLs mais restritas; funções comerciais ainda privilegiadas.
- `backend/security_events.py`: categorias de recusa controladas; NÃO constitui ainda coletor externo durável de eventos.
- `docs/AUDITORIA_C07_RECONCILIACAO_2026_10_17.md`: resultados da auditoria, reparo do replay C05 e pendências de Auth/REST.
- `scripts/test_s0_c07_recon_concurrency.sh`: duas revisões concorrentes do mesmo evento, uma única decisão auditada.
- `docs/CONTROLE_CUSTOS_GITHUB_ACTIONS_2026_10_17.md`: workflows enxutos, timeouts, cancelamento de execuções obsoletas e Auth/REST opt-in.
- `tests/S0_ACEITE.md`: status dos ensaios.

**Regra vigente:** um cliente pode atender-se em A, B e C com o mesmo telefone, com leads/históricos isolados por loja; número **emissor de atendimento da Prumo** é exclusivo de uma loja. Veja `docs/REGRA_NUMEROS_ATENDIMENTO_CLIENTE_2026_10_17.md`.

S0: gestores autenticados leem dados somente das lojas vinculadas; operadores leem leads/conversas apenas de casos atualmente atribuídos. A escrita direta em leads, ciclos e remessas continua bloqueada ao cliente. D3/D4 e fluxos bancários ainda não foram construídos.

Teste futuro: crie um banco local descartável `prumo_s0_test_*`, exporte `PRUMO_TEST_DATABASE_URL` e rode `./scripts/run-s0-local.sh`. **Não apontar para Supabase remoto.**

Migrações versionadas 001–006 e 008–027 (007 indevida retirada antes de deploy) não estão implantadas no Supabase. Suíte SQL e teste concorrente executados em CI; veja `tests/S0_ACEITE.md`. Não gravar segredos nem dados pessoais reais no repositório.


## S1 — primeira jornada visual sintética

A demonstração local da **Central de operações** está em `frontend/s1/`. Abra `frontend/s1/README.md` para servir em `http://127.0.0.1:4173` e executar testes Node 22, sem API externa, dados reais, autenticação ou persistência. O protótipo cobre visão de gestor por loja, operador apenas em caso designado, handoff humano com IA suspensa, notas, histórico, oito estados comerciais e remessa bancária estritamente fictícia. Para gates e limites, veja `docs/S1_001_JORNADA_HUMANA_VISUAL_2026_10_18.md` e `docs/MAPA_MENTAL.md`. **Não é uma interface de produção.**
