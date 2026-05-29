# SSE ストリーミングの内部実装解説

## Q. `streamChat` の `buffer` や `decoder` の値を具体的に示しながら何をしているか解説してほしい

### 前提: SSE のデータ形式

バックエンドが送ってくる生のバイト列はこんな形です：

```
data: {"type":"chunk","content":"今日","session_id":"u123"}\n\n
data: {"type":"chunk","content":"の歩数","session_id":"u123"}\n\n
data: {"type":"done","content":"","session_id":"u123"}\n\n
```

ポイントは **`\n\n` でイベントの区切り**、**`data: ` プレフィックス**の2点です。

### ① `TextDecoder` でバイト列 → 文字列

```ts
const decoder = new TextDecoder()
let buffer = ""

buffer += decoder.decode(value, { stream: true })
// value = [0xe4,0xbb,0x8a,0xe6,0x97,0xa5...]（"今日" のUTF-8バイト列）
// → buffer = 'data: {"type":"chunk","content":"今日",...}\n\n'
```

`{ stream: true }` は「まだ続きが来るかもしれないので、マルチバイト文字の途中で切れても保持しておく」という指定です。

### ② `buffer.split("\n\n")` でイベントを分割

```ts
const parts = buffer.split("\n\n")
buffer = parts.pop() ?? ""
```

受信データが途中で途切れることがあります：

```
// 1回目の read()
buffer = 'data: {"type":"chunk","content":"今日"}\n\ndata: {"type":"chunk","content":"の歩'

// split("\n\n") の結果
parts = [
  'data: {"type":"chunk","content":"今日"}',  // ← 完結している
  'data: {"type":"chunk","content":"の歩'     // ← 途中で切れている
]

// pop() で末尾（未完結）を取り出して buffer に残す
buffer = 'data: {"type":"chunk","content":"の歩'  // 次の read() で続きが来る
parts  = ['data: {"type":"chunk","content":"今日"}']  // こちらだけ処理
```

### ③ `data: ` プレフィックスを除いて JSON パース

```ts
for (const line of part.split("\n")) {
  if (!line.startsWith("data: ")) continue
  const chunk = JSON.parse(line.slice(6))
  // line       = 'data: {"type":"chunk","content":"今日",...}'
  // line.slice(6) = '{"type":"chunk","content":"今日",...}'
  // chunk      = { type: "chunk", content: "今日", session_id: "u123" }
}
```

---

## Q. SSE 自体がバイト列をストリーミングする技術なんですか？

「SSE はプロトコルの仕様、バイト列のストリーミングは HTTP の仕組み」と整理するのが正確です。

**HTTP（通常）**
```
クライアント → リクエスト → サーバー
クライアント ← レスポンス（一括） ← サーバー
```

**HTTP ストリーミング（SSEの土台）**
```
クライアント → リクエスト → サーバー
クライアント ← バイト列が少しずつ流れてくる ← サーバー（接続は切れない）
```

SSE が決めているのはフォーマットだけです：
- `data:` で始める
- `\n\n` で区切る
- `Content-Type: text/event-stream` を返す

バイト列を流す仕組み自体は HTTP が持っています。

---

## Q. てっきり JSON で返すものだと思っていました

JSON も返せますし、このプロジェクトも JSON を返しています。「JSON を返す」のと「バイト列でストリーミングする」は別のレイヤーの話です。

```
バイト列（HTTP層）
  └── テキスト（UTF-8デコード後）
        └── SSEフォーマット（data: ... \n\n）
              └── JSON（data: の中身）
```

| | 通常 JSON | SSE |
|---|---|---|
| いつ処理できる | 全部届いてから | 届いた分からすぐ |
| デコード | fetch が自動でやる | 自分で TextDecoder |
| ループ | 不要 | 必要（まだ来るから） |

---

## Q. HTTP は `application/json` でも内部的にはバイト列で扱い、フロントエンドの HTTP クライアントがよしなにデコードしてくれている？

そうです。

```ts
// 通常の fetch（JSON一括）
const response = await fetch("/api/data")
const json = await response.json()
// response.json() が内部で以下を全部やってくれる
//   1. バイト列を全部受け取るまで待つ
//   2. UTF-8 デコード
//   3. JSON.parse
```

SSE の場合は `response.json()` のような「全部来たら一括処理」ができないため、手動で `while` ループを回してバイト列を受け取り続ける必要があります。これが `api.ts` の `while` ループの正体です。

---

## Q. `response.body.getReader()` とは？

`response.body` は `ReadableStream` というブラウザのストリーム API です。

```
response.body          → ReadableStream（バイト列が流れてくるストリーム）
  .getReader()         → ReadableStreamDefaultReader（ストリームを読み取るリーダー）
    .read()            → { done: boolean, value: Uint8Array | undefined }
```

```
サーバー
  ↓ バイト列が流れてくる
ReadableStream（response.body）
  ↓ getReader() でリーダーを取得（1ストリームに1リーダーのみ）
ReadableStreamDefaultReader
  ↓ read() を await するたびに次のチャンクが来るまで待つ
{ done: false, value: Uint8Array([...]) }  // チャンク到着
{ done: false, value: Uint8Array([...]) }  // チャンク到着
{ done: true,  value: undefined }          // ストリーム終了
```

`getReader()` を呼ぶとストリームが**ロック**されます。ロック中は他の場所から同じ `response.body` を読めなくなります。

---

## Q. `onDone` で渡した `setStreaming(false)` がロックを解放しているように見えるが、あってますか？

いいえ、それは別々の話です。

| | 何をしているか | 誰が決めているか |
|---|---|---|
| `done: true` | ストリーム終了・ロック解放 | Web Streams API の仕様 |
| `onDone` / `setStreaming(false)` | 送信ボタンを再度押せるようにする | アプリの実装 |

`done: true` はサーバーが接続を閉じたことを示す仕様上のシグナルで、ロック解放はブラウザが自動でやります。`onDone` がなくてもストリームのロックは解放されます。

---

## Q. `decoder.decode(value, { stream: true })` に入る値はどんなもの？

バックエンドが `"今日"` を含む SSE チャンクを送った場合：

```ts
// value（デコード前の Uint8Array）
value = Uint8Array([
  100, 97, 116, 97, 58, 32,        // "data: "
  123, 34, 116, 121, 112, 101, 34, // '{"type"'
  58, 34, 99, 104, 117, 110, 107,  // ':"chunk'
  34, 44, 34, 99, 111, 110, 116,   // '","cont'
  101, 110, 116, 34, 58, 34,       // 'ent":"'
  228, 187, 138, 230, 151, 165,    // "今日"（UTF-8: 各3バイト）
  34, 125, 10, 10                  // '"}\n\n'
])

// デコード後
buffer += 'data: {"type":"chunk","content":"今日"}\n\n'
```

`"今"` は `[228, 187, 138]`、`"日"` は `[230, 151, 165]` という3バイトで表現されます。

### `{ stream: true }` が必要な理由

ネットワークの都合で `"今"` の3バイトが2回に分割されることがあります：

```ts
// 1回目の read()
value = Uint8Array([..., 228, 187])  // "今" の途中で切れた

// { stream: true } なし → "今" を表現できず文字化け
// { stream: true } あり → 続きが来るまで内部バッファに保持

// 2回目の read()
value = Uint8Array([138, ...])  // "今" の残り1バイト + 続き
// → "今" が完成して正しくデコードされる
```
