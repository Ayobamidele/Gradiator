
# 🎓 Gradiator Slack Bot

This Slack bot tracks student scores, displays leaderboards, and allows users to submit and view their progress in a competitive, gamified way.

---

## 🚀 Available Slash Commands

### 1. `/grade`

**Usage**:
```
/grade
```
or
```
/grade file_id=F12345678
```

**What It Does**:
- Processes a recently uploaded file containing student scores.
- If no `file_id` is provided, the bot finds the latest file uploaded by the user.
- Parses the file and updates each student's score.

---

### 2. `/leaderboard`

**Usage**:
```
/leaderboard
```
or
```
/leaderboard backend
```

**What It Does**:
- Shows the top 10 students either across all tracks or within a specific track.

**Valid Tracks**:
- backend
- frontend
- design
- devops
- data_analysis
- project_management

---

### 3. `/myscore`

**Usage**:
```
/myscore
```

**What It Does**:
- Displays your total score across all tracks.
- Shows per-track breakdown including:
  - Total score
  - Most recent stage
  - Most recent stage’s score

**Response**:
- Sent as a private DM.

---

## 📝 Example Flow

1. Upload an Excel or CSV score file in Slack.
2. Run `/grade` to process the file.
3. Run `/leaderboard backend` to view rankings.
4. Run `/myscore` to get your own score summary.

---

## 🛠️ Setup Notes

- Bot Permissions Needed:
  - `commands`
  - `chat:write`
  - `files:read`
  - `users:read`
  - `im:write`

- Register slash commands in your Slack App with appropriate request URLs pointing to:
  - `/slack/score`
  - `/slack/leaderboard`
  - `/slack/myscore`

---
