# StitchGuard vs Wilcom — Análise de Equivalência

> **Documento de referência:** Comparação entre as capacidades do Wilcom EmbroideryStudio
> e o que o StitchGuard implementa atualmente.

## Resumo Executivo

| Capacidade | Wilcom | StitchGuard | Gap |
|------------|--------|-------------|-----|
| **Digitalização automática (IA)** | ✅ Instant Intelligent Auto-Digitizing | ✅ cli_anything (pyembroidery) | 🟡 Wilcom mais avançado |
| **Edição de pontos** | ✅ Controle granular completo | ✅ 7 operações pós-edição | 🟡 Wilcom mais completo |
| **Validação** | ✅ Manual (humano) | ✅ 11 itens automáticos | ✅ StitchGuard superior |
| **Formatos** | ✅ 70+ formatos | ✅ DST/PES/EXP via pyembroidery | 🟡 Wilcom mais amplo |
| **API/Automação** | ✅ Wilcom Automation | ✅ REST API completa | ✅ Equivalente |
| **Cloud** | ✅ WilcomWorkspace | ✅ Docker + S3 | ✅ Equivalente |
| **Gestão de jobs** | ❌ Não possui | ✅ Fila + polling + auth | ✅ StitchGuard superior |
| **Billing** | ❌ Não possui | ✅ Asaas integrado | ✅ StitchGuard superior |
| **Laudo técnico** | ❌ Não possui | ✅ HTML/PDF com scores | ✅ StitchGuard superior |

---

## 1. Digitalização Automática (IA)

### Wilcom
- **Instant Intelligent Auto-Digitizing**: Converte imagens em bordado automaticamente
- Algoritmo proprietário otimizado para bordado comercial
- Resultado: rascunho em ~2 minutos

### StitchGuard
- **cli_anything**: Usa pyembroidery para converter JSON → .DST
- Suporta: retângulos, círculos, polígonos
- **image_processor**: Converte SVG/PNG → pontos
- Resultado: rascunho em ~1 segundo

### Avaliação
| Critério | Wilcom | StitchGuard |
|----------|--------|-------------|
| Velocidade | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Qualidade do rascunho | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Formatos de entrada | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Customização | ⭐⭐⭐ | ⭐⭐⭐⭐ |

**Conclusão:** Wilcom tem qualidade superior, mas StitchGuard é mais rápido e flexível para automação.

---

## 2. Edição de Pontos

### Wilcom
- Controle granular sobre densidade, compensação, underlay
- Tipos de preenchimento: satin, fill, running, motif
- Efeitos 3D (puff)
- 240+ fontes profissionais
- Integração com CorelDRAW

### StitchGuard (Pós-Editor)
- **7 operações:**
  1. `compensacao_pull` — Desloca pontos perpendicularmente
  2. `ajustar_densidade` — Reamostra pontos
  3. `reordenar_blocos` — Reordena sequência de costura
  4. `inserir_ponto` — Adiciona ponto em posição específica
  5. `remover_ponto` — Remove ponto por índice
  6. `adicionar_underlay` — Adiciona pontos de suporte
  7. `remover_underlay` — Remove pontos de suporte

### Avaliação
| Critério | Wilcom | StitchGuard |
|----------|--------|-------------|
| Número de ferramentas | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Controle granular | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Facilidade de uso | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Automação | ⭐⭐ | ⭐⭐⭐⭐⭐ |

**Conclusão:** Wilcom é mais completo para edição manual. StitchGuard é melhor para automação em massa.

---

## 3. Validação

### Wilcom
- Validação manual (humano abre o arquivo e verifica)
- Sem checklist automatizado
- Depende da experiência do digitador

### StitchGuard
- **Checklist 11 itens automáticos:**
  1. Tipo de tecido
  2. Compensação
  3. Amarração (underlay)
  4. Densidade
  5. Saltos
  6. Ordem de costura
  7. Ângulos do satin
  8. Nós (lock stitch)
  9. Limite de pontos
  10. Limite de cores
  11. Cabe no aro
- **Score global** com threshold 0.85
- **Laudo técnico** HTML/PDF

### Avaliação
| Critério | Wilcom | StitchGuard |
|----------|--------|-------------|
| Automatização | ⭐ | ⭐⭐⭐⭐⭐ |
| Confiabilidade | ⭐⭐⭐ (humano) | ⭐⭐⭐⭐ (IA + humano) |
| Rastreabilidade | ⭐ | ⭐⭐⭐⭐⭐ |
| Documentação | ⭐⭐ | ⭐⭐⭐⭐⭐ |

**Conclusão:** StitchGuard é **muito superior** em validação automatizada.

---

## 4. Formatos Suportados

