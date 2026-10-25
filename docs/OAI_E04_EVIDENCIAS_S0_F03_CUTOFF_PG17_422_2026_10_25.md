# OAI E04 — prova literal de valores F03/S0 e corte histórico

Data: 25 de outubro de 2026. Autoridade e escopo: branch feat/oai-s0-f03-history-port-20261023, PR #1 Draft. S2 referenciada em commit fixado ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c. Somente PostgreSQL 17 descartável e testes Node nativos. Supabase hospedado permanece adiado para integração geral posterior. Sem merge, dados reais, OpenAI API, Meta API ou produção.

## Nova entrega

- backend/s0_f03_crossfront_evidence_local.py: nova porta exclusiva S0 que recebe a proposta F03 JavaScript sem confiar em valores, IDs de mensagem ou flags de autorização declarados pela IA.
- A S0 primeiramente executa o contrato físico já existente para a proposta (reserva CAS, escopo, cinco versões, catálogo, integridade, identidade e HMAC). Depois busca por conta própria o conteúdo histórico da mesma pessoa/concessionária até o fechamento humano, com bloqueio transacional de lead/conversas e selo de conteúdo HMAC conferido novamente.
- Para cada campo, verifica tipo e valor literal da proposta contra uma mensagem física explicitamente citada. A fonte deve estar no conjunto autorizado daquele lead e ser anterior ao corte. Qualquer valor literal contraditório em outra mensagem da mesma pessoa, mesmo de outro caso anterior, exige revisão. Após isso, repete o contrato S0.
- A evidência de laboratório é deliberadamente apenas a sintaxe de mensagem inteira campo_sintetico=valor_sintetico. Não interpreta linguagem natural, não prova renda/identidade, não valida documentação bancária ou áudios. O retorno S0_EVIDENCE_REVIEW_ONLY não executa escrita, status, Meta, F02 nem transforma modelo em gestor.
- backend/tests/test_s0_f03_crossfront_evidence_local.py: dez testes unitários de esquema exato, identificador, valor, controles proibidos, expressão literal e não vazamento.
- backend/tests/test_s0_f03_pg17_integration.py: testes físicos 204–215 (12 novos) usando avaliação real do JS da S2 sobre fixture e rechecagem física S0. Incluem fonte literal correta, falta de prova, contradição antiga omitida pelo JS, ID inventado, fonte de caso anterior legítimo, valor inventado mesmo com JS aprovando, HMAC quebrado por mudança após resposta, autorização adulterada, linguagem natural não estruturada, duas fontes iguais, preservação real do snapshot de encerramento humano e recusa de mensagem posterior ao corte.

## Teste e certificação

GitHub Actions SUCCESS: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40190227042

HEAD de código certificado: e5d88d6575b7735282ae9d9c1ed3fcbf4300b994.

- S0 físico/local: 84/84 testes Python PASS.
- F03 físico/local e unitário: 338/338 testes Python PASS, dos quais 215 de integração PostgreSQL.
- Total Python: 422/422 PASS.
- S2 F01/F02/F03: 269/269 testes Node nativos PASS, com SHA de código S2 fixado.
- Total de verificações das duas suítes executadas no mesmo CI: 691; NÃO são 691 casos de produto ponta a ponta, nem equivalem aos 70 oráculos documentais SYN de E02.
- A autenticação histórica na ponte anterior usa um dublê S0 no ensaio e não deve ser chamada de prova de sessão real. A prova literal e o HMAC são físicos sobre PostgreSQL descartável, ainda não auditados para todos os escritores da operação.

## Estado e próximo gate

Há agora um fluxo verificável: JS F03 simulado -> proposta bruta com IDs de fontes -> porta S0 de revisão física -> comprovação literal sintética por mensagem, rejeição de contradição e respeito ao cutoff. Isso ainda não significa que F03 aplica campos automaticamente. A aplicação CAS do laboratório permanece uma porta separada que exige gestor S0 simulado.

Prioridades seguintes: contrato assinado/autorizado de evidência semântica real (não inferência fictícia), texto/áudio/mídia e política LGPD; integrar F01/F02 com S0 e S1 nos cenários E04; executar e homologar 70 SYN; preparar contrato definitivo de catálogo/ficha; revisão interfrentes; posterior integração concentrada do Supabase após autorização do responsável.

Não confundir quantidade de testes com porcentagem de término, nem promover E04 para E05.
