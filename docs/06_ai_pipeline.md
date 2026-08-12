# 6. AI Pipeline

## Design principle

The LLM is a bounded semantic service. It does not own workflow state, decide whether citations exist, store data, or receive unrestricted web content. Traditional code owns those responsibilities.

## Provider interface

```text
LLMProvider
  plan(question) -> ResearchPlan
  extract_claims(source_text, source_id) -> ClaimDraft[]
  compare_claims(left, right) -> EvidenceAssessmentDraft
  synthesise(question, claims, assessments) -> ConclusionDraft[]
```

The application receives a configured provider name and model through environment variables. API keys are never stored in database records, logs, or the repository.

## Provider decision

Use a free cloud provider for the challenge; do not depend on a slow local model. **Groq is the recommended first integration** because its free plan and models are currently documented, its OpenAI-compatible API reduces integration effort, and its inference speed suits a live demo. The implementation remains provider-neutral so a fallback can be added without changing the workflow.

The exact model will be selected after a small structured-output test. Selection criteria: valid JSON reliability, instruction following, speed, free-tier rate limits, and availability from India. Do not lock a model name into the architecture or UI.

## Structured outputs

Each AI stage has a Pydantic response model. Invalid JSON/root shapes, unknown claim IDs, missing excerpts, unsupported enums, or unsupported conclusions are rejected and retried once with a repair prompt; further failure is logged. The application records when an AI-response repair was used.

## Prompt-injection and grounding controls

- System instruction states that source text is untrusted reference material, never a command.
- Source text is separated with clear delimiters and clipped to a known maximum.
- Extraction is performed per source snapshot, not from an uncontrolled aggregate of web pages.
- Synthesis receives structured claims and relationships, not raw web pages.
- Citation validation happens in application code, not by trusting the model.

## Transparency metadata

Store provider name, model name, prompt-template version, stage, timestamp, and non-secret error/status metadata per run. This supports reproducibility without retaining secrets or unnecessary raw prompts.
