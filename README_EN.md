<div align="center">
  <img src="IMG/Nuxt.png" style="width: 128px; height: 128px;">
</div>

<h1 align="center">
  ATMOSPHERE-PANEL
</h1>

<p align="center">
  <!-- HTML5 -->
  <a href="https://developer.mozilla.org/en-US/docs/Web/HTML" target="_blank"><img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5"/></a>
  <!-- Vue.js -->
  <a href="https://vuejs.org/" target="_blank"><img src="https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white" alt="Vue.js"/></a>
  <!-- Tailwind CSS -->
  <a href="https://tailwindcss.com/" target="_blank"><img src="https://img.shields.io/badge/Tailwind_CSS-38BDF8?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind CSS"/></a>
  <!-- Nuxt.js -->
  <a href="https://nuxt.com/" target="_blank"><img src="https://img.shields.io/badge/Nuxt.js-00DC82?style=for-the-badge&logo=nuxtdotjs&logoColor=white" alt="Nuxt.js"/></a>
  <!-- TypeScript -->
  <a href="https://www.typescriptlang.org/" target="_blank"><img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript"/></a>
  <!-- Python -->
  <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/></a>
  <!-- FastAPI -->
  <a href="https://fastapi.tiangolo.com/" target="_blank"><img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <!-- SQLite -->
  <a href="https://www.sqlite.org/" target="_blank"><img src="https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/></a>
  <!-- bcrypt (Shields.io uses a generic Security badge instead) -->
  <a href="https://github.com/pyca/bcrypt" target="_blank"><img src="https://img.shields.io/badge/Bcrypt-000000?style=for-the-badge&logo=security&logoColor=white" alt="bcrypt"/></a>
  <!-- License -->
  <a href="https://opensource.org/licenses/MIT" target="_blank"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="MIT License"></a>
</p>

<p align="center">
  English | <a href="README.md">简体中文</a> | <a href="README_JP.md">日本語</a>
</p>

<p align="center">
  This project aims to create a versatile, restrained, reliable, and intuitive Minecraft server control panel.
</p>

## Quick Start
Clone the repository
  ```bash
  git clone https://github.com/MiryexOvO/ATMOSPHERE-Panel.git
  ```

## Frontend Development ([Nuxt 4.6.2](https://nuxt.com/docs/getting-started/introduction))

```bash
# 1. Enter the project directory
cd frontend

# 2. Install dependencies (npm is used as an example below)
npm install

# 3. Start the development server
npm run dev

# 4. Deploy to production
npm run build

# 5. Preview the production version locally
npm run preview
```
 
Default panel port: `27777`, configurable  
Visit `http://127.0.0.1:5173`. Nuxt currently uses client-side rendering, and the API is proxied to FastAPI `27777` through `/api`  
On the first startup, the terminal prints the 20-character initial password only once

## Backend ([FastAPI](https://fastapi.tiangolo.com/))

### Linux

```bash
# 1. Enter the project directory
cd backend

# 2. Create a virtual environment
python3 -m venv .venv

# 3. Activate the virtual environment
source .venv/bin/activate  # Windows users should use: .venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start the development server
uvicorn app.main:app --host 0.0.0.0 --port 27777 --reload
```

### Windows

```powershell
# 1. Enter the project directory
cd backend

# 2. Temporarily allow script execution for the current session (to avoid permission errors)
Set-ExecutionPolicy -Scope Process Bypass

# 3. Run the Windows startup script
.\run_windows.ps1
```

Do not use the Linux command `.venv/bin/activate`; the Windows virtual environment entry point is `.venv\\Scripts\\python.exe`  
If the system pip for Python 3.14 is damaged, it is recommended to use Python 3.12 or 3.13 to create the virtual environment

## License
This project is licensed under the [MIT License](LICENSE) ^ ^ 

## Maintenance and Support  
Maintained by [Miryex](https://www.astrelia7.com).