# Auditoria do gateway de segurança — Prumo S0 (17/10/2026)

**Escopo:** branch `feat/s0-fundacao-prumo`, migrações 023–024, pacote `backend/identity_boundary.py`, testes de acesso PostgreSQL/GoTrue e estado remoto Supabase. **Não** equivale a pentest, homologação Meta, auditoria LGPD completa ou autorização para produção.

**Parecer:** **GO somente para continuar o desenvolvimento sintético sob controles atuais; NO-GO para exposição de API, credenciais operacionais, merge ou implantação remota.**

## 1. Referências normativas auditadas

- `26_Contratos_Conceituais_Eventos_APIs_v0_1.md`: ator individual autenticado, idempotência, histórico comercial distinto por concessionária, auditabilidade e CT-28/29. Escrita MCP requer confirmação dupla do mesmo ator e só operações aprovadas.
- `39_Protocolo_Validacao_Confiabilidade_RLS_Retencao_Recuperacao_v0_1.md`: isolamento A/B, revogação, concorrência e restauração em ambiente exclusivamente sintético.
- `40_Contratos_Interfaces_Campos_Operacionais_Rastreabilidade_v0_1.md`: backend revalida permissão/versão e minimiza identificadores e segredos expostos.
- `41_Decisao_Aprovada_Matriz_Permissoes_Gestor_Operador_MCP_v1_0.md`: D41-03 restringe MCP inicial a importação e atribuição/remanejamento com dupla confirmação. D41-05/06 exigem concessão de poderes e manutenção privilegiada por humanos autorizados. O gateway de C07/C08 é **backend interno simulado, não MCP**, e não amplia poderes dessas decisões.

## 2. Achados e reparos

| ID | Gravidade para uso real | Descrição | Situação |
|---|---|---|---|
| AUD-GW-01 | Média | Auditoria persistia UUID bruto de `auth.sessions.id`, também utilizado nas validações de sessão do gateway. Retenção desnecessária de identificador relevante para autorização. | **Corrigido** na migration `024_s0_auditoria_sessao_fingerprint.sql`: migra dados de auditoria para impressão SHA-256, remove a coluna original e reemite wrappers com `search_path=''`. Teste `GW-07` PASS. A impressão ainda é dado pseudonimizado sujeito à política LGPD. |
| AUD-GW-02 | Baixa | JWT Base64 malformado após resposta de verificação de GoTrue poderia produzir exceção `binascii.Error` sem mapeamento para acesso negado. | **Corrigido** no Python e no teste unitário `test_03b` (negação controlada). |
| AUD-GW-03 | Média | Os testes não afirmavam explicitamente dono/SECURITY DEFINER/grants das duas wrappers nem proibição de escrita na tabela de auditoria. | **Cobertura ampliada** por `GW-06`: owner postgres, privilégio de EXECUTE apenas no papel restrito, anon/auth/service_role negados e nenhuma leitura/escrita de log ao gateway. PASS. |
| AUD-GW-04 | **Alta — BLOQUEIO produção** | As wrappers `SECURITY DEFINER` usam `p_ator` e `p_sessao` como argumentos, verificando que formam um par de sessão ativo. Um agente que tenha credencial SQL do gateway e conheça um par válido pode invocá-las diretamente **sem apresentar token GoTrue** à camada Python. O gateway não valida criptograficamente o JWT no PostgreSQL. | **Não resolvido nesta etapa**: exige nova fronteira de confiança, segregação/rotação de credenciais e threat model antes de expor login/serviço em produção. O teste integrado atual prova segurança da rota Python, não resistência a login SQL comprometido. |
| AUD-GW-05 | Alta — BLOQUEIO produção | `SECURITY DEFINER` é de propriedade do papel privilegiado `postgres`, requerido pelas funções de domínio atuais (`current_user='postgres'`). Comprometimento ou bug de wrapper pode executar mutações com amplos privilégios. | **Risco aceito apenas no S0 isolado.** Revisar/reestruturar wrappers e papel proprietário mínimo antes de qualquer hospedagem operacional; não presumir que NOLOGIN elimine essa elevação dentro da função. |
| AUD-GW-06 | Média | A tabela de auditoria registra APPLIED/ALREADY_APPLIED, não negativas/erros: rejeições fazem rollback e não deixam trilha persistente nela. | **Pendente**: observabilidade central, logs de negação minimizados, segregação e retenção, sem reintroduzir dados pessoais/tokens. |
| AUD-GW-07 | Média | API HTTP, TLS, gestão de segredos, rate limit, recuperação, rotação de credenciais e alertas ainda não existem. | **Pendente** para homologação de serviço. Não disponibilizar endpoint ou login comercial. |

