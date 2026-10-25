# E04 F03 — proteção contra colisão de identidade entre leads (25/10/2026)

Escopo: contrato offline, fontes sintéticas S0 no PostgreSQL 17 descartável. **Sem construir/usar Supabase hospedado**. Registro associado ao PR #1 Draft, na branch F03, que permanece sem merge/deploy.

## Achado que motivou o reforço
A aplicação de ficha e o contrato anterior recusavam pendência de identidade S0 existente, mas não verificavam uma segunda ficha/lead correspondente ao mesmo número em outra representação (telefone ou alias), quando **não** havia registro de pendência. Isso permitiria uma ficha fictícia ser editada apesar de dois candidatos de identidade na mesma concessionária.

## Remediação implementada
O módulo `backend/s0_f03_identity_uniqueness_local.py` verifica, por concessionária, se qualquer identificador do lead (telefone + aliases) coincide com um identificador **de outro lead** por igualdade ou variante brasileira. Um segundo lead candidato é conflito, não merge. A consulta utiliza somente fontes S0 físicas locais e identificadores derivados do banco.

O controle é chamado dentro da transação por três portas: (1) reserva F03, (2) consulta de contrato, (3) CAS humano sintético. A reserva passa a segurar o mesmo lock transacional de loja de que as portas de contrato/CAS e os triggers de inserção/alteração/remoção dos leads, aliases e pendências dependem. Assim, uma nova inserção de candidato fica serializada com a decisão de escrita. Outra concessionária não bloqueia por engano a loja avaliada.

Nenhuma chave de identidade é escolhida pelo modelo, nenhum HOLD libera acesso, e alteração de cadastro real continua fora do escopo.

## Política de integração final pedida pelo responsável
As frentes serão amadurecidas em paralelo, depois haverá integração geral de seus contratos; **a construção no Supabase hospedado será feita em etapa concentrada posterior**, após revisão do conjunto. CI PostgreSQL descartável e artefatos SQL versionados não equivalem a instalação no Supabase remoto.

## Situação de conclusão
Esta entrega mitiga uma classe específica de conflitos. Ainda faltam decisão final de permissões entre S0/S1, aprovação humana operacional, leitura de mídia e retenção LGPD, mapeamento do catálogo/ficha definitivos, interfaces e processamento efetivo F01/F02/F03, ensaio de integração transversal e GO/NO-GO. Não inferir porcentagem global do número de testes.