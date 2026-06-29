# Irish International Student Hub
 
A web application that helps international students living in Ireland manage two everyday challenges of student life in one place: **tracking personal expenses** and **keeping up with household bin collection schedules**.
 
Students can record and visualise their spending, set monthly budgets and savings goals, and — using their Eircode and chosen waste-collection provider — see their upcoming bin collection dates with colour-coded bin types and receive an email reminder the evening before each collection.

---
 
## Features
 
- **Secure accounts** — registration and login with JWT-based authentication; passwords hashed with bcrypt. No banking credentials are ever requested or stored.
- **Expense Tracker** — add, edit, delete and view expenses organised by category; set monthly category budgets; track savings goals; view pie and bar charts of spending.
- **Budget alerts & savings goals** — notifications as spending approaches or exceeds a budget, and progress tracking towards savings targets.
- **Bin Schedule Tracker** — enter an Eircode and select a provider (e.g. Greyhound, Panda, Thorntons) to see upcoming collections, with each bin type (general waste, recycling, organic) colour-coded.
- **Email reminders** — a scheduled background task sends a reminder the evening before a collection via Gmail SMTP.
- **Unified dashboard** — a single combined view of recent spending, budget status, savings progress and upcoming bin collections.
- **Responsive UI** — works on desktop and mobile browsers.
