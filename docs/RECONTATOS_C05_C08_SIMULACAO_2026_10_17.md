# Prumo — C05/C08 Recontatos sintéticos e cancelamento (17/10/2026)

## Regras aplicadas e fontes
Em conformidade conceitual com os documentos vigentes **09** (catálogo, envios e eventos), **13A** (oito estados comerciais), **26** (C02, C05, C06, C08), **38** (S2-A3/A5/A6), **39** (IDM-05, REC-05 e opt-out condicionado). Este incremento é engenharia **simulada**, não homologação do WhatsApp.

- **C05 (simulado):** cria `planos_recontato_sinteticos` e uma linha de `envios_template_sinteticos` para cada tentativa futura, com template/versionamento existente em `catalogo_templates_sinteticos`. Apenas templates com `aprovado_simulacao=true`, no escopo da loja, podem ser usados. Essa aprovação **não é aprovação da Meta**.
- O mesmo telefone de cliente pode estar em A e B; cada loja possui plano próprio e RLS por loja. Um canal emissor pertence a **uma concessionária**.
- **C06 (apenas ensaio):** `reservar_envio_sintetico` muda uma tentativa programada para `reservado`, mediante elegibilidade técnica no instante simulado. **Não chama a Meta, não envia, não confirma envio/entrega**.
- **C08/C02 (simulados):** cada nova mensagem recebida pelo C02, inclusive com vários ciclos possíveis, cancela no mesmo commit planos ativos do **lead daquela loja**, gravando eventos para cada tentativa `programado` ou `reservado`. Cancelar não apaga registros nem modifica os oito estados comerciais.
- C08 gestor: `cancelar_plano_gestor_sintetico` cancela **apenas o plano selecionado**, exige ator gestor vinculado, escopo e `expected_version`, é idempotente para repetição da operação válida e preserva versão/eventos.
- Atores autenticados leem só metadados de planos/tentativas/eventos da sua loja quando têm papel gestor. Não recebem poderes de UPDATE. Funções de mutação em `prumo_private`, não expostas aos papéis API.
- Bloqueio por linha e ordem **lead → plano → tentativa** evita que duas transações de banco reservem e cancelem simultaneamente o mesmo envio simulado, independentemente da ordem de início, conforme `scripts/test_s0_recontato_race.sh`.

## Critérios validados pela suíte PostgreSQL (dados fictícios)
- Plano A e B independentes, criado uma vez por chave de idempotência e payload.
- Template inexistente/não aprovado ou plano não elegível não prossegue.
- Reserva simulada não é estado enviado/entregue.
- Resposta do cliente cancela tentativa reservada ou ainda programada, preservando evento e sem afetar a loja B.
- Tentativa cancelada não volta a ser reservada.
- Cancelamento repetido não duplica efeito; versão antiga e gestor de outra loja são negados.
- Corridas em duas conexões: reserva→inbound e inbound→reserva não permitem nova reserva obsoleta.

**Evidência de execução:** consultar `tests/S0_ACEITE.md` após conclusão da regressão da branch.

## Itens propositalmente não implementados
1. **Nenhuma transmissão** ou integração real da Meta, nenhum aceite/sent/delivered/read, nenhuma chamada de IA Planejadora e nenhum n8n.
2. Agenda (1 a 5 itens sintéticos) é **limite técnico de ensaio**, não política comercial aprovada. Os números/cadências finais (primeira abordagem, duas adicionais, 2–5 após conversa) e horários dependem da homologação externa e da regra oficial.
3. Ainda **não existe** opt-in, opt-out real por emissor/finalidade, timezone de cliente, janela da Meta, limite de volume, consentimento legítimo, callback tardio, resultado incerto, retentativa de transmissão, duas falhas consecutivas qualificadas, reconciliação ou recuperação de outbox real.
4. Não criar período de 24 horas ou marcar `perdido` sem comprovante real do **template final efetivamente enviado**. Cancelamento de plano jamais muda status comercial.
5. O argumento `p_ator` deve ser derivado de identidade autenticada pelo backend privilegiado; não aceitar do navegador. Nenhuma permissão de execução das funções privadas foi concedida a usuários comuns.
6. Não realizar merge nem implantar migrations comerciais no Supabase hospedado sem revisão humana, teste integrado e gate LGPD/Meta.

**Estado:** válido apenas para continuar programação e testes em sandbox sintético.
