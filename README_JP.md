<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="header/header-dark-jp.png">
    <source media="(prefers-color-scheme: light)" srcset="header/header-light-jp.png">
    <img src="header/header-dark-jp.png" width="700" alt="Banner">
  </picture>
</p>

<p align="center">
  <a href="https://developer.mozilla.org/en-US/docs/Web/HTML" target="_blank"><img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5"/></a>
  <a href="https://vuejs.org/" target="_blank"><img src="https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white" alt="Vue.js"/></a>
  <a href="https://tailwindcss.com/" target="_blank"><img src="https://img.shields.io/badge/Tailwind_CSS-38BDF8?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind CSS"/></a>
  <a href="https://nuxt.com/" target="_blank"><img src="https://img.shields.io/badge/Nuxt.js-00DC82?style=for-the-badge&logo=nuxtdotjs&logoColor=white" alt="Nuxt.js"/></a>
  <a href="https://www.typescriptlang.org/" target="_blank"><img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript"/></a>
  <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://fastapi.tiangolo.com/" target="_blank"><img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <a href="https://www.sqlite.org/" target="_blank"><img src="https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/></a>
  <a href="https://github.com/pyca/bcrypt" target="_blank"><img src="https://img.shields.io/badge/Bcrypt-000000?style=for-the-badge&logo=security&logoColor=white" alt="bcrypt"/></a>
  <a href="https://opensource.org/licenses/MIT" target="_blank"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="MIT License"></a>
</p>

<p align="center">
  <a href="./README_EN.md">English</a> | <a href="./README.md">简体中文</a> | 日本語
</p>

ATMOSPHERE-PANEL は、Web ベースの Minecraft サーバー管理パネルです。認証で保護されたインターフェースから、サーバーインスタンスの登録、サーバーコアとバージョンの選択、バックエンド API によるデプロイと稼働管理を行えます。

プロジェクトは次の 2 つの部分で構成されています。

- `frontend/` — Nuxt ベースの Web インターフェース
- `backend/` — SQLite ストレージとデプロイ API を備えた FastAPI サービス

## 目次

