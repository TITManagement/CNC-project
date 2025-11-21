# 開発環境セットアップスクリプト
import os
import sys
import subprocess

def main():
    print("[INFO] Python仮想環境を作成します...")
    subprocess.run([sys.executable, '-m', 'venv', '.venv'], check=True)
    print("[INFO] requirements.txtをインストールします...")
    pip_path = os.path.join('.venv', 'bin', 'pip')
    subprocess.run([pip_path, 'install', '-r', 'requirements.txt'], check=True)
    print("[INFO] セットアップ完了！")

if __name__ == "__main__":
    main()
