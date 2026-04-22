 
PRP: Legal Advisor Agent — Full System Implementation  
Feature file: PRPs/INIT.md 
Date: 2026-04-20 
Confidence score: 8/10  
 
Overview  
Build a production-ready Legal Advisor Agent SaaS with two core AI workflows, a secure AWS backend, and a Next.js frontend 
with credit-based billing. The system is built on the Strands Agents SDK with Amazon Bedrock as the LLM provider.  
 
Critical Documentation URLs  
* Strands Agents SDK: https://strandsagents.com/docs/user-guide/quickstart/overview/
* Strands Tools Reference: https://strandsagents.com/docs/user-guide/concepts/tools/
* Strands Bedrock provider: https://strandsagents.com/docs/user-guide/concepts/model-providers/amazon-bedrock/
* Strands Multi-agent: https://strandsagents.com/docs/user-guide/concepts/multi-agent/agent-to-agent/
* Strands Observability: https://strandsagents.com/docs/user-guide/observability-evaluation/observability/
* AWS Comprehend PII detection: https://docs.aws.amazon.com/comprehend/latest/dg/how-pii.html  
* boto3 Comprehend: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/comprehend.html  
* AWS CDK Python: https://docs.aws.amazon.com/cdk/v2/guide/work-with-cdk-python.html  
* AWS Amplify v6 Next.js: https://docs.amplify.aws/nextjs/build-a-backend/auth/connect-your-frontend/  
* Stripe Next.js integration: https://stripe.com/docs/payments/checkout/how-checkout-works  
* LangFuse Python SDK: https://langfuse.com/docs/sdk/python/sdk-v3 
 
Project Structure  
kao-legal/ 
├── pyproject.toml 
├── .env.example 
├── uv.lock 
├── src/ 
│ └── kao_legal/ 
│ ├── init.py 
│ ├── config/ 
│ │ ├── init.py 
│ │ ├── settings.py # pydantic-settings, all env vars 
│ │ └── tests/ 
│ │ └── test_settings.py 
│ ├── agents/ 
│ │ ├── init.py 
│ │ ├── legal_advisor_agent.py # Main Strands Agent 
│ │ ├── meeting_summary_workflow.py # Use-case 1 orchestration 
│ │ ├── document_intake_workflow.py # Use-case 2 orchestration 
│ │ └── tests/ 
│ │ ├── test_meeting_summary.py 
│ │ └── test_document_intake.py 
│ ├── tools/ 
│ │ ├── init.py 
│ │ ├── s3_document_tool.py # Fetch + parse docs from S3 
│ │ ├── anonymization_tool.py # PII detection + replacement 
│ │ ├── email_draft_tool.py # Format structured → email 
│ │ ├── meeting_notes_tool.py # Normalize transcript/notes 
│ │ ├── summary_export_tool.py # Write results to S3/DynamoDB 
│ │ └── tests/ 
│ │ ├── test_s3_document_tool.py 
│ │ ├── test_anonymization_tool.py 
│ │ └── test_email_draft_tool.py 
│ ├── api/ 
│ │ ├── init.py 
│ │ ├── handlers.py # FastAPI or Lambda handlers 
│ │ ├── models.py # Pydantic request/response models 
│ │ ├── auth.py # Cognito JWT verification 
│ │ ├── credits.py # DynamoDB credit management 
│ │ └── tests/ 
│ │ ├── test_handlers.py 
│ │ └── test_credits.py 
│ └── prompts/ 
│ ├── system_prompt.txt 
│ ├── meeting_summary_prompt.txt 
│ └── document_intake_prompt.txt 
├── infra/ 
│ └── cdk/ 
│ ├── app.py 
│ ├── stacks/ 
│ │ ├── storage_stack.py # S3 buckets 
│ │ ├── compute_stack.py # ECS Fargate / Lambda 
│ │ ├── api_stack.py # API Gateway 
│ │ ├── auth_stack.py # Cognito 
│ │ └── database_stack.py # DynamoDB 
│ └── requirements.txt 
└── frontend/ 
└── landing-page/ 
├── package.json 
├── src/ 
│ ├── app/ 
│ │ ├── layout.tsx 
│ │ ├── page.tsx # Marketing landing 
│ │ ├── dashboard/ 
│ │ │ ├── page.tsx 
│ │ │ ├── meeting/page.tsx 
│ │ │ └── documents/page.tsx 
│ │ └── api/ 
│ │ ├── webhooks/stripe/route.ts 
│ │ └── upload-url/route.ts 
│ ├── components/ 
│ │ ├── AuthProvider.tsx 
│ │ ├── MeetingSummaryForm.tsx 
│ │ └── DocumentUpload.tsx 
│ └── lib/ 
│ ├── amplify.ts 
│ └── api.ts 
└── public/  
 
Phase 1: Project Scaffolding  

### pyproject.toml

```toml
AWS 
Bedrock 
S3 
DynamoDB 
Cognito 
Stripe 
LangFuse 
App 
```
[project] 
name = "kao-legal" 
version = "0.1.0" 
requires-python = ">=3.12" 
dependencies = [ 
"strands-agents>=0.1.0", 
"strands-agents-tools>=0.1.0", 
"boto3>=1.34.0", 
"fastapi>=0.115.0", 
"mangum>=0.19.0", # ASGI adapter for Lambda 
"pydantic>=2.7.0", 
"pydantic-settings>=2.3.0", 
"langfuse>=3.0.0", 
"python-jose[cryptography]>=3.3.0", # Cognito JWT 
"httpx>=0.27.0", 
"structlog>=24.4.0", 
]  
[project.optional-dependencies] 
dev = [ 
"pytest>=8.2.0", 
"pytest-asyncio>=0.23.0", 
"pytest-cov>=5.0.0", 
"ruff>=0.5.0", 
"mypy>=1.10.0", 
"moto[s3,dynamodb,comprehend]>=5.0.0", # AWS mocks for tests 
"pytest-mock>=3.14.0", 
]  
[tool.ruff] 
line-length = 100 
target-version = "py312"  
[tool.ruff.lint] 
select = ["E", "F", "I", "UP"]  
[tool.mypy] 
strict = true 
ignore_missing_imports = true  
[tool.pytest.ini_options] 
asyncio_mode = "auto" 
testpaths = ["src"]  
.env.example  
AWS_REGION=us-east-1 
AWS_PROFILE=default  
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6-v1:0 
BEDROCK_REGION=us-east-1  
S3_RAW_DOCUMENTS_BUCKET=kao-legal-raw-docs 
S3_ANONYMIZED_BUCKET=kao-legal-anonymized 
S3_SUMMARIES_BUCKET=kao-legal-summaries  
DYNAMODB_USERS_TABLE=kao-legal-users 
DYNAMODB_CREDITS_TABLE=kao-legal-credits 
DYNAMODB_AUDIT_TABLE=kao-legal-audit  
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX 
COGNITO_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX 
COGNITO_REGION=us-east-1  
STRIPE_SECRET_KEY=sk_test_... 
STRIPE_WEBHOOK_SECRET=whsec_... 
CREDITS_PER_DOLLAR=100  
LANGFUSE_SECRET_KEY=sk-lf-... 
LANGFUSE_PUBLIC_KEY=pk-lf-... 
LANGFUSE_HOST=https://cloud.langfuse.com  
LOG_LEVEL=INFO 
ENVIRONMENT=development  
```
 
Phase 2: Configuration Layer  

### src/kao_legal/config/settings.py


from functools import lru_cache 
from pydantic_settings import BaseSettings, SettingsConfigDict 
class Settings(BaseSettings): 
model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)  
# AWS
aws_region: str = "us-east-1"
bedrock_model_id: str = "us.anthropic.claude-sonnet-4-6-v1:0"
bedrock_region: str = "us-east-1"
# S3
s3_raw_documents_bucket: str
s3_anonymized_bucket: str
s3_summaries_bucket: str
# DynamoDB
dynamodb_users_table: str
dynamodb_credits_table: str
dynamodb_audit_table: str
# Cognito
cognito_user_pool_id: str
cognito_client_id: str
cognito_region: str = "us-east-1"
# Stripe
stripe_secret_key: str
stripe_webhook_secret: str
credits_per_dollar: int = 100
# LangFuse
langfuse_secret_key: str = ""  langfuse_public_key: str = ""
langfuse_host: str = "https://cloud.langfuse.com"
# App
log_level: str = "INFO"
environment: str = "development"
@lru_cache 
def get_settings() -> Settings: 
return Settings()  
```
 
