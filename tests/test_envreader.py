import contextlib
import io
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

# supaya server.py bisa di-import dari folder tests/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server

NAMA = "IRIS_TES_ANGKA"


def jalankan(nilai, default=120.0):
    """Panggil server.env_float dengan variabel palsu. Kembalikan (hasil, teks_stdout)."""
    with mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop(NAMA, None)
        if nilai is not None:
            os.environ[NAMA] = nilai
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            hasil = server.env_float(NAMA, default)
    return hasil, buf.getvalue()


class TestEnvFloat(unittest.TestCase):
    def test_tidak_diset_pakai_default_tanpa_peringatan(self):
        hasil, out = jalankan(None)
        self.assertEqual(hasil, 120.0)
        self.assertEqual(out, "")

    def test_kosong_dan_spasi_pakai_default_tanpa_peringatan(self):
        for nilai in ("", "   "):
            hasil, out = jalankan(nilai)
            self.assertEqual(hasil, 120.0)
            self.assertEqual(out, "")

    def test_angka_valid_dipakai(self):
        self.assertEqual(jalankan("30")[0], 30.0)
        self.assertEqual(jalankan("2.5")[0], 2.5)
        self.assertEqual(jalankan(" 45 ")[0], 45.0)

    def test_tidak_valid_pakai_default_dengan_peringatan(self):
        for nilai in ("abc", "0", "-5", "inf", "nan"):
            hasil, out = jalankan(nilai)
            self.assertEqual(hasil, 120.0, nilai)
            self.assertIn("[WARN]", out, nilai)


if __name__ == "__main__":
    unittest.main()
