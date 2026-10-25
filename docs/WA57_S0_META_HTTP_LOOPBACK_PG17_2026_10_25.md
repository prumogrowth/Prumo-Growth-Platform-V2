# WA-57 — Contrato HTTP offline estrito até WA55

**25/10/2026 — somente loopback `127.0.0.1`, Node.js e PostgreSQL 17 descartável.**

## Escopo

A WA57 implementa um receptor HTTP/1.1 de laboratório no arquivo `supabase/tests/s0_wa_061_meta_http_loopback_transport.mjs`. A fábrica `createWa57OfflineLoopback({bridge})` não aceita endereço externo nem expõe o objeto servidor; `start()` liga numa porta efêmera exclusivamente em `127.0.0.1`, `address()` inspeciona o destino e `stop()` fecha irreversivelmente o fixture.

Aceita **somente POST** para `/__wa57_lab/status`, HTTP/1.1 local, `Host: 127.0.0.1:<porta>`, um único `Content-Type: application/json`, `Content-Length` decimal, positivo e no máximo 262.144 bytes, e um único `X-Hub-Signature-256: sha256=<64 dígitos hexadecimais minúsculos>`. Permite apenas cabeçalho adicional `Connection`, sem duplicatas; não aceita Transfer-Encoding, Content-Encoding, cabeçalhos de proxy, redirecionamento, rota alternativa, GET, queries, cabeçalhos extras ou ambíguos. Requisições `Expect` são recusadas antes da resposta automática `100 Continue`; parsing HTTP inválido responde `400` no laboratório.

Lê os bytes em memória dentro do limite, verifica que o total equivale ao comprimento anunciado e transmite **exclusivamente** o buffer recebido e assinatura à ponte WA56. Resposta `202` só existe quando a ponte devolve a decisão sintética `LAB_META_RAW_TO_WA55_FORENSIC_ONLY`, recibo `WA55_PG17_SINGLE_LAB_ONLY` e todos os campos comerciais falsos. Erro, formato inadequado ou tentativa de produção falham fechados. Toda resposta carrega `x-wa57-lab-only=true`, `cache-control=no-store`, `meta_ack_emitted=false`; a resposta HTTP em `127.0.0.1` **não constitui ACK Meta real**.

## Validação

O novo teste `supabase/tests/s0_wa_061_meta_http_loopback_transport.test.mjs` possui **40 marcadores** após WA56: ciclo de vida loopback, rotas, métodos, host, assinatura, cabeçalhos, duplicatas, Content-Length/Transfer-Encoding, HTTP/1.0, `Expect: 100-continue`, falhas da ponte e respostas comerciais indevidas, além do ensaio real de HTTP → WA46 HMAC bruto → WA45/WA44 ticket → WA56 confirmação → WA55 arquivamento forense PG17. A reiteração do mesmo evento deve produzir apenas uma linha forense. A cadeia utiliza credenciais fictícias criadas na execução. Os testes históricos WA39–56 (511/511) são mantidos; total **551/551** somente após CI `SUCCESS` do commit final.

## Limitações e bloqueios

Não existe endpoint público ou serviço de rede implantado, app Meta registrado para esta ponte, segredo produtivo, identidade M2M/IAM confiável, ACK recebido pela Meta, Graph API, envio de mensagem, retry, alteração comercial, integração com S1 ou Supabase hospedado. Filtros HTTP do Node são apropriados ao fixture, **não** uma validação de cadeia de proxy TLS/publicação. A expressão `202` é resposta local do ensaio, nunca confirmação de entrega pela Meta. A S1 não precisa executar nenhuma alteração nesta etapa.

**Próxima etapa candidata:** auditar coerência de status HTTP, retransmissões e colapso seguro de tentativas repetidas quando houver quedas de conexão, ainda offline, antes de discutir autenticação e infraestrutura produtivas.
