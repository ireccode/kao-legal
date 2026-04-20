This document defines the initial context layer, core use cases, and implementation blueprint for a Legal Advisor Agent built with Strands Agents on AWS (Bedrock AgentCore), including a paid front‑end landing page.
The goal is to make this file the “single source of truth” that both humans and the agent can rely on for behavior, architecture, and constraints.

1. Purpose and Scope
The Legal Advisor Agent supports lawyers and their clients by:
* Generating structured email summaries with confirmation of key instructions after a meeting between lawyer and client.
* Orchestrating an anonymized document‑intake workflow that pulls files from Google Drive or email, anonymizes customer data, and sends a sanitized package to an AI agent for pre‑analysis and draft preparation.
This system is built on:
* Strands Agents SDK with Amazon Bedrock as the primary model provider. 
* AWS services for orchestration, storage, security, and monitoring.
* A web landing page where users authenticate, purchase credits, and then invoke the agent.
This project focuses on the agent layer (tools, prompts, context) and the minimal production‑ready AWS implementation, not on deep model training.

2. Core Use Cases
2.1 Post‑Meeting Email Summary and Instruction Confirmation
User: Lawyer
Trigger: After finishing a client meeting, the lawyer wants a clean summary and explicit instruction confirmation to send to the client.
Input sources (one or more):
* Transcript of the call (e.g., from Zoom/Teams).
* Lawyer’s short bullet‑point notes.
* Calendar / matter metadata (client name, matter ID, jurisdiction, practice area).
Agent responsibilities:
* Extract key facts: parties, matter description, jurisdiction, key dates, deadlines.
* Identify explicit instructions: what the client asked the lawyer to do, what the lawyer agreed to do, and any next steps.
* Highlight assumptions, open questions, and items needing client confirmation.
* Generate a professional, legally conservative email draft from the lawyer to the client.
Output:
* Email body in plain text/HTML, ready to send, including:
    * Meeting summary.
    * List of agreed instructions and next steps, clearly enumerated.
    * Any caveats or limitations the lawyer wants to note (e.g., “This is not formal advice until confirmed in writing.”).
Constraints:
* No new legal advice; only restate or structure what’s in the source material.
* Respect jurisdiction and confidentiality guidelines specified in configuration.
* Avoid committing the firm to actions that were not explicitly agreed.

2.2 Anonymized Document Intake via Google Drive / Email
User: Lawyer and/or Intake Paralegal
Goal: Automate intake of client documents while protecting PII by anonymizing data before AI processing.
Input sources:
* Email inbox (e.g., intake@firm.com) or dedicated folder.
* Google Drive folder where clients upload files.
Workflow (high‑level):
1. Detect new documents in:
    * Specified Google Drive folder; or
    * Specified email inbox (attachments).
2. Store raw documents in a secure, encrypted S3 bucket with strict IAM controls.
3. Run an anonymization step to:
    * Detect names, addresses, phone numbers, emails, IDs, and other PII.
    * Replace with stable anonymized codes (e.g., CLIENT_01, ADDRESS_01).
    * Produce a mapping table stored in a secure, access‑restricted location (not exposed to the AI agent).
4. Send only the anonymized content to the AI agent.
5. The agent:
    * Classifies documents (contract, correspondence, court filing, etc.).
    * Extracts key terms, deadlines, counterparties, and risks.
    * Generates a structured summary for the lawyer.
6. A separate, internal process (not the AI agent) can de‑anonymize if needed when a lawyer reviews the output.
Outputs:
* Anonymized, structured JSON summary for each batch or document set.
* Optional draft email to the lawyer summarizing what was received and key points.
Constraints:
* PII mapping must never be sent to the model.
* All external tools must respect data residency, retention, and legal‑ethics rules.
* The anonymization logic must be deterministic enough that lawyers can cross‑reference later.

3. Context Engineering Strategy
We follow a layered context approach inspired by the “context engineering” guide:
3.1 Context Layers
1. System / Role Layer
    * Defines the agent as a Legal Support Assistant, not a lawyer.
    * Emphasizes summarization, structuring, and document handling, not giving original legal advice.
2. Capability Layer
    * Enumerates allowed operations: summarization, classification, extraction, drafting emails, interacting with tools.
    * Explicitly forbids: definitive legal opinions, jurisdiction‑specific advice, or client‑facing commitments.
3. Workflow Layer
    * Encodes the two primary workflows described above.
    * Provides step‑by‑step behavior the agent should follow when invoked for each use case.
4. Guardrails / Safety Layer
    * Instructions on hallucination control, uncertainty expression, and disclaimers.
    * Data handling rules (no re‑identification attempts, no guessing real names).
