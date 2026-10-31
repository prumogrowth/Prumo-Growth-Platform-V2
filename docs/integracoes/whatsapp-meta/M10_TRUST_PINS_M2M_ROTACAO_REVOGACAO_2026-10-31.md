# M10 — Custódia de credenciais, trust anchors e principal M2M: escopo de laboratório

**Data:** 31/10/2026. **Estado:** controles de **pré-verificação offline** na frente Meta concluídos sob contrato proposto, **M10 permanece pendente** de identidade operacional S0, custódia Infra e ratificação humana. Nenhum token, chave privada, endpoint, envio ou credencial real foi criado.

## Decisões e dependências existentes (sem duplicatas)
- A [Issue canônica #2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2) já solicita a S0/S1 e Infra a autoridade do recibo Ed25519, principal M2M, trust anchor independente, rotação/revogação e política HTTP/ACK. O parecer da S0 é **técnico, laboratório apenas**, não aceite.
- A [Issue #8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8) solicita a fonte persistente de App/rota/WABA/número/canal, grants e revisão, além da custódia da referência de secret slots. A S0 publicou parecer preliminar, ainda sem cadastro/serviço operacional.
- A [Issue #4](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/4) exige reuso dessas solicitações, respostas na mesma Issue, sem autorização produtiva por comentário ou silêncio.

## Evidências próprias M10
- [`wa10-service-trust-pin-audit.ts`](../../../integrations/whatsapp-meta/wa10-service-trust-pin-audit.ts): verificador puro, sem I/O, que vincula um contexto de **serviço afirmado pelo host de testes** a um pin de chave pública Ed25519 e invoca o [verificador S0 lab já existente](../../../integrations/whatsapp-meta/cloud-s0-ed25519-receipt-interop.ts). **Não cria assinatura nova nem reinterpreta o contrato da S0.**
- [`wa10-service-trust-pin-audit.test.ts`](../../../integrations/whatsapp-meta/wa10-service-trust-pin-audit.test.ts): 39 ensaios adversariais com fixture assinada por Python/S0, mostrando seleção exata do pin e recusa após revogação, troca de contexto, chave falsificada, expiração, versão stale, duplicação de chaves/serviço, getter e entradas malformadas.
- [CI após hardening M10 — run 41212816731](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41212816731), código Meta `9c256e9b6c44f06059b14f4e2b176d17b31bf478`: 1.287/1.287 testes offline, incluindo 39 WA10, scanner de fontes aprovado; a confirmação de job físico fica sujeita ao resultado exibido pelo próprio GitHub Actions.

### Invariantes verificadas

1. **Pin não autorreferencial:** a chave de validação vem da registry passada por um host confiável, **não do corpo do recibo**. Mesmo um recibo Ed25519 sintético válido é negado quando há pin não correspondente, revogado, ainda STAGED, expirado ou com revisão errada.
2. **Separação de serviço e pessoa:** o contexto M2M de laboratório exige `principal_ref`, `issuer_ref`, `m2m_key_id`, revisão, App e `audience` explícitos. Não autoriza principal humano/IA e não usa um JWT de sessão de usuário.
3. **Rotação/revogação:** é possível representar janela controlada de duas chaves **distintas** ativas por App/instância quando identificadas por ID/revisão. Revogar a anterior nega seus recibos, ainda que a assinatura criptográfica continue correta. Reutilizar a mesma chave sob novo ID, inclusive na mesma loja, é negado como falsa rotação.
4. **Isolamento:** chaves públicas não podem ser cadastradas em mais de uma App; o mesmo `principal_ref` não pode pertencer a concessionárias/Apps diferentes no registro candidato. Duplicidade de registros ou campos extras contaminam o trust registry inteiro e geram recusa.
5. **Menor privilégio sem falsa autoridade:** mesmo quando a assinatura bate, a saída é `LAB_PIN_AND_RECEIPT_MATCHED_UNRATIFIED`, com `m2m_authenticated=false`, `key_custody_verified=false`, `pin_authority_ratified=false`, `production_authorized=false`, `ack_allowed=false`, `send_authorized=false` e `s0_write_authorized=false`.
6. **Minimização:** a decisão retorna só classificação e indicadores falsos de autoridade, sem expor chaves, escopos, número, nomes de slots ou credenciais.

## Fronteira de confiança — o que o laboratório NÃO prova

A registry `wa10-meta-service-trust.lab.v0.1-candidate` e o `Wa10HostContext` são **fixtures injetadas pelo mesmo ensaio**. Portanto, uma assinatura válida e a igualdade do contexto **não provam autenticação de principal M2M, autoridade de quem provisionou os pins, custódia/rotação em vault/KMS, ACL, correspondência com S0 produtiva ou titularidade Meta**. O runtime futuro **deve** autenticar o chamador, obter a registry de autoridade distinta do recibo/payload e aplicar revisão/revogação em fonte transacional antes de uso.

O preflight apenas compara metadados de principal e chaves públicas. Não interpreta recibos como `HTTP 200`, não autoriza retry, envio, implantação, credencial Meta de App nem operação S0.

## Critérios de aceite operacional ainda abertos

- [ ] S0/S1 identificar dono do emissor de recibos e serviço M2M, transportes/identidade e público-alvo; implementar autenticação real e revogação transacional com prova positiva/negativa.
- [ ] Infra/Proprietário ratificar autoridade de emissão e distribuição da **chave pública previamente confiada**, custódia da privada em KMS/HSM (ou solução formal aprovada), modelo de rotação de overlap, revogação emergencial, auditoria e prevenção de downgrade.
- [ ] Infra/Meta validar custódia segregada de GET verify token, POST App Secret e Graph access token, secret slot somente referencial, grants mínimos por App/tenant, inventário de provedor e renovação sem exposição em CI/Issues.
- [ ] S0/Meta comprovar divergência de revisão, race de revogação e recuperação após falha sem reutilização de permissão; regras de retenção, logs mínimos, disponibilidade e rollback de configuração.
- [ ] S0/Meta/Infra ratificar HTTP ACK na **#2**, e cadastro/grants na **#8**; revisar chave e contexto em ambiente de homologação autorizado. Nenhum aceite por silêncio, nenhuma ampliação de poderes.
- [ ] Apenas após as revisões, comprovar integração hospedada sob aprovação humana explícita. Não fechar M10 com base em fixtures.

**Conclusão:** este ciclo entrega prevenção offline de auto-pinning, falsa rotação e compartilhamento de principal, **sem estabelecer identidade operacional**. M10-A/B/C podem ser registrados como feitos no laboratório; M10-D e o marco M10 seguem abertos. Nenhuma escrita em S0/S1, alteração de Infra, Graph real, merge ou deploy.


## Adendo pós-vistoria de segurança — 31/10/2026

Os **39 testes M10** informados acima são o recorte histórico anterior à auditoria. A revisão encontrou e corrigiu arrays de pins/principais que ainda permitiam invocação de getters e listas esparsas. Foram adicionadas 3 regressões; a M10 tem agora **42 testes próprios**. [CI 41222509935](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41222509935): 1.344/1.344 Meta offline + 18 PG17, fonte funcional `60f789df841485e8cce41525f4517f00c6975e91`. [Auditoria unificada M01–M11](AUDITORIA_RETROSPECTIVA_M01_M11_2026-10-31.md). M10-D continua `[ ]`: nenhuma fixture comprova autenticação M2M ou custódia real.
