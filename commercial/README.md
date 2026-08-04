# L5 — Commercial (Billing + Delivery)

**Responsabilidade:** Cobrança via Asaas, entrega do arquivo final, e notificações.

**Stack:** Python + Asaas API + Google Drive API + SMTP

**Módulos:**
- `asaas.py`: cria cobrança, webhook de pagamento
- `entrega.py`: upload para Google Drive, gera link público, envia e-mail

**Fluxo:**
1. Validação aprovada → `entrega.upload()` → Drive
2. Gera link → `asaas.cria_cobranca()` → boleto/Pix
3. Envia e-mail com link + boleto anexado
