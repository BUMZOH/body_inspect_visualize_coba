# Tkinterで1つのアニメーションGIFをループ再生する方法

## 1. 目的

Tkinterでアニメーションを表示する場合、**複数のGIFファイルを用意する必要はない**。

アニメーションGIFは、1つの `.gif`
ファイル内部に複数の画像（フレーム）を格納できる。

``` text
crystal.gif
    │
    ├─ frame 0
    ├─ frame 1
    ├─ frame 2
    ├─ frame 3
    └─ ...
```

ブラウザなどではアニメーションGIFを指定すると自動再生されるが、今回のTkinter方式では、GIF内部のフレームをPython側で順番に表示してアニメーションさせる。

基本的な流れは次のとおり。

``` text
1つのGIFファイル
        ↓
Pillowで各フレームを取得
        ↓
TkinterのLabelへ表示
        ↓
after()で次のフレームへ切り替え
        ↓
最後まで行ったら最初へ戻る
```

------------------------------------------------------------------------

## 2. 必要なライブラリ

画像処理には **Pillow** を使用する。

インストールされていない場合は次のコマンドでインストールする。

``` text
pip install pillow
```

この最小サンプルで追加する外部ライブラリはPillowだけである。

------------------------------------------------------------------------

## 3. ファイル構成

今回のテストプログラムでは `crystal.gif` を使用している。

``` text
animated_gif_test/
│
├─ app.py
└─ crystal.gif
```

将来Factory Botを使用する場合も、例えば次のように1ファイルでよい。

``` text
animated_gif_test/
│
├─ app.py
└─ factory_bot.gif
```

------------------------------------------------------------------------

## 4. 今回の最小サンプル全文

``` python
import tkinter as tk

from PIL import Image, ImageTk


GIF_PATH = "crystal.gif"


root = tk.Tk()
root.title("Animated GIF Test")
root.geometry("500x500")


# ================================================
#   Load GIF
# ================================================
gif = Image.open(GIF_PATH)

frames = []

for frame_no in range(gif.n_frames):
    gif.seek(frame_no)

    frame = ImageTk.PhotoImage(gif.copy())
    frames.append(frame)


# ================================================
#   Show GIF
# ================================================
label = tk.Label(root)
label.pack(expand=True)

current_frame = 0


def update_animation():
    global current_frame

    label.configure(image=frames[current_frame])

    current_frame += 1

    if current_frame >= len(frames):
        current_frame = 0

    root.after(100, update_animation)


update_animation()

root.mainloop()
```

------------------------------------------------------------------------

## 5. GIFファイルの指定

``` python
GIF_PATH = "crystal.gif"
```

表示するアニメーションGIFを指定する。

重要なのは、ここで指定している画像ファイルが **1つだけ**
という点である。

複数のGIF画像をPythonで順番に読み替える方式ではない。

------------------------------------------------------------------------

## 6. GIFファイルを開く

``` python
gif = Image.open(GIF_PATH)
```

Pillowの `Image.open()` でGIFファイルを開く。

この1ファイル内部に複数のフレームが格納されている。

------------------------------------------------------------------------

## 7. GIF内部のフレーム数

Pillowでは、

``` python
gif.n_frames
```

でGIF内部のフレーム数を取得できる。

例えば20フレームなら、

``` text
crystal.gif

 ├─ frame 0
 ├─ frame 1
 ├─ frame 2
 ├─ ...
 └─ frame 19
```

となる。

そのため、

``` python
for frame_no in range(gif.n_frames):
```

で全フレームを順番に処理できる。

------------------------------------------------------------------------

## 8. フレームを選択する

``` python
gif.seek(frame_no)
```

`seek()` でGIF内部の対象フレームへ移動する。

``` python
gif.seek(0)
```

なら最初のフレーム、

``` python
gif.seek(1)
```

なら2番目のフレームとなる。

------------------------------------------------------------------------

## 9. Tkinterで表示できる画像へ変換する

``` python
frame = ImageTk.PhotoImage(gif.copy())
```

現在選択しているフレームを `gif.copy()` でコピーし、Tkinterで表示できる
`ImageTk.PhotoImage` に変換する。

------------------------------------------------------------------------

## 10. 全フレームをリストへ保存する

最初に空のリストを作る。

``` python
frames = []
```

各フレームを、

``` python
frames.append(frame)
```

で追加する。

結果は概念的に次のようになる。

``` text
frames
 │
 ├─ [0] frame 0
 ├─ [1] frame 1
 ├─ [2] frame 2
 ├─ [3] frame 3
 └─ ...
```

再生時には、このリストから画像を順番に取り出す。

------------------------------------------------------------------------

## 11. 表示用Label

``` python
label = tk.Label(root)
label.pack(expand=True)
```

アニメーション表示用の `Label` を作る。

`Label` は文字だけでなく、`image` オプションへ `PhotoImage`
を指定することで画像も表示できる。

------------------------------------------------------------------------

## 12. 現在のフレーム番号

``` python
current_frame = 0
```

現在表示するフレーム番号を管理する。

最初は0なので、

``` python
frames[0]
```

から再生を開始する。

------------------------------------------------------------------------

## 13. アニメーション処理

中心となる処理は次の関数である。

``` python
def update_animation():
    global current_frame

    label.configure(image=frames[current_frame])

    current_frame += 1

    if current_frame >= len(frames):
        current_frame = 0

    root.after(100, update_animation)
```

この関数が繰り返し実行されることでアニメーションになる。

------------------------------------------------------------------------

## 14. 現在のフレームを表示する