Phase 3: Core Tools  

Pattern — Strands @tool decorator  
CRITICAL: Strands uses the function docstring as the tool description 
passed to the model. It must be complete and accurate. 
from strands import tool  
@tool 
def fetch_document_from_s3(s3_key: str, bucket_name: str) -> str: 
""" 
Fetch a document from S3 and return its text content.  
Args:
s3_key: The S3 object key for the document.
bucket_name: The S3 bucket name.
Returns:
The extracted text content of the document.
Raises:
ValueError: If document type is not supported (PDF, DOCX, TXT).
"""
...
```

### src/kao_legal/tools/s3_document_tool.py


import boto3 
from strands import tool 
from kao_legal.config.settings import get_settings  
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".eml"}  
@tool 
def fetch_document_from_s3(s3_key: str, bucket_name: str | None = None) -> str: 
""" 
Fetch a document from the secure S3 raw-documents bucket and return its text content. 
Supports PDF, DOCX, TXT, and EML file formats. 
Args:
s3_key: The S3 object key for the document.
bucket_name: Optional bucket override; defaults to configured raw documents bucket.
Returns:
Extracted plain text content of the document.
"""
settings = get_settings()
bucket = bucket_name or settings.s3_raw_documents_bucket
s3 = boto3.client("s3", region_name=settings.aws_region)
response = s3.get_object(Bucket=bucket, Key=s3_key)
content_type = response["ContentType"]
body = response["Body"].read()
return _extract_text(body, s3_key, content_type)
def _extract_text(body: bytes, key: str, content_type: str) -> str: 
ext = "." + key.rsplit(".", 1)[-1].lower() if "." in key else "" 
if ext not in SUPPORTED_EXTENSIONS: 
raise ValueError(f"Unsupported document type: {ext}") 
if ext == ".txt" or "text/plain" in content_type: 
return body.decode("utf-8", errors="replace") 
if ext == ".pdf": 
# Use pypdf (add to pyproject.toml) 
import io 
from pypdf import PdfReader 
reader = PdfReader(io.BytesIO(body)) 
return "\n".join(page.extract_text() or "" for page in reader.pages) 
if ext == ".docx": 
import io 
from docx import Document # python-docx 
doc = Document(io.BytesIO(body)) 
return "\n".join(p.text for p in doc.paragraphs) 
return body.decode("utf-8", errors="replace")  
```

### src/kao_legal/tools/anonymization_tool.py


CRITICAL SECURITY NOTE: This tool runs PII detection and returns ONLY anonymized text. The PII→token mapping is stored in a 
restricted S3 location, never returned to the agent.  
import json 
import re 
import uuid 
import boto3 
from strands import tool 
from kao_legal.config.settings import get_settings 
Comprehend PII entity types to anonymize 
PII_ENTITY_TYPES = [ 
"NAME", "ADDRESS", "EMAIL", "PHONE", "SSN", 
"DATE_TIME", "BANK_ACCOUNT_NUMBER", "CREDIT_DEBIT_NUMBER", 
"PASSPORT_NUMBER", "DRIVER_ID", "URL", 
]  
COMPREHEND LIMITS: max 5KB per request, max 25 entities returned per call 
Must chunk text and handle pagination 
MAX_COMPREHEND_BYTES = 4500 # Stay under 5KB limit  
@tool 
def anonymize_document(text: str, document_id: str) -> str: 
""" 
Detect and replace PII entities in document text with stable anonymous codes. 
The PII mapping is stored securely and never returned. 
Returns only the anonymized text safe for AI processing.  
Args:
text: The raw document text to anonymize.
document_id: Unique identifier used to namespace mapping keys.
Returns:
Anonymized text with PII replaced by codes like PERSON_01, ADDRESS_01.
"""
settings = get_settings()
comprehend = boto3.client("comprehend", region_name=settings.aws_region)
mapping: dict[str, str] = {}         anonymized = _anonymize_chunks(text, comprehend, mapping, document_id)
_store_pii_mapping(document_id, mapping, settings)
return anonymized
def _anonymize_chunks( 
text: str, 
comprehend, 
mapping: dict[str, str], 
document_id: str, 
) -> str: 
"""Chunk text, detect PII in each chunk, build global mapping.""" 
chunks = _chunk_text(text, MAX_COMPREHEND_BYTES) 
entity_counters: dict[str, int] = {} 
result_parts = []  
for chunk in chunks:                                                                                                           entities = _detect_pii_entities(chunk, comprehend)                                                                         anonymized_chunk, entity_counters = _replace_entities(                                                                         chunk, entities, mapping, entity_counters, document_id                                                                 )                                                                                                                          result_parts.append(anonymized_chunk)                                                                                                                                                                                                             return "".join(result_parts)                                                                                                                                                                                                                                                                                                                                                     
def _detect_pii_entities(text: str, comprehend) -> list[dict]: 
response = comprehend.detect_pii_entities(Text=text, LanguageCode="en") 
return response.get("Entities", [])  
def _replace_entities( 
text: str, 
entities: list[dict], 
mapping: dict[str, str], 
counters: dict[str, int], 
document_id: str, 
) -> tuple[str, dict[str, int]]: 
# Sort entities by offset descending to replace without shifting indices 
sorted_entities = sorted(entities, key=lambda e: e["BeginOffset"], reverse=True) 
text_list = list(text)  
for entity in sorted_entities:                                                                                                 pii_value = text[entity["BeginOffset"]:entity["EndOffset"]]                                                                entity_type = entity["Type"]                                                                                                                                                                                                                          # Stable: same raw value gets same token within a document                                                                 lookup_key = f"{document_id}:{entity_type}:{pii_value}"                                                                    if lookup_key not in mapping:                                                                                                  counters[entity_type] = counters.get(entity_type, 0) + 1                                                                   token = f"{entity_type}_{counters[entity_type]:02d}"                                                                       mapping[lookup_key] = token                                                                                                                                                                                                                       token = mapping[lookup_key]                                                                                                text_list[entity["BeginOffset"]:entity["EndOffset"]] = list(token)                                                                                                                                                                                return "".join(text_list), counters                                                                                                                                                                                                                                                                                                                                              
def _chunk_text(text: str, max_bytes: int) -> list[str]: 
chunks = [] 
while text: 
chunk = text[:max_bytes].encode("utf-8") 
# Back off until valid UTF-8 boundary 
while len(chunk) > 0: 
try: 
chunk.decode("utf-8") 
break 
except UnicodeDecodeError: 
chunk = chunk[:-1] 
decoded = chunk.decode("utf-8") 
chunks.append(decoded) 
text = text[len(decoded):] 
return chunks  
def _store_pii_mapping(document_id: str, mapping: dict, settings) -> None: 
"""Store mapping in restricted S3 bucket — NEVER returned to agent.""" 
s3 = boto3.client("s3", region_name=settings.aws_region) 
key = f"mappings/{document_id}.json" 
s3.put_object( 
Bucket=settings.s3_raw_documents_bucket, 
Key=key, 
Body=json.dumps(mapping).encode(), 
ServerSideEncryption="aws:kms", 
)  
```

### src/kao_legal/tools/email_draft_tool.py


from strands import tool  
@tool 
def format_email_draft( 
meeting_summary: str, 
agreed_actions: list[str], 
deadlines: list[str], 
open_questions: list[str], 
lawyer_name: str, 
client_name: str, 
matter_id: str, 
jurisdiction: str = "", 
) -> dict: 
""" 
Format a structured meeting summary into a professional client email draft. 
Returns subject line, plain text body, and HTML body. 
Does not generate new legal advice — only structures provided information.  
Args:
meeting_summary: Brief narrative summary of the meeting.
agreed_actions: List of explicitly agreed actions/instructions.
deadlines: List of key dates and deadlines mentioned.
open_questions: Items requiring client clarification or confirmation.
lawyer_name: Full name of the lawyer sending the email.
client_name: Client's name for salutation.
matter_id: Matter reference number for subject line.
jurisdiction: Optional jurisdiction for footer disclaimer.
Returns:
Dict with keys: subject, body_text, body_html.
"""
disclaimer = (
f"This email summarizes our meeting and is not formal legal advice"
f"{f' under {jurisdiction} law' if jurisdiction else ''}. "
"All instructions are subject to formal written confirmation."  )
actions_text = "\n".join(f"  {i+1}. {a}" for i, a in enumerate(agreed_actions))
deadlines_text = "\n".join(f"  - {d}" for d in deadlines) if deadlines else "  None noted."
questions_text = "\n".join(f"  - {q}" for q in open_questions) if open_questions else "  None."
body_text = f"""Dear {client_name},
Thank you for your time today. Please find below a summary of our meeting and the agreed next steps.  
MEETING SUMMARY 
{meeting_summary}  
AGREED ACTIONS AND INSTRUCTIONS {actions_text}  
KEY DATES AND DEADLINES {deadlines_text}  
OPEN QUESTIONS (Require Your Confirmation) 
{questions_text}  
Please review and confirm the above is an accurate record. If you have any corrections or additions, please let me know 
within 48 hours.  
DISCLAIMER: {disclaimer}  
Warm regards, 
{lawyer_name} 
"""  
subject = f"Meeting Summary — Matter {matter_id}"                                                                                                                                                                                                     return {                                                                                                                       "subject": subject,                                                                                                        "body_text": body_text,                                                                                                    "body_html": _text_to_html(body_text),                                                                                 }                                                                                                                                                                                                                                                                                                                                                                              
def _text_to_html(text: str) -> str: 
import html 
lines = html.escape(text).split("\n") 
return " 
\n".join(lines)  
```

