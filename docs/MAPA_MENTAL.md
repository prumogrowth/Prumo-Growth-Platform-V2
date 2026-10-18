# Prumo — mapa mental simples

```mermaid
flowchart TD
  P[Prumo] --> E[Entrada por concessionária]
  E --> IMP[Lotes por loja]
  E --> INB[Mensagens C02 por canal exclusivo]
  INB --> L
  INB --> PEND[Multiplos ciclos: revisao humana]
  IMP --> L[Cliente por loja → lead/ciclo: 8 estados]
  L --> EV[Eventos de status]
  L --> IA[IA Vendedora]
  IA --> H[Atendimento humano]
  H --> CAD[Cadastro versionado]
  CAD --> BAN[Remessa humana ao Banco]
  BAN --> RES[Resultado com prova]
  L --> REC[Recontatos]
  REC --> PLA[Planejadora: templates aprovados]
  REC --> ELIG[C04: elegibilidade e opt-out por loja/canal]
  ELIG --> CAN
  REC --> CAN[Resposta ou gestor: cancelar pendentes]
  INB --> CAN
  P --> C07[C07 simulado: callbacks tecnicos, sem reenvio]
  C07 --> RC[Sem correlacao: reconciliacao pendente]
  C07 --> RISK[Falha ou incerteza: sem retry automatico]
  RC --> GEST[Revisao do gestor: versao e justificativa]
  RISK --> GEST
  P --> AUTH[Backend S0: GoTrue verificado + sessao ativa]
  AUTH --> OP[Comandos sintéticos restritos: gestor/versao/loja]
  AUTH --> GWAY[Papel NOLOGIN, wrappers C07/C08]
  GWAY --> AUD[Auditoria de comandos aplicados sem dados sensiveis]
  GWAY --> ROT[Chaves HMAC: ativar, revogar e historico de versao]
  GWAY --> NONCE[Nonce unico, limpeza conservadora]
  AUTH --> NEG[Negativas sanitizadas sem token ou PII]
  OP --> GEST
  P --> ADM[Gestão e MCP com confirmação]
  P --> DB[Supabase: dados, RLS e auditoria]
  P --> INT[Integrações futuras]
  INT --> WA[Meta WhatsApp]
  INT --> OAI[OpenAI API]
  INT --> N[n8n a decidir]
```

S0 fundação: telefone de cliente pode existir em A/B/C com históricos isolados; emissor Prumo exclusivo por loja; importação C01, ingresso C02, elegibilidade C04, planos C05 e cancelamento C08 simulados com eventos e idempotência; nenhuma transmissão externa. S0 testes sintéticos; S1 operação humana/banco simulados; S2 IA/Meta simulados; S3 MCP controlado; S4 ativação real somente por autorização específica. Não há IA Analista autônoma. Nenhum dado cruza lojas.