``` python
label.configure(image=frames[current_frame])
```

`frames` リストから現在のフレームを取り出してLabelへ表示する。

``` text
current_frame = 0 → frames[0]
current_frame = 1 → frames[1]
current_frame = 2 → frames[2]
```

この画像切り替えが連続して行われることで、人間の目にはアニメーションとして見える。

------------------------------------------------------------------------

## 15. 次のフレームへ進む

``` python
current_frame += 1
```

表示後にフレーム番号を1つ進める。

``` text
0
↓
1
↓
2
↓
3
↓
...
```

------------------------------------------------------------------------

## 16. 最後まで行ったら先頭へ戻す

``` python
if current_frame >= len(frames):
    current_frame = 0
```

最後のフレームを超えたら0へ戻す。

20フレームなら、

``` text
0 → 1 → 2 → ... → 19 → 0 → 1 → ...
```

となり、無限ループする。

------------------------------------------------------------------------

## 17. after()によるフレーム切り替え

``` python
root.after(100, update_animation)
```

`after()` は、指定時間経過後に関数を実行するTkinterの機能である。

今回の場合、

``` text
100ms待つ
    ↓
update_animation()を実行
```

となる。

したがって、

``` text
frame 0を表示
    ↓
100ms
    ↓
frame 1を表示
    ↓
100ms
    ↓
frame 2を表示
    ↓
...
```

という動きになる。

100msは0.1秒なので、単純計算では1秒間に約10フレーム表示する。

------------------------------------------------------------------------

## 18. time.sleep()を使わない理由

TkinterのGUIアニメーションでは基本的に、

``` python
time.sleep()
```

ではなく、

``` python
root.after()
```

を使用する。

GUIを担当するメインスレッドで `time.sleep()`
を実行すると、その時間はTkinterのイベント処理も停止してしまう。

一方 `after()` は、

``` text
100ms後にこの関数を実行してください
```

とTkinterのイベントループへ予約する仕組みである。

そのため、GUIを止めずにアニメーションを実行できる。

------------------------------------------------------------------------

## 19. 最初のアニメーション開始

``` python
update_animation()
```

最初の1回だけ自分で関数を呼ぶ。

その後は関数内部の、

``` python
root.after(100, update_animation)
```

が次回の実行を予約する。

``` text
update_animation()
       │
       ▼
100ms後に update_animation()
       │
       ▼
100ms後に update_animation()
       │
       ▼
...
```

------------------------------------------------------------------------

## 20. mainloop()

``` python
root.mainloop()
```

Tkinterのイベントループを開始する。

ウィンドウ表示、マウス、キーボード、`after()`
などは、このイベントループ上で処理される。

------------------------------------------------------------------------

## 21. 今回の方式で重要な点

今回採用する方式では、

``` text
frame_1.gif
frame_2.gif
frame_3.gif
frame_4.gif
```

のような複数ファイルは不要である。

必要なのは、

``` text
crystal.gif
```

のような **1つのアニメーションGIFファイル** だけである。

Python側で行うのは、そのファイル内部に格納された複数フレームを順番に表示する処理である。

つまり、

``` text
複数GIFファイルをPythonで切り替える
```

ではなく、

``` text
1つのアニメーションGIF
        ↓
内部フレームを取得
        ↓
Tkinterで順番に表示
```

という方式である。

------------------------------------------------------------------------

## 22. 今回は固定100msで再生する

この最小サンプルでは、

``` python
root.after(100, update_animation)
```

として、すべてのフレームを100ms間隔で表示する。

これは仕組みを確認するための最小構成である。

実際のアニメーションGIFには、

``` text
frame 0 → 80ms
frame 1 → 80ms
frame 2 → 150ms
frame 3 → 300ms
```

のように、フレームごとの表示時間が保存されている場合がある。

Pillowを使えばその時間情報を取得し、本来のGIFに近いタイミングで再生することもできる。

ただし、最初の動作確認では必要ないため、今回のサンプルでは固定100msとしている。

------------------------------------------------------------------------

## 23. 今後の発展

最小サンプルの動作を確認した後、必要に応じて次の機能を追加できる。

### GIF自身のフレーム時間を使用する

GIFに保存されている各フレームの表示時間を取得し、

``` python
root.after(duration, update_animation)
```

とする。

これによりGIF自身が持っている再生タイミングを利用できる。

### AnimatedGifクラスにする

アニメーション処理をクラス化すれば、アプリ本体では例えば、

``` python
bot = AnimatedGif(root, "factory_bot.gif")
bot.pack()
```

程度の記述だけでアニメーションGIFを表示できるようにできる。

ただし、最初から抽象化するのではなく、まず今回の単純なコードで原理と動作を確認し、必要になってから実施する。

------------------------------------------------------------------------

## 24. まとめ

TkinterでアニメーションGIFを扱う場合、画像素材は1つのアニメーションGIFファイルでよい。

``` text
1つのアニメーションGIF
        ↓
Image.open()
        ↓
n_framesでフレーム数を取得
        ↓
seek()で各フレームを選択
        ↓
ImageTk.PhotoImageへ変換
        ↓
framesリストへ保存
        ↓
Labelへ順番に表示
        ↓
after()で次の表示を予約
        ↓
最後まで行ったらframe 0へ戻る
```

今回の最小サンプルでは、アニメーション処理にスレッドや動画再生ライブラリを使用しない。

**Pillow + Tkinterの `after()`
だけで、1つのアニメーションGIFを繰り返し再生する。**

まずはこの構成を基本形として使用する。
