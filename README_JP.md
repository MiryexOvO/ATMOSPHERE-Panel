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
  <!-- bcrypt（Shields.io uses a generic Security badge instead） -->
  <a href="https://github.com/pyca/bcrypt" target="_blank"><img src="https://img.shields.io/badge/Bcrypt-000000?style=for-the-badge&logo=security&logoColor=white" alt="bcrypt"/></a>
  <!-- License -->
  <a href="https://opensource.org/licenses/MIT" target="_blank"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="MIT License"></a>
</p>

<p align="center">
  <a href="README_EN.md">English</a> | <a href="README.md">简体中文</a> | 日本語
</p>

<p align="center">
  多用途で、節度があり、信頼性が高く、直感的な Minecraft サーバーコンソールの作成を目指しています。
</p>

## クイックスタート
リポジトリをクローンします
  ```bash
  git clone https://github.com/MiryexOvO/ATMOSPHERE-Panel.git
  ```

## フロントエンド開発（[Nuxt 4.6.2](https://nuxt.com/docs/getting-started/introduction)）

```bash
# 1. プロジェクトフォルダに移動
cd frontend

# 2. 依存関係をインストール（以下は npm を例にしています）
npm install

# 3. 開発サーバーを起動
npm run dev

# 4. 本番環境へデプロイ
npm run build

# 5. 正式版をローカルでプレビュー
npm run preview
```
 
デフォルトのパネルポート：`27777`、設定可能  
`http://127.0.0.1:5173` にアクセスしてください。現在 Nuxt はクライアントサイドレンダリングを使用しており、API は `/api` を通じて FastAPI `27777` にプロキシされます  
初回起動時、ターミナルには 20 文字の初期パスワードが一度だけ表示されます

## バックエンド（[FastAPI](https://fastapi.tiangolo.com/)）

### Linux

```bash
# 1. プロジェクトフォルダに移動
cd backend

# 2. 仮想環境を作成
python3 -m venv .venv

# 3. 仮想環境を有効化
source .venv/bin/activate  # Windows ユーザーは .venv\Scripts\activate を使用してください

# 4. 依存関係をインストール
pip install -r requirements.txt

# 5. 開発サーバーを起動
uvicorn app.main:app --host 0.0.0.0 --port 27777 --reload
```

### Windows

```powershell
# 1. プロジェクトフォルダに移動
cd backend

# 2. 現在のセッションでスクリプトの実行を一時的に許可（権限エラーを回避するため）
Set-ExecutionPolicy -Scope Process Bypass

# 3. Windows 起動スクリプトを実行
.\run_windows.ps1
```

Linux コマンド `.venv/bin/activate` は使用しないでください。Windows の仮想環境のエントリーポイントは `.venv\\Scripts\\python.exe` です  
Python 3.14 のシステム pip が壊れている場合は、Python 3.12 または 3.13 を使用して仮想環境を作成することをおすすめします

## ライセンス
このプロジェクトは [MIT License](LICENSE) のもとで公開されています ^ ^ 

## メンテナンスとサポート  
Maintained by [Miryex](https://www.astrelia7.com)。