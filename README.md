# Glassboard

10/1/25 - Created Project

10/30/25 - Attempted Migration to RDS

Migrating to RDS:
- Select Oregon (us-west 2) and create RDS instance.
- Amazon RDS for PostgreSQL
- Single AZ.
- Standard Create
- Dev/Test
- Use AWS Secrets Manager
- Use an instance: db.t3.micro
- Use default VPC subnet group
- Security Group: Port 5432, Source my IP.
- Turn off RDS Extended Support.
- Once your instance status = “available”:
- After setup:
Copy the endpoint (looks like your-db.xxxxxxx.us-west-2.rds.amazonaws.com).

**After RDS Creation**
- Update your FastAPI DATABASE_URL:
```
DATABASE_URL = "postgresql+psycopg2://<username>:<password>@<endpoint>:5432/<dbname>"
```
- Run your DB migrations or Base.metadata.create_all(engine) to initialize tables.

11/1/25 - Prototype #1 Completed

## Glassboard Analytics Prototype

A lightweight analytics dashboard for small businesses to track website events such as clicks, purchases, and page visits. Built with FastAPI + SQLite (or PostgreSQL for production) and a simple frontend dashboard.  

**Features**
- Track user events on multiple sites via a unique tracking snippet
- View total clicks and top-clicked elements
- Filter events by site and time period (last day, week, month, year)
- Reset all events from the dashboard
- Frontend dashboard with auto-refresh

**Prerequisites**
- Python 3.10+
- `pip` installed
- Optional: PostgreSQL or AWS RDS for production
- Browser for testing frontend HTML pages
- Clone glassboard repository

**Project Structure**
```
glassboard/
├── backend/
│ ├── main.py
│ ├── models.py
│ ├── database.py
│ ├── schemas.py
│ ├── routers/
│ │ ├── events.py
│ │ ├── __init__.py
│ │ ├── snippet.py
│ │ └── stats.py
├── database/
│ ├── events.db
│ └── schemas.sql
├── frontend/
│ ├── index.html # Dashboard page
│ ├── dashboard.js # JS for fetching stats and updating UI
│ └── demo-site.html # Test page for the snippet
├── README.md
├── .gitignore
└── requirements.txt
```

## Setup Instructions

**Install dependencies**

In parent directory:
```
pip install fastapi uvicorn sqlalchemy
pip install psycopg2-binary
```

For local testing, SQLite is used. Ensure Base.metadata.create_all(engine) is called on startup. For production, configure PostgreSQL or AWS RDS and update DATABASE_URL.


**Run the backend server locally**

You will need to change the db url as well to the local one.
```
uvicorn backend.main:app --reload
```
The server runs at http://127.0.0.1:8000.

**Open the dashboard**

Open frontend/index.html in a browser. Use the dropdown to select a site (demo123 or demo456). Stats auto-refresh every 5 seconds.

**Steps to test**
- Open frontend/demo-site.html in live server:
- Click buttons and links to generate events
- Observe backend logs (Received batch: {...})
- Open dashboard (index.html) and select demo123 in the dropdown to see stats update
- Reset events: Click the Reset All Events button in the dashboard. This calls /events/reset to clear all stored events.

**Adding multiple sites**
- Each site’s events will appear separately in the dashboard.
- Provide a unique site_id for each client and update their snippet:

```
<script src="http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/snippet/<unique-site-id>.js"></script>
```

**Notes**
- The backend supports filtering stats by site_id
- The frontend dashboard fetches stats using the selected site from the dropdown
- For production deployment, replace 127.0.0.1:8000 with your server domain
- You can migrate to PostgreSQL/AWS RDS for scalable storage
- Uses FastAPI with Python for backend. PostgreSQL in AWS RDS for database. React for Frontend.

**Future Improvements**
- Add Chart.js visualizations for top elements
- Add time range filters (day/week/month/year)
- Support multiple users with authentication
- Deploy backend and frontend for remote access
- Provide automated snippet generation per user

**Production Notes / Security**
- Eventually I'll need to replace allow_origins=["*"] with allow_origins=["https://myglassboard.com"] or something similar. The asterisk allows all sites which is a security hole and bad for production.


## ssh Instructions

1. Ensure the EC2 Instance is started on AWS.
2. Run the following code, using the Elastic IP of the instance (ec2-44-231-42-67.us-west-2.compute.amazonaws.com):

```
ssh -i "C:\Users\conno\OneDrive\Documents\glassboard\glassboard-rds-key.pem" ec2-user@ec2-44-231-42-67.us-west-2.compute.amazonaws.com
```
3. cd into the glassboard directory:
```
cd ~/glassboard
```
4. Run the file db_test.py in the root directory to ensure connection:
```
python db_test.py
```
5. Run the app either in the foreground or background with nohup:
```
uvicorn backend.main:app --host 0.0.0.0 --port 8000

nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
```
6. While running, test these links:
demo-site:
http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/frontend/demo-site.html
dashboard:
http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/frontend/index.html
start here at login:
http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/frontend/login.html

7. Tips:
To kill all uvicorn processes:
```
pkill -f uvicorn
```
To check the log
```
tail -f nohup.out
```

Use Alembic – an actual migration tool used with SQLAlchemy:
```
pip install alembic

alembic init alembic
```

Then every time you change your model:
```
alembic revision --autogenerate -m "Add Website table"

alembic upgrade head
```


To access PostgreSQL and look at tables and data:
```
psql -h glassboard-rds.c1ymcqk8mlq7.us-west-2.rds.amazonaws.com -U adminuser -d glassboard -W
```

If you have problems with logging in or registering your user, update or install bcrypt, which is the password hashing module used:
```
pip install bcrypt==3.2.0
```