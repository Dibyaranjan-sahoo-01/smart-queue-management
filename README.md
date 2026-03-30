# smart-queue-management
🧠 A virtual queue management system built with Flask — join online, track your position &amp; estimated wait time in real time.
.
.
.
.
## 📋 Smart Queue Management System

A lightweight, production-ready virtual queue system built with Python & Flask.
Users join the queue online, receive a unique token, and can track their position
and estimated wait time — no physical waiting required.

### ✨ Features
- 🎫 Token-based queue entry (A123, B456...)
- ⏱️ Real-time position & wait time estimation
- 🔄 Auto-refreshing status page every 30s
- 🧑‍💼 Admin dashboard to serve/remove customers
- 📊 Live queue stats (waiting, served, avg time)
- 🗃️ SQLite database — zero setup required

### 🛠️ Tech Stack
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript (Jinja2 templates)
- **Database:** SQLite
- **Prediction:** Formula-based (position × avg service time)

### 🚀 Run Locally
pip install -r requirements.txt
python app.py
# Open http://localhost:5000
.
.
## Features

### User Side
- Join queue with name, phone, and service type
- Get a unique token (e.g. A123, B456)
- See real-time position and estimated wait time
- Progress bar and journey timeline
- Auto-refreshing status page every 30s
- Leave queue anytime

### Admin Side
- Live dashboard with queue stats
- Serve or remove customers in one click
- Served history for the day
- Adjustable average service time (slider)
- Auto-refreshing every 30s

### Wait Time Prediction
```
Estimated Wait = (position - 1) × avg_service_time
```
- Starts at 8 min/person (configurable)
- Updates dynamically as people are served

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Join queue page |
| POST | `/join` | Submit queue form |
| GET | `/queue/<token>` | User status page |
| GET | `/status/<token>` | JSON status (for polling) |
| POST | `/leave/<token>` | Leave the queue |
| GET | `/admin` | Admin dashboard |
| POST | `/admin/serve/<id>` | Mark as served |
| POST | `/admin/remove/<id>` | Remove from queue |
| POST | `/admin/settings` | Update settings |
| GET | `/api/queue` | Full queue JSON |

## Project Structure

```
smart_queue/
├── app.py              ← Flask backend + all routes
├── requirements.txt    ← pip install -r requirements.txt
├── database.db         ← SQLite (auto-created on first run)
├── templates/
│   ├── index.html      ← Join queue page
│   ├── queue.html      ← User status page
│   └── admin.html      ← Admin dashboard
└── model/              ← (future: AI-based prediction)
```

## Upgrade Path

| Feature | How to add |
|---------|-----------|
| SMS alerts | Twilio API when position ≤ 3 |
| AI wait prediction | Scikit-learn on served_at history |
| Real-time push | Flask-SocketIO |
| Multi-counter | Add `counter_id` column to queue table |
| Auth for admin | Flask-Login |
