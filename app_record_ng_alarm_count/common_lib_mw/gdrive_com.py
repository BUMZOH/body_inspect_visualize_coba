#===========================================================================
#      GoogleDriveアップロードプログラム
#      Update on 2025.10.15
# -------------------------------------------------------------------------- 
# ワーキングディレクトリに以下のファイルを配置すること(GDriveの認証に必要)
# settings.yaml / client_secrets.json / saved_credentials.json
# 
#===========================================================================
import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


def upload_to_gdrive(file_path:str,folder_id:str)->None:
  """ 指定したPNGファイルをGoogleDriveにアップロードする

  Args:
      file_name (str): アップロード対象ファイルのパス
      folder_id (str): フォルダID(URLから取得)
  """

  cwd = os.getcwd()   # 現在のワーキングディレクトリ保存
  os.chdir(os.path.dirname(__file__))     # スクリプト本体にディレクトリ移動

  gauth = GoogleAuth()
  gauth.CommandLineAuth()
  drive = GoogleDrive(gauth)
  
  file_name = os.path.basename(file_path)
  # print(f'file_name = {file_name}')
  
  ## Check Whether File Exists
  qstr = 'title = "'  + file_name + '" and "' + folder_id + '" in parents and trashed=false'
  # print(qstr)
  files = drive.ListFile({'q': qstr}).GetList()

  if len(files) > 0:
    # Overwrite
    file = files[0]
    # print('File Exists on Drive :\t', file['title'], ' (', file['id'], ')')
  else:
    # Create New
    # print('Create New File')
    file = drive.CreateFile({'title': file_name, 'mimeType': 'image/png', 'parents': [{'id': folder_id}]})
  
  ## Upload
  file.SetContentFile(file_path)
  file.Upload()

  os.chdir(cwd)   # ワーキングディレクトリを元に戻す



# テストコード(動作確認用) -----------------------------------------------------------------
if __name__=='__main__':
    fpath = "C:/my_data/img_opdata.png"
    # フォルダ：マイドライブ\K_共有ファイル\共有ファイル(全体)\IMAGE
    # https://drive.google.com/drive/folders/1Bu-KASatQAinYbR7hW0zUXEWz2YsWrO0
    folder_id = '1Bu-KASatQAinYbR7hW0zUXEWz2YsWrO0'
    upload_to_gdrive(fpath, folder_id)
    print('Upload to Google-Drive complete!')
