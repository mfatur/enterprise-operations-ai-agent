# Enterprise Operations AI Agent

An AI-powered sales intelligence application that combines **FastAPI, LangGraph, Gemini, PostgreSQL, and a web-based dashboard** to analyze sales data through natural-language questions.

The system allows users to interact with sales data using an AI Agent instead of manually writing SQL queries or calculating business metrics.

## Overview

**Enterprise Operations AI Agent** is an AI-native sales intelligence application designed to answer operational sales questions and provide real-time dashboard insights.

Users can ask questions such as:

* How much is the total revenue?
* How many products have been sold?
* What are the top 3 best-selling products?
* What is the average order value?

The AI Agent uses **LangGraph** to orchestrate the reasoning and tool-calling workflow, while **Gemini** acts as the language model.

Sales metrics are retrieved from **PostgreSQL** through dedicated sales tools.

## Features

### AI Sales Agent

Natural-language interaction with sales data using a Gemini-powered LangGraph Agent.

### Sales Dashboard

The dashboard provides:

* Total Revenue
* Products Sold
* Average Order Value
* Top Products
* Revenue by Region

### Tool-Based Data Access

The AI Agent can use dedicated sales tools to retrieve business metrics from the database rather than relying on generated answers alone.

### REST API

FastAPI exposes endpoints for:

* AI chat
* Dashboard metrics
* Application health/root endpoint

### Production Deployment

The backend and frontend are served through the deployed FastAPI application.

## Architecture

```text
                         User
                           │
                           ▼
                  ┌─────────────────┐
                  │    Frontend     │
                  │ HTML / CSS / JS │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │     FastAPI     │
                  │   REST API      │
                  └───────┬─────────┘
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
       ┌─────────────┐          ┌─────────────┐
       │ LangGraph   │          │  Dashboard  │
       │ AI Agent    │          │   Metrics   │
       └──────┬──────┘          └──────┬──────┘
              │                        │
              ▼                        ▼
       ┌─────────────┐          ┌─────────────┐
       │   Gemini    │          │ Sales Tools │
       │     LLM     │          └──────┬──────┘
       └─────────────┘                 │
                                       ▼
                               ┌─────────────┐
                               │ PostgreSQL  │
                               └─────────────┘
```

## How the AI Agent Works

The application follows a tool-based agent architecture:

```text
User Question
      │
      ▼
   FastAPI
      │
      ▼
 LangGraph Agent
      │
      ▼
    Gemini
      │
      ├── determine required information
      │
      ▼
  Sales Tools
      │
      ▼
 PostgreSQL
      │
      ▼
  Tool Result
      │
      ▼
    Gemini
      │
      ▼
 Natural Language Answer
      │
      ▼
   Frontend
```

For example:

```text
User:
"Berapa total revenue?"

        ↓

Sales AI Agent

        ↓

get_total_revenue()

        ↓

PostgreSQL

        ↓

Rp303.950.000

        ↓

AI response:
"Total revenue adalah Rp303.950.000."
```

## Tech Stack

### Backend

* Python 3.13
* FastAPI
* Uvicorn
* Pydantic

### AI

* Google Gemini
* Google GenAI SDK
* LangChain Core
* LangChain Google GenAI
* LangGraph

### Database

* PostgreSQL
* Psycopg

### Frontend

* HTML5
* CSS3
* Vanilla JavaScript
* Chart.js

### Development & Deployment

* Git
* GitHub
* FastAPI Cloud

## Project Structure

```text
enterprise-operations-ai-agent/
│
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   └── sales_agent.py
│   │   │
│   │   ├── core/
│   │   │   └── logging_config.py
│   │   │
│   │   ├── database/
│   │   │   └── connection.py
│   │   │
│   │   ├── llm/
│   │   │   └── client.py
│   │   │
│   │   ├── schemas/
│   │   │   └── agent.py
│   │   │
│   │   ├── services/
│   │   │   └── order_service.py
│   │   │
│   │   ├── tools/
│   │   │   └── sales_tools.py
│   │   │
│   │   └── main.py
│   │
│   ├── scripts/
│   │   ├── smoke_sales_agent.py
│   │   ├── smoke_sales_agent_interactive.py
│   │   ├── smoke_sales_tools.py
│   │   └── smoke_tool_node.py
│   │
│   └── tests/
│       ├── integration/
│       └── unit/
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── .gitignore
└── README.md
```

