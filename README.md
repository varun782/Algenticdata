
live Application link : https://agentic-data-migration-planner-and.vercel.app

# Agentic Data Migration Planner & Reconciliation Workbench

## 🚀 What is this project?
This application is an intelligent assistant designed to help businesses move their data from old systems (like a legacy CRM) into new, modern systems without losing or breaking information along the way.

Data migrations are usually tedious, highly technical, and prone to error. This application solves that problem by acting as an "Agentic Planner". 

Instead of engineers writing hundreds of manual data mapping rules by hand, our AI Agent analyzes the old system, analyzes the new system, and automatically figures out exactly how the data should be moved. 

## ✨ Key Features for Business & Technical Teams

1. **AI-Powered Mapping Strategy**
   - The AI automatically proposes how fields from your old database connect to the new database (e.g., figuring out that a single `full_name` column should be intelligently split into `first_name` and `last_name`).
   - It proactively identifies **Risks** (e.g., "What if someone only has a first name?") and asks **Clarification Questions** before allowing any data to be moved.

2. **Zero-Risk "Dry Run" Engine**
   - Before any real data is touched, the application runs a strict simulation (Dry Run).
   - It safely tests the AI's proposed rules against sample data to ensure it doesn't break any strict database constraints. 
   - It shows you exactly how many records will succeed and "quarantines" any records that fail so humans can review them.

3. **Safe Execution & Reconciliation**
   - Once a human explicitly approves the AI's plan, the application executes the migration, inserting the data safely into the target database.
   - It guarantees no duplicates are created and compares total record counts to ensure nothing was lost.

4. **One-Click Rollbacks**
   - If something looks wrong after a migration is finished, the user can click "Rollback" to instantly undo the entire migration, reverting the target database back to its exact previous state.

## 🛠️ How to Run the Application

This is a complete full-stack web application powered by **Python, FastAPI, SQLite, and Google's Gemini AI**.

### Prerequisites
You will need Python installed on your computer. We recommend using `uv` (a fast Python package manager). You also need a Gemini API Key. 

### Starting the Server
1. Clone this repository.
2. Create a `.env` file in the main folder and add your API key:
   ```text
   GEMINI_API_KEY=your_api_key_here
   ```
3. Start the backend server:
   ```bash
   uv run uvicorn main:app --host 127.0.0.1 --port 8000
   ```
4. Open your web browser and go to `http://127.0.0.1:8000` to interact with the interactive Dashboard!

---
*Built as a demonstration of advanced Agentic workflows and deterministic data reconciliation.*
