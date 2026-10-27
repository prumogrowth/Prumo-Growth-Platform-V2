# Regra vigente — números do cliente versus atendimento Prumo

Data: 17/10/2026. Confirmação explícita do responsável.

## Número do cliente (identidade por loja)
- O mesmo número de cliente **pode** entrar em contato com A, B e C.
- Cada loja mantém seu próprio `leads_loja`, `ciclos_comerciais`, conversas, remessas e histórico, sem compartilhamento cruzado.
- Chave do lead no banco: `unique(concessionaria_id, telefone_cliente_normalizado)`, sem `UNIQUE` global do telefone do cliente.
- Importações C01 somente deduplicam o mesmo cliente **dentro da própria loja**; em loja diferente, é um lead independente.

## Número de atendimento da Prumo (canal emissor/receptor)
- Um número usado para atendimento pela Prumo só pode pertencer a **uma concessionária por vez**; A e B nunca atendem simultaneamente pelo mesmo emissor.
- A tabela `canais_loja` tem `identificador_emissor UNIQUE` global e `concessionaria_id` exclusivo; vínculos por FK composta entre loja, conversa e canal evitam associação cruzada.
- Para mudança futura de titularidade do número de atendimento, exigir procedimento humano e preservação de histórico; tal fluxo não foi implementado.

## Controle de qualidade
- Testes SQL: mesmo telefone A/B permitido e canais emissores duplicados proibidos.
- Concorrência A/B: importações simultâneas do mesmo telefone resultam em **dois** leads/ciclos isolados; não em rejeição.
- RLS: gestor lê exclusivamente sua loja; operador apenas casos atribuídos.
- Testes usam valores totalmente sintéticos.

## Histórico de correção
A migração 007 (cliente globalmente único) foi retirada sem deploy; por isso **a sequência de arquivos versionados tem salto de 006 para 008**, propositalmente. A migração 008 mantém o escopo de leitura de lead pelo operador designado.

O documento `DECISAO_POSTERIOR_EXCLUSIVIDADE_NUMEROS_2026_10_17.md` foi expressamente retratado e não rege o produto. Esta versão prevalece na implementação.

S0 permanece em desenvolvimento; ainda exige homologação real Auth/REST, revisão LGPD, backup e aceite humano antes de implantação.
