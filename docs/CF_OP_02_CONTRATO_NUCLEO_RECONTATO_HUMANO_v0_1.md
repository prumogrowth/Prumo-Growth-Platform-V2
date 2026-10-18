# CF-OP-02/S0 — Contrato do núcleo: cadeia pós-humana, roteamento e três relógios | v0.1

Data: 18/10/2026. **Direção de negócio confirmada pelo responsável [D-negócio]; interfaces [P/R]; Meta/Banco/LGPD [V].** Proprietário: núcleo S0. Referências: PR #7, issue #6, pacote 17/10 docs 03 ATD-01B, 13A, 21, 22, 26 C02/C04–C12 e 41 D41, e S1-002. Não é API implantada, SQL ou autorização de envio.

## Contratos de domínio e autoridade

**S0-A: concluir atendimento humano.** Receber comando do frontend com caso e versão; autenticar o profissional da Prumo e sua atribuição atual na concessionária, registrar conclusão técnica única, fixar snapshot de mensagens do caso (corte, versão e finalidade) e pedir extração/análise silenciosa à OpenAI. Conclusão não é venda, remessa, perda nem encerramento imediato de janela visual; não reativa IA Vendedora.

**S0-B: template individual após expirar 24h.** Operador ainda responsável por atendimento NÃO concluído pode selecionar template e versão já aprovados e solicitar envio. S0 revalida caso/loja, atribuição, C04 elegibilidade, opt-out, categoria Meta, catálogo, janela, escopo, custo e concorrência com outros planos; só então produz intenção de envio para Meta. Template outbound não abre janela de mensagens livres sem novo inbound.

**S0-C: pedido de nova cadeia C05.** Origens candidatas: fase IA sem handoff; solicitação expressa de operador humano autorizado; análise pós-conclusão inconclusiva elegível. S0 entrega apenas histórico minimizado do mesmo caso/loja e catálogo/versionamento/limites à IA Planejadora. Ela PROPÕE versões de templates, quantidade, horários, fontes e justificativas. S0 valida, persiste plano novo e tentativas, com idempotência. Para cliente já atendido e silencioso, referência ATD-01B de 2 a 5 tentativas mais template final separado. Handoff cancela planos incompatíveis antigos C08/C10; plano pós-humano é **NOVO**, jamais ressuscita plano cancelado.

**S0-D: resposta recebida C02/C08.** Persistir inbound único e cancelar tentativas incompatíveis, preservando histórico. A responsabilidade vem do estado atual do CASO: se jamais houve handoff e ainda elegível, IA Vendedora; depois de qualquer handoff, humano atribuído e ativo (ou redistribuído), sem reativar IA Vendedora. Mensagem recebida durante processamento invalida snapshot obsoleto; última mensagem do CLIENTE redefine prazo da janela Meta.

**S0-E: encerramento por silêncio C09 ampliado.** A especificação original C09 do doc.26 exige ciclo elegível **sob IA**. O responsável confirmou a **extensão funcional a cadeias de casos humanos elegíveis**. Antes da implementação, S0 deve ratificar matriz de elegibilidade por fase/status. Exigir template FINAL aprovado e SEPARADO, prova de envio EFETIVO e instante confiável, +24h inteiras sem inbound, plano vigente, status pré-banco habilitado, consentimento/opt-out válido e conferência atômica contra resposta/concorrência. Só então marcar perdido por silêncio uma vez e retirar da fila ATIVA, **sem apagar histórico**. Nunca contar de agendamento, aceite HTTP, janela Meta ou envio falho/incerto. Nunca aplicar a cadastro enviado ao banco (recusa definitiva apenas com prova do Banco e lançamento humano, doc.21), vendido ou já perdido.

**S0-F: mudança de operador.** A S1-002 mantém e remaneja vínculos humanos atômicos e auditados. S0 consulta atribuição atual antes de comandos e envios e não devolve inbound a operador revogado. Não redistribui entre concessionárias.

## Três marcos distintos

1. **Janela Meta:** 24 horas desde último inbound do CLIENTE para mensagens livres; depois só template elegível. Isso NÃO conclui atendimento e NÃO marca perdido.
2. **Conclusão humana:** clique técnico autorizado; desencadeia OpenAI sem fechar conversa enquanto janela ainda aberta; se expirar e caso já concluído, frontend retira da LISTA ativa mantendo dados históricos. Se não concluído, segue pendente e pode usar template/cadeia.
3. **Silêncio pós-template final:** 24h desde prova de envio efetivo do template de encerramento; somente fase elegível pode receber perdido após conferências.

## Matriz de elegibilidade proposta [R], não autorização de produção

- Sob IA sem handoff: seguir C05–C09 já previstos quando elegível.
- Em atendimento pelo operador: **candidato** para plano pós-humano e C09 ampliado somente com guarda completa.
- Cadastro enviado ao operador: **decisão específica pendente**; dados prontos aguardando remessa não significam silêncio elegível.
- Cadastro enviado ao banco: **proibido C09 por silêncio**; recusa definitiva é ato humano comprovado.
- Vendido ou perdido: **proibido reaproveitar C09** para alterar ciclo histórico.
- Cliente solicita retorno em data certa: OpenAI propõe compromisso fundamentado, sem inventar horário ou deixar de revalidar elegibilidade.
- Desistência explícita, falta de dado obrigatório e opt-out NÃO são automaticamente “silêncio pós-final”; necessitam rota específica.

## Fronteiras — divisão sem invasão

- **S0**: valida autoria/escopo, consulta status e permissões, congela snapshots, decide elegibilidade, grava ficha/planos/transições e audita.
- **OpenAI**: somente extrai, classifica com fontes e propõe agenda/quantidade/templates autorizados; não grava, não envia, não escolhe operador nem marca perdido/vendido.
- **Frontend**: somente pede ação e exibe projeções confirmadas do backend; não calcula autoridade, não chama OpenAI/Meta diretamente.
- **WhatsApp/Meta**: transporta, valida canais/identidade de eventos e traz prova de recebido/enviado; não decide status comercial e não arquiva caso.
- **Equipe Prumo S1-002**: regula ativo/revogado e atribuição transacional; S0 consulta direito atual.
- **Banco**: venda/negativa por evidência e ato humano, sem inferência do modelo.

## Pendências e aceite

G1: reconciliar C09 “sob IA” com extensão humana por matriz de status e atos bancários; G2: conciliar C08/C10 versus plano NOVO pós-humano e escolha manual em paralelo; G3: fechar envelope UI→S0 e S0↔OAI (issue #4), versionamento/idempotência; G4: revalidar Meta/LGPD, opt-out/custo e prova real de sent; G5: executar cenários CF2-01–34 da PR #7 em sandbox. **Todos esses gates permanecem pendentes; nenhum teste executado por este documento.**
