"""Configuração de testes — fixtures compartilhadas.

O banco SQLite usa IDs únicos por teste (uuid) para garantir isolamento.
Não é necessário deletar o banco entre testes.
"""
import os
import shutil
import tempfile

import pytest


@pytest.fixture
def tmp_artifacts():
    """Cria diretório temporário para artefatos e limpa após o teste."""
    tmp_dir = tempfile.mkdtemp(prefix="stitchguard-test-")
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)
