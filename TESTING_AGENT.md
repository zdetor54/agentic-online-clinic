# Testing Guide for Agentic Workflow

## Prerequisites

1. **Azure OpenAI Credentials:**
   Already configured in `.env` file ✅
   - Uses Azure OpenAI deployment
   - Default model: `gpt-4.1-mini`
   - All credentials loaded automatically

2. **Start FastAPI Server:**
   ```powershell
   # Terminal: uvicorn
   & .venv\Scripts\python.exe -m uvicorn src.api.main:app --reload
   ```

3. **Start Streamlit UI:**
   ```powershell
   # Terminal: streamlit
   & .venv\Scripts\streamlit.exe run ui/clinic.py
   ```

## Test Cases

### Test 1: Search for Patient
**Prompt:** "Find patient John Doe"
**Model:** gpt-4.1-mini (default)
**Expected:** Agent searches and returns matching patients

### Test 2: View Patient by ID
**Prompt:** "Show me patient with ID 1"
**Model:** gpt-4.1-mini
**Expected:** Agent retrieves specific patient details

### Test 3: Create New Patient
**Prompt:** "Create a new patient named Sarah Johnson, born on 1990-05-15, Female, phone 555-1234"
**Model:** gpt-4 (if available)
**Expected:** Agent creates patient and confirms

### Test 4: Complex Query
**Prompt:** "Search for all patients with phone number containing 555"
**Model:** gpt-4.1-mini
**Expected:** Agent searches by phone

## Model Selection

The UI now includes a model dropdown. You can choose:
- **gpt-4.1-mini** (default, fast and cost-effective)
- **gpt-4** (more capable, slower)
- **gpt-3.5-turbo** (fastest, less capable)

> **Note:** Model names must match your Azure OpenAI deployment names

## Debugging Tips

1. **Check logs:** Look for agent tool calls in terminal
2. **API errors:** Check FastAPI terminal for stack traces
3. **UI errors:** Check Streamlit terminal
4. **Azure OpenAI errors:**
   - Verify credentials in `.env` file
   - Check deployment name matches your Azure portal
   - Ensure API version is correct

## Configuration

All Azure OpenAI settings are in `.env`:
```
AZURE_OPENAI_API_KEY="your-key"
AZURE_OPENAI_ENDPOINT="https://your-endpoint.cognitiveservices.azure.com/"
AZURE_OPENAI_API_VERSION="2024-12-01-preview"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4.1-mini"
```

## Architecture Flow

```
User Input (UI)
  → POST /agent/process
    → process_agent_request()
      → PydanticAI Agent
        → Tools (search_patients, create_patient, get_patient_by_id)
          → FastAPI Endpoints (/patients/)
            → CRUD Functions
              → Database
```

## Next Steps

- Test with real OpenAI API key
- Add more sophisticated prompts
- Add conversation history
- Add validation feedback to user
