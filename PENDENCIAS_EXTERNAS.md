# Pendências Externas — StitchGuard

Categorização por "quem desbloqueia" (todos atualmente pendentes).

## A) Dados do ateliê (fornecidos pelo dono do ateliê — Maycon)

| Pendência | Onde | Status |
|---|---|---|
| **Marca/modelo da máquina do ateliê** (formato, agulhas, campo, trim) | `domain/maquinas.py` + `domain/questionario_maquina.py` | **Questionário criado. Aguardando preenchimento** |
| Validação real dos presets (densidade cetim, compensações) com ateliê | `domain/presets.py:76` TODO | Aberto |
| Densidades/limites reais por tecido (toalha, fralda do Danilo) | `domain/presets.py` | Aberto |

## B) Instalação externa (software na máquina de dev)

| Pendência | Onde | Status |
|---|---|---|
| Ink/Stitch CLI (exige Inkscape — GUI, frágil em headless) | `generation/providers/inkstitch.py` | Hook pendente (contornado por cli_anything interno) |

## C) Conta/credencial (chaves, OAuth, secrets)

| Pendência | Onde | Status |
|---|---|---|
| Asaas API key + `ASAAS_WEBHOOK_SECRET` (sandbox) | `commercial/asaas.py` | Pendente |
| Google Drive OAuth | `commercial/entrega.py` | Pendente |
| SMTP (email de entrega) | `commercial/entrega.py` | Pendente |
| Trello API (fila MVP) | `infra/fila.py` | Pendente |
| Colar chave SSH pública no GitHub + host alias `github.com-stitchguard` | `~/.ssh/` | Chave criada, não colada |

## D) Terceiros pagos / humanos / infra futura

| Pendência | Onde | Status |
|---|---|---|
| Wilcom APIs (cost 1, dificuldade `high`) | `generation/providers/wilcom.py` | Pendente |
| Digitador humano (fallback — sistema de tickets) | `generation/providers/humano.py` | Pendente |
| Postgres/Redis, deploy (Docker/Vercel) | `infra/` | Futuro |

---

**Nenhuma pendência bloqueante para o núcleo atual:** geração, validação e otimização já funcionam de ponta a ponta.
