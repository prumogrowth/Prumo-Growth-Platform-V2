# CF-OP-02 — Auditoria após atualização dos contratos de cinco frentes

Data 18/10/2026. Base: direção funcional confirmada pelo responsável; PR #7/issue #6; documentos normativos 03, 13A, 21, 22, 26 e 41 do pacote auditado, mais D-ORG-01. **Escopo:** comunicação/contratos do repositório privado, sem teste de código, integração real, execução de templates, cobrança ou Supabase hospedado.

## Evidência de gravação em cada branch proprietária

| Frente | Branch / commit auditado | Contrato proprietário criado | Artefatos da frente também atualizados |
| --- | --- | --- | --- |
| Núcleo S0 | feat/s0-fundacao-prumo / 3bb3316652e96a76c88e62c71b0c956d5bcc6c06 | docs/CF_OP_02_CONTRATO_NUCLEO_RECONTATO_HUMANO_v0_1.md | docs/RECONTATOS_C05_C08_SIMULACAO_2026_10_17.md |
| Equipe Prumo S1-002 | feat/s1-002-equipe-prumo / dd0b600ec0bb7c390f4fd7ec8c52cafd9bbd6dbc | docs/S1_002_I2_CONTRATO_REMANEJAMENTO_AUTOMATICO_CF_OP_02_v0_1.md | docs/S1_002_EQUIPE_PRUMO_PORTAO_INICIAL_2026_10_18.md |
| OpenAI | feat/s2-openai-adapter-sintetico / 124bbc9f6bce5fbb7b8b9a1c47c01f24784443a6 | docs/integracoes/openai/OAI_08_CONTRATO_PLANEJADORA_POS_HUMANA_CF_OP_02_v0_1.md | OAI-05, OAI-07, E01 v0.2 (nos próprios caminhos da frente) |
| Interface visual | feat/frontend-plataforma-visual / ae2f2b723bb7c62f6c727c45e07f722ab2e6cfd9 | frontend/docs/09_CF_OP_02_CONTRATO_VISUAL_JANELA_CADEIAS_v0_1.md | frontend/docs/05_CONTRATO_FV02_CONCLUSAO_EXTRAÇÃO_POS_HUMANA_v0_1.md e frontend/README.md |
| WhatsApp/Meta | docs/whatsapp-meta-concessionária de demonstração-poc-20261017 / 8b4489e7c9759ca386bb20f7f35b172691125901 | docs/integracoes/whatsapp-meta/wa07-contrato-janela-e-templates-cf-op-02-v0_1.md | integrations/whatsapp-meta/README.md |

**Verificação técnica dos commits:** cinco comparações GitHub mostraram exatamente UM commit novo por frente, somente arquivos Markdown (2+2+4+3+2 = **13 arquivos**, cinco contratos novos e oito referências/adendos preexistentes), **sem alteração de código, SQL, workflow ou infra**. Branches separadas, sem merge, sem sobrescrever trabalho da outra frente. A S1-002 continua empilhada sobre S0; seus links para contrato S0 são referências de revisão, não fusão de conteúdo.

## Limites de propriedade verificados

| Função | Único dono da operação | Quem somente solicita/fornece contexto |
| --- | --- | --- |
| Fechamento técnico, versão/snapshot do caso, ficha, status e persistência de planos | S0 | Front pede; OpenAI propõe; Meta transporta |
| Situação ativo/suspenso, concessão organizacional Prumo e remanejamento atômico | S1-002 | S0 valida atribuição atual; Front apresenta; IA/Meta não atribuem |
| Extração, análise do desfecho, compromisso temporal e agenda sugerida com templates preaprovados | OpenAI | S0 entrega contexto/catálogo e valida; não há escritura/envio pela IA |
| Botões de concluir, template individual, solicitar cadeia, indicador de janela, fila e histórico | Frontend | S0 entrega allowed_actions/estado autoritativo; browser não decide direito |
| Inbound/callback, evento de envio real, identidade App/WABA e transporte de template aprovado | WhatsApp/Meta | S0 autoriza tentativa, mede relógios e decide estado; Meta não marca perdido |

**Regras idênticas preservadas:** handoff definitivo; responda ao humano se humanizado e à IA apenas se ainda for caso IA elegível; três marcos independentes (Meta: 24h do inbound do cliente; conclusão humana: evento técnico; C09: 24h depois do final comprovadamente ENVIADO); plano pós-humano sempre novo e diferente de plano cancelado no handoff; opção template único ou cadeia, 2–5 tentativas como referência para atendidos silenciosos e final separado; histórico nunca eliminado; nenhum caso de outra loja; status comercial oito canônicos; `cadastro enviado ao banco` NUNCA vai a perdido por silêncio — negativa do Banco exige comprovação e lançamento humano; `vendido` não sofre reversão por silêncio.

## Riscos que não devem ser apresentados como resolvidos

1. **C09 do doc.26 ainda diz “sob IA”**. A orientação do responsável amplia a regra de negócio aos casos humanos elegíveis, mas C09 físico por estado/versão e procedimento de emenda do acervo canônico ainda exigem aceite S0. Caso `cadastro enviado ao operador` permanece em revisão; não converter em perda automaticamente.
2. **Contratos são candidatos**: os eventos/commandos propostos em S0, FV e WA e os payloads OpenAI não são endpoints assinados nem testados. OAI-05 versus E01 ainda têm nomes de campos diferentes. A issue #4 continua aberta.
3. **C04/Meta/LGPD/Banco [V]**: sem prova de permissões Meta, consentimento/opt-out/categoria/limites, sent oficial ou remessa bancaria autorizada; nenhum template real pode ser enviado por este aceite documental.
4. **I2 ainda não implementada**: migration 038 só bloqueia leitura de inativo, não remaneja; prova 7/7 S1E pertence ao I1, não ao contrato I2.
5. **A interface nova é documento**, ainda não é botão funcional; os cenários CF2-01–34 e adicionais OAI8/FV3/WA7/I2 **não foram executados**.
6. As revisões foram registradas por esta coordenação nos arquivos das branches, mas a **aceitação explícita dos responsáveis pelas outras frentes** e teste de compatibilidade executável ainda faltam. Comentário/commit não representa confirmação de leitura de uma pessoa ou de um processo paralelo.

## Veredito e notificação necessária

**ATUALIZAÇÃO DOCUMENTAL: CONCLUÍDA NAS CINCO FRENTES.** Separação de escopo por responsabilidade: coerente em revisão textual, sem invasão identificada nos 13 arquivos modificados. **CONCILIAÇÃO EXECUTÁVEL, HOMOLOGAÇÃO E TESTES: PENDENTES.** O responsável deve notificar: 1) núcleo S0; 2) equipe Prumo S1-002; 3) OpenAI; 4) frontend; 5) WhatsApp/Meta. Cada uma deve ler seu contrato, cotejar PR #7/issue #6, confirmar a fronteira e sinalizar divergências antes de implementar. Não anunciar alinhamento final de APIs nem atualizar a régua de progresso.
