# Configuration du connecteur SAP OData

## Prérequis SAP

### Activer SAP Gateway
- ECC : SPRO → SAP NetWeaver → Activation d'OData
- S/4HANA : déjà activé par défaut

### Activer les services OData nécessaires

**Transaction** : `/IWFND/MAINT_SERVICE`

| Module | ECC (OData v2) | S/4HANA (OData v2) |
|--------|---------------|---------------------|
| Factures MM (MIRO) | `MM_IV_GDC_MIRO_SRV` | `API_SUPPLIER_INVOICE_SRV` |
| Commandes achat | `MM_PUR_PO_MAINT_SRV` | `API_PURCHASEORDER_PROCESS_SRV` |
| Commandes vente | `SD_SALESORDER_SRV` | `API_SALES_ORDER_SRV` |
| Stocks | `MMIM_MATERIAL_STOCK_SRV` | `API_MATERIAL_STOCK_SRV` |

### Créer un utilisateur RFC dédié

Autorisations minimales requises :

```
S_RFC        — FUGR : SYST, SRFC, RFC1
MM_IV        — M_RECH_WRK (pour MIRO / API_SUPPLIER_INVOICE_SRV)
MM_PUR       — M_BEST_BSA (pour ME23N / API_PURCHASEORDER_PROCESS_SRV)
SD           — V_VBAK_AAT (pour VA03 / API_SALES_ORDER_SRV)
MMIM         — M_MSEG_BWA (pour stocks)
```

---

## Variables d'environnement

### Auth Basic (ECC / S/4HANA on-premise)

```bash
SAP_CONNECTOR=odata
SAP_ODATA_BASE_URL=https://my-sap-host.company.com
SAP_ODATA_USER=RFC_COPILOT
SAP_ODATA_PASSWORD=motdepasse_secret
SAP_CLIENT=100
SAP_LANGUAGE=FR
SAP_VERSION=auto        # détection automatique
SAP_VERIFY_SSL=true
SAP_TIMEOUT_CONNECT=10.0
SAP_TIMEOUT_READ=30.0
SAP_MAX_RETRIES=3
```

### Auth OAuth2 (S/4HANA Cloud / BTP)

```bash
SAP_CONNECTOR=odata
SAP_ODATA_BASE_URL=https://my-tenant.s4hana.ondemand.com
SAP_OAUTH_URL=https://my-tenant.authentication.eu10.hana.ondemand.com/oauth/token
SAP_OAUTH_CLIENT_ID=sb-copilot-client!t12345
SAP_OAUTH_CLIENT_SECRET=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SAP_OAUTH_SCOPE=
SAP_CLIENT=100
SAP_VERSION=s4hana
```

### Circuit breaker

```bash
SAP_CB_FAILURE_THRESHOLD=5   # ouvrir après 5 échecs consécutifs
SAP_CB_RECOVERY_TIMEOUT=60   # tenter HALF_OPEN après 60 secondes
```

---

## Test de connectivité

### Vérifier la disponibilité du Gateway

```bash
curl -u RFC_COPILOT:motdepasse \
  "https://SAP_HOST/sap/opu/odata/IWFND/CATALOGSERVICE/ServiceCollection?\$top=1&\$format=json"
```

Réponse attendue : HTTP 200 avec body JSON contenant `"d": {"results": [...]}`

### Tester un service spécifique (facture S/4HANA)

```bash
curl -u RFC_COPILOT:motdepasse \
  "https://SAP_HOST/sap/opu/odata/sap/API_SUPPLIER_INVOICE_SRV/A_SupplierInvoice('5100000001')?\$format=json"
```

### Tester le CSRF (écriture)

```bash
# 1. Obtenir le token
curl -u RFC_COPILOT:motdepasse \
  -H "x-csrf-token: Fetch" \
  -X GET "https://SAP_HOST/sap/opu/odata/" \
  -v 2>&1 | grep "x-csrf-token"

# 2. Utiliser le token dans une requête POST
```

---

## Mode sandbox SAP API Business Hub

Pour tester sans un vrai système SAP :

1. Créer un compte sur [SAP API Business Hub](https://api.sap.com)
2. S'abonner aux APIs nécessaires
3. Copier votre clé API

```bash
SAP_SANDBOX=true
SAP_SANDBOX_API_KEY=votre-cle-api-sandbox
SAP_VERSION=s4hana
SAP_CONNECTOR=odata
SAP_ODATA_BASE_URL=https://sandbox.api.sap.com/s4hanacloud
```

> **Note** : La sandbox est lente et instable. Le circuit breaker est désactivé en mode sandbox. Utilisez des timeouts plus longs (défaut : 30s).

---

## Endpoint /health avec métriques

Une fois le connecteur OData configuré, `GET /api/v1/health` retourne :

```json
{
  "status": "ok",
  "connector": "odata",
  "circuit_breaker": "CLOSED",
  "sap_metrics": {
    "total_requests": 42,
    "successful_requests": 41,
    "failed_requests": 1,
    "success_rate": 0.976,
    "avg_duration_ms": 234.1,
    "requests_by_service": {"mm_invoice": 20, "mm_purchase_order": 10},
    "errors_by_type": {"timeout": 1},
    "last_error": "timeout",
    "last_success_at": "2024-01-15T14:23:00Z"
  },
  "cache": {
    "hits": 12,
    "misses": 30,
    "hit_rate": 0.286,
    "size": 8
  }
}
```

---

## Dépannage

| Symptôme | Cause probable | Solution |
|----------|---------------|----------|
| HTTP 401 | Mauvais credentials | Vérifier `SAP_ODATA_USER` / `SAP_ODATA_PASSWORD` |
| HTTP 403 (non-CSRF) | Droits insuffisants | Ajouter les autorisations SAP manquantes |
| HTTP 503 dans l'API | Circuit breaker OPEN | Attendre `SAP_CB_RECOVERY_TIMEOUT` secondes ou redémarrer |
| SSL error | Certificat SAP auto-signé | `SAP_VERIFY_SSL=false` (dev uniquement) |
| Timeout | SAP Gateway lent | Augmenter `SAP_TIMEOUT_READ` |
| Version détectée incorrecte | Catalog Service non activé | Forcer `SAP_VERSION=ecc` ou `s4hana` |
