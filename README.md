# 📚 Habit Tracker – Study Like a Pro

> "We work in silence. Our success will be the noise."

Welcome to **Habit Tracker**, your all-in-one personal dashboard to track study habits, visualize progress, and stay consistent with your goals. This project is under private development — a silent build-up to something powerful. 💥

---

## 🚀 Features

* ✅ Log daily study sessions with time, duration, subject, and location
* 📊 Weekly analytics: total hours, daily average, best/worst day, and streaks
* 📅 Clean calendar view (coming soon)
* 📈 Beautiful bar chart visualization via Chart.js
* 🌙 Dark mode support (experimental)
* 🔒 Local SQLite DB (lightweight and portable)

---

## 🛠 Tech Stack

| Layer    | Technology    |
| -------- | ------------- |
| Backend  | Python, Flask |
| Frontend | HTML, CSS     |
| Charts   | Chart.js      |
| Database | SQLite        |

---

## 🧠 Project Structure

```
habit-tracker/
├── app.py                 # Flask server
├── studying.db            # SQLite database
├── templates/             # HTML templates
│   ├── main.html          # Home input form
│   └── studying.html      # Stats and charts
├── static/
│   └── style.css          # Styling
└── README.md              # You are here
```

---

## 🔧 Setup & Run Locally

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/habit-tracker.git
cd habit-tracker
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install flask
```

### 4. Run the app

```bash
python app.py
```

Then go to `http://127.0.0.1:5000` in your browser.

---

## 📌 To-Do / Roadmap

* [x] Basic study tracking system
* [x] Weekly chart + stats view
* [ ] Subject-based filters and breakdowns
* [ ] Monthly and all-time views
* [ ] Export to CSV/Excel
* [ ] User accounts + login
* [ ] Mobile optimization
* [ ] Public launch! 🎉

---

## 👤 Author

**Hicham** – *silent coder, building loud impact.*

> Connect later, when the time is right.

---

## 📢 License

This project is private for now. License will be revealed upon public release.
