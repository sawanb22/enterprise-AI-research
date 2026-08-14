import base64
import json
import logging
from typing import Any
from urllib.parse import quote

import httpx

from ..config import Settings

logger = logging.getLogger(__name__)


class VisionProcessor:
    """Extracts analytical data and structured summaries from diagram and chart images using Bedrock Converse API."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model_id = settings.effective_vision_model_id
        self.max_calls = settings.max_vision_calls_per_doc
        self.region = settings.aws_region
        self.endpoint_url = settings.bedrock_endpoint_url
        self.bearer_token = settings.effective_bedrock_bearer_token

        if self.endpoint_url:
            self.base_endpoint = self.endpoint_url.rstrip("/")
        else:
            self.base_endpoint = f"https://bedrock-runtime.{self.region}.amazonaws.com"

        self.boto_client = None
        if not self.bearer_token:
            try:
                import boto3

                client_kwargs: dict[str, Any] = {"region_name": self.region}
                if settings.aws_access_key_id and settings.aws_secret_access_key:
                    client_kwargs["aws_access_key_id"] = settings.aws_access_key_id
                    client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
                    if settings.aws_session_token:
                        client_kwargs["aws_session_token"] = settings.aws_session_token
                if self.endpoint_url:
                    client_kwargs["endpoint_url"] = self.endpoint_url

                self.boto_client = boto3.client("bedrock-runtime", **client_kwargs)
            except Exception as exc:
                logger.debug("Could not initialize boto3 for VisionProcessor: %s", exc)

    def summarize_image(self, image_bytes: bytes, page_context: str = "", image_format: str = "png") -> str:
        """Analyze a chart/diagram image and extract analytical numbers, labels, and trends."""
        if not image_bytes or not self.settings.is_vision_configured:
            return ""

        prompt = (
            "You are an expert document data analyst. Analyze this diagram or chart extracted from a report.\n"
            "Extract and summarize:\n"
            "1. Diagram Type & Title (if visible)\n"
            "2. Key Metrics & Exact Numbers shown (axes, data points, legends, labels)\n"
            "3. Core Trend, Comparison, or Analytical Finding\n"
            f"Surrounding Page Context: {page_context[:400] if page_context else 'None'}\n"
            "Keep the response concise, factual, and strictly data-oriented."
        )

        # 1. Bearer token / Mantle invocation
        if self.bearer_token:
            url = f"{self.base_endpoint}/model/{quote(self.model_id, safe='')}/converse"
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            # Bedrock converse payload
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "image": {
                                    "format": image_format.lower() if image_format.lower() in ("png", "jpeg", "webp", "gif") else "png",
                                    "source": {"bytes": base64.b64encode(image_bytes).decode("utf-8")},
                                }
                            },
                            {"text": prompt},
                        ],
                    }
                ],
                "inferenceConfig": {"maxTokens": 400, "temperature": 0.1},
            }

            try:
                with httpx.Client(timeout=45.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        output_msg = data.get("output", {}).get("message", {}).get("content", [])
                        texts = [item.get("text", "") for item in output_msg if "text" in item]
                        return " ".join(texts).strip()
                    else:
                        logger.debug("Vision Converse HTTP %d: %s", resp.status_code, resp.text[:200])
                        return ""
            except Exception as exc:
                logger.debug("Vision API request failed: %s", exc)
                return ""

        # 2. AWS IAM / Boto3 invocation
        elif self.boto_client:
            try:
                response = self.boto_client.converse(
                    modelId=self.model_id,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "image": {
                                        "format": image_format.lower() if image_format.lower() in ("png", "jpeg", "webp", "gif") else "png",
                                        "source": {"bytes": image_bytes},
                                    }
                                },
                                {"text": prompt},
                            ],
                        }
                    ],
                    inferenceConfig={"maxTokens": 400, "temperature": 0.1},
                )
                output_msg = response.get("output", {}).get("message", {}).get("content", [])
                texts = [item.get("text", "") for item in output_msg if "text" in item]
                return " ".join(texts).strip()
            except Exception as exc:
                logger.debug("Boto3 Vision converse failed: %s", exc)
                return ""

        return ""
