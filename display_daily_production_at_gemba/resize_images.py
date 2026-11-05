"""
画像一括リサイズツール

【機能】
指定フォルダ内のPNG/JPG画像を一括リサイズするCLIツール。
フォルダ選択にはTkinterのフォルダ選択ダイアログを使用する。

【リサイズ方式】
Cover方式（中央クロップ）を採用する。
元画像と出力画像の縦横比が異なる場合、縦横それぞれの拡大縮小率を計算し、
大きい方の倍率でリサイズする。
その後、指定サイズからはみ出した部分を画像中央を基準に均等にトリミングする。
これにより、元画像の縦横比を維持しながら、余白のない指定ピクセル数の画像を生成する。

【主な仕様】
- 対象形式：PNG、JPG、JPEG
- 出力サイズ：横幅・高さをCLIで指定
- 補間方式：LANCZOS（高品質）
- 保存形式：元画像と同じ形式
- JPG品質：95（固定）
- 出力先：選択フォルダ内のoutputフォルダ
- 出力先が存在する場合：output_001、output_002...を作成
- 元画像は変更しない
- サブフォルダ内の画像は処理しない

【必要ライブラリ】
Pillow（pip install pillow）
Tkinter（Python標準ライブラリ）
"""
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from PIL import Image, ImageOps


JPEG_QUALITY = 95
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def get_output_folder(source_folder):
    output_folder = source_folder / "output"
    number = 1

    while output_folder.exists():
        output_folder = source_folder / f"output_{number:03d}"
        number += 1

    output_folder.mkdir()
    return output_folder


def resize_image(source_path, output_path, width, height):
    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image)
        image = ImageOps.fit(
            image,
            (width, height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )

        if source_path.suffix.lower() in {".jpg", ".jpeg"}:
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            image.save(output_path, quality=JPEG_QUALITY)
        else:
            image.save(output_path, format="PNG")


def select_source_folder():
    root = tk.Tk()
    root.withdraw()
    try:
        folder = filedialog.askdirectory(
            parent=root,
            title="画像フォルダを選択してください",
        )
    finally:
        root.destroy()
    return Path(folder) if folder else None


def main():
    print("=== Image Resize ===")
    source_folder = select_source_folder()
    if source_folder is None:
        print("フォルダ選択をキャンセルしました。")
        return

    if not source_folder.is_dir():
        print("エラー: フォルダが存在しません。")
        return

    try:
        width = int(input("出力幅 (px): "))
        height = int(input("出力高さ (px): "))
        if width <= 0 or height <= 0:
            raise ValueError
    except ValueError:
        print("エラー: 幅と高さには正の整数を指定してください。")
        return

    image_files = sorted(
        path for path in source_folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not image_files:
        print("対象のPNG/JPG画像がありません。")
        return

    output_folder = get_output_folder(source_folder)
    success_count = 0

    for source_path in image_files:
        output_path = output_folder / source_path.name
        try:
            resize_image(source_path, output_path, width, height)
            print(f"OK: {source_path.name}")
            success_count += 1
        except (OSError, ValueError) as error:
            print(f"NG: {source_path.name} ({error})")

    print(f"\n完了: {success_count}/{len(image_files)} 件")
    print(f"保存先: {output_folder}")


if __name__ == "__main__":
    main()
