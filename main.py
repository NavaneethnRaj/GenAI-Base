import os, requests, json
from urllib.parse import urlparse
from google import genai
from google.genai import types
from dotenv import load_dotenv

from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI()

# Load env once
load_dotenv()
client = genai.Client()
@app.post("/extract/")
async def extract_product_tables_from_pdf(
    file_url: str = Form(...),
    prompt: str = Form(...),
    token: str = Form(...)
):

    if resp.headers.get("Content-Type", "").startswith("text/html"):
        test_url = f"{file_url.strip()}?user_token={token}"
        resp = requests.get(test_url)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Failed to fetch file: {resp.text[:200]}")

    if "application/pdf" not in resp.headers.get("Content-Type", ""):
        raise HTTPException(status_code=400, detail=f"File is not a PDF, got Content-Type={resp.headers.get('Content-Type')}")

    # Get PDF bytes
    pdf_bytes = resp.content

    # Call Gemini model
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            prompt  # your custom prompt
        ]
    )

    # Extract model text
    model_output = None
    if response.candidates:
        parts = response.candidates[0].content.parts
        if parts and hasattr(parts[0], "text"):
            model_output = parts[0].text

    if not model_output:
        raise HTTPException(status_code=500, detail="Gemini returned empty response")

    # Handle possible ```json ... ``` wrappers
    cleaned_output = model_output.strip()
    if cleaned_output.startswith("```"):
        cleaned_output = "\n".join(
            line for line in cleaned_output.splitlines() if not line.strip().startswith("```")
        )

    #  Parse JSON safely
    try:
        json_data = json.loads(cleaned_output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini did not return valid JSON: {str(e)}")

    return {"data": json_data}

@app.post("/FileUpload/")
async def Fileupload_Convert_(
    file: UploadFile = File(...),
    prompt: str = Form(...)
):

    # Read the uploaded PDF file bytes
    pdf_bytes = await file.read()

    # Call the model and get the response
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(
                data=pdf_bytes,
                mime_type='application/pdf',
            ),
            prompt
        ]
    )

    # Prepare CSV filename based on uploaded PDF filename (with .csv extension)
    original_filename = file.filename
    if original_filename and original_filename.lower().endswith('.pdf'):
        csv_filename = original_filename[:-4] + ".csv"
    else:
        csv_filename = (original_filename or "output") + ".csv"

    output_dir = "files"
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, csv_filename)

    # Save CSV response
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(response.text)

    # Return the CSV file as a response
    return FileResponse(csv_path, filename=csv_filename, media_type='text/csv')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8668)