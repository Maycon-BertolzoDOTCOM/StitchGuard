# Pesquisa de Convenções do Setor de Bordado (Brasil)

Consolidado a partir de buscas de mercado (2026). Objetivo: mapear convenções reais
para os presets (`domain/presets.py`), limites e catálogo (`domain/maquinas.py`)
do StitchGuard. Fontes anotadas em cada item.

---

## 1. Densidade de ponto

**Definição (galpaodasmaquinas.com.br/blog, Rodrigo Leal - Eng. Têxtil UFRN):**
densidade = quantidade de **pontos por centímetro (ppc)**. Afeta aparência, durabilidade
e resistência à lavagem. Densidade errada => bordado "pobre" (rala) ou "sobrecarregado".

**Por tecido (galpaodasmaquinas):**
| Tecido | Densidade |
|---|---|
| Seda / organza (leves) | Baixa (evita rasgo/deformação) |
| Algodão / jersey (médios) | Média |
| Jeans / lona (pesados) | Alta (permite mais detalhe) |

**Por técnica (galpaodasmaquinas):**
| Técnica | Densidade |
|---|---|
| Ponto cheio (satin) | Alta |
| Preenchimento (fill) | Média/Alta |
| Bordado intrincado | Média-Alta/Muito alta |

**Referência numérica (1001ferramentas.com — confiança baixa, mistura cross-stitch):**
grossa = 40, média = 80, fina = 120 pontos/cm². Fórmula `total = área(cm²) × densidade`.
No bordado digitalizado (Wilcom/PE-Design) a densidade é controlada por **espaçamento
entre passadas (mm/ponto)**, variando por tipo (fill/satin/running).

**Cross-check com fichas técnicas (matrizes.edmaisestudio.com — logomarcas, bastidor 10×10):**
| Matriz | Dim (mm) | Área (cm²) | Pontos | pts/cm² |
|---|---|---|---|---|
| Farmácia Popular | 42,8 × 78,8 | 33,7 | 7620 | ~226 |
| IFA Técnico | 85,6 × 93,3 | 79,9 | 7597 | ~95 |
| Fametro | 90,0 × 28,5 | 25,7 | 7931 | ~309 |
| C Técnica | 90,0 × 27,6 | 24,8 | 4432 | ~179 |
| Martha Falcão | 87,4 × 53,1 | 46,4 | 3265 | ~70 |

Obs.: logomarcas densas (tatami + satin + relevo) variam 70–300 pts/cm²; o número
"média ≈ 80" só encaixa nos casos leves. Para o StitchGuard o controle relevante é o
**espaçamento mm/ponto** já usado nos presets.

### Mapeamento p/ presets atuais
| Preset | Densidade (mm/passo) | Alinhamento com convenção |
|---|---|---|
| malha | 0,35–0,45 (fechada) | Consistente: jersey = densidade alta/média-alta |
| jeans | 0,40–0,50 | Consistente: jeans = pesado, suporta densa |
| nylon | 0,35–0,45 | OK (sintético solta ponto) |
| bone | 0,35–0,45 | OK (casquete firme) |
| cetim ralo/padrão/denso | 0,45–0,60 / 0,40–0,55 / 0,35–0,50 | Consistente com "seda/organza = baixa densidade" (passo maior). **TODO validar com ateliê.** |
| generico | 0,35–0,50 | Padrão neutro |

---

## 2. Tamanhos padrão e bastidores

**Bastidor padrão de matrizes (EdMais, matrizesparabordados.com.br, nataligabriela.com.br):**
- Padrão de mercado: **10×10 cm** (matrizes projetadas "para bastidor 10×10").
- Conjuntos vendidos em **10 tamanhos**: 10×10, 11×11, 12×12, 13×13, 14×14, 15×15,
  16×16, 13×18 e 16×26 cm.
- Bastidores inclusos em máquina doméstica Brother BP1530L: **13×18, 10×10, 16×26 cm**.

**Regra de qualidade (EdMais e mercado):** "Não é recomendado redimensionar as matrizes
para não comprometer a qualidade" — logo, redimensionamento tem custo de re-digitalização
(= regra de negócio p/ o orçamento, não validada no L4).

### Mapeamento p/ catálogo
- `generica` (aro 300×300) cobre folga o padrão 10×10..16×26. OK.
- Máquinas de aro pequeno (janome-mb-4 = 160, brother-pr1050x = 200) reprovam item 11
  para matrizes padrão — comportamento atual correto.
- Sugestão de melhoria futura: adicionar bastidores padrão por máquina (10×10, 13×18,
  16×26) como presets de `campo_*` no catálogo, refletindo os kits reais.

---

## 3. Ponto cheio (satin) — largura máxima

