# OAI E04 — atestação S0 de mídia sintética, hashes, finalidade e retenção

**Data:** 25/10/2026. **Estado:** concluído e certificado como contrato offline de laboratório PG17. Não é ferramenta de transcrição, endpoint real, serviço Meta ou grant de conteúdo à OpenAI.

## Contrato implantado somente em repositório (não no Supabase hospedado)

- `supabase/tests/s0_f03_media_attestation_local_only.sql` cria uma tabela de comprovações S0 somente na execução PostgreSQL 17 descartável: concessionária, encerramento humano, caso, mensagem original, finalidade única E04, versão da chave, SHA-256 dos bytes de mídia, SHA-256 da transcrição sintética, HMAC-SHA256 e validade. Nenhum áudio, imagem, documento ou texto transcrito é armazenado nessa tabela.
- A gravação é condicionada à mesma concessionária, lead do caso humano e mensagem anterior ao horário de corte. A classificação física S0 da fonte precisa ser AUDIO ou DOCUMENT com hash de mídia idêntico. IMAGE, VIDEO e UNKNOWN não são aceitos no contrato desta etapa.
- A tabela e os registros são imutáveis (inserção única, sem update/delete). ACL impede leitura de contas cliente/serviço comuns; escrita de fixture somente pelo papel proprietário local postgres. O campo de finalidade é restrito a F03_POST_HUMAN_REVIEW_SYNTHETIC e o prazo precisa ser posterior à criação. Isso não prova aplicação de política real de retenção LGPD.
- `backend/s0_f03_media_attestation_local.py` implementa a conferência privada por S0: primeiro exige o gate físico anterior de F03 (histórico HMAC, versões/CAS, identidade, campos, escopo e catálogo); depois compara hashes dos bytes sintéticos e texto transcrito de uma entrada de confiança do próprio laboratório contra o recibo imutável, recomputa o HMAC, rejeita prazo expirado ou desvio de finalidade e repete a revalidação S0 após a consulta.
- Resultado positivo: `MEDIA_DIGEST_REVIEW_ONLY`. Não concede autorização de leitura ao modelo, não altera ficha, não manda mensagens, não aciona F02 e **não desbloqueia** o gate de evidência textual de F03: AUDIO e DOCUMENT continuam classificados como mídia não verificada para extração de dados.

## O que a prova NÃO estabelece

O sistema ainda **não** buscou bytes reais no armazenamento Meta/WhatsApp, não fez STT ou extração de documentos, não verificou assinatura de provedor, não produziu evidência semântica, não inferiu renda/identidade, não demonstrou autorização LGPD para transcrição nem obteve aceite humano operacional. O HMAC só comprova consistência dos bytes e da transcrição sintética **quando a origem de ambos já é confiável na S0**. O fixture atual não prova essa confiabilidade no mundo real. São necessárias integração e auditoria específicas antes de elevar esse dado de estágio.

## Testes certificados e correção realizada

GitHub Actions: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40192764536

- Código certificado: `53ba00b9d9dc9186929628437e9aeb8f5a38f41e`.
- Python S0: **84/84** testes aprovados.
- Python F03: **373/373**, incluindo **240 testes físicos PG17**; dez testes unitários novos e dezessete novos físicos (224–240) para mídia.
- Node nativo na versão fixada da S2: **269/269** testes aprovados.
- **457/457 Python** e **269/269 Node**, total de 726 verificações em duas suítes distintas executadas no mesmo GitHub Actions. Isso NÃO equivale aos 70 oráculos SYN E02 nem significa jornada real F01/F02/F03 em produção.
- Durante a execução inicial, o teste de finalidade proibida esperava um erro de CHECK, mas o banco recusou primeiro por hash não correspondente. O teste foi corrigido para apresentar um hash válido e isolar a regra de finalidade; a suíte integral posterior confirmou `SUCCESS`.

## Próximas dependências

1. Definir fonte real assinada/autorizada pela S0 de mídia e transcrições, prova de integridade de bytes e mecanismo de extração auditável, com segregação LGPD, consentimento/finalidade e minimização.
2. Rastrear validade semântica de fatos financeiros e documentos; não promover hash de transcrição a verdade comprovada.
3. Executar a matriz SYN-01..70 e ampliar o fluxo F01→humano→F03→F02 com integração dos contratos da S0/S1/Meta, ainda com dados sintéticos.
4. Preparar posteriormente o pacote de migração ordenada e integração geral no **Supabase hospedado somente após autorização do responsável**. Nenhum banco remoto, cliente real, merge, deploy ou E05 foi usado agora.
