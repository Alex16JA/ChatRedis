# 💬 DockerChat

Application de chat en temps réel dans le terminal, basée sur **Redis Pub/Sub** et construite avec **Textual** (TUI Python).

---

## 📋 Prérequis

- Python 3.11+
- Redis (local ou via Docker)
- pip

---

## 🚀 Installation

```bash
# Cloner le dépôt
git clone https://github.com/votre-utilisateur/DockerChat.git
cd DockerChat

# Installer les dépendances
pip install textual redis requests
```

### Lancer Redis avec Docker

```bash
docker run -d -p 6379:6379 redis
```

---

## ▶️ Utilisation

```bash
python app.py
```

---

## ⌨️ Commandes disponibles

| Commande | Description |
|---|---|
| `/username <pseudo>` | Changer votre pseudo |
| `/channel <canal>` | Rejoindre un canal de discussion |
| `/server <hôte>` | Se connecter à un autre serveur Redis |
| `/weather <ville>` | Afficher la météo du jour (défaut : Paris) |

### Raccourcis clavier

| Touche | Action |
|---|---|
| `Q` / `Ctrl+C` | Quitter l'application |
| `Ctrl+X` | Effacer la conversation |
| `Entrée` | Envoyer un message |

---

## 🏗️ Architecture

```
DockerChat/
├── app.py          # Application principale (logique + UI)
├── styles.css      # Styles Textual (thème sombre)
└── .idea/          # Configuration IDE (PyCharm)
```

### Composants principaux

- **`ChatApp`** — Application Textual principale, gère les événements et l'affichage
- **`Conversation`** — Gère la connexion Redis, les canaux et l'envoi/réception de messages
- **`MessageBox`** — Widget d'affichage d'un message dans la conversation
- **`StatusBar`** — Barre d'état affichant le serveur et le canal actifs

---

## ✨ Fonctionnalités

- 📡 **Chat en temps réel** via Redis Pub/Sub
- 🌐 **Multi-serveurs** — changez de serveur Redis à la volée
- 📺 **Multi-canaux** — rejoignez n'importe quel canal instantanément
- 🌦️ **Météo intégrée** avec mise en cache Redis (1h) via Open-Meteo & Nominatim
- 🖥️ **Interface TUI** entièrement dans le terminal

---

## 🛠️ Stack technique

| Outil | Rôle |
|---|---|
| [Textual](https://textual.textualize.io/) | Framework TUI Python |
| [Redis](https://redis.io/) | Broker de messages (Pub/Sub) + cache |
| [Open-Meteo](https://open-meteo.com/) | API météo gratuite |
| [Nominatim](https://nominatim.org/) | Géocodage (ville → coordonnées GPS) |

---

## 📄 Licence

MIT
