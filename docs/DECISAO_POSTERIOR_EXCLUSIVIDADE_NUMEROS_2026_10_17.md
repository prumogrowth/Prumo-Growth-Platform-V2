# DECISÃO POSTERIOR — Exclusividade de números entre concessionárias

Data: 17/10/2026 — orientação posterior do responsável.

**Nova regra operacional, adotada nesta branch:** um telefone de **cliente/lead** não pode estar vinculado simultaneamente a concessionárias distintas na Prumo. O número **emissor** de WhatsApp gerenciado pela Prumo também permanece único por loja — essa última exclusividade já existia.

## Divergência registrada (sem apagar o histórico)
As fontes anteriores 08A, 25, 26, 30, 38 e 43 expressamente admitiam um mesmo telefone de cliente nas lojas A e B, com históricos independentes; esse **cenário de teste foi substituído pela decisão posterior**. Permanece normativo o isolamento das lojas, das conversas e das provas. Não unificar histórico, movimentar lead, consultar loja alheia nem resolver telefone reciclado automaticamente.

## Implementação candidata
- Migração 007: UNIQUE global de telefone normalizado do lead + formato E.164; mantém chaves compostas e RLS por loja.
- Migração 006 ajustada: tentativa de importar o mesmo telefone pela segunda loja gera item rejeitado com motivo genérico `CONTATO_NAO_ELEGIVEL`, sem revelar nome, ID ou histórico da loja que já o possui; o lote preserva outras linhas válidas.
- Migração 008: leitura de lead do operador somente com caso ativo atribuído, vínculo vigente e mesma loja; sem leitura generalizada.
- Tests S0: A/B usam telefones distintos; colisão global direta é negada; importação de colisão retorna rejeição genérica; disputa simultânea entre duas lojas não cria duplicação.
- `canais_loja.identificador_emissor` já utiliza UNIQUE global: um número emissor por concessionária.

## Portões e questões ainda abertas
Esta regra muda um requisito de negócio e a política de índices globais do documento 30; deve entrar na **consolidação documental vigente** antes de produção. O índice global de telefone pode facilitar correlação interlojas pelo banco privilegiado, exigindo análise de minimização/LGPD, privilégios e registro de alçadas. O motivo genérico impede expor a loja titular, mas não elimina inferência operacional pela recusa. Não há regra aprovada de transferência, exclusão, reciclagem ou contestação de titularidade; operações devem ser bloqueadas e encaminhadas a processo humano até essa decisão.

Nenhum número real ou credencial foi empregado. Não implantar no Supabase remoto antes da validação em ambiente integrado e dos controles LGPD.
