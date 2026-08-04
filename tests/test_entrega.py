"""Testes do módulo de entrega."""
from infra.entrega import (
    upload_para_drive,
    gerar_link_download,
    listar_arquivos_cliente,
)


class TestUploadParaDrive:
    def test_stub_sem_credentials(self):
        """Sem credentials, retorna stub."""
        result = upload_para_drive(
            arquivo_path="/tmp/teste.dst",
            nome_cliente="João",
            job_id="abc123",
        )
        assert result["ok"] is True
        assert result["stub"] is True
        assert "file_id" in result
        assert "download_url" in result


class TestGerarLinkDownload:
    def test_gerar_link(self):
        result = gerar_link_download(job_id="abc123")
        assert result["ok"] is True
        assert "download_url" in result
        assert "expira_em" in result
        assert result["expiracao_horas"] == 24

    def test_gerar_link_customizado(self):
        result = gerar_link_download(job_id="abc123", expiracao_horas=48)
        assert result["expiracao_horas"] == 48


class TestListarArquivosCliente:
    def test_listar_stub(self):
        result = listar_arquivos_cliente("João")
        assert result["ok"] is True
        assert result["stub"] is True
        assert result["arquivos"] == []
