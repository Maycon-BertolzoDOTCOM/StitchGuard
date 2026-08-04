#!/bin/bash
# StitchGuard - Script de Setup Rápido

set -e

echo "🧵 StitchGuard - Setup"
echo "========================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.13+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python $PYTHON_VERSION encontrado"

# Create venv
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "📚 Instalando dependências..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q -r requirements-dev.txt

# Copy env example
if [ ! -f ".env" ]; then
    echo "⚙️  Criando .env a partir do exemplo..."
    cp .env.example .env
    echo "   ⚠️  Edite o .env com suas credenciais!"
fi

# Run tests
echo "🧪 Executando testes..."
rm -f stitchguard.db
python -m pytest tests/ -q --tb=line

echo ""
echo "✅ Setup concluído!"
echo ""
echo "Próximos passos:"
echo "  1. Edite o .env com suas credenciais"
echo "  2. Execute: source venv/bin/activate"
echo "  3. Inicie a API: uvicorn application.main:app --reload"
echo "  4. Acesse: http://localhost:8000/docs"
