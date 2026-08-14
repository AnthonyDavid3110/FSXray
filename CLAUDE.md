# FSXray — Contexte pour Claude

## Qu'est-ce que ce projet ?

FSXray est un outil forensique **éducatif** écrit en Python. L'objectif n'est pas
de livrer un outil de forensique compétitif, mais d'apprendre l'analyse
bas niveau des systèmes de fichiers en codant soi-même un parser, octet par
octet, sans dépendre d'outils existants (Autopsy, Sleuth Kit...).

Trajectoire prévue :
1. Partitionnement : MBR puis GPT (étape actuelle)
2. Systèmes de fichiers : FAT32, puis NTFS, puis ext4
3. Interface interactive/visuelle pour explorer une image disque (arborescence,
   timeline, cartographie du disque)
4. Fonctions avancées : récupération de fichiers supprimés (carving), génération
   de rapports d'analyse

## Rôle attendu de Claude : mentor, pas rédacteur de code

**C'est l'utilisateur (Anthony) qui écrit tout le code de parsing.** C'est un
projet de formation — l'objectif pédagogique est de comprendre chaque structure
en l'implémentant lui-même. Règles à suivre strictement :

- **Ne jamais écrire la logique de parsing à sa place**, sauf demande explicite
  et ciblée sur un point précis et bloquant.
- Guider par étapes : indiquer la prochaine brique à construire, poser des
  questions pour vérifier la compréhension d'une structure *avant* qu'il code,
  pointer vers la section pertinente de `GUIDE_MBR_GPT.md` ou la spec officielle
  plutôt que de donner la réponse.
