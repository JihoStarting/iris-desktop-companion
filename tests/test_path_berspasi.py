import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("HERMES_WIN_HOME", "/mnt/c/Users/Axioo Pongo")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server


class TestPathBerspasi(unittest.TestCase):
    def test_folder_berspasi_di_luar_win_home(self):
        self.assertEqual(server.to_windows_paths("/mnt/z/Projek AI waifu Dekstop/a.txt"),
                         "Z:\\Projek AI waifu Dekstop\\a.txt")

    def test_nama_file_berspasi(self):
        self.assertEqual(server.to_windows_paths("/mnt/c/Data/laporan akhir.docx"),
                         "C:\\Data\\laporan akhir.docx")

    def test_bullet_dan_backtick(self):
        self.assertEqual(server.to_windows_paths("- `/mnt/d/Folder Saya/x.png`"),
                         "- `D:\\Folder Saya\\x.png`")

    def test_titik_penutup_kalimat(self):
        self.assertEqual(server.to_windows_paths("/mnt/z/Folder Saya/x.txt."),
                         "Z:\\Folder Saya\\x.txt.")

    def test_path_di_bawah_win_home_berspasi(self):
        self.assertEqual(server.to_windows_paths("/mnt/c/Users/Axioo Pongo/Downloads/a.txt"),
                         "C:\\Users\\Axioo Pongo\\Downloads\\a.txt")

    def test_path_di_tengah_kalimat_aturan_lama(self):
        self.assertEqual(server.to_windows_paths("File ada di /mnt/c/Data/a.txt, silakan buka."),
                         "File ada di C:\\Data\\a.txt, silakan buka.")

    def test_path_di_tengah_kalimat_tidak_menelan_teks(self):
        self.assertEqual(server.to_windows_paths("Simpan ke /mnt/c/Data/a.txt lalu selesai"),
                         "Simpan ke C:\\Data\\a.txt lalu selesai")

    def test_teks_biasa_tidak_berubah(self):
        self.assertEqual(server.to_windows_paths("Tidak ada path di sini."), "Tidak ada path di sini.")

    def test_root_drive(self):
        self.assertEqual(server.to_windows_paths("/mnt/c"), "C:\\")


if __name__ == "__main__":
    unittest.main()
