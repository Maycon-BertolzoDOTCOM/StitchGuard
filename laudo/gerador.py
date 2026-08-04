"""Laudo técnico — geração de PDF com resultados de validação.

Gera um documento HTML que pode ser impresso como PDF.
Inclui:
- Dados do job (data, tecido, máquina)
- Checklist 11 itens com scores
- Gráfico de barras visual
- Recomendações automáticas
- Código QR para preview SVG
"""
import datetime
import os
import uuid


def _cor_score(score: float | None) -> str:
    """Retorna cor baseada no score."""
    if score is None:
        return "#9CA3AF"  # cinza (pendente)
    if score >= 0.85:
        return "#10B981"  # verde (aprovado)
    if score >= 0.5:
        return "#F59E0B"  # amarelo (atenção)
    return "#EF4444"  # vermelho (reprovado)


def _status_texto(score: float | None) -> str:
    """Retorna texto descritivo do score."""
    if score is None:
        return "Pendente"
    if score >= 0.85:
        return "Aprovado"
    if score >= 0.5:
        return "Atenção"
    return "Reprovado"


def _barra_html(score: float | None, largura: int = 100) -> str:
    """Gera barra de progresso HTML."""
    if score is None:
        return f'<div style="width:{largura}px;height:16px;background:#E5E7EB;border-radius:8px;"></div>'
    pct = int(score * largura)
    cor = _cor_score(score)
    return f'<div style="width:{largura}px;height:16px;background:#E5E7EB;border-radius:8px;overflow:hidden;"><div style="width:{pct}px;height:100%;background:{cor};"></div></div>'


