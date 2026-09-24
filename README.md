# ARM Services Nellore — Website + Admin Portal

Flask app: public marketing site + password-protected admin portal for leads.

## Local run

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000  
Admin: http://127.0.0.1:5000/admin/login

## Default admin login

```
Username: Cuziamchaithu_1
Password: r%t@D213kK%Z
```

**Change this password immediately** after first login (Admin → Change Password).

## Deploy on Render (Free)

1. Push this repo to GitHub.
2. Go to https://render.com → Sign up with GitHub.
3. **New → Web Service** → connect your repo.
4. Settings:

| Field            | Value                              |
|------------------|------------------------------------|
| Runtime          | Python 3                           |
| Build Command    | `pip install -r requirements.txt`  |
| Start Command    | `gunicorn app:app`                 |
| Instance Type    | Free                               |

5. Environment Variables (Advanced):

| Key             | Value                          |
|-----------------|--------------------------------|
| `ARM_SECRET_KEY`| any strong random string       |
| `PYTHON_VERSION`| `3.12.0` (optional)            |

6. Create Web Service → wait for build → live URL ready.

### Important free-tier notes

- Service sleeps after 15 min idle (first visit takes 30-60 sec).
- SQLite database is **ephemeral** — data can be lost on restart/redeploy.
- Always change the default admin password.
- Update WhatsApp number in `templates/index.html`.

## File structure

```
app.py
requirements.txt
README.md
templates/
  index.html
  admin_login.html
  admin_dashboard.html
  admin_change_password.html
static/
  style.css
  admin.css
```