**hatch.embroideryhelp.net:** satin stitch máximo de **12,1 ou 12,7 mm** de largura,
variando por máquina/software.
**pixel2lines.com/pt:** ao ajustar cetim, conferir largura + espaçamento + underlay
(base) + compensação de tração + tensão em teste de costura.

### Mapeamento
- Catálogo usa `max_ponto_mm = 12.1` nas máquinas — alinhado ao limite de mercado.
- Item 5 (saltos) e limites de máquina já cobrem o caso; ponto satin de largura >12,7mm
  é problema de **geração** (L3), não de validação — registrar como regra futura de L3.

---

## 4. Precificação e orçamento (mercado BR)

**Programação de matriz (matrizbordados.com.br, 2025/26):** R$ 40,00 a R$ 100,00
conforme complexidade, cobrada à parte do bordado.

**Tabela de preço do bordado por nº de pontos (matrizbordados.com.br):**
| Nº de pontos | R$/ponto | Valor unitário |
|---|---|---|
| 01 – 1.500 | 0,0054 | R$ 8,00 |
| 1.501 – 3.000 | 0,0034 | R$ 10,00 |
| 3.001 – 4.500 | 0,0028 | R$ 12,00 |
| 4.501 – 6.000 | 0,0025 | R$ 15,00 |
| 6.001 – 8.000 | 0,0022 | R$ 17,60 |
| 8.001 – 10.000 | 0,0020 | R$ 20,00 |
| 10.001 – 15.000 | 0,0015 | R$ 22,50 |
| 15.001 – 20.000 | 0,0013 | R$ 25,75 |
| 20.001 – 25.000 | 0,0012 | R$ 29,00 |
| 25.001 – 30.000 | 0,0011 | R$ 32,00 |
| 30.001 – 35.000 | 0,0010 | R$ 35,00 |
| 35.001 – 40.000 | 0,00095 | R$ 38,00 |
| 40.001 – 45.000 | 0,00092 | R$ 41,00 |
| 45.001 – 50.000 | 0,00090 | R$ 44,00 |
| 50.001 – 55.000 | 0,00086 | R$ 47,00 |
| 55.001 – 60.000 | 0,00084 | R$ 50,00 |

Ex.: 4.902 pts × 0,0025 = **R$ 12,25**.
Tabela já inclui linha, agulhas, entretela, depreciação, energia e horas de trabalho.
**Matriz cobrada à parte.** Margem de lucro recomendada: 30%–100%.

**Fórmula sugerida (scribd, GUIA-PRATICO):**
`preço = (mil pontos × R$/mil) + materiais + criação da matriz + margem de lucro`.

**Preço de matrizes prontas (mercado):** R$ 7,00 (lunala) a R$ 24,99 (EdMais brasões);
a maioria R$ 9,50–19,99. Concorrente com precificação por IA: matrizdobordado.com.br.

### Implicações p/ StitchGuard
- `limite_pontos` dos presets (15k bone … 50k genérico) alinha com a faixa da tabela
  (até 60k), que cobre o mercado de peças avulsas.
- Regra de negócio futura (commercial/orçamento): usar a tabela R$/ponto para precificar
  o bordado e a faixa R$40–100 para a digitalização. Não é validação L4.
- Otimização de saltos (L3→L4) reduz tempo de máquina → reduz custo por peça.

---

## 5. Formatos e compatibilidade de máquinas

**Convenção de formatos por marca (EdMais, comunidadedobordado.com):**
| Formato | Máquinas |
|---|---|
| PES | Brother, Babylock |
| JEF | Janome, Elna, Kenmore |
| XXX | Singer, Cantor |
| DST | Tajima e máquinas industriais (e "todas") |
| EXP | Bernina, Melco |
| HUS | Husqvarna |

**Compatibilidade testada (EdMais):** Brother, Janome, Singer, Tajima, Barudan.
**Tecidos citados em fichas:** Gabardine, Brim, Sarja, Malha Piquet.

### Mapeamento
- Catálogo `formato_nativo` (dst/pes/jef…) segue a convenção acima. Consistente.
- Fichas reforçam a escolha **DST como formato universal** da `generica`.

---

## 6. Velocidade e produção

- Brother BP1530L (doméstica): **850 ppm**, área máx 160×260 mm.
- Bordado industrial: velocidade mais alta, maior controle de densidade
  (galpaodasmaquinas).
- Tempo por peça é insumo do custo (pts ÷ ppm) — base para orçamento.

---

## 7. Pendências de pesquisa (não bloqueantes)

- Densidade numérica típica em pts/cm² para digitalização BR é difusa nos sites;
  referências confiáveis pedem validação com digitalizador humano/ateliê (pendência A de
  `PENDENCIAS_EXTERNAS.md`).
- Tabelas de preço variam por região/ateliê; a tabela acima é uma referência 2025/26,
  atualizada anualmente pelo autor.