def gerar_laudo_html(
    job_id: str,
    resultado: dict,
    validacoes: list[dict] | None = None,
    operacoes_edicao: list[str] | None = None,
    stats_editado: dict | None = None,
) -> str:
    """Gera HTML do laudo técnico.

    Args:
        job_id: identificador do job
        resultado: dict com resultado do pipeline (score_global, itens, resumo, etc.)
        validacoes: lista de validações do banco (opcional)
        operacoes_edicao: operações de pós-edição aplicadas (opcional)
        stats_editado: estatísticas após edição (opcional)

    Returns:
        HTML completo do laudo
    """
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    score_global = resultado.get("score_global", 0.0)
    aprovado = resultado.get("aprovado", False)
    resumo = resultado.get("resumo", {})
    itens = resultado.get("itens", {})

    # Montar linhas da tabela de itens
    linhas_tabela = ""
    for nome, item in itens.items():
        score = item.get("score")
        cor = _cor_score(score)
        status = _status_texto(score)
        detalhe = item.get("detalhe", "")
        barra = _barra_html(score)

        linhas_tabela += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #E5E7EB;">{nome}</td>
            <td style="padding:8px;border-bottom:1px solid #E5E7EB;text-align:center;">
                <span style="color:{cor};font-weight:bold;">{score if score is not None else '—'}</span>
            </td>
            <td style="padding:8px;border-bottom:1px solid #E5E7EB;text-align:center;">
                <span style="color:{cor};">{status}</span>
            </td>
            <td style="padding:8px;border-bottom:1px solid #E5E7EB;">{barra}</td>
            <td style="padding:8px;border-bottom:1px solid #E5E7EB;font-size:12px;">{detalhe}</td>
        </tr>
        """

    # Seção de edição (se aplicavel)
    secao_edicao = ""
    if operacoes_edicao:
        ops_html = ", ".join(operacoes_edicao)
        stats_html = ""
        if stats_editado:
            stats_html = f"""
            <p><strong>Pontos após edição:</strong> {stats_editado.get('pontos', '—')}</p>
            <p><strong>Dimensões:</strong> {stats_editado.get('largura_mm', '—')} x {stats_editado.get('altura_mm', '—')} mm</p>
            """
        secao_edicao = f"""
        <div style="margin-top:24px;padding:16px;background:#F0F9FF;border-radius:8px;border:1px solid #BAE6FD;">
            <h3 style="margin:0 0 8px 0;color:#0369A1;">Edição Aplicada</h3>
            <p><strong>Operações:</strong> {ops_html}</p>
            {stats_html}
        </div>
        """

    # Recomendações
    recomendacoes = []
    if not aprovado:
        for nome, item in itens.items():
            if item.get("score") is not None and item["score"] < 0.85:
                recomendacoes.append(f"- {nome}: {item.get('detalhe', '')}")

    secao_recomendacoes = ""
    if recomendacoes:
        rec_html = "<br>".join(recomendacoes)
        secao_recomendacoes = f"""
        <div style="margin-top:24px;padding:16px;background:#FEF3C7;border-radius:8px;border:1px solid #FCD34D;">
            <h3 style="margin:0 0 8px 0;color:#92400E;">Recomendações</h3>
            <p style="margin:0;">{rec_html}</p>
        </div>
        """

    # URL do preview
    preview_url = f"https://stitchguard.com.br/v1/preview/{job_id}"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Laudo Técnico — StitchGuard — Job {job_id}</title>
    <style>
        @media print {{
            body {{ font-size: 10pt; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body style="font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:24px;color:#1F2937;">

    <!-- Cabeçalho -->
    <div style="text-align:center;border-bottom:2px solid #2563EB;padding-bottom:16px;margin-bottom:24px;">
        <h1 style="margin:0;color:#2563EB;">StitchGuard</h1>
        <p style="margin:4px 0 0 0;color:#6B7280;">Laudo Técnico de Validação de Matriz de Bordado</p>
    </div>

    <!-- Dados do Job -->
    <div style="display:flex;justify-content:space-between;margin-bottom:24px;">
        <div>
            <p style="margin:4px 0;"><strong>Job ID:</strong> {job_id}</p>
            <p style="margin:4px 0;"><strong>Data:</strong> {agora}</p>
        </div>
        <div style="text-align:right;">
            <p style="margin:4px 0;"><strong>Score Global:</strong>
                <span style="font-size:24px;font-weight:bold;color:{_cor_score(score_global)};">{score_global:.2f}</span>
            </p>
            <p style="margin:4px 0;">
                <span style="padding:4px 12px;border-radius:4px;background:{'#10B981' if aprovado else '#EF4444'};color:white;font-weight:bold;">
                    {'APROVADO' if aprovado else 'REPROVADO'}
                </span>
            </p>
        </div>
    </div>

    <!-- Resumo -->
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px;">
        <div style="padding:12px;background:#F3F4F6;border-radius:8px;text-align:center;">
            <p style="margin:0;font-size:24px;font-weight:bold;color:#2563EB;">{resumo.get('pontos', '—')}</p>
            <p style="margin:4px 0 0 0;font-size:12px;color:#6B7280;">Pontos</p>
        </div>
        <div style="padding:12px;background:#F3F4F6;border-radius:8px;text-align:center;">
            <p style="margin:0;font-size:24px;font-weight:bold;color:#2563EB;">{resumo.get('largura_mm', '—')}x{resumo.get('altura_mm', '—')}</p>
            <p style="margin:4px 0 0 0;font-size:12px;color:#6B7280;">mm</p>
        </div>
        <div style="padding:12px;background:#F3F4F6;border-radius:8px;text-align:center;">
            <p style="margin:0;font-size:24px;font-weight:bold;color:#2563EB;">{resumo.get('passo_medio_mm', '—')}</p>
            <p style="margin:4px 0 0 0;font-size:12px;color:#6B7280;">mm/ponto</p>
        </div>
    </div>

    <!-- Checklist -->
    <h2 style="color:#1F2937;border-bottom:1px solid #E5E7EB;padding-bottom:8px;">Checklist de Validação (11 itens)</h2>
    <table style="width:100%;border-collapse:collapse;margin-top:12px;">
        <thead>
            <tr style="background:#F9FAFB;">
                <th style="padding:8px;text-align:left;border-bottom:2px solid #E5E7EB;">Item</th>
                <th style="padding:8px;text-align:center;border-bottom:2px solid #E5E7EB;">Score</th>
                <th style="padding:8px;text-align:center;border-bottom:2px solid #E5E7EB;">Status</th>
                <th style="padding:8px;text-align:center;border-bottom:2px solid #E5E7EB;">Barra</th>
                <th style="padding:8px;text-align:left;border-bottom:2px solid #E5E7EB;">Detalhe</th>
            </tr>
        </thead>
        <tbody>
            {linhas_tabela}
        </tbody>
    </table>

    <!-- Edição -->
    {secao_edicao}

    <!-- Recomendações -->
    {secao_recomendacoes}

    <!-- QR Code / Link -->
    <div style="margin-top:24px;text-align:center;padding:16px;background:#F9FAFB;border-radius:8px;">
        <p style="margin:0 0 8px 0;font-size:12px;color:#6B7280;">Preview visual desta matriz:</p>
        <p style="margin:0;"><a href="{preview_url}" style="color:#2563EB;">{preview_url}</a></p>
    </div>

    <!-- Rodapé -->
    <div style="margin-top:32px;padding-top:16px;border-top:1px solid #E5E7EB;text-align:center;font-size:11px;color:#9CA3AF;">
        <p style="margin:0;">StitchGuard — Fábrica Autônoma de Matrizes de Bordado</p>
        <p style="margin:4px 0 0 0;">Documento gerado automaticamente em {agora}</p>
    </div>

</body>
</html>"""

    return html


def salvar_laudo(html: str, caminho: str) -> str:
    """Salva HTML do laudo em arquivo."""
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(html)
    return caminho


def gerar_laudo(
    job_id: str,
    resultado: dict,
    caminho_saida: str | None = None,
    operacoes_edicao: list[str] | None = None,
    stats_editado: dict | None = None,
) -> str:
    """Gera e salva laudo técnico.

    Args:
        job_id: identificador do job
        resultado: dict com resultado do pipeline
        caminho_saida: caminho para salvar o HTML (None = gera nome automático)
        operacoes_edicao: operações de pós-edição aplicadas (opcional)
        stats_editado: estatísticas após edição (opcional)

    Returns:
        Caminho do arquivo gerado
    """
    html = gerar_laudo_html(
        job_id,
        resultado,
        operacoes_edicao=operacoes_edicao,
        stats_editado=stats_editado,
    )

    if caminho_saida is None:
        caminho_saida = f"laudo_{job_id}_{uuid.uuid4().hex[:8]}.html"

    return salvar_laudo(html, caminho_saida)