- [機能](#features)
- [すぐ使える（単一プロセス構成）](#standalone)
- [ソースの取得](#source)
- [フロントエンド開発](#frontend-dev)
- [バックエンド開発](#backend-dev)
- [サービス管理](#service-management)
- [開発チェック](#dev-checks)
- [ビルドとリリース（メンテナー向け）](#maintainer-build)
- [ライセンス](#license)
- [メンテナンスとサポート](#support)

<a id="features"></a>

## 機能

- 安全なパスワードハッシュとセッション Cookie による認証
- インスタンス ID、ポート、稼働状態の管理
- Java 版、Bedrock 版、MCDR のコアとバージョン選択
- `.zip` / `.tar.gz` のサーバーコアと Modpack のアップロード（展開時にパストラバーサルと危険ファイルを検査）
- デプロイ時の Java バージョンと JVM メモリ設定
- 公式リソースの参照とミラー設定
- SQLite によるローカルデータストレージ

<a id="standalone"></a>

## すぐ使える（単一プロセス構成）

> - **依存関係なし**：リリースパッケージには Web インターフェースと独立した Python ランタイムが含まれており、Node.js・Python・Nginx を別途デプロイする必要はありません。
> - **単一ポートでアクセス**：1 つのプロセス、1 つのポートでパネル全体を提供します。
> - **外部依存**：Java、BDS、MCDR などのゲーム／管理ランタイムはインスタンスごとに用意する必要があり、パネルのダウンロードパッケージには含まれていません。

### Linux / systemd

一行コマンドでインストール：

```bash
# install.sh を取得して実行し、引数をそのまま渡します（root 以外では自動で sudo を使用）
curl -fsSL https://raw.githubusercontent.com/MiryexOvO/ATMOSPHERE-Panel/main/install.sh \
  | bash -s -- --yes --port 27777
```

対話式インストール：

```bash
# ポートを質問します。プロセス置換により stdin を入力に使用できます
bash <(curl -fsSL https://raw.githubusercontent.com/MiryexOvO/ATMOSPHERE-Panel/main/install.sh)
```

> リリースのダウンロードが GitHub の 504 やタイムアウトで失敗する場合は、GitHub プロキシ経由で取得できます（このコマンドのみに適用）：

```bash
curl -fsSL https://raw.githubusercontent.com/MiryexOvO/ATMOSPHERE-Panel/main/install.sh \
  | ATMOSPHERE_GH_PROXY=https://gh-proxy.com bash -s -- --yes --port 27777
```

既定の入口：`http://<サーバーアドレス>:27777`

| パラメータ | 説明 |
| --- | --- |
| `--yes --port 27777` | 非対話でインストールし、入口ポートを指定 |
| `--version v0.3.0` | リリースバージョンを固定 |
| `--dir /opt/atmosphere-panel` | プログラムディレクトリを変更（既定値。`/opt` 配下であること） |
| `--plan --no-color` | インストール計画のプレビューのみ |

インストーラーは GitHub Releases から対応アーキテクチャのパッケージをダウンロードし、SHA256 を検証、展開して `atmosphere-panel` サービスを登録し、Web ページと API を確認します。`curl`、`tar`、`sha256sum` が必要です。現在は Linux x64、Windows x64、macOS arm64 を提供しており、その他のアーキテクチャは各自でビルドする必要があります。

**初回利用**

- 初期アカウント `Atmo7` とランダムパスワードはインストール終了時に表示され、`/opt/mc-panel/initial-password.txt`（パーミッション 0600）に保存されます
- このファイルが存在する間はいつでも確認できます：`sudo atmosphere password`
- パスワードを忘れた場合や再設定する場合：`sudo atmosphere reset-password`
- パスワードを変更すると認証情報ファイルは自動的に削除され、以前のパスワードは表示できなくなります
- データは `/opt/mc-panel` に保存されます。更新時も保持されますが、アップグレード前にバックアップしてください
- インストーラーは新規インストールと、このインストーラーが作成したディレクトリに対応しています
- 旧ソースインストールから移行する場合は、バックアップ、データベースの移行、旧フロントエンドと Nginx サービスの停止が必要です
- パネルは既存の systemd インスタンス管理のため root で実行されます。ゲームインスタンスは `mc-panel` アカウントを使用します
- 公開済みの Release のみインストールできます。下書きや失敗した Actions は latest になりません

よく使うコマンド：

```bash
# パネルのログを追跡
sudo journalctl -u atmosphere-panel -f
# 初期認証情報を表示（ファイルが存在する間）
sudo atmosphere password
# パスワードを再設定し、認証情報ファイルを書き直す
sudo atmosphere reset-password
# パネルサービスを再起動
sudo systemctl restart atmosphere-panel
```

### Windows / macOS

まず [Releases](https://github.com/MiryexOvO/ATMOSPHERE-Panel/releases) から対応プラットフォームの圧縮ファイルをダウンロードして展開します：

```powershell
# Windows：展開後にターミナルで実行
.\atmosphere-panel.exe --port 27777
```

```bash
# macOS：実行権限を付与して起動
chmod +x ./atmosphere-panel
./atmosphere-panel --port 27777
```

`http://127.0.0.1:27777` を開きます。データは既定で実行ファイル隣の `data/` に保存されるため、書き込み可能なディレクトリに置いてください。`ATMOSPHERE_DATA_DIR` と `ATMOSPHERE_DB_PATH` で変更できます。macOS 版は未署名・未公証です。

### インストーラーについて

- `scripts/install-release.sh`：バイナリインストーラー。リリースのダウンロード、SHA256 の検証、展開、systemd への登録、Web/API の確認を行います
- `install.sh`：互換用の入口。既定で `install-release.sh` に転送し、`--from-source` を付けた場合のみ旧ソースインストールに進みます
- 一行コマンドは `install.sh` を取得し、そこから `install-release.sh` をダウンロードして実行します。ソースのクローンやビルドは不要で、root でない場合は自動で sudo を使います

<a id="source"></a>

## ソースの取得

```bash
# ソースをクローンしてプロジェクトディレクトリに移動
git clone https://github.com/MiryexOvO/ATMOSPHERE-Panel.git
cd ATMOSPHERE-Panel
```

開発ポート：Web `5173`、バックエンド API `27777`。Nuxt はクライアントサイドレンダリングを使用し、`/api` を FastAPI にプロキシします。

<a id="frontend-dev"></a>

## フロントエンド開発（Nuxt 4.6.2）

```bash
# フロントエンドディレクトリに移動
cd frontend
# 依存関係をインストール
pnpm install
# 開発サーバー
pnpm dev
# サーバー上で開発する場合（外部公開）
pnpm dev --host
# 本番ビルド
pnpm build
# 本番ビルドをプレビュー
pnpm preview
```

`http://127.0.0.1:5173` にアクセスします。初回起動時、ターミナルに 20 文字の初期パスワードが表示され、データディレクトリの `initial-password.txt` にも書き込まれます。

<a id="backend-dev"></a>

## バックエンド開発（FastAPI）

### Linux / macOS

```bash
# バックエンドディレクトリに移動
cd backend
# 仮想環境を作成
python3 -m venv .venv
# 仮想環境を有効化
source .venv/bin/activate
# Python の依存関係をインストール
pip install -r requirements.txt
# データディレクトリを指定して開発サーバーを起動
export ATMOSPHERE_DATA_DIR="$PWD/data"
python -m app.launcher --host 0.0.0.0 --port 27777
```

> Python 3.11 以上がインストールされていることを確認してください。

### Windows

```powershell
# バックエンドディレクトリに移動
cd backend
# 現在のセッションのみスクリプト実行を許可し、権限エラーを回避
Set-ExecutionPolicy -Scope Process Bypass
# プロジェクト提供の Windows 起動スクリプトを実行
.\run_windows.ps1
```

> Windows では `.venv\Scripts\python.exe` を使用し、`.venv/bin/activate` は実行しないでください。
>
> Python 3.14 のシステム pip が壊れている場合は、Python 3.12 または 3.13 で仮想環境を作成してください。

<a id="service-management"></a>

## サービス管理

ソースインストールで systemd サービスを登録すると利用できます：

```bash
# サービスの状態を確認
sudo atmosphere status
# バックエンドのログを追跡
sudo atmosphere logs
# パネルサービスを再起動
sudo atmosphere restart
# パネルサービスを停止
sudo atmosphere stop
# 初期認証情報を表示（認証情報ファイルが存在する間）
sudo atmosphere password
# パスワードを再設定し、認証情報ファイルを書き直す
sudo atmosphere reset-password
```

<a id="dev-checks"></a>

## 開発チェック

```bash
# フロントエンドの本番ビルドチェック
cd frontend && npm run build
# バックエンドの Python 構文チェック
cd ../backend && find app -name "*.py" -print0 | xargs -0 -n1 python3 -m py_compile
```

<a id="maintainer-build"></a>

## ビルドとリリース（メンテナー向け）

対象システムに Python 3.12、Node.js 24、プロジェクト指定の pnpm をインストールしてから実行します：

```bash
# バックエンドの依存関係と PyInstaller をインストール
python -m pip install -r backend/requirements.txt pyinstaller==6.11.1
# プラットフォーム向けリリースを生成（例：v0.2.0）
python scripts/build-release.py --version v0.2.0
# 生成したリリースの起動スモークテストを実行
python scripts/smoke-release.py
```

- 成果物：`release/` 配下のプラットフォーム別圧縮ファイルと SHA256 ファイル。スクリプトが実際のサイズを表示します
- 実行に必要なもののみをパッケージします。`node_modules`、ソースデータベース、Java、サーバーデータは含まれません
- 単一ファイルの実行ファイルは初回起動時にランタイムを一時展開します

リリース手順：

1. `v*` タグをプッシュすると 3 プラットフォームのビルドが開始されます
2. すべて成功すると **リリースの下書き** が自動で作成されます
3. 添付ファイル、各プラットフォームの結果、更新内容を確認して手動で公開すると、インストーラーが latest を取得できるようになります
4. Actions の手動実行はビルド成果物のみを生成します。タグの自動プッシュやリリースの自動公開は行いません

<a id="license"></a>

## ライセンス

このプロジェクトは [MIT License](LICENSE) を採用しています

<a id="support"></a>

## メンテナンスとサポート

Maintained by [Miryex](https://www.astrelia7.com)
