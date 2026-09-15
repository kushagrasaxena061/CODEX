# DARWIN: Autonomous AI Coding Assistant

## What is this project?
DARWIN is a fully functional, automated, and local AI coding assistant. It operates autonomously using a custom Python backend and local LLMs to manage your codebase, write software, and execute terminal commands without relying on external cloud APIs.

## Features
- **Autonomous File Management:** Creates, reads, appends, and modifies files safely using a custom "Human-Forgiving" fuzzy-matching logic.
- **Self-Correcting QA:** Includes a strict Verifier agent that tests if the AI's code actually satisfies your prompt, automatically forcing retries and providing debugging feedback if it fails.
- **Terminal & Git Integration:** Runs terminal commands natively and can securely and seamlessly push code to GitHub.
- **Safe Sandboxing:** Operates entirely inside a dedicated, auto-generating local sandbox folder to prevent accidental damage to your system files.

---

## How to Install and Run on a New Laptop

Follow these steps to set up and run the project from scratch.

### 1. Install System Requirements
Before cloning the repository, make sure you have the following installed on your machine:
- **Python 3.10 or higher**
- **[Ollama](https://ollama.com/)** (Required to run the local AI models). Make sure the Ollama application is running in your background or menu bar.

Once Ollama is installed, open your terminal and download the required models (modify model names if your settings use specific ones):
```bash
ollama pull llama3

# Clone the Repository
git clone [https://github.com/kushagrasaxena061/DARWIN.git](https://github.com/kushagrasaxena061/DARWIN.git)
cd DARWIN


# Setup the Python Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

# Install Dependencies
pip install -r requirements.txt

# Run the Project
./start.sh