## 3. Evidências de testes

- [**PostgreSQL 17 #39082947695 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39082947695): migração `024`, testes de papéis `GW-01..GW-07`, **16 testes unitários Python** e regressões S0 anteriores. `GW-07` verificou que a tabela auditada já não tem a coluna UUID bruto, que o fingerprint é consistente e que a sessão em claro não aparece no registro.
- [**Supabase local Auth/REST #39082125663 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39082125663): `AUTH-01..13` incluindo escopo A/B, sessão revogada e login de gateway limitado no **baseline da migração 023**. A suíte integrada Auth/REST **não foi repetida após a migração 024**, para respeitar o orçamento de minutos. Antes de qualquer homologação do esquema 024 via GoTrue/PostgREST, é necessária nova execução específica com gatilho opt-in.
- Testes não provam ausência de todas as falhas, resistência a roubo de credencial ou adequação jurídica/Meta. `Security Advisor` do Supabase hospedado não avalia automaticamente as migrações ainda **não implantadas** no GitHub.

## 4. Invariantes preservados

- Mesmo telefone de cliente pode existir em lojas A/B/C com leads e histórico segregados. Cada número emissor Prumo permanece exclusivo de uma concessionária.
- Gateway não envia mensagem, não executa MCP, não altera parâmetros IA, não marca venda/perda por inferência, não concede gestor global e não permite acesso D3/D4.
- Segurança sintética: conexão SQL de testes apenas em localhost, papel técnico NOLOGIN/NOINHERIT, duas wrappers e ausência de SELECT direto de dados e da tabela de auditoria.
- Migrações candidatas **001–006 e 008–024** somente na branch privada, sem merge. Nenhuma migração ou tabela comercial no Supabase hospedado.

## 5. Gate

**GO:** manter testes SQL, modelagem de credenciais, observabilidade de recusas e desenho do serviço de menor alçada em sandbox.

**NO-GO:** implantação remota, dados reais, Meta/Banco/OpenAI/n8n, credencial gateway de produção, API pública ou merge até resolução expressa das fragilidades AUD-GW-04/05 e demais requisitos de autorização/recuperação.

A auditoria registra o limite da confiança: **um papel com poucas permissões não equivale a autenticação do ator dentro do banco**. O controle do token ainda depende do backend confiável e da proteção de sua credencial SQL.

## Atualização de tratamento de risco — 18/10/2026

O bloqueio **AUD-GW-04** registrado acima foi **parcialmente mitigado** pela migration `025_s0_prova_dupla_gateway.sql`: o papel SQL restrito perdeu EXECUTE nas wrappers sem assinatura. Agora exige assinatura HMAC-SHA256 de uma segunda chave, curta duração (30s + tolerância de relógio) e nonce de uso único, vinculando ator/sessão, loja, versão e comando. Essa barreira foi testada em [PostgreSQL #39083792469 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39083792469) e em [GoTrue/REST local #39083914275 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39083914275).

**O risco não está encerrado para produção:** o runtime possui a senha SQL e a chave HMAC. Comprometimento de ambos, exfiltração do material da chave ou ataque ao proprietário privilegiado `postgres` podem contornar essa defesa. Também faltam armazenamento e rotação de chaves, observabilidade segura de negativas e recuperação. Assim, AUD-GW-04 permanece **bloqueio para produção**, mas a variante específica de **senha SQL isolada com par ator/sessão conhecido** passa a estar mitigada nos cenários S0 testados. A migration 025 não foi aplicada no projeto Supabase hospedado.

Guia: `docs/GATEWAY_PROVA_DUPLA_S0_2026_10_18.md`.

## Atualização adicional — ciclo de vida de chaves e negativas (17/10/2026)

A migration **026** e o módulo `backend/security_events.py` ampliaram os controles de S0: nova chave precisa ser registrada inativa, ativada por versão/justificativa, pode coexistir temporariamente com a anterior e, uma vez revogada, nunca é reativada. Identificadores anti-replay são limpos somente após dez minutos, com registro da quantidade excluída. O backend permite categorizar negativas sem JWT, IDs ou texto do cliente, mas o logger ainda depende de coletor externo protegido.

Evidências: [PostgreSQL #39084739387 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39084739387) (KEY-01..05 e 24 testes unitários) e [Auth/REST local #39084803545 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39084803545) (AUTH-01..14). Esses testes **não encerram** os riscos de SEGREDO SQL + HMAC simultaneamente comprometidos, `SECURITY DEFINER` dono `postgres`, ausência de cofre de segredos, coleta durável de negativas, recuperação/restore e retenção LGPD. **NO-GO para produção/merge/deploy remoto permanece.**
