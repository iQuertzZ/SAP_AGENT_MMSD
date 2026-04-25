# Deployment Guide — SAP MM/SD AI Copilot

## Architecture de déploiement

```
GitHub Actions CI/CD
│
├── push main/develop → CI (lint + tests + docker build + push GHCR)
├── push main          → Deploy to production (SSH)
├── workflow_dispatch  → Manual deploy (staging or production)
└── release tag        → Auto-deploy to staging
```

---

## 1. Secrets GitHub à configurer

**Settings → Secrets and variables → Actions**

### Secrets globaux (tous les workflows)

| Secret | Description | Exemple |
|--------|-------------|---------|
| `ANTHROPIC_API_KEY` | Clé API Anthropic (optionnelle — fallback sur rule engine si absente) | `sk-ant-...` |
| `SECRET_KEY` | Clé de signature JWT — générer avec `openssl rand -hex 32` | `a1b2c3d4...` |
| `CODECOV_TOKEN` | Token Codecov (optionnel) | `uuid-...` |

### Secrets environment `production`

| Secret | Description | Exemple |
|--------|-------------|---------|
| `DEPLOY_HOST` | IP ou domaine du serveur de production | `195.201.12.34` |
| `DEPLOY_USER` | Utilisateur SSH | `deploy` |
| `DEPLOY_KEY` | Clé privée SSH ED25519 (voir section SSH ci-dessous) | `-----BEGIN OPENSSH...` |
| `DEPLOY_PATH` | Chemin du repo cloné sur le serveur | `/opt/sap-copilot` |
| `GHCR_TOKEN` | Personal Access Token avec `read:packages` | `ghp_...` |
| `DATABASE_URL` | URL PostgreSQL de production | `postgresql+asyncpg://user:pass@db:5432/sap_copilot` |

### Secrets environment `staging`

| Secret | Description |
|--------|-------------|
| `STAGING_HOST` | IP ou domaine du serveur de staging |
| `STAGING_USER` | Utilisateur SSH |
| `STAGING_KEY` | Clé privée SSH |
| `STAGING_PATH` | Chemin sur le serveur |
| `GHCR_TOKEN` | Token GHCR |

---

## 2. Environments GitHub à créer

**Settings → Environments**

### `production`

- **Required reviewers** : ajouter ton username GitHub
- **Deployment branches** : `main` uniquement
- **Wait timer** : 0 minutes
- Ajouter tous les secrets production listés ci-dessus

### `staging`

- **Required reviewers** : aucun
- **Deployment branches** : `develop`, `main`
- Ajouter les secrets staging

---

## 3. Génération de la clé SSH de déploiement

### Sur ta machine locale

```bash
# Générer une clé ED25519 dédiée au déploiement
ssh-keygen -t ed25519 -C "sap-copilot-deploy" -f ~/.ssh/sap_copilot_deploy

# Afficher la clé publique
cat ~/.ssh/sap_copilot_deploy.pub
```

### Sur le serveur

```bash
# Ajouter la clé publique dans les authorized_keys de l'utilisateur de déploiement
echo "ssh-ed25519 AAAA... sap-copilot-deploy" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Dans GitHub Secrets

- Secret `DEPLOY_KEY` = contenu complet de `~/.ssh/sap_copilot_deploy` (clé **privée**, incluant `-----BEGIN OPENSSH PRIVATE KEY-----`)

---

## 4. Préparation du serveur

```bash
# Installer Docker et Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Créer le répertoire de déploiement
sudo mkdir -p /opt/sap-copilot
sudo chown deploy:deploy /opt/sap-copilot

# Cloner le repo
cd /opt/sap-copilot
git clone https://github.com/iQuertzZ/SAP_AGENT_MMSD .

# Créer le fichier .env.prod (NE PAS COMMITTER)
cp .env.example .env
# Éditer .env avec les valeurs de production
```

---

## 5. Workflows GitHub Actions

### CI — Déclenchement automatique

```
push main / develop / PR vers main
  → lint (ruff + mypy + tsc)
  → test-backend (pytest + coverage ≥80%)
  → test-frontend (npm run build)
  → docker-build + push GHCR  [main/develop seulement]
  → deploy production          [main seulement, avec approbation]
```

### CD — Déploiement manuel

```bash
# Via GitHub UI : Actions → CD — Manual Deploy → Run workflow

# Via CLI (nécessite gh CLI)
make deploy-staging
make deploy-prod
```

### Security — Audit hebdomadaire

```
push main + chaque lundi 02:00 UTC
  → dependency-scan (pip-audit + npm audit)
  → docker-scan (Trivy SARIF → GitHub Security)
  → secret-scan (Gitleaks)
```

---

## 6. GHCR — GitHub Container Registry

Les images sont publiées sur :

```
ghcr.io/iquertzz/sap_agent_mmsd/backend:latest       (main)
ghcr.io/iquertzz/sap_agent_mmsd/backend:develop      (develop)
ghcr.io/iquertzz/sap_agent_mmsd/backend:sha-<hash>   (chaque commit)

ghcr.io/iquertzz/sap_agent_mmsd/frontend:latest
ghcr.io/iquertzz/sap_agent_mmsd/frontend:sha-<hash>
```

### Rendre les images publiques

```
GitHub → Packages → backend → Package settings → Change visibility → Public
```

Ou pull avec auth :

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u iQuertzZ --password-stdin
docker pull ghcr.io/iquertzz/sap_agent_mmsd/backend:latest
```

---

## 7. Alternatives de déploiement

### Railway

```bash
# Commenter le job "deploy" dans ci.yml et décommenter :
# - uses: railwayapp/railway-action@v1
#   with:
#     railway_token: ${{ secrets.RAILWAY_TOKEN }}
```

Secret requis : `RAILWAY_TOKEN` (depuis railway.app → Account → API Tokens)

### Render

```bash
# Appel webhook Render pour déclencher un redéploiement
# curl -X POST "${{ secrets.RENDER_DEPLOY_HOOK_URL }}"
```

Secret requis : `RENDER_DEPLOY_HOOK_URL` (depuis Render → Service → Settings → Deploy Hook)

---

## 8. Test local du pipeline (nektos/act)

```bash
# Installer act
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Simuler le job lint
make ci-local

# Dry-run
act -j test-backend --dry-run
act -j lint --dry-run
```

---

## 9. Vérification post-déploiement

```bash
# Health check
curl https://your-domain.com/api/v1/health
# Attendu : {"status":"ok","version":"1.0.0","git_sha":"abc1234...","connector":"mock"}

# Connexion admin
curl -X POST https://your-domain.com/api/v1/auth/login \
  -d "username=admin@sap-copilot.local&password=<FIRST_ADMIN_PASSWORD>"
```

---

## 10. Rollback

```bash
# Déployer une version précédente via GitHub UI ou :
gh workflow run cd.yml \
  -f environment=production \
  -f image_tag=sha-<previous-sha> \
  -f run_migrations=false
```

**Important** : ne jamais rollback les migrations Alembic en production sans plan de rollback testé.
