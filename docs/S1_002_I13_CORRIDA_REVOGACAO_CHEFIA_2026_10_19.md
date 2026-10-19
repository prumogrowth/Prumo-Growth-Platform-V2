# S1-002/I13 — Corrida entre transferência manual e mudança de chefia

**Escopo:** equipe Prumo; branch Draft PR #5. Correção de segurança sintética em PostgreSQL 17 descartável, sem alterar S0, IA, Meta, frontend, grants A/B/C nem status comercial.

## Falha identificada na revisão I12

A movimentação manual I12 validava que gestor supervisionava os operadores de origem e destino, mas lia essas associações privadas sem bloqueá-las. Se a composição da equipe fosse alterada concorrentemente, uma operação poderia usar uma autorização que deixara de existir. Também não bloqueava a linha de estado do próprio gestor contra suspensão simultânea. A validação de concessões da concessionária no operador de destino já possuía trava, mas a **autoridade do gestor** permanecia uma lacuna.

## Reparo 050

A nova versão de `prumo_private.s1_mover_atendimento_da_equipe` bloqueia com `FOR SHARE`, em ordem definida, as três linhas da equipe envolvidas: solicitante, origem e destino; bloqueia igualmente os dois vínculos vigentes **gestor→operador**, ou o registro de responsável da plataforma quando aplicável. A checagem da autoridade acontece **depois** dessas travas. Se uma transferência de equipe ou suspensão estiver em andamento, o comando espera o commit e então revalida a alçada. Se a operação manual tiver obtido as travas primeiro, a mudança de chefia aguarda sua conclusão. Isso preserva a ordem transacional sem transformar gestor em dono de concessionárias.

O comando continua restrito ao executor `postgres` do sandbox, não é endpoint autorizado para pessoas reais. Mantém checagem exata de atribuição anterior, destino ativo/concessionária autorizada, caso humano operacional, uma única atribuição ativa, auditoria append-only e nenhuma concessão nova.

## Testes I13 (propostos até CI)

`scripts/test_s1_002_authority_race.sh` cria **duas sessões PostgreSQL reais** que disputam (a) remoção da associação de chefia do DESTINO e movimentação do atendimento e (b) suspensão global do GESTOR e movimentação; verifica rejeição após commit de ambos. Transfere então os operadores para um novo gestor e prova que ele pode executar transferência legítima, enquanto titular único, auditabilidade e grants ficam intactos. No runner, testes funcionais `S1M-01..12` e concorrentes `S1MR-01..04` executam novamente **após** instalar migration 050; suíte prévia I1–I11 também roda.

## Limites e bloqueios

Não é prova de Auth/GoTrue/PostgREST ou identidade de sessão validada. Uma função `current_user='postgres'` com ID do solicitante passado por parâmetro não pode ser exposta como RPC. Política de mudança de gestão, múltiplos gestores simultâneos, trabalhadores fora do turno, transferência ENTRE equipes, estado final de conclusão humana e capacidade de distribuição ainda precisam de contratos futuros. Nenhum deploy, merge, dado real ou percentual global novo.
