# S1-002 / I75A — Gate G3: contrato de aceitação por objeto e finalidade

**26/10/2026.** Primeira etapa da retomada após I74 certificada em CI descartável. **Ainda não é implementação ou homologação de RLS de produção.** Elaborado para evitar que a frente reabra I61–I74 sem necessidade. Responsabilidade de núcleo S0 continua com Codex.

## Bases normativas e precedência

- `docs/S1_002_01_CONTRATO_FUNCIONAL_VIGENTE_2026_10_22.md`, §§7 e 10–11, adendo A2/I51: histórico lógico **completo do mesmo contato e da mesma concessionária**, sem ampliar escrita, sem unir mesmo telefone de concessionárias distintas; Gestor restrito à própria equipe. Extensão contextual não concede automaticamente acesso bruto a dados D3/D4 ou anexos bancários.
- `docs/S1_002_02_MATRIZ_ADERENCIA_E_PENDENCIAS_2026_10_22.md`, G3: entitlement por caso para escrita, leitura contextual por contato/loja e revogação.
- I61: exceção por atribuição/caso/loja/ator canônicos; I62: transação assinada; I63: políticas de leitura candidatas de casos, atribuições, conversas e mensagens (8 policies) testadas em laboratório; I64–I68: superfície indireta, quarentena de wrappers, projeções e linhas administrativas limitadas. **Essas provas são baseline, não pendência a refazer.**
- I69–I74: exportação mínima e segurança do executor **certificadas em bancada**, mas não legitimam acesso a histórico D3/D4 ou mídias.

## Inventário de autorização (não presumir implantação)

| Superfície | Prova laboratorial existente | Falta para gate G3 |
| --- | --- | --- |
| `casos_humanos`, `atribuicoes_humanas` | I61/I63; caso atribuído/exceção ativa; perda de exceção revoga contexto | Política operacional com usuários e roteadores S0 efetivos |
| `conversas`, `mensagens` | I60/I63; histórico sem caso vinculado ao **mesmo** contato e loja; RLS de equipe | Prova de todos os ciclos históricos do contato, leitura contextual versus envio e integrações externas |
| `itens_lote`, `reencontros_lote`, `eventos_status_comercial` | I67; somente Gestor habilitado e contato com caso autorizado | Definição de colunas D2/D3/D4 e mascaramento; consumidores reais |
| `lotes_importacao`, `canais_loja` | I67 mantém cabeçalhos amplos em quarentena; I68/I69 visões/resumos controlados | Não liberar objetos brutos por conveniência; limitar projeção final por finalidade |
| **Mídias, anexos e dados D3/D4** | Nenhuma prova I63/I74 equivale a autorização fina para download/URL ou conteúdo bancário | **Dependência de contrato S0**: catálogo físico de objetos/colunas, armazenamento e ACL/URLs, retenção, chaves de identidade e finalidade |

Não assumir que existem tabelas SQL ou endpoints concretos de anexos sem inventário do núcleo S0; o gate exige primeiro sua identificação e propriedade.

## Cenários obrigatórios que definirão a execução I75

1. **I75-G3-01 — Leitura positiva:** Consultor com atribuição válida lê histórico antigo e atual do contato **na mesma loja**, preservando autoria e segmentos.
2. **I75-G3-02 — Isolamento:** mesmo número/telefone em concessionária diferente **não** confere acesso a ciclo, conversa ou mídia.
3. **I75-G3-03 — Exceção restrita:** Consultor sem grant amplo, mas com exceção I61 atual, obtém leitura contextual do mesmo contato; **escrita** continua limitada ao caso vigente.
4. **I75-G3-04 — Revogação em voo:** logout, fim de atribuição, troca de equipe, bloqueio/revogação I61 e perda de loja cortam direitos antes da próxima leitura autorizada; documentos emitidos antes não ganham autorização nova.
5. **I75-G3-05 — Gestor:** supervisão permite histórico de sua equipe, nunca acesso por mera coincidência de loja a caso de equipe alheia.
6. **I75-G3-06 — D3/D4:** nenhum dado cadastral/bancário bruto ou anexo é exposto pela simples existência de mensagem/contexto; cada objeto precisa de grant por finalidade, classificação e política.
7. **I75-G3-07 — Mídia indireta:** URL assinada, arquivo armazenado, thumbnail, prévia, exportação, metadados e cache exigem revogação e TTL compatíveis; não testar endpoint fictício.
8. **I75-G3-08 — Consumo/reporte:** projeções, RPCs e relatórios não devem oferecer atalho que ultrapasse as linhas/colunas liberadas por RLS; regressões I63–I74 devem permanecer verdes.

**Estado deste documento:** matriz de aceites e lacunas contratadas, **não 8/8 testes executados**. Somente após inventariar objetos/consumidores reais será possível vincular SQL ou testes HTTP verificáveis aos oito cenários, sem simular resultado de produção.

## Handoff mínimo necessário da S0/Codex

Solicitar apenas informações/contratos, **sem dados pessoais nem credenciais**:
- Identificação física/canônica de contatos, ciclos, conversas, mensagens e mídias por `loja+contato`; funcionamento após transferências e arquivamento.
- Lista de objetos/colunas/endpoints/consumidores D2/D3/D4, armazenamento de anexos e mecanismos de URLs/TTL/revogação atualmente implementados.
- Fonte de decisão de acesso e capacidade de impor revogação em cada leitura/download; classificação de dados e prazo de retenção para validação LGPD.
- Estratégia de validar regressões em ambiente descartável; nenhuma mudança ao núcleo oficial nem migração hospedada sem coordenação.

**Próximo passo I75B:** produzir inventário rastreável por objeto real e ampliar provas negativas apenas para lacunas confirmadas. NÃO repetir o desenvolvimento do signer/exportador I74, nem liberar dados brutos por hipótese.
