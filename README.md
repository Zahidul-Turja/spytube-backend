# SpyTube

**SpyTube** help's you monitor your own channel, track revenue and analize competitors as well.

## Features

- OAuth 2.0 with google as it dedicated to YouTube
- Analyze your channel
- Competetor analysis

---

## Project Set up

### Clone the repository

```bash
git clone https://github.com/Zahidul-Turja/spytube-backend.git
cd spytube-backend
```

### Build and run with docker

```bash
sudo docker compose up --build
```

### Migration cmd

```bash
sudo docker compose exec app python app/init_db.py
```
