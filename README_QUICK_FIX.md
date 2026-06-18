# 🔧 FIX RAPIDE - Erreur "Column 'language' n'existe pas"

## ⚡ Solution en 3 étapes (5 minutes)

### Étape 1: Lancer le diagnostic

```bash
cd Agent_Backend
python diagnose_schema.py
```

### Étape 2: Exécuter la migration

```bash
python fix_database.py
```

### Étape 3: Redémarrer le serveur

```bash
# Arrêter le serveur actuel (Ctrl+C)
# Puis relancer:
uvicorn src.Server:app --reload
```

## ✅ Vérifier que ça marche

```bash
curl -X GET http://localhost:8000/api/projects \
  -H "Authorization: Bearer <token>"
```

✅ Si vous recevez une réponse JSON, **C'EST RÉGLÉ!**

---

## 🆘 Si ça ne marche pas?

### Solution Alternative 1: SQL Manuel

```bash
cd Agent_Backend
python migrate_sql.py --print-sql
```

Copier le SQL et l'exécuter dans `psql`:

```bash
psql -U postgres -d agent_backend
```

Puis coller le SQL.

### Solution Alternative 2: Interface GUI

Utiliser DBeaver:
1. Clic droit sur table `projects`
2. `Add Column`
3. Name: `language`, Type: `VARCHAR(50)`, Nullable: ✓
4. Répéter pour: `prompt`, `steps`, `folder_name`, `download_url`, `provider`, `model`, `generation_time`

---

## 📊 Colonnes à ajouter (si vous faites manuellement)

| Colonne | Type | Nullable |
|---------|------|----------|
| language | VARCHAR(50) | YES |
| prompt | TEXT | YES |
| steps | TEXT | YES |
| folder_name | VARCHAR(100) | YES |
| download_url | VARCHAR(500) | YES |
| provider | VARCHAR(50) | YES |
| model | VARCHAR(100) | YES |
| generation_time | DOUBLE PRECISION | YES |

---

## 📝 Fichiers Créés pour Vous

| Fichier | Utilité |
|---------|---------|
| `fix_database.py` | ✅ Correction automatique complète |
| `diagnose_schema.py` | 📊 Diagnostic détaillé |
| `migrate_sql.py` | 📋 Migration SQL manuelle |
| `LANGUAGE_COLUMN_FIX.md` | 📚 Documentation détaillée |

---

## 🎯 Résumé du Problème & Solution

**Problème**: 
- La table PostgreSQL `projects` a été créée SANS les colonnes `language`, `provider`, etc.
- Mais le modèle SQLAlchemy les a depuis été mis à jour pour les inclure
- Résultat: SQLAlchemy demande une colonne qui n'existe pas en DB

**Solution**:
- Ajouter les colonnes manquantes à la table PostgreSQL
- Scripts automatisés fournis pour faire ça facilement

**Impact**:
- ✅ Endpoint `GET /api/projects` fonctionnera
- ✅ Vous pouvez créer et récupérer des projets
- ✅ Aucune donnée perdue, pas de reset de la DB

---

**Besoin d'aide?** Voir `LANGUAGE_COLUMN_FIX.md` pour la documentation complète.