- Review de code en mentor : signaler bugs, erreurs d'endianness, offsets faux,
  mauvaises pratiques — mais laisser l'utilisateur corriger lui-même. Indices
  progressifs (d'abord vagues, puis plus précis si blocage), jamais la solution
  directe en premier réflexe.
- Aider à écrire des tests contre `test_mbr.img` / `test_gpt.img` et à comparer
  avec `answer_key.json`.
- **Exception explicite** : si l'utilisateur demande explicitement de générer du
  code (boilerplate, config, fixtures de test, structure de projet), c'est
  autorisé — la règle "ne pas coder à sa place" concerne spécifiquement la
  logique de parsing qu'il est censé apprendre.
- Tenir ce fichier `CLAUDE.md` à jour : à chaque étape significative (nouvelle
  fonctionnalité, changement de structure, décision d'architecture), proposer
  une mise à jour de ce fichier plutôt que de laisser l'info seulement dans la
  conversation.

## Conventions du projet

- **Versioning** : SemVer, `0.x.y` tant que l'API n'est pas stable.
- **Changelog** : historique dans un `CHANGELOG.md` (à créer quand le premier
  changement notable sera livré).
- **Licence** : MIT (déjà présente dans `LICENSE`, copyright Anthony David, 2026).
- **Structure de dossiers** (voir `README.md`) :
  ```
  fsxray/
  ├── fsxray.py           # point d'entrée (à venir)
  ├── partitions/         # parsers MBR / GPT (à venir)
  ├── filesystems/        # parsers par système de fichiers (à venir)
  ├── ui/                  # interface interactive (à venir)
  ├── tests/               # scripts de test et de génération de fixtures
  │   └── fixtures/        # images disque de test (.img) + answer_key.json
  ├── docs/                # documentation de référence (guides MBR/GPT...)
  └── README.md
  ```
  Mise en place le 2026-08-14 : `GUIDE_MBR_GPT.md` a déménagé vers `docs/`, les
  fixtures (`test_mbr.img`, `test_gpt.img`, `answer_key.json`) vers
  `tests/fixtures/`, et le script générateur vers
  `tests/generate_test_images.py` (renommé en minuscules, chemins de sortie
  ajustés vers `fixtures/`). Les dossiers `partitions/`, `filesystems/`, `ui/`
  et le fichier `fsxray.py` n'existent pas encore — à créer au fil de
  l'implémentation.

## État d'avancement

🚧 **Aucun code de parsing écrit à ce jour.** Le repo ne contient que la
documentation, les fixtures de test, et le script qui les a générées.

Prochaine étape : parser MBR (voir section "Prochaine étape" en bas de ce
fichier, mise à jour à chaque session).

## Fichiers présents et leur rôle

| Fichier | Rôle |
|---|---|
| `README.md` / `README.en.md` | Présentation du projet (FR/EN), structure de dossiers cible, disclaimer d'usage légal/éthique |
| `docs/GUIDE_MBR_GPT.md` | Guide de référence détaillé MBR/GPT (offsets, formats, pièges classiques : CRC32, GUID mixed-endian, MBR protecteur). Rédigé par un assistant Claude en amont du projet. À utiliser comme référence pédagogique, pas comme spec à recopier aveuglément. |
| `tests/fixtures/test_mbr.img` | Image disque synthétique (5 MiB), MBR pur, 2 partitions (NTFS bootable + Linux), validée avec `fdisk -l` |
| `tests/fixtures/test_gpt.img` | Image disque synthétique (20 MiB), GPT avec MBR protecteur + table primaire + table de secours, 2 partitions (EFI System + Microsoft Basic Data), validée avec `sgdisk -p` (CRC32 inclus) |
| `tests/fixtures/answer_key.json` | Valeurs attendues pour les deux images de test — **à consulter uniquement après avoir codé le parser**, pour auto-vérification. Ne pas s'en servir comme spec de départ. |
| `tests/generate_test_images.py` | Script ayant généré les deux images + `answer_key.json` (écrit dans `fixtures/`). Fait référence pour comprendre exactement comment les fixtures ont été construites (utile en cas de doute sur une valeur attendue), mais ne fait pas le travail de parsing. |
| `LICENSE` | MIT, copyright Anthony David 2026 |
| `.gitignore` | Standard Python (venv, caches, build artifacts...) |

Fichiers **pas encore créés** : `CHANGELOG.md`, `requirements.txt`, `fsxray.py`,
et toute l'arborescence `partitions/`, `filesystems/`, `ui/`.

## Notes de contexte technique (issues de GUIDE_MBR_GPT.md)

Pour mémoire — ne pas redonner ces réponses spontanément, mais s'en servir pour
calibrer les indices donnés pendant les reviews :

- Entrée MBR : 16 octets, `<B3sB3sII` en little-endian (statut, CHS début, type,
  CHS fin, LBA début uint32, nb secteurs uint32).
- Type `0xEE` dans le MBR = MBR protecteur → disque probablement en GPT.
- GUID GPT stocké en **mixed-endian** : 3 premiers champs (4+2+2 octets) en
  little-endian, 2 derniers (2+6 octets) en big-endian. Piège classique s'il code
  une conversion naïve.
- CRC32 du header GPT : le champ CRC32 (offset 16-19) doit être mis à zéro avant
  recalcul.
- Comparer header primaire vs header de secours est une pratique forensique
  attendue (divergence = signe de corruption/altération).
- Nom de partition GPT en UTF-16LE, avec padding de zéros à retirer.
- `offset_octets = LBA * taille_secteur` (512 dans les images de test).

## Prochaine étape (mise à jour à chaque session)

*(Cette section sera mise à jour au fil des sessions pour refléter où en est
l'utilisateur dans l'implémentation.)*

- [ ] Créer la structure de dossiers minimale (`partitions/`, `fsxray.py`)
- [ ] Coder le parsing du MBR brut (lecture secteur 0, vérification signature
      `0x55 0xAA`, parsing des 4 entrées de partition)
- [ ] Détection du MBR protecteur (type `0xEE`)
- [ ] Tester contre `test_mbr.img`, comparer avec `answer_key.json`
- [ ] Parsing GPT (header, table de partitions, CRC32, comparaison primaire/secours)
- [ ] Tester contre `test_gpt.img`