### src/kao_legal/tools/summary_export_tool.py


import json 
from datetime import datetime, UTC 
from strands import tool 
import boto3 
from kao_legal.config.settings import get_settings  
@tool 
def export_summary( 
summary_data: dict, 
lawyer_id: str, 
client_code: str, 
matter_id: str, 
workflow_type: str, 
) -> str: 
""" 
Persist the agent's structured output to S3 and record an audit entry in DynamoDB. 
Returns the S3 key where the summary is stored.  
Args:
summary_data: The structured JSON summary from the agent.
lawyer_id: The authenticated lawyer's user ID.
client_code: Anonymized client identifier.
matter_id: The matter reference number.
workflow_type: Either 'meeting_summary' or 'document_intake'.
Returns:
S3 key of the stored summary.
"""
settings = get_settings()
timestamp = datetime.now(UTC).isoformat()
s3_key = f"{workflow_type}/{lawyer_id}/{matter_id}/{timestamp}.json"
s3 = boto3.client("s3", region_name=settings.aws_region)  s3.put_object(
Bucket=settings.s3_summaries_bucket,
Key=s3_key,
Body=json.dumps(summary_data).encode(),
ServerSideEncryption="aws:kms",
)
_write_audit_record(lawyer_id, client_code, matter_id, s3_key, workflow_type, settings)
return s3_key
def _write_audit_record( 
lawyer_id: str, 
client_code: str, 
matter_id: str, 
s3_key: str, 
workflow_type: str, 
settings, 
) -> None: 
dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region) 
table = dynamodb.Table(settings.dynamodb_audit_table) 
table.put_item(Item={ 
if settings.langfuse_secret_key:      from langfuse.callback import CallbackHandler      callbacks.append(CallbackHandler(          secret_key=settings.langfuse_secret_key,          public_key=settings.langfuse_public_key,          host=settings.langfuse_host,      ))   return Agent(      model=model,      system_prompt=SYSTEM_PROMPT,      tools=[          fetch_document_from_s3,          anonymize_document,          format_email_draft,          export_summary,      ],      callbacks=callbacks,  )  
  src/kao_legal/agents/meeting_summary_workflow.py

  from dataclasses import dataclass
  from strands import Agent
  from kao_legal.agents.legal_advisor_agent import create_legal_advisor_agent

  @dataclass
  class MeetingInput:
      transcript_or_notes: str
      lawyer_id: str
      lawyer_name: str
      client_code: str
      client_name: str
      matter_id: str
      meeting_date: str
      jurisdiction: str = ""
      topic_tags: list[str] = None

  @dataclass
  class MeetingOutput:
      meeting_summary: str
      agreed_actions: list[str]
      deadlines: list[str]
      open_questions: list[str]
      email_subject: str
      email_body_text: str
      email_body_html: str
      s3_summary_key: str
python
```
  MEETING_PROMPT_TEMPLATE = """Process the following meeting transcript/notes and produce a complete structured summary.
python
```
  MATTER DETAILS:
  - Matter ID: {matter_id}
  - Client: {client_code}
  - Lawyer: {lawyer_name}
  - Date: {meeting_date}
  - Jurisdiction: {jurisdiction or 'Not specified'}
  - Topics: {', '.join(topic_tags or [])}
python
```
  TRANSCRIPT/NOTES:
  {transcript_or_notes}
python
```
  REQUIRED OUTPUT:
  1. Extract a brief meeting_summary (2-4 sentences).
  2. List all agreed_actions as explicit instructions the lawyer agreed to take.
  3. List all deadlines and key dates mentioned.
  4. List open_questions that require client confirmation.
  5. Call format_email_draft with the above data.
  6. Call export_summary to persist the result.
  7. Return the final structured JSON."""

  def run_meeting_summary(meeting_input: MeetingInput) -> MeetingOutput:
      agent = create_legal_advisor_agent()
      prompt = MEETING_PROMPT_TEMPLATE.format(**{
          **meeting_input.__dict__,
          "topic_tags": meeting_input.topic_tags or [],
          "jurisdiction": meeting_input.jurisdiction,
      })
python
```
      response = agent(prompt)
      # Parse structured response — agent is prompted to return JSON
      import json
      result = json.loads(str(response))
      return MeetingOutput(**result)
python
```
  ---
  Phase 5: API Layer
python
```
  src/kao_legal/api/models.py

  from pydantic import BaseModel, Field
  from typing import Optional

  class MeetingSummaryRequest(BaseModel):
      transcript_or_notes: str = Field(..., min_length=50)
      client_code: str
      client_name: str
      matter_id: str
      meeting_date: str
      jurisdiction: str = ""
      topic_tags: list[str] = []

  class MeetingSummaryResponse(BaseModel):
      meeting_summary: str
      agreed_actions: list[str]
      deadlines: list[str]
      open_questions: list[str]
      email_subject: str
      email_body_text: str
      email_body_html: str
      s3_summary_key: str
      credits_consumed: int

  class DocumentIntakeRequest(BaseModel):
      s3_keys: list[str] = Field(..., min_items=1)
      client_code: str
      matter_id: str
      document_group_id: str

  class PresignedUploadRequest(BaseModel):
      filename: str
      content_type: str
      matter_id: str

  class PresignedUploadResponse(BaseModel):
      upload_url: str
      s3_key: str
      expires_in_seconds: int
python
```
  src/kao_legal/api/credits.py

  import boto3
  from botocore.exceptions import ClientError
  from kao_legal.config.settings import get_settings
python
```
  CREDITS_PER_MEETING_SUMMARY = 10
  CREDITS_PER_DOCUMENT = 5

  def deduct_credits(lawyer_id: str, amount: int) -> int:
      """
      Atomically deduct credits from a lawyer's account.
      Returns remaining credit balance.
      Raises InsufficientCreditsError if balance would go below zero.
      """
      settings = get_settings()
      dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
      table = dynamodb.Table(settings.dynamodb_credits_table)
python
```
      try:
          response = table.update_item(
              Key={"lawyer_id": lawyer_id},
              UpdateExpression="SET credits = credits - :amount",
              ConditionExpression="credits >= :amount",
              ExpressionAttributeValues={":amount": amount},
              ReturnValues="UPDATED_NEW",
          )
          return int(response["Attributes"]["credits"])
      except ClientError as e:
          if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
              raise InsufficientCreditsError(lawyer_
python
```
⏺ Something is blocking the Write tool. Let me output the full PRP directly here.
python
```
  ---
  PRP: Legal Advisor Agent — Full System Implementation
python
```
  Feature Overview
python
```
  Build a production-ready Legal Advisor Agent SaaS on AWS (Strands Agents + Bedrock AgentCore) with two core workflows and a
  paid Next.js frontend.
python
```
  Source of Truth
python
```
  PRPs/INIT.md — defines purpose, use cases, architecture, tools, workflows, security constraints, and project structure.
python
```
  ---
  Technology Stack
python
```
  ┌─────────────────┬───────────────────────────────────────────────────────┐
  │      Layer      │                      Technology                       │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ Agent framework │ strands-agents Python SDK                             │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ LLM provider    │ Amazon Bedrock (claude-sonnet-4-6 or claude-opus-4-7) │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ Agent runtime   │ ECS Fargate (or Lambda for lightweight)               │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ API             │ AWS API Gateway → FastAPI (Lambda) or ECS             │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ Auth            │ Amazon Cognito (User Pools + Identity Pools)          │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ Credits/billing │ DynamoDB + Stripe                                     │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ Storage         │ Amazon S3 (raw + anonymized documents)                │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ PII detection   │ Amazon Comprehend (+ regex fallback)                  │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ Observability   │ CloudWatch + LangFuse                                 │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ Frontend        │ Next.js 14 App Router                                 │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ Frontend auth   │ AWS Amplify v6 (Cognito)                              │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ IaC             │ AWS CDK (Python)                                      │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ Package manager │ uv                                                    │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ Linting         │ ruff (100-char lines)                                 │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ Type checking   │ mypy                                                  │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ Testing         │ pytest                                                │
  ├─────────────────┼───────────────────────────────────────────────────────┤
  │ Data validation │ Pydantic v2                                           │
  └─────────────────┴───────────────────────────────────────────────────────┘
python
```
  ---
  Key Documentation URLs
python
```
  - Strands Agents SDK: https://strandsagents.com/docs/user-guide/quickstart/overview/
  - Strands GitHub: https://github.com/strands-agents/sdk-python
  - Strands tools guide: https://strandsagents.com/docs/user-guide/concepts/tools/
  - Bedrock model IDs: https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html
  - AWS Comprehend PII: https://docs.aws.amazon.com/comprehend/latest/dg/how-pii.html
  - Boto3 Comprehend: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/comprehend.html
  - LangFuse Python SDK: https://langfuse.com/docs/sdk/python
  - AWS CDK Python: https://docs.aws.amazon.com/cdk/v2/guide/work-with-cdk-python.html
  - Next.js 14 App Router: https://nextjs.org/docs/app
  - AWS Amplify v6 Next.js: https://docs.amplify.aws/nextjs/
  - Stripe Next.js: https://stripe.com/docs/payments/quickstart
  - DynamoDB atomic writes:
  https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html
python
```
  ---
  Project Structure
python
```
  kao-legal/
  ├── pyproject.toml
  ├── .env.example
  ├── src/
  │   └── kao_legal/
  │       ├── __init__.py
  │       ├── config/
  │       │   ├── __init__.py
  │       │   ├── settings.py          # pydantic-settings
  │       │   └── tests/
  │       │       └── test_settings.py
  │       │
  │       ├── agents/
  │       │   ├── __init__.py
  │       │   ├── legal_advisor_agent.py      # Main Strands Agent
  │       │   ├── meeting_summary_workflow.py
  │       │   ├── document_intake_workflow.py
  │       │   └── tests/
  │       │       ├── test_legal_advisor_agent.py
  │       │       ├── test_meeting_summary_workflow.py
  │       │       └── test_document_intake_workflow.py
  │       │
  │       ├── tools/
  │       │   ├── __init__.py
  │       │   ├── s3_document_tool.py
  │       │   ├── anonymization_tool.py
  │       │   ├── email_draft_tool.py
  │       │   ├── meeting_notes_tool.py
  │       │   ├── summary_export_tool.py
  │       │   └── tests/
  │       │       ├── test_s3_document_tool.py
  │       │       ├── test_anonymization_tool.py
  │       │       ├── test_email_draft_tool.py
  │       │       └── test_summary_export_tool.py
  │       │
  │       ├── api/
  │       │   ├── __init__.py
  │       │   ├── app.py               # FastAPI application
  │       │   ├── routes/
  │       │   │   ├── __init__.py
  │       │   │   ├── meeting.py       # POST /meeting-summary
  │       │   │   ├── documents.py     # POST /document-intake
  │       │   │   ├── credits.py       # GET/POST /credits
  │       │   │   └── webhooks.py      # POST /webhooks/stripe
  │       │   ├── middleware/
  │       │   │   ├── __init__.py
  │       │   │   └── auth.py          # Cognito JWT verification
  │       │   └── tests/
  │       │       ├── test_meeting.py
  │       │       └── test_documents.py
  │       │
  │       └── infra/                   # CDK stacks (separate package)
  │
  ├── infra/
  │   ├── app.py
  │   └── stacks/
  │       ├── storage_stack.py         # S3 buckets, DynamoDB
  │       ├── auth_stack.py            # Cognito
  │       ├── api_stack.py             # API Gateway + Lambda/ECS
  │       └── agent_stack.py           # ECS Fargate for Strands
  │
  ├── frontend/
  │   └── landing-page/                # Next.js 14 app
  │       ├── package.json
  │       ├── app/
  │       │   ├── layout.tsx
  │       │   ├── page.tsx             # Marketing landing
  │       │   ├── (auth)/
  │       │   │   ├── sign-in/
  │       │   │   └── sign-up/
  │       │   └── (dashboard)/
  │       │       ├── layout.tsx       # Protected layout
  │       │       ├── meeting/
  │       │       ├── documents/
  │       │       └── credits/
  │       └── lib/
  │           ├── amplify-config.ts
  │           └── stripe-client.ts
  │
  ├── config/
  │   └── agent-prompts/
  │       ├── system_prompt.txt
  │       ├── meeting_summary_prompt.txt
  │       └── document_intake_prompt.txt
  │
  └── docs/
      ├── SECURITY.md
      └── RUNBOOK.md
python
```
  ---
  Critical Patterns and Code Examples
python
```
  1. Strands Agent with Bedrock Provider
python
```
  # src/kao_legal/agents/legal_advisor_agent.py
  from strands import Agent
  from strands.models import BedrockModel

  from kao_legal.config.settings import get_settings
  from kao_legal.tools.s3_document_tool import fetch_document
  from kao_legal.tools.anonymization_tool import anonymize_content
  from kao_legal.tools.email_draft_tool import draft_email
  from kao_legal.tools.meeting_notes_tool import normalize_notes
  from kao_legal.tools.summary_export_tool import export_summary
python
```
  settings = get_settings()
python
```
  SYSTEM_PROMPT = """You are a Legal Support Drafting Assistant helping lawyers structure
  information and draft communications based on provided materials.
python
```
  CAPABILITIES:
  - Summarize meetings and documents
  - Extract instructions, deadlines, and key facts
  - Draft professional emails and structured JSON summaries
python
```
  PROHIBITIONS:
  - Do NOT provide new legal advice or legal opinions
  - Do NOT fabricate facts, deadlines, or instructions
  - Do NOT attempt to re-identify anonymized entities (CLIENT_01, ADDRESS_01, etc.)
  - Do NOT commit the firm to actions not explicitly agreed in source material
python
```
  STYLE:
  - Clear, concise, formal but client-friendly tone
  - Use bullet lists for actions and deadlines
  - Ask clarifying questions if critical information appears missing
  - Include disclaimers: "This is not formal legal advice until confirmed in writing."
  """

  def create_legal_advisor_agent() -> Agent:
      model = BedrockModel(
          model_id=settings.bedrock_model_id,
          region_name=settings.aws_region,
          temperature=0.1,  # Low temperature for factual legal work
          max_tokens=4096,
      )
      return Agent(
          model=model,
          system_prompt=SYSTEM_PROMPT,
          tools=[
              fetch_document,
              anonymize_content,
              draft_email,
              normalize_notes,
              export_summary,
          ],
      )
python
```
  2. Strands Tool Definition Pattern
python
```
  # src/kao_legal/tools/email_draft_tool.py
  from strands import tool
  from pydantic import BaseModel

  class EmailDraftInput(BaseModel):
      meeting_summary: str
      agreed_actions: list[str]
      deadlines: list[dict]
      open_questions: list[str]
      client_name: str
      lawyer_name: str
      matter_id: str

  class EmailDraftOutput(BaseModel):
      subject: str
      body_text: str
      body_html: str

  @tool
  def draft_email(
      meeting_summary: str,
      agreed_actions: list[str],
      deadlines: list[dict],
      open_questions: list[str],
      client_name: str,
      lawyer_name: str,
      matter_id: str,
  ) -> dict:
      """
      Generate a professional email draft from lawyer to client after a meeting.
python
```
      Use this tool after extracting meeting facts to produce a formatted email
      confirming instructions, agreed actions, and next steps.
python
```
      Args:
          meeting_summary: Brief summary of the meeting discussion
          agreed_actions: List of actions explicitly agreed by parties
          deadlines: List of dicts with 'description' and 'due_date' keys
          open_questions: Items requiring client confirmation
          client_name: Full name of the client
          lawyer_name: Full name of the lawyer
          matter_id: Internal matter reference code
python
```
      Returns:
          Dict with 'subject', 'body_text', and 'body_html' keys
      """
      # Implementation builds the email template
      ...
python
```
  CRITICAL GOTCHA: Strands @tool decorated functions use the docstring as the tool description sent to the model. The docstring
   MUST be complete and accurate — the model uses it to decide when and how to call the tool. Missing or vague docstrings cause
   incorrect tool invocation.
python
```
  3. Anonymization Tool — PII Hard Wall
python
```
  # src/kao_legal/tools/anonymization_tool.py
  import boto3
  import re
  import hashlib
  from strands import tool
  from kao_legal.config.settings import get_settings
python
```
  # NOTE: The mapping table is NEVER returned to the agent.
  # It is stored in a restricted S3 bucket and only accessible
  # to internal de-anonymization processes, never the agent.

  @tool
  def anonymize_content(text: str, document_group_id: str) -> str:
      """
      Detect and replace PII in document text with stable anonymized codes.
python
```
      Processes text through AWS Comprehend PII detection and regex patterns.
      Returns ONLY the anonymized text. The PII mapping is stored securely
      and is NOT included in the return value.
python
```
      Args:
          text: Raw document text that may contain PII
          document_group_id: Unique group ID to generate stable codes (e.g., MATTER_001)
python
```
      Returns:
          Anonymized text with PII replaced by stable codes like CLIENT_01, ADDRESS_01
      """
      settings = get_settings()
      mapping: dict[str, str] = {}
      anonymized = text
python
```
      # AWS Comprehend: chunk to 5KB limit
      entities = _detect_pii_entities(text, settings.aws_region)
python
```
      # Sort by offset descending to replace without shifting positions
      for entity in sorted(entities, key=lambda e: e["BeginOffset"], reverse=True):
          original = text[entity["BeginOffset"]:entity["EndOffset"]]
          code = _generate_stable_code(original, entity["Type"], mapping)
          mapping[code] = original
          anonymized = anonymized[:entity["BeginOffset"]] + code + anonymized[entity["EndOffset"]:]
python
```
      # Store mapping securely — never return it
      _store_mapping_secure(document_group_id, mapping, settings)
python
```
      return anonymized

  def _detect_pii_entities(text: str, region: str) -> list[dict]:
      """Calls AWS Comprehend, handles 5KB chunk limit."""
      client = boto3.client("comprehend", region_name=region)
      MAX_BYTES = 4900
      chunks = _chunk_text(text, MAX_BYTES)
      all_entities = []
      offset = 0
      for chunk in chunks:
          response = client.detect_pii_entities(Text=chunk, LanguageCode="en")
          for entity in response.get("Entities", []):
              entity["BeginOffset"] += offset
              entity["EndOffset"] += offset
          all_entities.extend(response.get("Entities", []))
          offset += len(chunk.encode("utf-8"))
      return all_entities

  def _generate_stable_code(original: str, entity_type: str, mapping: dict) -> str:
      """Generate deterministic anonymized code for an entity."""
      # Check if already mapped
      for code, val in mapping.items():
          if val == original:
              return code
      type_prefix = {
          "NAME": "PERSON",
          "ADDRESS": "ADDRESS",
          "EMAIL": "EMAIL",
          "PHONE": "PHONE",
          "SSN": "ID",
      }.get(entity_type, "ENTITY")
      count = sum(1 for k in mapping if k.startswith(type_prefix)) + 1
      return f"{type_prefix}_{count:02d}"
python
```
  4. Settings (pydantic-settings)
python
```
  # src/kao_legal/config/settings.py
  from pydantic_settings import BaseSettings
  from functools import lru_cache

  class Settings(BaseSettings):
      aws_region: str = "us-east-1"
      bedrock_model_id: str = "us.anthropic.claude-sonnet-4-6-v1:0"
      s3_raw_documents_bucket: str
      s3_anonymized_bucket: str
      s3_pii_mapping_bucket: str   # Highly restricted, never accessible to agent
      dynamodb_users_table: str = "kao-legal-users"
      dynamodb_audit_table: str = "kao-legal-audit"
      cognito_user_pool_id: str
      cognito_client_id: str
      stripe_secret_key: str
      stripe_webhook_secret: str
      langfuse_public_key: str = ""
      langfuse_secret_key: str = ""
      langfuse_host: str = "https://cloud.langfuse.com"
python
```
      model_config = {"env_file": ".env", "case_sensitive": False}

  @lru_cache()
  def get_settings() -> Settings:
      return Settings()
python
```
  5. Meeting Summary Workflow
python
```
  # src/kao_legal/agents/meeting_summary_workflow.py
  from dataclasses import dataclass
  from datetime import datetime
  from strands import Agent

  @dataclass
  class MeetingInput:
      transcript_or_notes: str
      lawyer_id: str
      client_code: str
      matter_id: str
      meeting_date: datetime
      jurisdiction: str
      topic_tags: list[str]

  @dataclass
  class MeetingOutput:
      meeting_summary: str
      agreed_actions: list[dict]
      deadlines: list[dict]
      open_questions: list[str]
      email_subject: str
      email_body_text: str
      email_body_html: str

  def run_meeting_summary(agent: Agent, input_data: MeetingInput) -> MeetingOutput:
      """Execute the post-meeting summary workflow."""
      prompt = f"""
      Process this meeting transcript/notes and produce:
      1. A structured internal summary
      2. A professional client email draft
python
```
      MATTER: {input_data.matter_id}
      CLIENT CODE: {input_data.client_code}
      DATE: {input_data.meeting_date.isoformat()}
      JURISDICTION: {input_data.jurisdiction}
python
```
      TRANSCRIPT/NOTES:
      {input_data.transcript_or_notes}
python
```
      Steps:
      1. Use normalize_notes to prepare the input
      2. Extract parties, agreed instructions, deadlines, open questions
      3. Use draft_email to create the client email
      4. Use export_summary to save the structured output
python
```
      Return the structured summary JSON and email draft.
      """
      response = agent(prompt)
      return _parse_workflow_output(response)
python
```
  6. API Layer — FastAPI with Cognito JWT Auth
python
```
  # src/kao_legal/api/middleware/auth.py
  import boto3
  from fastapi import HTTPException, Security
  from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
  from jose import jwk, jwt
  from jose.utils import base64url_decode
python
```
  security = HTTPBearer()
python
```
  async def verify_cognito_token(
      credentials: HTTPAuthorizationCredentials = Security(security),
  ) -> dict:
      """Verify Cognito JWT and return claims."""
      token = credentials.credentials
      # Fetch JWKS from Cognito (cache this in production)
      settings = get_settings()
      jwks_url = (
          f"https://cognito-idp.{settings.aws_region}.amazonaws.com/"
          f"{settings.cognito_user_pool_id}/.well-known/jwks.json"
      )
      claims = _verify_jwt(token, jwks_url, settings.cognito_client_id)
      return claims
python
```
  # src/kao_legal/api/routes/meeting.py
  from fastapi import APIRouter, Depends, HTTPException, status
  from pydantic import BaseModel
  from kao_legal.api.middleware.auth import verify_cognito_token
  from kao_legal.agents.legal_advisor_agent import create_legal_advisor_agent
  from kao_legal.agents.meeting_summary_workflow import MeetingInput, run_meeting_summary
python
```
  router = APIRouter(prefix="/api/v1/meeting", tags=["meeting"])

  class MeetingSummaryRequest(BaseModel):
      transcript_or_notes: str
      client_code: str
      matter_id: str
      meeting_date: str
      jurisdiction: str
      topic_tags: list[str] = []

  @router.post("/summary")
  async def create_meeting_summary(
      request: MeetingSummaryRequest,
      claims: dict = Depends(verify_cognito_token),
  ) -> dict:
      lawyer_id = claims["sub"]
      await _check_and_deduct_credits(lawyer_id, cost=1)
python
```
      agent = create_legal_advisor_agent()
      meeting_input = MeetingInput(
          transcript_or_notes=request.transcript_or_notes,
          lawyer_id=lawyer_id,
          client_code=request.client_code,
          matter_id=request.matter_id,
          meeting_date=datetime.fromisoformat(request.meeting_date),
          jurisdiction=request.jurisdiction,
          topic_tags=request.topic_tags,
      )
      output = run_meeting_summary(agent, meeting_input)
      return output.__dict__
python
```
  7. DynamoDB Credits — Atomic Decrement
python
```
  # src/kao_legal/api/routes/credits.py
  import boto3
  from botocore.exceptions import ClientError

  def deduct_credits(user_id: str, amount: int, table_name: str, region: str) -> int:
      """Atomically deduct credits. Raises if insufficient."""
      dynamodb = boto3.resource("dynamodb", region_name=region)
      table = dynamodb.Table(table_name)
      try:
          response = table.update_item(
              Key={"user_id": user_id},
              UpdateExpression="SET credits = credits - :amount",
              ConditionExpression="credits >= :amount",
              ExpressionAttributeValues={":amount": amount},
              ReturnValues="UPDATED_NEW",
          )
          return response["Attributes"]["credits"]
      except ClientError as e:
          if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
              raise InsufficientCreditsError(f"User {user_id} has insufficient credits")
          raise
python
```
  8. Next.js Frontend — Key Patterns
python
```
  // frontend/landing-page/lib/amplify-config.ts
  import { Amplify } from "aws-amplify";
python
```
  // GOTCHA: Must configure in a Client Component ('use client'),
  // NOT in layout.tsx (Server Component). Use a wrapper component.
  export function configureAmplify() {
    Amplify.configure({
      Auth: {
        Cognito: {
          userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID!,
          userPoolClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID!,
          loginWith: {
            email: true,
          },
        },
      },
    });
  }
python
```
  // frontend/landing-page/app/(dashboard)/layout.tsx
  // Protected layout — check auth server-side
  import { fetchAuthSession } from "aws-amplify/auth/server";
  import { redirect } from "next/navigation";
  import { runWithAmplifyServerContext } from "@/lib/amplify-server-utils";
python
```
  export default async function DashboardLayout({ children }) {
    const authenticated = await runWithAmplifyServerContext({
      nextServerContext: { cookies },
      operation: async (contextSpec) => {
        const session = await fetchAuthSession(contextSpec);
        return !!session.tokens;
      },
    });
    if (!authenticated) redirect("/sign-in");
    return <>{children}</>;
  }
python
```
  // Pre-signed S3 upload pattern
  // 1. Frontend calls POST /api/v1/documents/upload-url
  // 2. Backend returns { uploadUrl, key }
  // 3. Frontend PUTs directly to S3 with the pre-signed URL
  // GOTCHA: Set correct Content-Type header on PUT, must match what was signed
python
```
  async function uploadToS3(file: File, presignedUrl: string) {
    await fetch(presignedUrl, {
      method: "PUT",
      body: file,
      headers: { "Content-Type": file.type },
    });
  }
python
```
  ---
  Implementation Tasks (Ordered)
python
```
  Phase 1: Project Foundation
python
```
  - T1: Initialize uv project, pyproject.toml, ruff, mypy config
  - T2: Create .env.example with all required variables
  - T3: Implement config/settings.py with pydantic-settings + tests
  - T4: Create directory structure per project layout above
python
```
  Phase 2: Agent Tools
python
```
  - T5: Implement tools/s3_document_tool.py — fetch/parse documents from S3 (PDF/DOCX/TXT support via pypdf2/python-docx)
  - T6: Implement tools/anonymization_tool.py — AWS Comprehend PII + chunking + secure mapping storage
  - T7: Implement tools/meeting_notes_tool.py — normalize/segment transcript text
  - T8: Implement tools/email_draft_tool.py — structured email template generator
  - T9: Implement tools/summary_export_tool.py — write JSON output to DynamoDB + S3
  - T10: Write unit tests for all tools (mock boto3 with moto)
python
```
  Phase 3: Agent + Workflows
python
```
  - T11: Implement agents/legal_advisor_agent.py — Strands Agent with Bedrock + all tools
  - T12: Implement agents/meeting_summary_workflow.py
  - T13: Implement agents/document_intake_workflow.py
  - T14: Write integration tests for workflows (mock Bedrock responses)
  - T15: Create system prompts in config/agent-prompts/
python
```
  Phase 4: API Layer
python
```
  - T16: Implement FastAPI api/app.py with CORS + structured error handling
  - T17: Implement api/middleware/auth.py — Cognito JWT verification with JWKS caching
  - T18: Implement api/routes/meeting.py — POST /meeting-summary
  - T19: Implement api/routes/documents.py — POST /document-intake + GET upload-url
  - T20: Implement api/routes/credits.py — GET credits + atomic deduction
  - T21: Implement api/routes/webhooks.py — Stripe webhook → credit increment
  - T22: Write API tests with httpx + pytest-asyncio
python
```
  Phase 5: Infrastructure (CDK)
python
```
  - T23: infra/stacks/storage_stack.py — S3 buckets (raw, anonymized, mapping), DynamoDB tables
  - T24: infra/stacks/auth_stack.py — Cognito User Pool + App Client
  - T25: infra/stacks/api_stack.py — API Gateway + Lambda (FastAPI via Mangum)
  - T26: infra/stacks/agent_stack.py — ECS Fargate for Strands agent runtime
  - T27: IAM roles — agent role (Bedrock + S3 anonymized only), API role, mapping-bucket policy (deny agent role)
python
```
  Phase 6: Frontend
python
```
  - T28: Initialize Next.js 14 app (npx create-next-app@latest)
  - T29: Configure Amplify v6 for Cognito auth (sign-in/sign-up flows)
  - T30: Protected dashboard layout with server-side auth check
  - T31: Meeting Summary page — form + polling for results
  - T32: Document Intake page — multi-file upload via pre-signed URLs
  - T33: Credits page — balance display + Stripe payment link/embed
  - T34: Stripe checkout + webhook confirmation flow
python
```
  Phase 7: Observability
python
```
  - T35: LangFuse integration in agent (callback/tracer on Strands agent)
  - T36: CloudWatch structured logging (Python structlog)
  - T37: Token usage tracking per request → store in DynamoDB audit table
python
```
  ---
  Critical Gotchas and Constraints
python
```
  Strands Agents SDK
python
```
  - Install: uv add strands-agents
  - Bedrock model ID format: us.anthropic.claude-sonnet-4-6-v1:0 (cross-region prefix us. required for Claude 4.x models)
  - @tool docstrings ARE the tool descriptions — make them detailed and accurate
  - The Agent object is stateful per session. Create a new instance per API request or use thread-local storage
  - Tool functions must be synchronous in current Strands SDK; use asyncio.run() wrappers if needed
python
```
  Anonymization (PII Hard Wall)
python
```
  - AWS Comprehend detect_pii_entities max input: 5KB per call — MUST chunk larger documents
  - The PII mapping S3 bucket MUST have an explicit deny IAM policy blocking the agent's execution role
  - Anonymization must be deterministic per document_group_id — use a hash-seeded counter, not random UUIDs
  - Run anonymization as a separate Lambda function (not inside the agent) so the mapping is never in agent memory
python
```
  DynamoDB Credits
python
```
  - Use ConditionExpression="credits >= :amount" for atomic deduction — never read-then-write
  - Initialize new users with credits on Cognito post-confirmation Lambda trigger
python
```
  Cognito + Next.js Amplify v6
python
```
  - Amplify v6 has a breaking change from v5: use fetchAuthSession not Auth.currentSession()
  - Configure Amplify in a 'use client' component (e.g., AmplifyProvider.tsx), wrap layout.tsx body
  - For server-side auth checks, use runWithAmplifyServerContext — different API from client-side
python
```
  S3 Pre-signed URLs
python
```
  - Generate with s3_client.generate_presigned_url("put_object", ...) not get_object
  - Set expiry to 300 seconds (5 min) — enough for upload, short enough for security
  - Frontend must PUT with matching Content-Type header
python
```
  Stripe Webhooks
python
```
  - Always verify webhook signature with stripe.Webhook.construct_event(payload, sig_header, secret)
  - Use idempotency keys when incrementing credits to prevent double-crediting on retries
python
```
  ---
  System Prompt Files
python
```
  config/agent-prompts/system_prompt.txt
python
```
  You are a Legal Support Drafting Assistant helping lawyers structure information
  and draft communications based on provided materials only.
python
```
  ROLE: Legal Support Drafting Assistant (NOT a lawyer)
  FIRM: Kao Legal Services
python
```
  ALLOWED OPERATIONS:
  - Summarize meetings and extract key facts
  - Classify and analyze documents
  - Draft professional emails from lawyer to client
  - Structure data into JSON summaries
  - Ask clarifying questions when information is incomplete
python
```
  STRICT PROHIBITIONS:
  - Do NOT provide new legal advice or legal opinions beyond restating source material
  - Do NOT fabricate facts, deadlines, instructions, or names
  - Do NOT attempt to reverse-engineer or guess real identities behind anonymized codes
  - Do NOT commit the firm to obligations not explicitly stated in source materials
python
```
  HALLUCINATION CONTROL:
  - If information is missing, state "Not specified in provided materials"
  - Use phrases like "According to the meeting notes..." not "The client said..."
  - Flag assumptions clearly with "ASSUMPTION:" prefix
python
```
  DISCLAIMER: Always include in client-facing emails:
  "This communication summarizes our recent discussion. It does not constitute
  formal legal advice. Please review carefully and contact us if any items require
  clarification before confirming."
python
```
  ---
  Security Architecture
python
```
                      ┌─────────────────────────────────┐
                      │  RESTRICTED S3 (PII Mapping)    │
                      │  Policy: DENY agent IAM role    │
                      └─────────┬───────────────────────┘
                                │ Write only (Lambda)
                                │
  ┌──────────┐   raw    ┌──────────────────┐  anonymized  ┌─────────────────┐
  │  Client  │ ──────►  │ Anonymization    │ ──────────►  │  Strands Agent  │
  │(Browser) │          │ Lambda           │              │  (ECS Fargate)  │
  └──────────┘          │ (no Bedrock)     │              │  Bedrock only   │
                        └──────────────────┘              └─────────────────┘
                                                                  │
                                                           ┌──────┴──────┐
                                                           │  S3 Anon    │
                                                           │  DynamoDB   │
                                                           │  (audit)    │
                                                           └─────────────┘
python
```
  ---
  Validation Gates
python
```
  # 1. Setup
  uv venv && uv sync
python
```
  # 2. Linting + formatting
  uv run ruff check --fix .
  uv run ruff format .
python
```
  # 3. Type checking
  uv run mypy src/
python
```
  # 4. Unit tests (with moto for AWS mocking)
  uv run pytest src/ -v --cov=src --cov-report=term-missing
python
```
  # 5. Integration test: agent tool invocation (requires AWS creds)
  uv run pytest src/ -v -m integration
python
```
  # 6. API smoke test (requires running server)
  uv run uvicorn kao_legal.api.app:app --reload &
  curl -X POST http://localhost:8000/api/v1/meeting/summary \
    -H "Authorization: Bearer $TEST_JWT" \
    -H "Content-Type: application/json" \
    -d '{"transcript_or_notes": "Client agreed to purchase property...", \
         "client_code": "CLI001", "matter_id": "MAT001", \
         "meeting_date": "2026-04-20T10:00:00", "jurisdiction": "NSW"}'
python
```
  # 7. Frontend type check
  cd frontend/landing-page && npx tsc --noEmit
python
```
  # 8. CDK synth (validates all stacks)
  cd infra && uv run cdk synth
python
```
  ---
  pyproject.toml Starter

  [project]
  name = "kao-legal"
  version = "0.1.0"
  requires-python = ">=3.12"
  dependencies = [
      "strands-agents>=0.1.0",
      "boto3>=1.34.0",
      "pydantic>=2.0.0",
      "pydantic-settings>=2.0.0",
      "fastapi>=0.111.0",
      "uvicorn>=0.30.0",
      "python-jose[cryptography]>=3.3.0",  # JWT verification
      "mangum>=0.17.0",                    # Lambda ASGI adapter
      "pypdf>=4.0.0",
      "python-docx>=1.1.0",
      "stripe>=9.0.0",
      "langfuse>=2.0.0",
      "structlog>=24.0.0",
      "httpx>=0.27.0",
  ]

  [project.optional-dependencies]
  dev = [
      "pytest>=8.0.0",
      "pytest-asyncio>=0.23.0",
      "pytest-cov>=5.0.0",
      "moto[s3,dynamodb,comprehend]>=5.0.0",
      "ruff>=0.4.0",
      "mypy>=1.10.0",
      "boto3-stubs[s3,dynamodb,comprehend,bedrock-runtime]>=1.34.0",
  ]

  [tool.ruff]
  line-length = 100
  target-version = "py312"

  [tool.ruff.lint]
  select = ["E", "F", "I", "N", "W", "UP"]

  [tool.mypy]
  python_version = "3.12"
  strict = true
  ignore_missing_imports = true

  [tool.pytest.ini_options]
  testpaths = ["src"]
  asyncio_mode = "auto"
  markers = ["integration: marks tests requiring AWS credentials"]
python
```
  ---
  Quality Checklist
python
```
  - All necessary context included (architecture, tools, workflows, security)
  - Validation gates are executable by AI agent
  - References existing CLAUDE.md conventions (uv, ruff, pydantic v2, vertical slice, TDD)
  - Clear implementation path (37 ordered tasks across 7 phases)
  - Error handling documented (credits, PII wall, JWT, Stripe idempotency)
  - Gotchas documented (Amplify v6, Strands docstrings, Comprehend limits, DynamoDB atomic writes)
  - Security architecture explicitly documented (PII mapping bucket deny policy)
  - System prompts included
  - Frontend patterns included (Next.js 14 App Router, server vs client components)
python
```
  PRP Confidence Score: 8.5/10
python
```
  Deductions:
  - (-1.0) Strands Agents SDK is relatively new (2024/2025); exact API signatures may shift — implementing agent should verify
  against live docs at https://strandsagents.com/docs/user-guide/quickstart/python/
  - (-0.5) CDK stack details are high-level; exact Bedrock IAM permission strings and VPC configuration for ECS will need
  iteration
python
```
  ---
python
```
⏺ The PRP is written above (the Write tool encountered issues, so it's output here as instructed). Here's a summary of what's
  included:
python
```
  PRP covers:
  - Full 7-phase implementation (37 ordered tasks): project setup → tools → agent → API → CDK infra → Next.js frontend →
  observability
  - Critical code patterns for Strands @tool definitions, Bedrock model config, Cognito JWT auth, DynamoDB atomic credit
  deduction, S3 pre-signed uploads, and Next.js Amplify v6
  - PII hard wall architecture — the anonymization Lambda is isolated from the agent with an explicit IAM deny policy on the
  mapping bucket
  - System prompt text ready to use in config/agent-prompts/
  - Executable validation gates (ruff, mypy, pytest with moto, CDK synth, API smoke test)
  - All CLAUDE.md conventions followed (uv, ruff 100-char, pydantic v2, vertical slice, TDD, no comments except non-obvious
  WHY)
python
```
  Score: 8.5/10 — high confidence for one-pass implementation; the only uncertainty is exact Strands SDK API signatures which
  should be verified against https://strandsagents.com/docs/user-guide/quickstart/python/ during implementation.


---
## Lessons Learned (Deployment & Debugging Phase)

### 1. Architecture Alignment (Apple Silicon vs. AWS)
*   **Problem:** Building Docker images on Apple Silicon (arm64) for Lambda/Fargate defaults to `x86_64` in CDK/Docker unless explicitly overridden, leading to `Runtime.InvalidEntrypoint` errors.
*   **Lesson:** Always force `--platform=linux/arm64` in Dockerfiles and set `architecture=lambda.Architecture.ARM_64` (Lambda) or `runtime_platform=ecs.CpuArchitecture.ARM64` (Fargate) in CDK when developing on M-series Macs.

### 2. Bedrock Regional Connectivity & Inference Profiles
*   **Problem:** Direct foundation model IDs (e.g., `anthropic.claude-3-sonnet...`) often fail with `ValidationException` in non-US regions like `ap-southeast-2` (Sydney) due to account-specific throughput constraints.
*   **Lesson:** Use **Inference Profiles** (prefix `au.` or `apac.`) for Bedrock in regional deployments. They handle cross-region routing and typically have more generous on-demand quotas.
*   **Quota Tip:** `apac.anthropic.claude-3-5-sonnet-20241022-v2:0` has significantly higher throughput limits in Sydney compared to Haiku profiles.

### 3. Workflow Timeouts & Async Job Pattern
*   **Problem:** API Gateway has a **hard 29-second timeout**. Bedrock agents performing complex tool chains (PII detection → model logic → S3 export) often exceed 60-180 seconds.
*   **Lesson:** Implement the **Async Submit/Poll Pattern**.
    *   **Submit (POST):** Deducts credits, creates a job record in DynamoDB, triggers an asynchronous Lambda invocation (`InvocationType="Event"`), and returns a `job_id` immediately (202 Accepted).
    *   **Poll (GET):** Client polls `/jobs/{job_id}` until `status == "completed"`.
*   **Self-Invocation:** A single Lambda can act as both the API handler and the background worker by checking the incoming event shape and self-invoking asynchronously.

### 4. CDK Circular Dependencies
*   **Problem:** Self-referencing a Lambda's ARN or Name in its own IAM policies or Environment Variables via CDK tokens (e.g., `self.fn.function_arn`) creates a CloudFormation circular dependency.
*   **Lesson:** Use a **literal function name** (string) and manually construct the ARN using pseudo-parameters: `f"arn:aws:lambda:{Aws.REGION}:{Aws.ACCOUNT_ID}:function:{name}"`.

### 5. Credit Safety & Idempotent Refunds
*   **Problem:** Deducting credits before a task starts risks "stealing" credits if the task fails or times out.
*   **Lesson:** Use an atomic DynamoDB `update_item` with a `ConditionExpression` to deduct upfront, but wrap the entire background worker in a `try/except` block that calls a `refund_credits` utility on **any** failure (including timeouts and throttles).

### 6. Stateful Error Handling (Heal-on-Read)
*   **Problem:** If a background Lambda is killed by a 300s timeout, it may fail to update the job status to "FAILED" in DynamoDB, leaving it stuck in "RUNNING".
*   **Lesson:** 
    *   **Tighten Boto:** Set `read_timeout=60` and `max_attempts=2` so the model fails well within the 300s Lambda limit, leaving headroom for the status update.
    *   **Heal-on-Read:** The polling endpoint should check if a job is `RUNNING` but has an `error` field or is older than expected, and automatically update its status to `FAILED`.

```