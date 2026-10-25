# WA-59 — Limites de admissão HTTP, conexões lentas e saturação S0/Meta

**25 de outubro de 2026 — apenas Node.js `127.0.0.1` e PostgreSQL 17 descartável.**

## Objetivo

Limitar recursos do receptor HTTP experimental sem confundir o resultado de testes de saturação com disponibilidade da API Meta ou com capacidade produtiva. A frente S0 continua isolada da S1, da `main` e de qualquer implantação Supabase hospedada. A Issue #3 do repositório trata da auditoria preliminar de CI **S1**: não autoriza otimização, alterações de workflow ou implantação e não é aplicada neste ciclo.

## Alteração implementada

Arquivo `supabase/tests/s0_wa_061_meta_http_loopback_transport.mjs` (WA57, estendido aditivamente na WA59):

- `MAX_INFLIGHT=4`: reserva vaga após conferir método, rota e cabeçalhos e **antes** de armazenar bytes; resposta 503 `LAB_HTTP_BUSY` quando saturado, sem chamar WA56/WA55. Liberação da vaga em `finally`, inclusive erro, queda de conexão e exceções.
- `MAX_SOCKETS=16`: limite de conexões TCP aceitas pelo `http.Server` **exclusivamente local**, não um garantidor de resposta HTTP a toda conexão adicional. O runtime pode encerrar novas conexões ao atingir o teto.
- `IDLE_MS=1200`: encerramento de conexão inativa, incluindo headers/corpos que parem de chegar. Não cria ACK, status Meta ou concessão comercial.
- `MAX_BYTES=262144` por corpo continua vigente da WA57. Reserva simultânea permitida: **4 × 262.144 = 1.048.576 bytes de conteúdo de requisições**, fora overhead de buffers TCP, Node/V8, respostas e PostgreSQL; não é limite total de memória do processo.
- O endpoint segue preso a `127.0.0.1`, com porta efêmera, corpo com Content-Length, headers estritos, HMAC do corpo bruto, ticket WA45/WA44, ponte WA56 e entrada selada WA55. Nada disso habilita HTTP público.

## Validação e eficiência

Suíte **`supabase/tests/s0_wa_063_http_admission_limits_pg17.test.mjs` — 24 provas novas**, executadas no final do runner próprio da S0 após WA39–58. São verificadas quatro conexões incompletas consumindo as vagas, quinta solicitação rejeitada 503 sem invocar a ponte, rejeições de cabeçalhos inválidos mesmo sob carga, liberação depois do fechamento das conexões, novo processamento sem vagas perdidas, fechamento de cabeçalho lento e corpo incompleto, quatro chamadas já dentro da ponte mais quinta recusada, erro transiente que libera vaga e ensaio físico com cliente PG17 restrito: saturação sem INSERT, retomada com uma observação, quatro retransmissões concorrentes com resultados de replay e nenhuma duplicação no ledger original.

Não repetimos a matriz de protocolo da WA57 nem a de erros/retransmissão da WA58; sua cobertura permanece no runner. **Base:** 587 provas WA39–58. **WA59:** +24. **Total:** 611 provas, condicionado a CI `SUCCESS` em SHA exato.

## Limites da evidência

Limites escolhidos são parâmetros de proteção **do laboratório**, não metas de throughput ou orçamento produtivo. As provas não incluem tráfego externo, múltiplas instâncias, reinício real de processo, ataques distribuídos ou calibração em dispositivos/infra reais. Cabeçalhos HTTP são conferidos apenas pelo Node local; chaves e identidade de serviço são sintéticas. O 202 de loopback não é ACK da Meta. Nenhuma alteração em workflows de outras frentes, `feat/s1-002-equipe-prumo`, `main`, Supabase hospedada, Meta Graph/WhatsApp ou operações comerciais. PR permanece Draft, sem merge.

**Próxima candidata (WA60):** provar consistência de admissão e forense sob desligamento/reinício controlado do processo local, com variação de instância de laboratório e sem construir serviço externo antes dos gates de autenticação e implantação.

**Coordenação S1:** nenhuma ação exigida para WA59. Integrações futuras seguirão branch específica, validação e autorização expressa.
