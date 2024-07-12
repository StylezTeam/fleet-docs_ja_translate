# このツールについて

このツールは、OpenAIのAPIを使って、英語のマークダウン形式のファイルを日本語に変換するものです。

変換元のファイルは、英語のマークダウン形式である必要があります。
翻訳先のファイルは、日本語のマークダウン形式に変換されます。

## 必要な物

- python3
- OpenAIのAPIキー
以下の環境変数でAPIキーを実行するシェルで定義してください。

```
OPENAI_API_KEY=
```

## 動かし方

本リポジトリは、git subtreeで読み込ませて利用することをおすすめします。

1. 翻訳したいリポジトリをローカルにcloneする
2. 翻訳したいリポジトリ名に_jaと付けたリポジトリをGitLabやGitHub上で作成する。
   これを翻訳されたファイルを保存するターゲットリポジトリとします。
3. ターゲットリポジトリをローカルにcloneする。
4. 本スクリプトを入れるツール用リポジトリを作成する。
4. ツール用リポジトリに本リポジトリ(gpt-translate-common-en-ja)をgit subtreeで読み込む
5. 翻訳前のファイルが入っているディレクトリをmarkdown_translator_openai.py内で定義
(定義例: SOURCE_DIR = os.path.abspath(current_dir + "/../fleet-docs/docs") )
6. 翻訳後のファイルを入れるディレクトリをmarkdown_translator_openai.py内で定義
(定義例: TARGET_DIR = os.path.abspath(current_dir + "/../fleet-docs_ja/i18n/ja/docusaurus-plugin-content-docs") )
7. python3の仮想環境を作成して、有効化
8. pip3で必要なpythonモジュールをインストール
9. python3 ./markdown_translator_openai.py で翻訳を開始する

## ディレクトリ構造

- <翻訳したいリポジトリのディレクトリ>
- <翻訳後のファイルを入れるリポジトリ>
- <本ツールを入れるツール用リポジトリ>
上記のように並列に並べてください。

## 補足

### 4. git subtree での読み込ませ方

```
cd /<ターゲットリポジトリ>
git subtree add 
```

### 5. 

### 6. 

### 7. 仮想環境の作り方

```
python3 -m venv <env_name>
```

#### 作成例
```
python3 -m venv venv
```

#### アクティベート

```
source <env_name>/bin/activate
```

```
source venv/bin/activate
```

### 8. pip3で必要なpythonモジュールをインストール

```
pip install -r requirements.txt
```


