# Prumo Growth — Coordenação S0 (Codex) e S1-002

Data de registro: 26/10/2026. Atualização de responsabilidades comunicada pelo responsável pelo projeto.

## Autoridade e propriedade

- **S0 (núcleo/domínio comercial)**: Codex é o responsável principal pelo desenvolvimento e pela coordenação de mudanças no núcleo oficial.
- **S1-002 (Equipe Prumo)**: segue desenvolvendo e validando autorização, hierarquia, equipe, gestão e operações correlatas **somente** em `feat/s1-002-equipe-prumo`.
- **Domínio S0 permanece canônico**: a S1 não assume propriedade de clientes, contatos, casos, conversas, lotes, atribuições nem relações comerciais.
- O trabalho das demais frentes, os PRs e os incrementos existentes continuam válidos e devem ser considerados pelo Codex na integração coordenada.

## Novo protocolo para dependências S0

Quando um incremento S1-002 exigir alteração no domínio S0:

1. Recuperar o HEAD e contratos atuais do núcleo S0 e verificar possíveis avanços do Codex ou propostas concorrentes.
2. Implementar a **proposta isoladamente** na branch da S1-002 quando necessário para provar o comportamento, sem incorporação ao núcleo oficial.
3. Adicionar regressões proporcionais de S0+S1, dados sintéticos e evidências de CI; diferenciar fixture experimental de migration oficial.
4. Documentar **contratos afetados, caminhos/arquivos alterados, razão da mudança, compatibilidade, riscos, dependências, cobertura de testes e pontos de conflito com o Codex**.
5. Encaminhar a proposta para **revisão e coordenação da frente S0** antes de qualquer incorporação ao núcleo, merge, implantação ou promoção das mudanças. Não assumir aprovação implícita por testes verdes.
6. Manter intactos os PRs, artefatos e commits já existentes; não apagar, sobrepor nem duplicar progresso válido de outras frentes.

## Restrições operacionais

- Não modificar a `main`, outras branches, ambiente hospedado ou produção sem autorização explícita.
- Não executar a Issue #3 como otimização implícita.
- Não transformar mudanças experimentais S0 em migrations de produção nem incorporar automaticamente à linha canônica.
- Uma dependência S0 não bloqueia a continuidade da S1 quando testes locais isolados permitem avanço seguro; conflito não resolvido deve ser registrado como pendência de integração.
- O último marco conhecido ao registrar este documento é **I73**, certificado em laboratório no commit `3cfa2b77c733fd36f1284e3adfd45fa198720162`. Este registro é apenas de governança: não altera código, testes, autorização ou critérios de certificação.

## Próxima frente técnica

A candidata I74 poderá estudar assinatura independente, nonce e defesa contra replay no executor de exportação, preservando a fronteira S0. Qualquer mudança que precise tocar contratos ou código do núcleo S0 seguirá o protocolo de proposta isolada descrito acima.
