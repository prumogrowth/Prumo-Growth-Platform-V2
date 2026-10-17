# Prumo — C02 recebimento de inbound SIMULADO (incremento S0)

Fonte: documentos vigentes 13A, 21–23 e 41; escopo técnico proposto nos documentos 25, 26 (C02), 38 e 40. Somente dados totalmente fictícios.

## O que foi implementado
1. Função interna `prumo_private.receber_mensagem_sintetica(canal, telefone_cliente, id_externo, texto)`, sem autorização para `anon`, `authenticated` ou `service_role`. Apenas `postgres` em execução confiável pode chamar. Não é endpoint Meta e não deve aceitar requisições públicas diretamente.
2. A concessionária é resolvida pelo `canal_id` de atendimento, que é exclusivo de uma loja. Cliente identificado por `(concessionaria_id,telefone_cliente_normalizado)`; portanto, a mesma pessoa pode conversar com A, B e C, mantendo leads/ciclos separados.
3. Validação de dados sintéticos, bloqueio por identificador externo, uma mensagem recebida por `(loja,canal,id_externo)`; reentrega idêntica retorna `ALREADY_APPLIED`. Mesmo identificador com payload diferente gera erro de conflito.
4. Conversa escopada por loja, canal, lead e ocorrência humana. Retornos `cadastro enviado ao banco` e `vendido` criam casos humanos sintéticos separados sem reverter o status comercial ou produzir venda fictícia.
5. Primeira entrada elegível no ciclo `aguardando primeiro disparo` ou `primeiro disparo enviado` registra evento e muda para `em atendimento pela IA`, mas **não executa a IA nem envia mensagem**.
6. Com caso humano prévio, o recebimento permanece com humano. Não há retomada automática da IA. Para múltiplos ciclos do mesmo lead, a mensagem é persistida com rota `HUMANO_PENDENTE` e pendência em `pendencias_inbound_simulado`, SEM associação arbitrária a ciclo/caso nem envio IA; a triagem humana real ainda será implementada.
7. Testes `supabase/tests/s0_c02_inbound.sql` e concorrência PostgreSQL 17; regressões da exclusividade de canal emissor, inclusive entradas vazias/formatos não canônicos simples.
8. Migrações 010/011 reforçam a validade básica do identificador emissor e persistem entrada ambígua para revisão. Não resolvem equivalência internacional de números Meta/telefones sem adaptador homologado.

## Limites importantes
- `IA_PENDENTE` e `HUMANO_PENDENTE` indicam **roteamento interno pendente**, não atendimento executado.
- Após migrations 012/013, **C02 cancela no banco** planos e tentativas sintéticos `programado` ou `reservado` do lead da MESMA loja no mesmo commit do inbound; o resultado é `recontatos` com contagem. Essa persistência não comprova cancelamento de envio externo, pois não existe emissor real.
- Nenhum webhook recebido é considerado autenticação Meta. A camada HTTP deverá validar assinatura, origem, replay, esquema oficial, consentimento/opt-out, horários e trilha de integração antes de habilitar ingestão externa.
- A abertura automática de caso em pós-remessa/pós-venda é mock de S0/S1; fila real, atribuição e eventos de caso ainda requerem implementação. Pendência de múltiplos ciclos não se converte em caso atribuído até decisão humana; requer fila operacional de triagem na próxima fatia.
- A transição de status e o conteúdo são estritamente sintéticos. Não há mensagens de cliente real, mídia, documento de identidade ou serviço conectado.
- Dados e políticas de RLS seguem o escopo de cada loja e caso. A função SQL privilegiada **não é delegável ao navegador**.
- Os ensaios SQL de concorrência e a integração local de GoTrue/PostgREST estão documentados no repositório. A lógica de recontatos é sintética e não compreende opt-out/Meta real, disparo, callback, retenção, recuperação, LGPD nem aceite operacional.

**Implantação:** candidato exclusivo no PR #1, sem merge. Não aplicar migrações comerciais no Supabase remoto antes de homologação com dados fictícios.
