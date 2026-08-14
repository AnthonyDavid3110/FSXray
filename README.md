# FSXray

Outil forensique éducatif pour explorer, analyser et visualiser de façon interactive la structure interne de systèmes de fichiers, à partir d'images disque brutes.

## À propos

FSXray est un projet d'apprentissage en analyse forensique. L'objectif est de comprendre les structures de bas niveau des disques et systèmes de fichiers en les parsant soi-même, octet par octet, plutôt qu'en s'appuyant sur des outils existants (Autopsy, Sleuth Kit...).

Le projet démarre par le parsing des tables de partitionnement (MBR / GPT) et vise à évoluer vers le support de plusieurs systèmes de fichiers (FAT32, NTFS, ext4...), avec une interface interactive et visuelle pour explorer le contenu d'une image disque.

## État actuel

🚧 Projet en développement actif — première brique : parsing MBR et GPT.

## Fonctionnalités

**Disponible**
- Parsing du Master Boot Record (MBR) : table de partitions, types, secteurs de début/fin
- Parsing du GUID Partition Table (GPT) : en-tête, table de partitions, GUID, validation CRC32, comparaison header primaire/secours

**Prévu**
- Support de systèmes de fichiers : FAT32, NTFS, ext4
- Récupération de fichiers supprimés (carving)
- Interface interactive et visuelle (exploration de l'arborescence, timeline, cartographie du disque)
- Génération de rapports d'analyse

## Installation

```bash
git clone https://github.com/<ton-user>/fsxray.git
cd fsxray
pip install -r requirements.txt
```

## Utilisation

```bash
python fsxray.py chemin/vers/image.img
```

*(à adapter au fur et à mesure de l'implémentation)*

## Avertissement

Ce projet est destiné à un usage pédagogique. À utiliser uniquement sur des images disque créées par vous-même (VM, fichiers de test) ou dans un cadre légal explicite. Ne pas utiliser sur du matériel appartenant à des tiers sans autorisation.

## Structure du projet

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

## Licence

À définir.
