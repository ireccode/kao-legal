# Kao Legal Advisor Agent SaaS

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![AWS CDK](https://img.shields.io/badge/AWS-CDK-orange.svg)](https://aws.amazon.com/cdk/)
[![Next.js](https://img.shields.io/badge/Next.js-latest-black.svg)](https://nextjs.org/)
[![Strands Agents](https://img.shields.io/badge/Strands-Agents_SDK-blue.svg)](https://docs.strands.com/)

**Kao Legal** is a highly secure, AI-powered Legal Advisor Agent SaaS designed to support lawyers and their clients. Built with the **Strands Agents SDK** and **Amazon Bedrock**, this platform automates critical but time-consuming legal workflows—such as post-meeting instruction summaries and secure, PII-anonymized document intake. 

## 🚀 Key Features

### 1. Post‑Meeting Email Summary & Instruction Confirmation
Automates generating structured email summaries for lawyers to send to clients after a meeting.
* **Input**: Call transcripts (Zoom/Teams), lawyer's bullet point notes, matter metadata.
* **Extraction**: Identifies core facts, explicit instructions, assumed responsibilities, deadlines, and open questions.
* **Output**: A professional, legally conservative email draft, explicitly formatted with bulleted actions, assumptions, and necessary caveats.
* **Safety Rules**: Ensures the agent provides *no new legal advice* and respects predefined jurisdiction configurations.

### 2. Anonymized Document Intake (PII Protection)
Automate document ingestion while fully protecting client Personally Identifiable Information (PII).
* **Input Sources**: Direct uploads, Google Drive sync, or email attachments.
* **Secure Storage**: Temporarily houses raw documents in an encrypted S3 bucket with strict IAM constraints.
* **Anonymization Pipeline**: Automatically detects PII (Names, Addresses, Phones, Emails, IDs) and maps them to deterministic codes (`CLIENT_01`, `ADDRESS_01`) *before* they ever reach the LLM. 
* **Agent Operations**: The LLM processes only anonymized versions of the file to classify documents, extract key terms, highlight risks, and generate structural summaries.

## 🏗️ Architecture

The solution incorporates a decoupled, robust technical stack:
* **LLM & Agents**: Amazon Bedrock (`us.anthropic.claude-sonnet-4-6-v1:0` by default), orchestrated via the Strands Agents SDK.
* **Backend Framework**: Python (FastAPI, Pydantic) managed by `uv`.
* **Infrastructure**: AWS CDK (Python). Components include API Gateway, Lambda/Fargate, Storage (S3), NoSQL Data Store (DynamoDB for credits, users, and audit), and Auth (Amazon Cognito).
* **Frontend**: Next.js / React application for user authentication, landing page marketing, and the core dashboard (handling stripe/credit purchases, uploads, and outputs). 

## 📂 Repository Structure

```text
kao-legal/
├── src/kao_legal/         # Agent workflows, prompts, tools, and FastAPI routes
├── infra/                 # AWS CDK definitions (Stacks: Agent, API, Auth, Storage)
├── frontend/              # Next.js front-end landing page and dashboard
├── PRPs/                  # Project requirements, specifications, and architecture docs
├── pyproject.toml         # Python unified dependency management (uv/hatchling)
└── uv.lock                # Dependency lockfile
```

## 🛠️ Getting Started

### Prerequisites
* Python >= 3.12
* [uv](https://github.com/astral-sh/uv) package manager
* AWS CLI configured with active credentials
* Node.js & npm (for frontend and CDK)
* AWS CDK (`npm install -g aws-cdk`)


### 1. Backend Setup

This project uses `uv` for dependency management.

```bash
# Clone the repository
git clone https://github.com/ireccode/kao-legal.git
cd kao-legal

# Sync dependencies and create a virtual environment
uv sync

# Activate the virtual environment
source .venv/bin/activate

# Set up local environment variables
cp .env.example .env
```

### 2. Deploy infrastructure (AWS CDK)

```bash
cd infra
cdk bootstrap
cdk deploy --all
```

### 3. Frontend Setup

```bash
cd frontend/landing-page
npm install
npm run dev
```

## 🔒 Security & Data Privacy

* **Zero-PII to External LLMs**: PII is scrubbed and mapped to an encrypted S3 lookup table before any text is evaluated by the cloud model.
* **Tenant Isolation**: Credits, users, and mapping behaviors isolated using Amazon Cognito and explicit IAM roles. 
* **Ethical Constraints**: The underlying prompts deliberately limit the system from answering open-ended legal advice, enforcing the generation of simple, structured summaries.

## 🤝 Contributing

Contributions to improve the prompts, tool efficiency, and frontend UX are welcome! Please ensure all pull requests follow the pre-configured `ruff` styling guidelines and pass all formatting tests. Checkout `.github/workflows` (when created) for CI requirements.

## 📄 License

*(Add appropriate license information here. e.g. MIT, Proprietary, etc.)*
