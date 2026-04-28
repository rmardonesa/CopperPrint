<p align="center">
  <img width="150" height="150" alt="image" src="https://github.com/user-attachments/assets/f2e5e30b-6b83-4e69-a0b2-39e2f03eb0ab" />
</p>

<p align="center">
  
  <img src="https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white">
  <img src="https://img.shields.io/badge/SQL_Server-CC2927?style=for-the-badge&logo=microsoft-sql-server&logoColor=white">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Astro-FF5D01?logo=astro&logoColor=fff&style=for-the-badge">
  <img src="https://img.shields.io/badge/Sass-CC6699?style=for-the-badge&logo=sass&logoColor=white">
  <img src="https://img.shields.io/badge/Obsidian-4B275F?style=for-the-badge&logo=elixir&logoColor=white">
  <img src="https://img.shields.io/badge/BigQuery-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white">
  <img src="https://img.shields.io/badge/Power_BI-FFCB36?style=for-the-badge&logo=ScrollReveal&logoColor=white">
  <img src="https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white">
  
</p>

# 👷 CopperPrint

End-to-end ETL pipeline analyzing water consumption and copper production data from chilean mining (2014–2024)

## Overview

Data sourced from COCHILCO 🇨🇱 (Chilean Copper Commission) is extracted via Python, transformed into a star schema in SQL Server, and loaded into BigQuery as the analytical data warehouse. A Power BI dashboard connects via DirectQuery to expose six analytical views across production, water intensity, regional breakdown, and demand projections to 2034.

## Pipeline

COCHILCO → Python ETL → Docker / SQL Server → BigQuery → Power BI



## Tech Stack

- **ETL**: Python · pandas · SQLAlchemy · google-cloud-bigquery
- **OLTP**: SQL Server 2022 (Docker Compose) · T-SQL · star schema · 7 tables
- **DWH**: Google BigQuery · 6 analytical views · southamerica-west1
- **BI**: Power BI Service · DirectQuery · DAX
- **Web**: Astro · TypeScript · SCSS · Vercel
- **Environment**: Debian 12 · conda · lazydocker
- **Tools**: DBeaver · Obsidian · VSCode

## Local Setup

```bash
# 1. Start SQL Server
docker compose up -d

# 2. Run the pipeline (idempotent)
conda run -n copperprint python pipeline/main.py


(Requires .env with SQL Server credentials and a BigQuery service account JSON)

```


## Live View

https://copperprint.vercel.app


