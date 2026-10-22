# WA-25 — Finalidades e concessões independentes para templates (candidato offline)

**Data:** 22/10/2026 · **Frente:** WhatsApp/Meta · **PR:** [#2 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2) · **Classe:** implementação técnica [T] parcial das decisões [D] WDC-10/WDC-11, sem autorização produtiva.

## 1. Regras aprovadas atendidas nesta etapa

Fonte: [00 — WDC-10/11](./00-decisoes-vigentes-precedencia-documental-2026-10-21.md), [01 — §§5–6](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md), [WA-22](./wa22-revisao-cruzada-outras-frentes-contratos-2026-10-22.md).

- **Categoria Meta (MARKETING/UTILITY)** continua separada da **FINALIDADE INTERNA** e da **finalidade de consentimento/opt-out**. O código não confunde essas três dimensões.
- Um template pode ter múltiplas finalidades. **Associação à finalidade não é concessão de uso**: cada autorização exige grant separado para finalidade, tipo e identidade do ator, fluxo e campanha exata, dentro da mesma concessionária e WABA.
- A função apenas reduz os **candidatos** disponíveis à F02. Não cria templates, não sugere promoções por si, não libera envio, não altera estados comerciais.
- Snapshots sem status Meta `APPROVED`, desativados localmente, de versão não atual, com idioma diferente ou revisão de catálogo divergente são recusados.
- IDs duplicados com versões concorrentes são retidos conservadoramente em vez de selecionar versão arbitrária. Campos inesperados, getters, autorias presumidas e claims de envio são negados.
- Rechecagem de candidato no catálogo/contexto **novo** antes de prosseguir; toda saída continua com `send_authorized:false` e `production_authorized:false`.

## 2. Arquivos e contrato entregues

- [`template-purpose-eligibility.ts`](../../../integrations/whatsapp-meta/template-purpose-eligibility.ts): `selectPlannerTemplateCandidates()` e `recheckPlannerTemplateCandidate()`, interfaces de contexto, associação `purpose_refs` e concessões `grants`; execução pura e **sem rede, SQL, tokens ou alteração comercial**.
- [`template-purpose-eligibility.test.ts`](../../../integrations/whatsapp-meta/template-purpose-eligibility.test.ts): 18 casos `WA25-01..18` para isolamento de loja/WABA, grants independentes, papéis/identidade, fluxo/campanha, status e versões, escopo, sanitização e recheck.
- Os snapshots e grants são **contratos candidatos**, não DDL nem API de autorização de S0 homologados. A categoria Meta foi limitada a MARKETING/UTILITY como subconjunto offline; categorias futuras requerem contrato/versionamento de capacidades.

## 3. Limites, dependências e próximos gates obrigatórios

**Ainda não implementado:** persistência N:N de finalidades/grants, identidade autenticada de serviço/ator, permissões e grants administrativos efetivos, elegibilidade de público, consentimento/opt-out real, verificação de campanha/oferta vigente, refresh de status Meta Graph e função autorizadora operacional. Não foram criadas tabelas nem alteradas frentes S0/OpenAI/S1/MCP.

A S0 deve fornecer snapshots confiáveis, com escopo, revisão de catálogo e identidade do ator efetivamente autenticados; origem dos valores **não pode ser IA nem frontend**. Validações devem ocorrer antes da F02, na reserva e imediatamente antes do dispatch. O mero fornecimento de um objeto tipado **não autentica** seu emissor. Para campanhas, um `campaign_ref` igual permite apenas uma *candidatura*, nunca prova de oferta válida. Nenhum consentimento é concedido por equivalência de template/finalidade.

**Acoplamento próximo:** integrar selector a um catálogo durável autorizado quando o contrato S0/Meta estiver ratificado, combinando prova de identidade/grants revogáveis, fontes elegíveis de campanhas, snapshots versionados e reserva/transmissão. Até lá, a API Graph continua sem autorização de envio.

## 4. Evidência de execução

- Primeiro commit do módulo `7cb91dafb5880f8728d5bbe6690d07bcff075e35`, testes iniciais `b671b3de5bb1f40b62b716930b03c727402ba678`.
- **Endurecimento WA25:** o seletor também retorna lista vazia, sem lançar exceções, diante de arrays com traps/Proxies hostis (`4403684ff307d98f00fcff2d56dd87cca2c4040f`); WA25-13 ganhou regressões adversariais (`b7b9aafc643c3d46ba6cdd1fd4fe4406a2e9c6ca`). Os 18 cenários originais continuam identificados.
- A primeira rodada teve **17/18 testes WA-25 aprovados**, um teste com defeito no auxiliar de valor padrão; **corrigido o teste** em `9fd68b42383649d7f1cec5ebe82ab69449f747ba`. Não foi um defeito de produção da função testada.
- Execução [GitHub Actions #39812930599](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39812930599), HEAD `9fd68b4...`: **3 jobs SUCCESS**, com Node 22 WA-16/17 **44/44 PASS**, regressão **541/541 PASS**, PostgreSQL 17 WA06D/WA15C/WA16B **PASS**. Essa execução antecede a defesa adicional de Proxy; toda alteração posterior exige nova execução em SHA correspondente.
- Resultado: **implementação parcial, validada em Node offline; não homologada em Meta, S0 produtivo, Banco ou LGPD.**

**Propriedade:** somente pasta `integrations/whatsapp-meta/` e documentação da própria frente. Nenhum merge/deploy, nenhuma credencial, nenhum envio real.
