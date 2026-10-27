# Prumo — Auditoria de C04 antes de C07

**Data:** 17/10/2026. **Veredito:** GO para desenvolvimento **isolado e sintético** de C07; **NO-GO** para operação real, merge ou deploy comercial.

## Fontes normativas confrontadas
- `26_Contratos_Conceituais_Eventos_APIs_v0_1.md`: C02/C04/C05/C06/C08, CT-13 e proibição de inferir consentimento pela importação.
- `37_Playbooks_Excecoes_Banco_WhatsApp_Estados_v0_1.md`: PB-10, PB-11, DEC-17/18, resposta espontânea após opt-out, concorrência com executor.
- `38_Plano_Entregas_Incrementais_MVP_Criterios_Ativacao_v0_1.md`: S2-A5/A9; CAP-REAL-03.
- `39_Protocolo_Validacao_Confiabilidade_RLS_Retencao_Recuperacao_v0_1.md`: RET-06, REC e validações jurídico/privacidade.
- Regra posteriormente confirmada do produto: **mesmo telefone do cliente pode existir em A/B/C**, cada loja com lead e histórico próprios; **número emissor Prumo exclusivo por loja**.

## Achados e reparos realizados nesta rodada

| ID | Achado | Correção | Evidência |
|---|---|---|---|
| AUD-C04-01 | Faltava corrida explícita entre opt-out e reserva, em ambas as ordens | `scripts/test_s0_c04_optout_race.sh` com duas conexões e locks transacionais | `PASS C04-RACE` |
| AUD-C04-02 | Replay de planejamento cancelado só dizia `ALREADY_APPLIED`, sem comunicar estado inativo | Migration `017_c04_estado_replay_plano.sql`; retorno inclui `estado_plano`, `executavel_simulacao=false` e nenhuma transmissão | `PASS C04-REPLAY` |
| AUD-C04-03 | Após opt-out, o inbound espontâneo podia receber `IA_PENDENTE` e promover estado IA, apesar da restrição PB-11 | Migration `018_c04_inbound_pos_optout_humano.sql` cria ocorrência sintética de revisão humana quando não havia caso, preservando opt-out e status comercial; não liga IA | `PASS C04-04` ampliado |
| AUD-C04-04 | Faltava regressão explícita da semântica pós-opt-out no C02 | `s0_c04_elegibilidade_optout.sql` confirma rota humana, ausência de transição IA e de revogação do opt-out | `PASS C04-04` |

**Evidência do conjunto alterado:** [GitHub Actions PostgreSQL 17 #39073858011 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39073858011). A execução inclui C04-01..06, C04-REPLAY e C04-RACE, com C01/C02/C05/C08 e concorrência anteriores. Os testes não enviam WhatsApp.

**Autenticação/REST:** [#39073125189 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39073125189) no baseline imediatamente anterior aos reparos; a regressão Auth/REST da revisão atual deve ser tratada separadamente. A migração C04 preserva grants/RLS existentes e nega acesso direto às funções internas. Os testes integrados seguem limitados a usuários sintéticos e stack efêmera.

## Invariantes verificados
1. Importação não é comprovação de consentimento. Evidência fictícia não autoriza envio real.
2. Opt-out é persistido por concessionária, lead, emissor e finalidade; não apaga histórico; replay não recria agendamento nem converte resposta espontânea em opt-in.
3. Reserva de recontato e opt-out concorrem usando lock sobre o lead; ao final, nenhuma tentativa sintética do escopo permanece elegível.
4. Mesmo cliente em A/B não compartilha conversas, opt-out ou prova.
5. Nenhum dos oito estados comerciais é alterado apenas por opt-out; o novo caso humano sintético depende de atendimento efetivo posterior ainda não implementado.
6. Funções privadas continuam restritas aos testes internos; não existe sender externo.

## Riscos e decisões em aberto — NO-GO para uso real
- **DEC-17 [R/V]:** alcance de opt-out entre canais/concessionárias, controle de finalidade e parecer jurídico/Meta. Não presumir opt-out global nem permissão de B só porque A tem histórico.
- **DEC-18 [R/V]:** política final do atendimento espontâneo pós-opt-out, além do encaminhamento humano conservador no simulador.
- **Identidade confiável:** entrada do opt-out ainda não tem adaptador assinado/autenticado da Meta nem serviço que vincule o evento recebido ao canal/contato sem parâmetros arbitrários.
- **Provas jurídicas/operacionais:** a tabela de elegibilidade é fictícia e não prova base legal, categoria, consentimento, janela/limites Meta ou retenção LGPD.
- **Tratamento humano:** a rota `HUMANO_PENDENTE` é simulada; não há fila funcional de atribuição/resolução para esse tipo de ocorrência, nem justificativa de resultado externo.
- **Mensageria real:** C07 callbacks, falhas confirmadas e resultado incerto, reconciliação/retentativas e relógio do template final + 24h permanecem não implementados.
- **Continuidade:** backup/restauração, D3/D4, avaliação de logs, testes de recuperação, ambiente remoto homologado e revisão humana de segurança seguem pendentes.

**Gate:** seguir para C07 **exclusivamente como simulação técnica**, sem ligar Meta/OpenAI/Banco/n8n, sem dados de clientes reais e sem aplicar migrações comerciais ao Supabase hospedado. Este relatório é uma avaliação do escopo e dos testes realizados, não garantia absoluta de ausência de defeitos.