5. Implementation Layer
    * Tool schemas, AWS resource names and policies (high level), and front‑end interaction patterns.
    * Environment‑specific configuration kept in .env / AWS Parameter Store rather than in this file.
3.2 System Prompt (High‑Level Draft)
The actual prompt will be implemented in code, but conceptually:
* Role: “You are a Legal Support Drafting Assistant helping lawyers structure information and draft communications based on provided materials.”
* Capabilities:
    * Summarize meetings and documents.
    * Extract instructions, deadlines, and key facts.
    * Draft professional emails and structured JSON summaries.
* Prohibitions:
    * Do not provide new legal advice or opinions.
    * Do not fabricate facts or deadlines.
    * Do not attempt to re‑identify anonymized entities.
* Style:
    * Clear, concise, formal but client‑friendly email tone.
    * Use bullet lists for actions and deadlines.
    * Ask clarifying questions if critical information appears missing.

4. AWS and Strands Implementation Blueprint
4.1 Strands Agents / Bedrock Integration
We use the Strands Agents SDK with Amazon Bedrock as the primary model provider, following patterns from:
* sample-getting-started-with-strands-agents-course for agent creation, tool use, Bedrock configuration, and A2A patterns. 
* strands-agents-workshop for project structure, environment variables, and Bedrock setup. 
Key elements:
* Python‑based Strands agent scripts (similar to 01_basic_agents.py, 03_custom_models.py, 02_agent_tools.py). 
* Bedrock model provider configuration (following bedrock-default-config.py / bedrock-detailed-config.py patterns). 
* Tools for:
    * Email template generation.
    * Document parsing (e.g., via S3 + Lambda).
    * Google Drive / email integration (through MCP or custom HTTP tools).
    * Anonymization pipeline.
4.2 High‑Level AWS Architecture
Backend components:
* Amazon Bedrock: Primary LLM endpoint for the Legal Advisor Agent.
* Strands Agent runtime:
    * Deployed as a container (ECS Fargate) or Lambda‑based service hosting the Strands AgentCore runtime.
* API Gateway or Amazon CloudFront + Lambda@Edge:
    * Public HTTPS endpoint for the front‑end to invoke.
* Amazon Cognito:
    * User sign‑up/sign‑in, JWT tokens, social login if needed.
* Billing / Credits:
    * Either integrate with a third‑party payment provider (e.g., Stripe) and store credits in DynamoDB; or
    * Use a simple “credits” table keyed by Cognito user ID.
* Amazon DynamoDB:
    * Store user profiles, remaining credits, and minimal audit logs (prompts/outputs hashed or summarized).
* Amazon S3:
    * Secure storage of raw documents and anonymized variants.
* AWS Lambda:
    * Event‑driven intake (email / Drive), anonymization tasks, and orchestration.
* CloudWatch / X‑Ray / LangFuse:
    * Observability and evaluation, similar to Lab 6 in the Strands course. 
External services:
* Google Drive API integration via a Strands tool or MCP server.
* Email provider (e.g., SES or external SMTP/API) for sending the finalized emails from the lawyer.

5. Agent Tools and Workflows
5.1 Core Tools
The agent will use Strands tools (or MCP tools) for:
1. Document Fetching Tool
    * Fetches files from S3 by key.
    * Validates file type (PDF, DOCX, TXT, email).
    * Returns text chunks or parsed structures.
2. Anonymization Tool
    * Calls a dedicated Lambda or container that:
        * Runs PII detection (regex + ML/Comprehend or similar).
        * Produces anonymized text and a secure mapping.
    * Returns anonymized text only to the agent.
3. Meeting Notes / Transcript Tool
    * Accepts raw notes/transcript and meta (client code, matter ID).
    * Normalizes text and segments it for the model.
    * May store a summarized representation for later reference.
4. Email Draft Tool
    * Given structured summary and instructions, returns:
        * subject
        * body_text
        * body_html (optional).
    * The agent can call this to re‑format or adjust tone.
5. Summary Export Tool
    * Writes agent output (summary JSON + email draft) to DynamoDB/S3 for audit.
5.2 Workflow: Post‑Meeting Summary
Inputs to agent:
* Transcript or notes (raw text).
* lawyer_id, client_code, matter_id.
* Meeting metadata: date/time, jurisdiction, topic tags.
Steps (encoded in prompt + orchestration):
1. Normalize and chunk transcript/notes.
2. Extract:
    * Parties, roles, matter description.
    * Agreed instructions and responsibilities.
    * Deadlines, key dates, and follow‑ups.
3. Detect unclear or ambiguous points; note them in a separate section.
4. Generate structured internal JSON:
    * meeting_summary
    * agreed_actions
    * deadlines
    * open_questions
