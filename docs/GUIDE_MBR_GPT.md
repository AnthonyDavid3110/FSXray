# Guide : parser MBR / GPT toi-même

Fichiers fournis :
- `test_mbr.img` (5 MiB, disque MBR pur, 2 partitions)
- `test_gpt.img` (20 MiB, disque GPT avec MBR protecteur + table primaire + table de secours)
- `answer_key.json` (valeurs attendues, à comparer avec la sortie de ton parser — ne l'ouvre qu'après avoir codé, sinon ça gâche l'exercice)

Ces images ont été vérifiées avec `fdisk -l` et `sgdisk -p` (qui valide les CRC32), donc si ton parser n'arrive pas aux mêmes résultats, le bug est dans ton code, pas dans le fixture.

## 1. Structure du MBR (secteur 0, 512 octets)

| Offset | Taille | Contenu |
|---|---|---|
| 0 | 446 | Bootstrap code (ignorable) |
| 446 | 16 | Entrée de partition 1 |
| 462 | 16 | Entrée de partition 2 |
| 478 | 16 | Entrée de partition 3 |
| 494 | 16 | Entrée de partition 4 |
| 510 | 2 | Signature `0x55 0xAA` |

Format d'une entrée de partition (16 octets, little-endian) :

| Offset | Taille | Champ |
|---|---|---|
| 0 | 1 | Statut (`0x80` = bootable, `0x00` = non) |
| 1 | 3 | CHS début (legacy, ignorable) |
| 4 | 1 | Type de partition (ex: `0x07` NTFS, `0x83` Linux, `0xEE` protecteur GPT) |
| 5 | 3 | CHS fin (legacy, ignorable) |
| 8 | 4 | LBA de début (uint32 little-endian) |
| 12 | 4 | Nombre de secteurs (uint32 little-endian) |

Étapes suggérées :
1. Lire les 512 premiers octets.
2. Vérifier la signature aux offsets 510-511.
3. Parser les 4 entrées, ignorer celles où type = 0x00.
4. Si tu trouves une entrée de type `0xEE`, c'est un MBR protecteur → le disque est probablement en GPT, pas en MBR pur.

Module Python utile : `struct.unpack("<B3sB3sII", entry_bytes)`.

## 2. Structure du GPT

Le disque `test_gpt.img` contient :
- LBA 0 : MBR protecteur (même format que ci-dessus, une seule entrée type `0xEE`)
- LBA 1 : en-tête GPT primaire
- LBA 2 à 33 : table de partitions primaire (128 entrées × 128 octets = 32 secteurs)
- ... zone de données ...
- LBA (dernier-32) à (dernier-1) : table de partitions de secours (copie identique)
- LBA dernier : en-tête GPT de secours

### En-tête GPT (92 octets utiles, little-endian)

| Offset | Taille | Champ |
|---|---|---|
| 0 | 8 | Signature `"EFI PART"` |
| 8 | 4 | Révision (`0x00010000`) |
| 12 | 4 | Taille du header (92) |
| 16 | 4 | CRC32 du header (calculé avec ce champ à 0) |
| 20 | 4 | Réservé |
| 24 | 8 | LBA du header courant |
| 32 | 8 | LBA du header de secours |
| 40 | 8 | Premier LBA utilisable |
| 48 | 8 | Dernier LBA utilisable |
| 56 | 16 | GUID du disque (mixed-endian, voir plus bas) |
| 72 | 8 | LBA de début de la table de partitions |
| 80 | 4 | Nombre d'entrées dans la table |
| 84 | 4 | Taille d'une entrée (généralement 128) |
| 88 | 4 | CRC32 de la table de partitions |

### Entrée de partition GPT (128 octets)

| Offset | Taille | Champ |
|---|---|---|
| 0 | 16 | GUID du type de partition (mixed-endian) |
| 16 | 16 | GUID unique de la partition (mixed-endian) |
| 32 | 8 | Premier LBA |
| 40 | 8 | Dernier LBA |
| 48 | 8 | Flags d'attributs |
| 56 | 72 | Nom (UTF-16LE) |

## 3. Pièges classiques (importants en forensique)

**GUID mixed-endian.** Contrairement à une lecture naïve, un GUID GPT n'est PAS stocké tel quel : les 3 premiers champs (4+2+2 octets) sont en little-endian, les 2 derniers (2+6 octets) restent en big-endian. Si tu lis les 16 octets bruts sans réordonner, tes GUID seront faux (mais toujours "syntaxiquement valides", donc l'erreur passe inaperçue si tu ne compares pas avec une source de vérité).

**CRC32 du header.** Il faut mettre à zéro le champ CRC32 (offset 16-19) avant de recalculer, sinon ça ne matchera jamais. Utile en forensique : un CRC32 invalide sur le header primaire mais valide sur le header de secours est un signe de altération/corruption.

**Header primaire vs header de secours.** Un bon outil forensique compare les deux. S'ils diffèrent (GUID disque, nombre d'entrées, CRC), c'est suspect.

**MBR protecteur.** Sur un disque GPT, l'entrée MBR à l'offset 446 doit avoir type `0xEE` et couvrir tout le disque. Un MBR protecteur "hybride" avec plusieurs vraies partitions est un signe de manipulation ou de configuration bootable inhabituelle (rare, historiquement utilisé par certains Mac).

**Nom de partition en UTF-16LE.** Ne pas oublier de retirer les octets nuls de padding avant de décoder, sinon la chaîne contient des `\x00\x00...` à la fin.

**LBA → offset en octets.** `offset = LBA * taille_secteur` (512 dans nos images, mais certains disques modernes utilisent 4096 — un vrai outil devrait lire la taille de secteur plutôt que la coder en dur).

## 4. Ordre d'implémentation suggéré

1. Ouvrir le fichier en binaire, lire le secteur 0.
2. Parser MBR brut (4 entrées), afficher.
3. Détecter la présence d'une entrée `0xEE` → basculer en mode GPT.
4. Parser l'en-tête GPT primaire (LBA 1), vérifier signature `"EFI PART"`.
5. Recalculer le CRC32 du header et comparer au champ stocké → valider/invalider.
6. Lire la table de partitions (LBA indiqué dans le header, nombre d'entrées × taille d'entrée).
7. Recalculer le CRC32 de la table et comparer.
8. Parser chaque entrée non nulle (type GUID tout à zéro = entrée vide), convertir les GUID mixed-endian, décoder le nom.
9. Lire le header de secours (LBA = `backup_lba` du header primaire) et comparer avec le primaire.
10. Sortie : rapport listant partitions, types, tailles, statut de validation CRC, cohérence primaire/secours.

Compare ta sortie avec `answer_key.json` une fois que tu as un résultat.