### Wilcom
- 70+ formatos: DST, PES, EXP, HUS, VIP, XXX, JEF, SEW, etc.
- Leitura e escrita de todos os formatos

### StitchGuard (via pyembroidery)
- DST, PES, EXP, HUS, VIP, XXX, JEF, SEW, etc.
- Foco em DST para produção
- Conversão via pyembroidery

### Avaliação
| Critério | Wilcom | StitchGuard |
|----------|--------|-------------|
| Número de formatos | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Qualidade da conversão | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Facilidade | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**Conclusão:** Wilcom tem mais formatos, mas StitchGuard cobre os principais.

---

## 5. Automação e APIs

### Wilcom
- **Wilcom Automation**: APIs para criar, converter e gerenciar designs
- Requer licença do Wilcom
- Foco em integração desktop

### StitchGuard
- **REST API completa** (21 endpoints)
- JWT Auth
- Webhooks
- Docker ready
- Integração com qualquer sistema

### Avaliação
| Critério | Wilcom | StitchGuard |
|----------|--------|-------------|
| API REST | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Autenticação | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Documentação | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Facilidade de integração | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**Conclusão:** StitchGuard é **muito superior** para automação via API.

---

## 6. Gestão e Business

### Wilcom
- Foco em ferramentas de design
- Não possui: gestão de jobs, billing, auth, laudo

### StitchGuard
- **Gestão completa:** jobs, fila, polling, auth
- **Billing:** Asaas integrado (Pix/Boleto)
- **Laudo técnico:** HTML/PDF com scores
- **Feedback:** Aprovação/rejeição do cliente

### Avaliação
| Critério | Wilcom | StitchGuard |
|----------|--------|-------------|
| Gestão de jobs | ⭐ | ⭐⭐⭐⭐⭐ |
| Billing | ⭐ | ⭐⭐⭐⭐⭐ |
| Auth/Multi-tenancy | ⭐ | ⭐⭐⭐⭐⭐ |
| Documentação | ⭐⭐ | ⭐⭐⭐⭐⭐ |

**Conclusão:** StitchGuard é **muito superior** para gestão e negócio.

---

## 7. Arquitetura Comparada

```
WILCOM (Desktop)                    STITCHGUARD (Cloud)
─────────────────                   ───────────────────
Arte → Wilcom Desktop               Arte → API REST
  ↓                                   ↓
Auto-Digitizing (IA)                cli_anything (pyembroidery)
  ↓                                   ↓
Edição manual                       Pós-editor (7 operações)
  ↓                                   ↓
Validação (humano)                  Checklist 11 itens (IA)
  ↓                                   ↓
Exportar .DST                       Gerar .DST + Laudo
  ↓                                   ↓
Entrega manual                      Entrega automática + Billing
```

---

## 8. Recomendação para o StitchGuard

### Curto Prazo (MVP)
1. **Manter foco em automação** — StitchGuard já é superior em validação e gestão
2. **Melhorar cli_anything** — Adicionar mais tipos de formas e fontes
3. **Integrar com Wilcom** — Como provedor opcional (costTier 1)

### Médio Prazo
1. **Adicionar fontes** — Biblioteca de fontes de bordado (Hershey, etc.)
2. **Melhorar image_processor** — Mais tipos de arte (curvas, texto)
3. **Dashboard web** — Interface para clientes

### Longo Prazo
1. **Wilcom Automation** — Integrar APIs do Wilcom (quando disponível)
2. **ML/Treinamento** — Usar dataset MSEmbGAN para treinar classificador
3. **Multi-máquina** — Suporte a múltiplas máquinas simultaneamente

---

## 9. Conclusão

### O que StitchGuard JÁ FAZ melhor que Wilcom:
- ✅ Validação automatizada (11 itens vs. manual)
- ✅ Gestão de jobs e fila
- ✅ Billing e cobrança
- ✅ Laudo técnico documentado
- ✅ API REST completa
- ✅ Auth e multi-tenancy
- ✅ Deploy em cloud

### O que Wilcom FAZ melhor que StitchGuard:
- ✅ Qualidade de digitalização (IA proprietária)
- ✅ Mais formatos de arquivo
- ✅ Mais fontes e motivos
- ✅ Edição visual (GUI)

### Estratégia Recomendada
**Não competir com Wilcom em edição de pontos.** Em vez disso:
1. Usar **cli_anything** para rascunho rápido
2. Usar **pós-editor** para ajustes automáticos
3. Usar **checklist** para validação
4. Usar **Wilcom** como provedor opcional para casos complexos
5. Focar em **automação, gestão e negócio** (onde StitchGuard já é superior)

---

*Documento gerado em Ago/2026 — StitchGuard v0.2.0*
