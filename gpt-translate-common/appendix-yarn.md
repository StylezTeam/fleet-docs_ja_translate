# Yarnのインストール方法のメモ

## 1. 古いnodejsを削除する
```
sudo apt remove nodejs
```

## 2. 古いYarnの鍵を削除する（既に古い鍵がある場合）：
```
sudo apt-key del "72ECF46A56B4AD39C907BBB71646B01B86E50310"
```

## 3. 新しい方法でYarnの公開鍵をインストール：
```
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo gpg --dearmor -o /usr/share/keyrings/yarn-archive-keyring.gpg
```

## 4. 古いYarnのソースリストを削除（存在する場合）：
```
sudo rm /etc/apt/sources.list.d/yarn.list
```

## 5. 新しいYarnのソースリストを追加：
```
echo "deb [signed-by=/usr/share/keyrings/yarn-archive-keyring.gpg] https://dl.yarnpkg.com/debian stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
```

## 6. パッケージリストを更新：
```
sudo apt update
```

## 7. Node.jsをインストール（まだインストールされていない場合）：
```
sudo apt install nodejs
```

## 8. Yarnをインストール：
```
sudo apt install yarn
```

## 9. インストールを確認：
```
yarn --version
node --version
```

# 注意点：

Ubuntuのデフォルトのnodejsはバージョン12と古いため気をつける