## Sales Tools

The AI Agent has access to dedicated tools for retrieving sales information.

Current capabilities include:

| Tool                      | Purpose                        |
| ------------------------- | ------------------------------ |
| `get_total_revenue`       | Calculate total sales revenue  |
| `get_total_quantity_sold` | Calculate total units sold     |
| `get_average_order_value` | Calculate average order value  |
| `get_top_products`        | Retrieve best-selling products |
| `get_revenue_by_region`   | Retrieve revenue by region     |

This approach keeps business calculations in deterministic tools instead of asking the LLM to calculate everything itself.

## Dashboard API

### `GET /dashboard`

Returns the sales dashboard metrics.

Example response:

```json
{
  "total_revenue": 303950000.0,
  "total_quantity_sold": 85,
  "average_order_value": 30395000.0,
  "top_products": [
    {
      "product": "Wireless Mouse",
      "total_quantity": 35
    },
    {
      "product": "Mechanical Keyboard",
      "total_quantity": 22
    },
    {
      "product": "Laptop Pro",
      "total_quantity": 14
    }
  ],
  "revenue_by_region": [
    {
      "region": "West Java",
      "revenue": 156500000.0
    },
    {
      "region": "Central Java",
      "revenue": 75450000.0
    },
    {
      "region": "East Java",
      "revenue": 72000000.0
    }
  ]
}
```

## AI Chat API

### `POST /chat`

Accepts a natural-language sales question.

Request:

```json
{
  "question": "Berapa total revenue?"
}
```

Response:

```json
{
  "answer": "Total revenue adalah Rp303.950.000."
}
```

## Environment Variables

Create a `.env` file locally.

Example:

```env
GOOGLE_API_KEY=your_google_api_key
DATABASE_URL=your_postgresql_connection_string
```

Never commit `.env` or API keys to GitHub.

The repository already excludes environment files through `.gitignore`.

## Local Development

### 1. Clone the repository

```bash
git clone https://github.com/mfatur/enterprise-operations-ai-agent.git
cd enterprise-operations-ai-agent
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
```

### 3. Activate the virtual environment

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Configure environment variables

Create `.env` and provide the required Gemini and PostgreSQL credentials.

### 6. Run the application

```powershell
uvicorn backend.app.main:app --reload
```

The application will be available locally at:

```text
http://127.0.0.1:8000
```

## Testing

The project contains both unit and integration tests.

Run the test suite with:

```powershell
pytest
```

The project also contains smoke-test scripts for validating the AI Agent and sales tools.

## Deployment

The application is deployed as a FastAPI application.

The FastAPI backend serves both:

* REST API endpoints
* Frontend static files

This allows the deployed application to operate as a single web application rather than requiring a separate frontend hosting service.

## Example

A user can ask:

```text
Berapa total revenue?
```

The AI Agent retrieves the required information through the sales tools and returns:

```text
Total revenue adalah Rp303.950.000.
```

Another example:

```text
Apa 3 produk terlaris?
```

The Agent can retrieve the top products from the database and present the result in natural language.

## Current Dashboard Data

The current application provides the following sales insights:

* Total Revenue: **Rp303.950.000**
* Products Sold: **85 units**
* Average Order Value: **Rp30.395.000**

Top products:

1. Wireless Mouse — 35 units
2. Mechanical Keyboard — 22 units
3. Laptop Pro — 14 units

Revenue by region:

1. West Java — Rp156.500.000
2. Central Java — Rp75.450.000
3. East Java — Rp72.000.000

## Future Improvements

Potential improvements for future versions include:

* Authentication and role-based access
* More sales analysis tools
* Time-series sales analysis
* Automated anomaly detection
* More interactive visualizations
* Conversation memory
* Agent observability and tracing
* Production database scaling
* Automated CI/CD pipeline
* Containerized deployment with Docker

## Project Goal

This project demonstrates how an AI Agent can be integrated into an enterprise-style application to provide natural-language access to operational data.

The main focus is not simply generating text with an LLM, but combining:

**LLM + Agent Orchestration + Tools + Database + API + Frontend + Deployment**

to create a functional AI-native application.
