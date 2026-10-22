# S1-002 — decisão de nomenclatura dos perfis (21/10/2026)

**[D] Decisão expressa de produto — vigente na nomenclatura; mudança de estrutura técnica ainda não autorizada/realizada.**

## Nomes oficiais

| Denominação anterior | Denominação oficial a partir desta decisão | Equivalência |
| --- | --- | --- |
| Responsável / responsável da plataforma | **Diretor** | Mesmo perfil e mesmas competências do responsável atual |
| Gestor | **Gestor** | Sem mudança de nome |
| Operador | **Consultor** | Mesmo perfil e mesmas competências do operador atual |

**A mudança é terminológica, não uma alteração de autoridade, governança, concessões ou RLS.** Em especial:
- **Diretor** exerce as atribuições anteriormente reservadas ao *responsável da plataforma*, incluindo administração de contas de profissionais e concessões por concessionária, nos limites das regras de negócio vigentes.
- **Gestor** continua coordenando a própria equipe, supervisionando e transferindo atendimentos nas condições aprovadas; não recebe poderes exclusivos de diretor por causa da renomeação.
- **Consultor** continua realizando os atendimentos atribuídos, podendo consultar o histórico autorizado do próprio contato na mesma concessionária, mas sem acesso deliberado à carteira de colegas, conforme decisões específicas de atendimento e supervisão.

## Precedência, compatibilidade e alcance

1. **Em novos textos normativos da S1-002, empregar `diretor / gestor / consultor`.** Qualquer ocorrência de `responsável` ou `operador` como nome de papel em registros antigos deve ser lida com o mapeamento acima; tais arquivos são preservados como histórico, não reescritos indiscriminadamente.
2. **A equivalência não justifica migração imediata** de IDs, nomes de tabelas, funções SQL, enums, JWT claims, chaves de API, rotas, testes ou RLS. Até existir plano de migração e auditoria de compatibilidade, identificadores técnicos existentes permanecem os mesmos; o nome antigo em código não constitui perfil adicional.
3. A terminologia da experiência visual deverá ser alinhada com a frente de frontend em etapa própria. O registro desta decisão na S1 **não afirma** que a interface já tenha sido modificada.
4. A atualização semântica é aplicável às referências de papéis em decisões de negócio pertinentes à LiberaCred/Prumo; cada frente deve conciliar seu próprio contrato antes de mudar a implementação.
5. Esta decisão **não fecha questões pendentes** sobre primeiro contato humano, transferência manual para destinatário pausado ou permissões sensíveis de supervisão. Essas decisões permanecem independentes.
6. Para busca e interpretação da documentação, manter os pares de termos: `diretor (antigo responsável)`, `consultor (antigo operador)`. Isso preserva rastreabilidade e evita interpretar o mesmo perfil como dois papéis distintos.

## Referências relacionadas

- [Issue #10 — pausa de ingresso e gestão de equipe](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/10).
- [Regra vigente sobre a pausa](S1_002_ISSUE10_CORRECAO_PAUSA_INTAKE_2026_10_20.md).
- [Histórico I11 de gestão por equipe](S1_002_I11_GESTAO_POR_EQUIPE_PAUSA_GLOBAL_2026_10_19.md).
- [Marco de auditoria e consolidação](S1_002_MARCO_PAUSA_ALINHAMENTO_AUDITORIA_DOCUMENTOS_2026_10_20.md).

**Status operacional:** decisão documental publicada na branch S1-002; nenhuma mudança funcional, migration, merge, deploy ou Supabase hospedado decorre deste registro.

## Identidade do produto comercial versus software — reafirmação [D] de 22/10/2026

**Libera Credi (também grafado LiberaCred em documentos históricos) é o produto de crédito da instituição financeira; NÃO é o nome da plataforma que estamos criando.** Enquanto a marca da aplicação não for escolhida, usar **plataforma** ou **plataforma de atendimento e vendas** em textos novos. Referências a LiberaCred só quando se tratar do produto financeiro promovido/comercializado, de regras bancárias ou de citações históricas. Não converter a Prumo, que aparece como operação/empresa em contratos, em nome oficial da aplicação por inferência.

Essa separação já constava no doc. 17 do pacote histórico de 17/10 e está reafirmada em [auditoria cruzada de 22/10](S1_002_AUDITORIA_CRUZADA_FRENTES_CONTRATOS_2026_10_22.md), seção 0. Não é renomeação técnica ou mudança de contrato com a instituição financeira.
