## SimbaServerless

FastAPI handlers for Discord interactions, deployed through Mangum or Vercel.

### Required environment variables

- `APPLICATION_ID`: Discord application ID.
- `CLIENT_PUBLIC_KEY`: Discord application public key used to verify interaction signatures.
- `TOKEN`: Discord bot token for bot-authenticated API calls.
- `ENCRYPT_KEY`: shared key for the `/recruit` endpoint and recruit payloads.
- `SUPABASE_URL` and `SUPABASE_KEY`: Supabase connection settings.

Optional deployment-specific variables may be required by the EV.io integration, including `KEY`, `VALUE`, and `CHANNEL_IDS`.

### Local development

Install the pinned dependencies, export the environment variables, and start FastAPI:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn src.main:app --reload
```

The Discord interaction endpoint is `/interactions`. Discord requests must include valid Ed25519 signature headers. Signatures older than five minutes are rejected.

### Tests

Run the standard-library regression tests with:

```powershell
python -m unittest discover -s tests -v
```

### Deployment

- AWS Lambda uses `src.lambda_handler.handler` through Mangum.
- Vercel uses `src/main.py` as configured in `vercel.json`.
- Docker uses the AWS Lambda Python base image and the same handler.
