# Branch Protection - Configuração Manual

> **Nota:** Branch Protection requer **GitHub Pro** para repositórios privados.

## Como configurar manualmente:

1. Acesse: https://github.com/Maycon-BertolzoDOTCOM/StitchGuard/settings/branches

2. Clique em **"Add branch protection rule"**

3. Configure:
   - **Branch name pattern:** `master`
   - ✅ **Require a pull request before merging**
     - ✅ Dismiss stale pull request approvals when new commits are pushed
     - Require approvals: `1`
   - ✅ **Require status checks to pass before merging**
     - ✅ Require branches to be up to date before merging
     - Status checks: `test`
   - ✅ **Require conversation resolution before merging**
   - ❌ **Do not allow force pushes**
   - ❌ **Do not allow deletions**

4. Clique em **"Create"**

## Alternativa: Tornar o repositório público

Se quiser Branch Protection sem GitHub Pro, torne o repositório público:

```bash
gh repo edit Maycon-BertolzoDOTCOM/StitchGuard --visibility public
```

> **Atenção:** Isso tornará o código visível para todos.
