# Datasets para StitchGuard

## MSEmbGAN Dataset

**Descrição:** 30.000+ imagens de bordado com anotações de tipos de ponto.

**Fonte:** Universidade Têxtil de Wuhan (Professor Hu Ximrong)

**Conteúdo:**
- `images/embroidery/` - Imagens finais de bordado
- `images/content/` - Imagens de conteúdo original (arte de entrada)
- `annotations/` - Anotações de ponto único e múltiplos pontos

**Uso no StitchGuard:**
1. Treinar classificador de tipos de ponto (satin, fill, running)
2. Criar sistema de recomendação de parâmetros
3. Validar modelos contra benchmark acadêmico

**Como baixar:**
```bash
# Baixa tudo
python datasets/download_msembgan.py --output ./datasets

# Apenas estrutura (sem download)
python datasets/download_msembgan.py --skip-download
```

**Formato das anotações:**
```json
{
  "image_id": "00001",
  "stitch_types": ["satin", "fill", "running"],
  "regions": [
    {"type": "satin", "bbox": [x, y, w, h]},
    {"type": "fill", "bbox": [x, y, w, h]}
  ]
}
```

## Embroidery Streamlines

**Descrição:** Pesquisa da Universidade de Hong Kong sobre streamlines de bordado.

**Fonte:** embroidery-streamlines (GitHub)

**Conteúdo:**
- `samples/` - Exemplos de bordado
- `models/` - Modelos treinados

**Uso no StitchGuard:**
- Referência para algoritmos de geração de caminhos
- Base para futuras implementações de IA

## Processed

Dados processados para treinamento:
- `classifier/` - Dados para classificador de tipos de ponto
- `recommender/` - Dados para recomendador de parâmetros

## Dados Proprietários (futuro)

Com o StitchGuard em produção, coletaremos:
- Parâmetros reais usados por tecido
- Resultados de validação
- Feedback do clientes

Meta: 500-1.000 matrizes reais para dataset proprietário.
