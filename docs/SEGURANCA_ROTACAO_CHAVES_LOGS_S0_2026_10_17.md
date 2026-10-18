# Prumo — Ciclo de chaves HMAC, retenção de nonce e negativas sanitizadas (17/10/2026)

**Estado:** desenvolvimento S0 **exclusivamente fictício**, versionado em branch privada e ensaiado em PostgreSQL descartável. Não há implantação no Supabase hospedado, chave de produção, servidor HTTP ou integração Meta/Banco/OpenAI.

## Alinhamento com a documentação normativa

Contratos 26 e 40 exigem ator e origem confiáveis, comandos idempotentes, trilha auditável, falhas tratadas sem reenvio cego e validação de escopo. Documento 39 exige revogação efetiva, retenção e recuperação demonstráveis. A matriz D41-01–06 mantém gestor limitado à loja, operador ao caso atribuído, e o MCP inicial **restrito às operações aprovadas com confirmação dupla**. Este desenvolvimento é um gateway interno de C07/C08 sintético, **não MCP**.

A análise `docs/AUDITORIA_GATEWAY_S0_2026_10_17.md` e a migração 025 motivaram duas melhorias: ciclo de vida previsível para a segunda chave HMAC e observabilidade de recusas sem registrar credenciais, mensagens ou identificadores de clientes.

## Migração 026 — administração restrita da chave

`supabase/migrations/202610180026_s0_ciclo_chaves_e_retencao_nonce.sql`:

- Novas chaves são registradas **desativadas**, com material mínimo de 32 bytes e janelas de validade definidas. O ID de chave é estável e o material não pode ser alterado para simular uma rotação silenciosa: deve-se **registrar um novo ID com novo segredo**, apenas em procedimento administrativo isolado e autorizado.
- Função interna `prumo_private.alterar_estado_chave_gateway_s0(chave,expected_version,ativar,motivo)` executável **somente por `postgres`**, não pelo login técnico. Exige versão atual, justificativa de 10–300 caracteres e, para ativação, janela temporal válida. A mudança incrementa versão e fica numa tabela de eventos sem segredo.
- Para uma rotação simulada sem indisponibilidade: cadastrar nova chave inativa; ativá-la; passar o assinador confiável a usar novo ID/segredo; conferir as respostas; **revogar** a chave anterior. Uma chave revogada não pode voltar a ser ativada, e novas provas assinadas com ela são recusadas imediatamente.
- `gateway_eventos_chave_s0` guarda somente chave_id, evento `REGISTRADA/ATIVADA/REVOGADA`, versões e timestamp. Não grava o conteúdo secreto. O proprietário privilegiado ainda pode administrar as tabelas; não é trilha imutável contra um superusuário.
- `prumo_private.expurgar_nonces_gateway_s0(corte)` só permite apagar identificadores consumidos **há mais de 10 minutos**, preservando margem sobre validade máxima de assinatura (30s mais tolerância de relógio). Cada limpeza registra corte e quantidade. Não está agendada automaticamente; o operador de banco precisará executar ou automatizar sob política aprovada.
- Alterações em `gateway_chaves_assinatura_s0` preservam segredo, ID e janela originais na versão atual; uma revogação é terminal no modelo S0.

**Atenção:** a chave HMAC permanece armazenada em `bytea` numa tabela privada da mesma instância PostgreSQL. Isso **não é um cofre de segredos**, e um superusuário comprometido pode acessá-la. Não executar procedimentos de inserção de segredo no SQL Editor hospedado ou por pipelines que registrem parâmetros sem desenho de proteção. A migração 026 **não contém nem gera segredos reais**.

## Eventos sanitizados de negativas

`backend/security_events.py` define `SanitizedDenialLogger`, que registra somente categoria controlada (`INPUT_REJECTED`, `AUTH_DENIED`, `IDENTITY_UNAVAILABLE`) e comando permitido (`cancelar_plano`, `conciliar_c07` ou `desconhecido`). `AuthenticatedCommands` pode receber o logger por injeção: erros dessas três classes são registrados antes de serem propagados. Falha do logger **não converte uma negativa em autorização**.

**Nunca registrar** nesse mecanismo: JWT/Bearer, segredo HMAC, senha SQL, UUID do ator/sessão/cliente, telefone, texto de mensagem, justificativa, SQL dinâmico ou mensagem bruta de exceção. Operações desconhecidas são normalizadas para `desconhecido` e não geram injeção de texto do usuário nos logs.

**Limite importante:** é apenas um ponto de integração com o logger Python; **não** é ainda auditoria externa durável, centralizada ou independente do processo. Negativas que nem chegam ao `AuthenticatedCommands` (por exemplo, acesso SQL direto ou erro de infraestrutura anterior) não ficam necessariamente registradas. Falta definir coletor, armazenamento, retenção, controle de acesso, alertas, correlação minimizada e recuperação.

## Ensaios e evidências

- [PostgreSQL 17 #39084739387 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39084739387): migrations candidatas até **026**, `KEY-01..05`, **24 testes unitários Python** e regressões C01/C02/C04/C05/C07/C08. Ativação versionada, coexistência temporária, revogação definitiva, janela temporal, assinatura antiga negada, nonce único, limpeza conservadora e proibição ao gateway foram exercitados.
- A suíte integrada GoTrue/PostgREST deve constar com **resultado real**, separadamente. Sua execução só ocorre sob etiqueta explícita `run-auth-integration`, com teto de 12 minutos. **Nunca inferir PASS por teste apenas escrito.**
- Nenhum teste cria credencial operacional; testes usam senhas e chaves **intencionalmente fictícias**.

## Gates e riscos ainda abertos

1. Segredo SQL e segredo HMAC ainda residem no mesmo processo do protótipo local; comprometimento combinado continua capaz de contornar a barreira HMAC. Exigir isolamento operacional e revisão de threat model.
2. As funções `SECURITY DEFINER` seguem com proprietário privilegiado `postgres`. Precisa reduzir privilégios do proprietário e auditar cada caminho antes de produção.
3. Gestão central de segredos, política de rotação real, implantação segura, recuperação de chave perdida e proteção de memória ainda não implementadas.
4. Negativas precisam de sink externo durável, proteção contra adulteração, controle de acesso, retenção LGPD e alertas.
5. A retenção de nonce é um mecanismo sintético de manutenção, não um sistema automatizado de limpeza em produção. Testes de concorrência/restore dos segredos e do ledger ainda pendentes.
6. Respeitar mesmo telefone de cliente entre concessionárias A/B/C, isolamento por loja e número emissor Prumo exclusivo. Oito estados comerciais e restrição de reenvio pós-incerteza intactos.

**Gate atual:** GO apenas para continuar desenvolvimento e auditoria em S0; **NO-GO para merge, Supabase remoto, usuários reais, webhook/WhatsApp e produção** sem autorização humana específica.
