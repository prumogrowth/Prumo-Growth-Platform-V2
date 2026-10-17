# Prumo — C04 elegibilidade/opt-out sintéticos (17/10/2026)

## Requisitos aplicados
Fontes: `26_Contratos_Conceituais_Eventos_APIs` C04 (CNT-01–03), C05/C06/C08; `37_Playbooks_Excecoes` PB-10/PB-11 e DEC-17/18; `38_Plano_Entregas` S2-A9/CAP-REAL-03; `39_Protocolo_Validacao` RET-06.

**Regra fundamental:** número de cliente pode aparecer nas lojas A/B/C com históricos isolados. Número emissor de atendimento Prumo não pode ser compartilhado. **Alcance do opt-out entre concessionárias continua DEC-17 [R/V]**, portanto NÃO se inventou política global nem cadastro de clientes global.

## Implementação somente para testes sintéticos

- Migration `016_c04_elegibilidade_optout_sintetico.sql` cria `evidencias_elegibilidade_sinteticas` e `supressoes_contato_sinteticas`. Ambas exigem escopo loja+lead+emissor+finalidade; os dados operacionais não vazam entre concessionárias.
- Verificação `prumo_private.verificar_contato_sintetico` distingue `INDETERMINADO` (sem prova), `INELEGIVEL` (opt-out) e `ELEGIVEL_SOMENTE_SIMULACAO` (prova criada com identificador fictício). Toda resposta contém `real=DEPENDENCY_UNVERIFIED`. **Jamais equivale a autorização Meta/LGPD**.
- C05 só agenda plano com evidência fictícia explicitamente inserida na loja/canal/finalidade de teste e sem supressão correspondente; a mera importação não é prova.
- C06, mesmo que o plano exista, revalida evidência, opt-out, estado técnico, estado comercial e template antes de reserva. Não transmite mensagem externa.
- `registrar_optout_sintetico` grava evento idempotente, cancela planos e tentativas ainda programadas/reservadas **somente** naquele lead, loja, emissor e finalidade e preserva histórico. Repetição da chave não duplica efeitos.
- Uma entrada espontânea C02 não modifica as tabelas de elegibilidade/supressão, tampouco gera opt-in implícito. **Após opt-out no mesmo emissor/finalidade, C02 envia à rota humana pendente**, sem promover status comercial para IA (migração 018). A ocorrência continua sintética; a resolução humana real está pendente.
- Repetição idempotente de um plano já cancelado devolve `estado_plano=cancelado` e `executavel_simulacao=false` (migração 017), sem criar nova tentativa.
- Gestor com vínculo ativo pode consultar metadados do próprio escopo; usuários anônimos/operadores sem poder correspondente e outras lojas não podem ler nem gravar por REST. Mudanças somente por processo interno `postgres` em sandbox.
- Nenhuma interface externa, automação de mensagens nem IA decide consentimento nesta etapa.

## Evidência sintética e status
- `supabase/tests/s0_c04_elegibilidade_optout.sql`: C04-01 a C04-06 (ausência de prova, segregação A/B, opt-out, idempotência, inbound e RLS). PostgreSQL 17 CI; evidência no `tests/S0_ACEITE.md`.
- `scripts/test_s0_auth_rest_local.py`: AUTH-10 cobre as duas tabelas novas via GoTrue+PostgREST local com JWT emitido em ambiente descartável; consultar resultado do pipeline no checklist de aceite.

## Pendências e proibições
1. **Política jurídica e Meta [R/V]:** controlador/operador, base legal, opt-in com prova, opt-out entre emissores/lojas, retenção, tipo de produto financeiro, categorias/janela/limites de templates. Nenhuma autorização real presumida.
2. Confirmação real do pedido, autenticação de evento externo, contestação de titularidade, gerenciamento de revogação de evidências e fila de decisão humana ainda não implementados.
3. Uma marca de `verificada_simulada` é apenas entrada de **teste**. Não inserir prova real nem ativar envio por esta estrutura sem arquitetura/autorizações novas.
4. C07 callbacks Meta, envio incerto, C09 fim de silêncio e regra de duas falhas qualificadas não implementados. Não contar 24h do agendamento/reserva.
5. Não compartilhar conversas/status entre lojas nem criar exclusividade global do telefone do cliente.
6. Sem merge, sem migração comercial no Supabase hospedado, sem segredo Meta/OpenAI/n8n e sem usuários/telefones reais.

**Gate:** GO para próxima engenharia de simulador de falhas/resultado técnico; NO-GO para integração ou mensagem comercial real.
