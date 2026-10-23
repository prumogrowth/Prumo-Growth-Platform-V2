# WA-41 — Isolamento do verificador HMAC Meta na S0 (PG17, somente laboratório)

**23/10/2026 · [PR #17 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/17) · candidato aditivo sobre o PR S0 #1, sem alterar S1, PR Meta #2 ou Supabase hospedado.**

## Motivação e alcance

Na WA-40, a função `meta_arquivar_handoff_assinado_fixture_s0` possuía a chave de laboratório, validava o HMAC, consumia nonce e chamava o gravador S0/043; tudo sob o proprietário `postgres` via `SECURITY DEFINER`. Esse acoplamento é inadequado para um serviço real.

**WA-41 reduz apenas a superfície do componente criptográfico**: a verificação da assinatura HMAC interna e consumo único de nonce foram movidos para `meta_verificar_handoff_fixture_s0`, cujo proprietário é `prumo_s0_meta_signer_lab`: `NOLOGIN`, `NOINHERIT`, `NOBYPASSRLS`, sem privilégios de negócio, sem `CREATE` no schema e sem acesso às tabelas de evidências ou às rotinas humanas. O papel vê somente os campos requeridos da chave fictícia; insere e consulta nonces fictícios sob políticas RLS exclusivas. `anon`, `authenticated`, `service_role`, o ingressor Meta e os gateways humanos **não podem executar diretamente o verificador**.

O wrapper existente WA40 continua sob `postgres` exclusivamente para chamar a função legada S0/043, que ainda depende desse proprietário. Após validar formato e escopo, o wrapper invoca o verificador de menor privilégio e, na mesma transação, arquiva a evidência. Rejeição de MAC, prazo, chave ou nonce, falha de escopo e gravação forense fazem rollback integral. **Isto é uma redução parcial, não uma porta mínima de ponta a ponta.**

## Arquivos e provas

- `supabase/migrations/202610230045_s0_meta_isolar_verificador_fixture.sql`: papel técnico local; grants de colunas estritos; políticas RLS; acesso limitado a `pgcrypto.hmac`; mudança de proprietário somente da função `meta_verificar_handoff_fixture_s0` e atualização aditiva do wrapper WA40. Não insere nenhuma chave.
- `supabase/tests/s0_wa_045_meta_signer_privilegios.sql`: **16 invariantes de papel, propriedade, ACLs e RLS**, incluindo impossibilidade de acessar evidências ou a assinatura de operação humana S0.
- `scripts/run-s0-local.sh` e `.github/workflows/wa39-s0-meta-offline.yml`: a regressão completa original da S0, **WA39 18/18**, **WA40 25/25** (assinatura, expiração, adulteração, replay concorrente, cancelamento e rollback) mais as **16 novas verificações**, em PostgreSQL 17 descartável. Não há execução real da API Meta.

## Riscos e bloqueios ainda pendentes

1. **Identidade de serviço real não existe:** `SET ROLE` sob usuário `postgres` é uma fixture PG17 e não prova autenticação de uma máquina na rede. Nunca criar login `prumo_s0_meta_ingress_lab` para obter uma rota produtiva.
2. **Gravação S0 ainda privilegiada:** wrapper WA40 continua `postgres` porque a S0/043 foi criada como `SECURITY INVOKER` e exige `current_user='postgres'`. Um futuro incremento terá de reduzir esse privilégio também, com revisão da transação, locks e RLS existentes, sem modificar S1.
3. **Revogação concorrente:** ao limitar o verificador à leitura de chaves sem `UPDATE`, a verificação não usa `FOR SHARE`. A política de serialização da rotação/revogação e seu momento em relação ao COMMIT ainda requer contrato específico e prova física. Os testes atuais cobrem chave revogada **antes** do handoff, não provam a corrida de revogação durante a operação.
4. **Envelope não unificado:** o contrato de texto canônico S0/044 usa UUID + campos técnicos e é distinto do envelope de laboratório WA34/35. A versão, canonicalização, propósito, audiência e chave gerida pela Infra devem ser ratificados de forma conjunta; não presumir interoperabilidade.
5. **Origem Meta não certificada:** uma assinatura interna válida não equivale à verificação HMAC do corpo de webhook Meta; também não autoriza ACK, Graph, campanhas, IA, prova de entrega ou transição comercial. A concessionária 01 continua restrita a futuro piloto com números permitidos.

**Conclusão:** ainda não aplicar 043/044/045 no Supabase hospedado; ainda não mesclar os PRs Draft. Próximo trabalho: provar alinhamento exato do formato interno emitido pela frente Meta com a função receptora S0 e reduzir com segurança a propriedade da operação forense.
