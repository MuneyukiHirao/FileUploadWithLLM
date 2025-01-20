# README

This repository contains a prototype system for uploading and transforming data files (XLSX/CSV/JSON) using a Large Language Model (LLM). The system is intended to help map user-defined file formats into a standardized data model and automatically generate Python code to transform the data accordingly. It also provides a simple authentication step (`test/test`), error handling, and a basic user interface built with React and Flask.

---

## Purpose

- **File Upload**: Accepts XLSX, CSV, or JSON files (up to 500MB).
- **Data Mapping with LLM**:
  - Detects table headers.
  - Proposes mapping from file columns to required fields of the system’s data model (e.g., a “Customer Master”).
  - Allows natural language corrections of the mapping.
- **Code Generation**: Uses another LLM model to generate Python code that transforms the uploaded data into the required format.
- **Error Handling**: 
  - Displays errors for file corruption, invalid extension, unsupported formats, or LLM rate limit errors.
  - Displays up to 100 error rows in case of data processing issues and then halts.

---

## Features

- **Simple Authentication**: Users log in with username/password (`test/test`) before accessing the upload page.
- **Automatic Header Detection**: The LLM identifies whether a header row exists and which columns map to which fields.
- **Natural Language Remapping**: Users can provide textual instructions to adjust the proposed mapping.
- **Python Code Generation**:
  - After confirming the final mapping, automatically generates a Python script for data transformation.
  - Executes the generated script to produce the final data file.
- **Error Reporting**: Up to 100 errors are displayed on-screen if the data contains invalid rows or if a required field is missing.

---

## Project Structure

```
project_root/
├── server.py
├── app/
│   ├── __init__.py (optional)
│   ├── file_to_json.py
│   ├── llm_api.py
│   ├── main_processor.py
│   └── code_generation.py
├── test/
│   ├── test_main_processor.py
│   ├── test_llm_flow.py
│   ├── test_code_generation.py
│   └── data/
├── system_prompt_header_detection.md
├── system_prompt_mapping.md
├── system_prompt_code_generation.md
├── requirements.txt
└── frontend/
    ├── package.json
    ├── src/
    │   ├── components/
    │   │   ├── Login.jsx
    │   │   └── ...
    │   ├── App.jsx
    │   └── index.js
    └── ...
```

- **`server.py`**: The Flask application entry point.  
- **`app/`**: Python modules for file processing, LLM API calls, and code generation.  
- **`test/`**: Contains various test scripts for the `app/` functionality.  
- **`frontend/`**: React application (Create React App).  
- **`system_prompt_*.md`**: Prompt files for the LLM.

---

## Technology Stack

- **Backend**: Python, Flask
- **Frontend**: React (Create React App)
- **LLM API**: OpenAI (e.g., `gpt-4o`, `o1-mini`)
- **Storage**: Azure Blob Storage (not fully shown here, but assumed for file persistence)
- **Testing**: Python `unittest`/`pytest` (in `test/` folder)

---

## Installation

To set up the environment, ensure you have **Python 3.9+** and **Node.js** installed.

1. **Clone the repository** (example):
\`\`\`bash
git clone https://github.com/example/FileUploadWithLLM.git
cd FileUploadWithLLM
\`\`\`

2. **Python dependencies**:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

3. **Frontend dependencies**:
\`\`\`bash
cd frontend
npm install
cd ..
\`\`\`

---

## Usage

### 1. Run the Flask Server

\`\`\`bash
python server.py
\`\`\`

- The Flask server starts on port 5000 by default.  
- Make sure the port is accessible or forwarded if using a service like GitHub Codespaces.

### 2. Run the React App

\`\`\`bash
cd frontend
npm start
\`\`\`

- By default, the React dev server runs on port 3000.  
- It will attempt to proxy API calls to port 5000 if `package.json` has a proxy setting:
  ```json
  {
    "name": "frontend",
    ...
    "proxy": "http://localhost:5000"
  }
  ```
- If you’re using GitHub Codespaces, confirm that both ports are forwarded (3000 for React, 5000 for Flask).

### 3. Open the App

- Visit `http://localhost:3000` (or your Codespaces URL).  
- Log in with **username**: `test`, **password**: `test`.
- After login, proceed to upload files, check mappings, and generate transformation code.

---

## Workflow Summary

1. **Login**: Enter `test/test`.
2. **Upload a File**: Choose an XLSX/CSV/JSON up to 500MB.  
3. **Header Detection & Mapping**:
   - The system calls the LLM to detect a header row (if any).
   - The system then proposes a mapping from file columns to required fields.  
4. **Mapping Corrections** (Natural Language):
   - You can type instructions such as “Use the second column for CustomerName instead.”
   - The system calls the LLM again to revise the mapping.
5. **Confirm & Generate Code**:
   - Once the required fields are all mapped, the system can generate a Python script for data transformation.
6. **Transform Data**:
   - The script is executed to produce the final file format.
   - Errors are displayed if any row is invalid; if errors reach 100, the process stops.

---

## Notes

- **Authentication** is intentionally minimal: a single user account for prototyping.  
- **CORS**: If developing locally, you may need to configure your Flask app with `flask_cors.CORS(app)` or set a proxy in `package.json` to allow requests from `localhost:3000`.  
- **Production Deployment**: For real-world scenarios, integrate a more robust authentication flow (e.g., Azure AD) and secure the environment variables for OpenAI API keys.  
- **Logging**: Errors and warnings are shown in the UI rather than stored in separate files.

---

## License

(No specific license provided in this example. Add your own license statement if needed.)

---

## Contributing

1. Fork the repository.
2. Create your feature branch (\`git checkout -b feature/new-feature\`).
3. Commit your changes (\`git commit -am 'Add new feature'\`).
4. Push to the branch (\`git push origin feature/new-feature\`).
5. Create a Pull Request.

---

_Thank you for using this prototype!_
