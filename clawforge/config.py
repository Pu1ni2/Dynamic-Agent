import os
from dotenv import load_dotenv

load_dotenv()

# Fix broken SSL_CERT_FILE env var (common in conda on Windows)
ssl_cert = os.environ.get("SSL_CERT_FILE")
if ssl_cert and not os.path.exists(ssl_cert):
    os.environ.pop("SSL_CERT_FILE")

# Debate settings
MAX_ROUNDS = int(os.getenv("MAX_ROUNDS", "3"))

# API settings — OpenRouter
API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

# Model for debate phases (DA + Evaluator in Phase 1-4)
DEBATE_MODEL = "anthropic/claude-3-5-sonnet-20241022"

# Model for DA validation/compilation (Phase 6)
VALIDATION_MODEL = "anthropic/claude-3-5-sonnet-20241022"

# Model tiers for sub-agents (Phase 5)
TIER_TO_MODEL = {
    "FAST": "anthropic/claude-3-5-haiku-20241022",
    "BALANCED": "anthropic/claude-3-5-sonnet-20241022",
    "HEAVY": "anthropic/claude-3-5-sonnet-20241022",
}

