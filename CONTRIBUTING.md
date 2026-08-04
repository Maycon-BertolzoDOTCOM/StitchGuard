# Contribuindo para o StitchGuard

Obrigado por contribuir com o StitchGuard!

## Guia Rápido

1. Faça o fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Faça suas alterações
4. Execute os testes (`make test`)
5. Faça o commit (`git commit -m 'feat: adiciona nova feature'`)
6. Push para a branch (`git push origin feature/nova-feature`)
7. Abra um Pull Request

## Desenvolvimento

### Setup

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/StitchGuard.git
cd StitchGuard

# Execute o setup
./setup.sh

# Ative o venv
source venv/bin/activate
```

### Comandos Úteis

```bash
make help        # Mostra todos os comandos
make test        # Executa testes
make lint        # Verifica código
make run         # Inicia API
make docker      # Sobe com Docker
```

### Estrutura do Projeto

```
StitchGuard/
├── application/     # API FastAPI (L1)
├── domain/         # Regras de negócio (L2)
├── generation/     # Geração de .dst (L3)
├── validation/     # Checklist (L4)
├── commercial/     # Billing (L5)
├── infra/          # Storage e fila (L6)
├── post_editor/    # Pós-edição
├── laudo/          # Laudo técnico
├── tests/          # Testes
└── scripts/        # Scripts auxiliares
```

### Convenções

- **Commits**: Use [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat:` nova funcionalidade
  - `fix:` correção de bug
  - `docs:` documentação
  - `test:` testes
  - `refactor:` refatoração

- **Código**: Siga PEP 8
  - Use `ruff` para lint
  - Max 88 caracteres por linha
  - Docstrings em português

- **Testes**: Escreva testes para todas as funcionalidades
  - Testes unitários em `tests/`
  - Use pytest
  - Mantenha cobertura > 80%

### Branches

- `master`: Produção estável
- `develop`: Desenvolvimento
- `feature/*`: Novas funcionalidades
- `fix/*`: Correções de bugs
- `release/*`: Preparação para release

### Pull Requests

- Título claro e descritivo
- Descreva as mudanças
- Referencie issues relacionadas
- Inclua testes se aplicável
- Certifique-se que CI passa

### Issues

Use as issues para:
- Reportar bugs
- Sugerir funcionalidades
- Discutir mudanças
- Fazer perguntas

## Perguntas?

Abra uma issue ou entre em contato!
