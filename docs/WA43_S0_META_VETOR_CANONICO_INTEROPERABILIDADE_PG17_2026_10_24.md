# WA-43 — Paridade de bytes e HMAC do contrato interno S0/044 (PG17)

**24/10/2026 · [Novo repositório oficial](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA) · [PR Draft de integração S0/Meta #2](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/2) · branch `feat/wa39-s0-meta-forensic-bridge-20261023`.**

## Contexto

O espelhamento preservou tanto a branch de WhatsApp/Meta `docs/whatsapp-meta-concessionária de demonstração-poc-20261017` (HEAD inicial `d9cd4b8f1de222324c92f2fec8053b0b91dcfe5d`) quanto a branch de integração S0/Meta acima (HEAD inicial `26f279dbaadfbdd248274ce2ec7c69aaea659121`). O PR novo é baseado em `feat/s0-fundacao-prumo`, **não em `main`**. A WA42 foi revalidada no novo repositório pelo [workflow #40061435947](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40061435947): S0 inteira, WA39 18/18, WA40 25/25, WA41 16/16, WA42 23/23.

A WA42 detectou que o envelope **Meta WA34/35**, assinado sobre vetor JSON com `issuer`, `audience`, `binding_revision`, `issued_at_ms` e outros campos, difere do envelope **S0/044**, assinado sobre campos delimitados por `|`, chave UUID, propósito e horário UNIX em segundos. **Não são intercambiáveis** e nenhum componente recebe direito de envio porque a verificação HMAC técnica funcionou.

## Incremento WA43 — prova material sem autorização

Arquivo `supabase/tests/s0_wa_047_assert_handoff_canonical_pg17.py`: em PostgreSQL 17 descartável, compara a função S0/044 `meta_material_handoff_fixture_s0` com uma serialização Python independente dos mesmos campos. Confere que:

1. os bytes de texto são iguais e têm prefixo/finalidade esperados;
2. cada um dos **15 campos** altera a materialização e a MAC HMAC-SHA256, em ambos os lados, sem colisão sintética entre esses vetores;
3. um MAC sobre JSON ao estilo WA34 **não** equivale a MAC sobre material S0/044;
4. um pacote real para a fixture com chave artificial e nonce UUID é aceito estritamente para `LAB_OBSERVED_UNVERIFIED`;
5. alteração sem nova assinatura, replay, MAC da serialização errada e ausência de nonce/evidência correspondente resultam em negação;
6. as flags de envio, ACK, retry externo, produção, entrega confirmada e transição comercial continuam **todas falsas**.

São **18 marcadores de verificação** introduzidos no `scripts/run-s0-local.sh` e no workflow PG17 já existente. As duas concessionárias, bindings S0/041-042 e status forenses S0/043 são os mesmos dados sintéticos. A chave fictícia de WA43 é inserida somente na base descartável pelo teste Python — nenhuma credencial, token, número comercial real ou segredo de produção entrou no Git.

## O que esta prova NÃO significa

- Não existe integração com a API Graph, envio, webhook real, Supabase hospedado, autenticação de serviço de rede nem autorização de `ACK` HTTP.
- **WA34/35 ainda não emite o material S0/044**. Este teste comprova interoperabilidade Python→PostgreSQL **para o contrato S0**, não interoperabilidade efetiva WA34→S0.
- O proprietário do wrapper de gravação WA40 continua `postgres` no ambiente de laboratório. O papel NOLOGIN não substitui uma identidade M2M verdadeira.
- A revogação WA42 protege transações que usam sua função de revogação; administradores capazes de alterar diretamente a tabela de chaves contornam o protocolo.
- A frente S1 permanece separada. **WA43 não exige mudanças S1**. Para operação comercial futura, é preciso pedir à equipe S1 contrato de concessão/atribuição, revogação e ordem de bloqueios interfrentes antes de alterar suas estruturas.

**Estado:** somente testes e documentação candidatos. Sem merge em `main`, sem deploy e sem alteração de frentes fora deste PR.
