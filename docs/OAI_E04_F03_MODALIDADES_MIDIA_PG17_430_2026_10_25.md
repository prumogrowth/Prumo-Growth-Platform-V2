# E04 F03/S0 — Classificação explícita da modalidade da fonte — 25/10/2026

## Decisão de implantação
Somente GitHub em branch experimental e PostgreSQL 17 descartável. O responsável decidiu acumular desenvolvimento das frentes, reconciliar os contratos e somente depois preparar a integração geral concentrada no Supabase hospedado, antes de testes reais. Não criar/deployar migrações no Supabase remoto. Este arquivo documenta fixture local de laboratório, não o ambiente final.

## Mudança implementada
- `supabase/tests/s0_f03_message_modalities_local_only.sql` contém registro imutável e restrito por concessionária+ID da mensagem. Modalidades de teste: `TEXT`, `AUDIO`, `IMAGE`, `VIDEO`, `DOCUMENT`, `UNKNOWN`. Somente `TEXT` com estado `NATIVE_TEXT_FIXTURE` é elegível para prova literal; qualquer mídia permanece `MEDIA_UNVERIFIED`. O hash opcional do anexo é apenas metadado e não equivale a transcrição, conteúdo ou assinatura de um provedor.
- Antes de aceitar a evidência literal, `backend/s0_f03_crossfront_evidence_local.py` exige classificação S0 para **todas as mensagens do histórico até o fechamento**, e retorna `MEDIA_REVIEW_REQUIRED` se alguma delas estiver sem classificação ou não for texto. Não permite à F03 corrigir ou inventar classificação, nem confiar na alegação `s0Verified` do JavaScript.
- As validações prévias não foram afrouxadas: origem e corte S0, histórico com HMAC vivo, escopo da mesma loja/pessoa, versões, identidade, reserva CAS, campos e catálogo. O resultado positivo é somente `S0_EVIDENCE_REVIEW_ONLY`; **nenhuma ficha é escrita e não há transmissão ao modelo**.
- Classificações são append-only, proibidas para anon, authenticated, service_role, gateway e signer. Mesmo o proprietário local de testes não pode atualizar/deletar classificação após inserida. Essa fixture é operada como `postgres` local, não descreve credenciais ou papel de implantação futura.
- O arquivo `scripts/run-s0-f03-pg17-local.sh` carrega a tabela somente depois de montar o PG17 descartável; as fixtures físicas criam classificação explícita de suas mensagens, sem depender de conteúdo fornecido pelo modelo.

## Evidência de execução
**GitHub Actions SUCCESS:** https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40190901375
**Código certificado:** `87e128625eb566d813eab27cf97eb2455a5741fa`.
- **84/84 S0** e **346/346 F03** testes Python aprovados: **430/430** Python, dos quais **223 físicos PG17 F03**.
- **269/269 testes Node nativos** da branch S2, obtida em checkout separado do SHA fixado `ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c`.
- São **699 verificações em duas suítes diferentes no mesmo CI**, não 699 cenários originais de produto nem os 70 oráculos SYN E02 homologados.
- Oito novos testes físicos PG17 (#216–223) cobrem áudio com falsa alegação de transcrição, imagem antiga não analisada, classificação ausente, ACL, imutabilidade, escopo de concessionária e tentativa de reclassificar mídia como texto.

## Limitações e próximo gate
A tabela local só identifica **tipos fictícios de fonte**; não lê anexos, não valida bytes reais, não faz STT, não classifica mídia da Meta e não verifica transcrições. Também não comprova a qualidade semântica de texto natural, renda ou documento bancário. O gate atual é intencionalmente conservador: uma mídia ainda não analisada em qualquer parte do histórico obriga revisão, mesmo que haja texto aparentemente suficiente; a eventual flexibilização exige prova verificável de que mídia anterior não contém evidência contraditória.
Próximos itens em E04: contrato S0 para recibos de mídia/transcrição/privacidade e proveniência verificada, ratificar direitos de leitura D2–D4 e histórico, preservar a separação entre consentimento do cliente, sessão S0, avaliação F03 e autorização humana de edição; ampliar jornada F01→humano→F03→F02; validar a matriz E02 original. E05, implantação e testes reais continuam pendentes da etapa geral posterior.