5. Call Email Draft Tool to create a client‑facing email.
6. Return both the structured JSON and email draft to the API layer.
5.3 Workflow: Anonymized Document Intake
Inputs:
* S3 keys (raw documents) prepared by intake Lambda.
* Metadata: client_code, matter_id, document_group_id.
Steps:
1. For each document:
    * Call Document Fetching Tool.
    * Pass content to Anonymization Tool.
2. Build an anonymized document set.
3. Run classification/extraction:
    * Document type.
    * Key clauses / issues.
    * Dates and obligations.
4. Produce structured JSON summary for each document and for the set.
5. Optionally generate an internal email draft to the lawyer summarizing the batch.

6. Front‑End Landing Page and Payment Flow
6.1 Landing Page Goals
The landing page is a simple, production‑ready front‑end that:
* Explains the value proposition for lawyers and firms.
* Allows users to sign up / sign in (via Cognito).
* Handles payment / credit purchase.
* Provides a dashboard to:
    * Upload meeting notes or transcripts.
    * Trigger the Post‑Meeting Summary workflow.
    * Upload or link document sets for anonymized intake.
    * View generated summaries and email drafts.
    * Track credits and billing.
6.2 Front‑End Stack (Suggested)
* Framework: React / Next.js SPA or SSR app.
* Auth: AWS Amplify UI components or direct Cognito integration.
* API Calls:
    * HTTPS calls to API Gateway endpoints secured with Cognito JWT.
* File Uploads:
    * Pre‑signed S3 URLs for upload.
* Payment:
    * Integrate Stripe/PayPal or similar; on successful payment, API increments credits in DynamoDB.
6.3 UX Flows
1. New user:
    * Lands on marketing page.
    * Clicks “Get Started”.
    * Signs up via Cognito.
    * Purchases initial credits.
    * Accesses dashboard.
2. Post‑meeting workflow:
    * Lawyer selects “Create Meeting Summary”.
    * Uploads transcript or pastes notes, fills out metadata.
    * Clicks “Generate Summary”, consumes credits.
    * Front‑end polls or uses WebSockets until agent returns output.
    * UI shows:
        * Structured summary.
        * Email draft.
        * “Copy to clipboard” and “Send via Email” options.
3. Document intake workflow:
    * Lawyer selects “Anonymize & Analyze Documents”.
    * Uploads documents or confirms linkage to a Google Drive folder/email address (configured out‑of‑band).
    * Triggers anonymization workflow, consumes credits per document/page.
    * UI presents anonymized summaries, tags, and internal email draft.

7. Security, Compliance, and Guardrails
* PII Handling:
    * Raw documents and mapping tables stored in tightly restricted S3 buckets.
    * Agent only sees anonymized data.
* Access Control:
    * Cognito groups/roles mapped to IAM roles for S3 and API access.
* Logging and Observability:
    * Use CloudWatch and, optionally, LangFuse as per the Strands examples to monitor prompts, token usage, and outcomes. 
* Ethical / Legal:
    * All client‑facing outputs must be reviewed by a qualified lawyer.
    * System includes reminders and disclaimers in emails.
* Rate Limits & Cost Controls:
    * Per‑user credit limits and per‑request size checks.
    * Background jobs for heavy processing, with clear progress indicators.

8. Project Structure (Proposed)
Aligning with the Strands examples, but focused on this product:

* /agents/
    * legal_advisor_agent.py (main Strands agent with tools and prompts)
    * meeting_summary_workflow.py
    * document_intake_workflow.py
* /tools/
    * s3_document_tool.py
    * anonymization_tool.py
    * email_draft_tool.py
    * google_drive_tool.py
* /infra/
    * cdk/ or terraform/ definitions for API Gateway, Lambda/ECS, S3, DynamoDB, Cognito, Bedrock permissions.
* /frontend/
    * landing-page/ (Next.js / React app).
* /config/
    * .env.example
    * bedrock-config.json
    * agent-prompts/ (system and workflow prompts, if not in code).
* /docs/
    * INITIAL.md (this file)
    * SECURITY.md
    * RUNBOOK.md

9. Next Steps
1. Define concrete system prompts and workflow prompts in /agent-prompts/, using this file as the source of truth.
2. Implement legal_advisor_agent.py using Strands Agents patterns for Bedrock providers and tools. 
3. Build and deploy the AWS infrastructure (minimum: API Gateway, Lambda/ECS, S3, DynamoDB, Cognito, Bedrock integration).
4. Implement the landing page with authentication, credit purchase, and core UI flows.
5. Add observability and evaluation (e.g., LangFuse, RAGAS‑style evaluation) as in the Strands samples, focusing on accuracy of instruction extraction and safety of anonymization.