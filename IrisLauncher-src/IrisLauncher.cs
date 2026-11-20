// by: KangJiho
// Iris Launcher v1.3 - satu exe: Start / Stop / Hermes / Doctor / Update + pengaturan + tray, notifikasi, preset, penampil log.
// Skrip PowerShell (iris-start/stop/hermes/doctor) tertanam di dalam exe dan diekstrak
// ke %LOCALAPPDATA%\IrisLauncher\scripts saat dijalankan. Pengaturan: %APPDATA%\IrisLauncher\settings.ini
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Net;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("Iris Launcher")]
[assembly: AssemblyProduct("Iris Launcher")]
[assembly: AssemblyDescription("Peluncur IRIS desktop companion: Start, Stop, Hermes, Doctor")]
[assembly: AssemblyCompany("KangJiho")]
[assembly: AssemblyCopyright("Copyright (c) 2026 KangJiho. All rights reserved")]
[assembly: AssemblyInformationalVersion("1.3.0")]
[assembly: AssemblyVersion("1.3.0.0")]
[assembly: AssemblyFileVersion("1.3.0.0")]

namespace IrisLauncher
{
    static class AppInfo
    {
        public const string Version = "1.3";

        [DllImport("kernel32.dll")]
        static extern bool SetProcessWorkingSetSize(IntPtr proc, IntPtr min, IntPtr max);

        // Lepas memori yang tidak terpakai ke Windows (dipanggil saat jendela diminimalkan).
        [DllImport("dwmapi.dll")]
        static extern int DwmSetWindowAttribute(IntPtr hwnd, int attr, ref int val, int size);

        static int CRef(Color c) { return c.R | (c.G << 8) | (c.B << 16); }

        // Bar judul gelap berwarna ungu tema (Windows 11; di Windows lama diabaikan).
        public static void Chrome(IntPtr h)
        {
            try
            {
                int dark = 1; DwmSetWindowAttribute(h, 20, ref dark, 4);
                int cap = CRef(Theme.Bg); DwmSetWindowAttribute(h, 35, ref cap, 4);
                int brd = CRef(Theme.Border); DwmSetWindowAttribute(h, 34, ref brd, 4);
                int txt = CRef(Theme.Text); DwmSetWindowAttribute(h, 36, ref txt, 4);
            }
            catch { }
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        class MEMORYSTATUSEX
        {
            public uint dwLength;
            public uint dwMemoryLoad;
            public ulong ullTotalPhys, ullAvailPhys, ullTotalPageFile, ullAvailPageFile, ullTotalVirtual, ullAvailVirtual, ullAvailExtendedVirtual;
            public MEMORYSTATUSEX() { dwLength = (uint)Marshal.SizeOf(typeof(MEMORYSTATUSEX)); }
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        static extern bool GlobalMemoryStatusEx([In, Out] MEMORYSTATUSEX lpBuffer);

        // Persen RAM sistem yang terpakai; -1 bila tidak terbaca.
        public static int RamPercent()
        {
            try
            {
                MEMORYSTATUSEX m = new MEMORYSTATUSEX();
                if (GlobalMemoryStatusEx(m)) return (int)m.dwMemoryLoad;
            }
            catch { }
            return -1;
        }

        public static void TrimMemory()
        {
            try
            {
                GC.Collect();
                GC.WaitForPendingFinalizers();
                using (Process me = Process.GetCurrentProcess())
                    SetProcessWorkingSetSize(me.Handle, (IntPtr)(-1), (IntPtr)(-1));
            }
            catch { }
        }
    }

    static class Theme
    {
        public static readonly Color Bg = ColorTranslator.FromHtml("#110E24");
        public static readonly Color Panel = ColorTranslator.FromHtml("#1D1838");
        public static readonly Color Text = ColorTranslator.FromHtml("#F1ECFF");
        public static readonly Color Muted = ColorTranslator.FromHtml("#A59CC9");
        public static readonly Color Accent = ColorTranslator.FromHtml("#B79CFF");
        public static readonly Color Green = ColorTranslator.FromHtml("#4ADE80");
        public static readonly Color Red = ColorTranslator.FromHtml("#F87171");
        public static readonly Color Gray = ColorTranslator.FromHtml("#5B5380");
        public static readonly Color Amber = ColorTranslator.FromHtml("#FBBF24");
        public static readonly Color BtnStart = ColorTranslator.FromHtml("#7C5CF0");
        public static readonly Color BtnStop = ColorTranslator.FromHtml("#C4467A");
        public static readonly Color BtnHermes = ColorTranslator.FromHtml("#8B5CF6");
        public static readonly Color BtnDoctor = ColorTranslator.FromHtml("#3A2F6B");
        public static readonly Color BtnOff = ColorTranslator.FromHtml("#241E42");
        public static readonly Color Border = ColorTranslator.FromHtml("#3B2F6E");
        public static readonly Color HeadTop = ColorTranslator.FromHtml("#3A2670");
        public static readonly Color HeadBot = ColorTranslator.FromHtml("#171230");
    }

    // Tombol bulat dengan gradasi ungu; BackColor jadi warna dasarnya.
    class RBtn : Button
    {
        bool hover, down;

        public RBtn()
        {
            SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint
                | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
        }

        protected override void OnMouseEnter(EventArgs e) { hover = true; Invalidate(); base.OnMouseEnter(e); }
        protected override void OnMouseLeave(EventArgs e) { hover = false; down = false; Invalidate(); base.OnMouseLeave(e); }
        protected override void OnMouseDown(MouseEventArgs e) { down = true; Invalidate(); base.OnMouseDown(e); }
        protected override void OnMouseUp(MouseEventArgs e) { down = false; Invalidate(); base.OnMouseUp(e); }
        protected override void OnEnabledChanged(EventArgs e) { Invalidate(); base.OnEnabledChanged(e); }

        static GraphicsPath Round(Rectangle r, int rad)
        {
            int d = rad * 2;
            GraphicsPath p = new GraphicsPath();
            p.AddArc(r.X, r.Y, d, d, 180, 90);
            p.AddArc(r.Right - d, r.Y, d, d, 270, 90);
            p.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
            p.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
            p.CloseFigure();
            return p;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.Clear(Parent != null ? Parent.BackColor : Theme.Bg);
            if (Width < 30 || Height < 24) return;
            Rectangle r = new Rectangle(0, 0, Width - 1, Height - 1);
            Color c = BackColor;
            Color top = (hover && Enabled) ? ControlPaint.Light(c, 0.45F) : ControlPaint.Light(c, 0.20F);
            Color bot = down ? ControlPaint.Dark(c, 0.10F) : c;
            using (GraphicsPath path = Round(r, 12))
            {
                using (LinearGradientBrush b = new LinearGradientBrush(r, top, bot, 90F))
                    g.FillPath(b, path);
                using (Pen pen = new Pen(Color.FromArgb(Enabled ? (hover ? 150 : 60) : 30, Color.White), 1F))
                    g.DrawPath(pen, path);
            }
            TextRenderer.DrawText(g, Text, Font, r, Enabled ? ForeColor : Theme.Muted,
                TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.EndEllipsis);
        }
    }

    enum ChipState { Off, On, Busy, Err }

    // Chip status yang bisa diklik: titik berwarna + nama layanan + keterangan kecil.
    class ServiceChip : Control
    {
        bool hover, down, pulse;
        ChipState state = ChipState.Off;
        string caption = "Mati";
        public string Title = "";
        bool hasUpdate;
        public bool HasUpdate
        {
            get { return hasUpdate; }
            set { if (hasUpdate != value) { hasUpdate = value; Invalidate(); } }
        }
        readonly Font nameFont = new Font("Segoe UI Semibold", 10F);
        readonly Font capFont = new Font("Segoe UI", 8.5F);
        readonly System.Windows.Forms.Timer pulseTimer = new System.Windows.Forms.Timer();

        public ServiceChip()
        {
            SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint
                | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
            Cursor = Cursors.Hand;
            pulseTimer.Interval = 450;
            pulseTimer.Tick += delegate { pulse = !pulse; Invalidate(); };
        }

        public ChipState State
        {
            get { return state; }
            set
            {
                if (state == value) return;
                state = value;
                if (value == ChipState.Busy) pulseTimer.Start(); else { pulseTimer.Stop(); pulse = false; }
                Invalidate();
            }
        }

        public string Caption
        {
            get { return caption; }
            set { if (caption != value) { caption = value; Invalidate(); } }
        }

        protected override void OnMouseEnter(EventArgs e) { hover = true; Invalidate(); base.OnMouseEnter(e); }
        protected override void OnMouseLeave(EventArgs e) { hover = false; down = false; Invalidate(); base.OnMouseLeave(e); }
        protected override void OnMouseDown(MouseEventArgs e) { down = true; Invalidate(); base.OnMouseDown(e); }
        protected override void OnMouseUp(MouseEventArgs e) { down = false; Invalidate(); base.OnMouseUp(e); }

        protected override void Dispose(bool disposing)
        {
            if (disposing) { pulseTimer.Dispose(); nameFont.Dispose(); capFont.Dispose(); }
            base.Dispose(disposing);
        }

        static Color Mix(Color a, Color b, float t)
        {
            return Color.FromArgb((int)(a.R + (b.R - a.R) * t), (int)(a.G + (b.G - a.G) * t), (int)(a.B + (b.B - a.B) * t));
        }

        static GraphicsPath Round(Rectangle r, int rad)
        {
            int d = rad * 2;
            GraphicsPath p = new GraphicsPath();
            p.AddArc(r.X, r.Y, d, d, 180, 90);
            p.AddArc(r.Right - d, r.Y, d, d, 270, 90);
            p.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
            p.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
            p.CloseFigure();
            return p;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.Clear(Parent != null ? Parent.BackColor : Theme.Bg);
            if (Width < 40 || Height < 24) return;

            Color accent = state == ChipState.On ? Theme.Green
                : state == ChipState.Busy ? Theme.Amber
                : state == ChipState.Err ? Theme.Red : Theme.Gray;

            Color fill = Mix(Theme.Panel, accent, state == ChipState.Off ? 0.0F : 0.14F);
            if (hover) fill = Mix(fill, Theme.Accent, 0.14F);
            if (down) fill = Mix(fill, Color.Black, 0.18F);

            Rectangle r = new Rectangle(0, 0, Width - 1, Height - 1);
            using (GraphicsPath path = Round(r, 12))
            {
                using (SolidBrush b = new SolidBrush(fill)) g.FillPath(b, path);
                Color bc = hover ? Theme.Accent : accent;
                int alpha = hover ? 220 : (state == ChipState.Off ? 110 : 190);
                using (Pen pen = new Pen(Color.FromArgb(alpha, bc), 1F)) g.DrawPath(pen, path);
            }

            int cy = Height / 2;
            int dot = 12;
            Rectangle dr = new Rectangle(16, cy - dot / 2, dot, dot);
            if (state == ChipState.On || state == ChipState.Busy)
            {
                int ha = state == ChipState.Busy ? (pulse ? 90 : 30) : 55;
                Rectangle halo = Rectangle.Inflate(dr, 5, 5);
                using (SolidBrush hb = new SolidBrush(Color.FromArgb(ha, accent))) g.FillEllipse(hb, halo);
            }
            using (SolidBrush db = new SolidBrush(accent)) g.FillEllipse(db, dr);

            TextFormatFlags f = TextFormatFlags.Left | TextFormatFlags.NoPadding | TextFormatFlags.EndEllipsis | TextFormatFlags.NoPrefix;
            int nh = TextRenderer.MeasureText(g, Title, nameFont, new Size(1000, 100), TextFormatFlags.NoPadding).Height;
            int ch = TextRenderer.MeasureText(g, caption, capFont, new Size(1000, 100), TextFormatFlags.NoPadding).Height;
            int top = (Height - (nh + ch + 1)) / 2;
            int tx = 38;
            int tw = Math.Max(10, Width - tx - 8);
            TextRenderer.DrawText(g, Title, nameFont, new Rectangle(tx, top, tw, nh), Theme.Text, f);
            Color cc = state == ChipState.Off ? Theme.Muted : accent;
            TextRenderer.DrawText(g, caption, capFont, new Rectangle(tx, top + nh + 1, tw, ch), cc, f);

            if (hasUpdate)
            {
                Rectangle br = new Rectangle(Width - 24, Height - 24, 15, 15);
                using (SolidBrush bb = new SolidBrush(Theme.Amber)) g.FillEllipse(bb, br);
                using (Font bf = new Font("Segoe UI", 8F, FontStyle.Bold))
                    TextRenderer.DrawText(g, "\u2191", bf, br, Theme.Bg,
                        TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);
            }
        }
    }

    // Panel dengan gradasi ungu dan garis aksen tipis di bawahnya.
    class GradPanel : Panel
    {
        public GradPanel()
        {
            SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint
                | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            if (Width < 2 || Height < 2) return;
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            using (LinearGradientBrush b = new LinearGradientBrush(ClientRectangle, Theme.HeadTop, Theme.HeadBot, 20F))
                g.FillRectangle(b, ClientRectangle);
            // kilau lembut di belakang logo
            Rectangle glow = new Rectangle(-30, -40, 260, 190);
            using (GraphicsPath gp = new GraphicsPath())
            {
                gp.AddEllipse(glow);
                using (PathGradientBrush pg = new PathGradientBrush(gp))
                {
                    pg.CenterColor = Color.FromArgb(90, 168, 120, 255);
                    pg.SurroundColors = new Color[] { Color.FromArgb(0, 168, 120, 255) };
                    g.FillPath(pg, gp);
                }
            }
            // garis aksen bawah: ungu -> merah muda -> transparan
            Rectangle line = new Rectangle(0, Height - 2, Width, 2);
            using (LinearGradientBrush lb = new LinearGradientBrush(line, Theme.Accent, Color.FromArgb(0, Theme.Accent), 0F))
            {
                ColorBlend cb = new ColorBlend(3);
                cb.Colors = new Color[] { Color.FromArgb(200, 139, 92, 246), Color.FromArgb(160, 236, 112, 190), Color.FromArgb(0, 236, 112, 190) };
                cb.Positions = new float[] { 0F, 0.45F, 1F };
                lb.InterpolationColors = cb;
                g.FillRectangle(lb, line);
            }
        }
    }

    // Pil ringkasan di header: "3 dari 6 layanan hidup" dengan titik warna.
    class SummaryPill : Control
    {
        int on, total = 6;
        readonly Font f = new Font("Segoe UI Semibold", 9.5F);

        public SummaryPill()
        {
            SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint
                | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw | ControlStyles.SupportsTransparentBackColor, true);
            BackColor = Color.Transparent;
        }

        public void SetCount(int n, int t) { if (on != n || total != t) { on = n; total = t; Invalidate(); } }

        protected override void Dispose(bool disposing) { if (disposing) f.Dispose(); base.Dispose(disposing); }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            Color c = on == 0 ? Theme.Gray : (on >= total ? Theme.Green : Theme.Amber);
            Rectangle r = new Rectangle(0, 0, Width - 1, Height - 1);
            int d = r.Height;
            using (GraphicsPath p = new GraphicsPath())
            {
                p.AddArc(r.X, r.Y, d, d, 90, 180);
                p.AddArc(r.Right - d, r.Y, d, d, 270, 180);
                p.CloseFigure();
                using (SolidBrush b = new SolidBrush(Color.FromArgb(70, 12, 8, 30))) g.FillPath(b, p);
                using (Pen pen = new Pen(Color.FromArgb(150, c), 1F)) g.DrawPath(pen, p);
            }
            Rectangle dot = new Rectangle(14, Height / 2 - 5, 10, 10);
            using (SolidBrush hb = new SolidBrush(Color.FromArgb(60, c))) g.FillEllipse(hb, Rectangle.Inflate(dot, 4, 4));
            using (SolidBrush db = new SolidBrush(c)) g.FillEllipse(db, dot);
            string txt = on == 0 ? "Semua mati" : (on >= total ? "Semua hidup" : on + " dari " + total + " hidup");
            TextRenderer.DrawText(g, txt, f, new Rectangle(32, 0, Width - 36, Height), Theme.Text,
                TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);
        }
    }

    enum StatusKind { Idle, Busy, Ok, Warn }

    // Status di kiri bawah: kosong saat diam, titik berdenyut saat bekerja, titik hijau/kuning setelah selesai.
    class StatusText : Control
    {
        StatusKind kind = StatusKind.Idle;
        string text = "";
        bool pulse;
        readonly Font f = new Font("Segoe UI", 9.5F);
        readonly System.Windows.Forms.Timer t = new System.Windows.Forms.Timer();

        public StatusText()
        {
            SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
            t.Interval = 450;
            t.Tick += delegate { pulse = !pulse; Invalidate(); };
        }

        public void Set(StatusKind k, string s)
        {
            kind = k; text = s ?? "";
            if (k == StatusKind.Busy) t.Start(); else { t.Stop(); pulse = false; }
            Invalidate();
        }

        protected override void Dispose(bool disposing) { if (disposing) { t.Dispose(); f.Dispose(); } base.Dispose(disposing); }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.Clear(Parent != null ? Parent.BackColor : Theme.Bg);
            if (kind == StatusKind.Idle || text.Length == 0) return;
            Color c = kind == StatusKind.Ok ? Theme.Green : Theme.Amber;
            Rectangle dot = new Rectangle(2, Height / 2 - 4, 8, 8);
            int ha = kind == StatusKind.Busy ? (pulse ? 110 : 30) : 50;
            using (SolidBrush hb = new SolidBrush(Color.FromArgb(ha, c))) g.FillEllipse(hb, Rectangle.Inflate(dot, 4, 4));
            using (SolidBrush db = new SolidBrush(c)) g.FillEllipse(db, dot);
            TextRenderer.DrawText(g, text, f, new Rectangle(20, 0, Width - 20, Height), Theme.Muted,
                TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding | TextFormatFlags.EndEllipsis);
        }
    }

    static class Res
    {
        public static Stream Open(string name)
        {
            return Assembly.GetExecutingAssembly().GetManifestResourceStream(name);
        }

        public static Image Logo()
        {
            using (Stream s = Open("logo.png")) { return Image.FromStream(s); }
        }

        public static Icon AppIcon()
        {
            using (Stream s = Open("iris.ico")) { return new Icon(s); }
        }

        public static string HistoryFile()
        {
            return Path.Combine(Path.GetDirectoryName(ScriptDir()), "update-history.log");
        }

        public static string ScriptDir()
        {
            string b = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            if (string.IsNullOrEmpty(b)) b = Path.GetTempPath();
            return Path.Combine(Path.Combine(b, "IrisLauncher"), "scripts");
        }

        // Menulis ulang skrip dari resource setiap kali launcher dibuka (selalu sama dengan versi exe).
        public static void ExtractScripts()
        {
            string dir = ScriptDir();
            Directory.CreateDirectory(dir);
            foreach (string n in new string[] { "iris-start.ps1", "iris-stop.ps1", "iris-hermes.ps1", "iris-doctor.ps1", "iris-service.ps1", "iris-update.ps1" })
            {
                using (Stream s = Open(n))
                using (FileStream f = new FileStream(Path.Combine(dir, n), FileMode.Create, FileAccess.Write))
                {
                    byte[] buf = new byte[8192];
                    int r;
                    while ((r = s.Read(buf, 0, buf.Length)) > 0) f.Write(buf, 0, r);
                }
            }
        }
    }

    class Settings
    {
        public string Proyek = "";
        public string Distro = "Ubuntu";
        public int TungguDetik = 90;
        public bool Penjaga = true;
        public bool Overlay = true;
        public bool StopSemua = true;
        public bool KonfirmasiStop = true;
        public bool AutoStart = false;
        public bool TutupMatikan = true;   // menutup launcher ikut mematikan semua layanan Iris
        public string LauncherRepo = "";   // pemilik/repo GitHub tempat rilis IrisLauncher.exe (untuk update launcher sendiri)
        public bool CekUpdate = true;      // cek update komponen di latar belakang saat launcher dibuka
        public bool VoiceGpu = true;       // VOICEVOX Windows (vv-engine): true = GPU (DirectML), false = CPU
        public bool MinimalKeTray = true;        // v1.1: minimalkan = sembunyi ke ikon tray
        public bool TutupKeTray = false;         // v1.1: tombol X hanya menyembunyikan ke tray
        public bool MulaiDenganWindows = false;  // v1.1: launcher dibuka saat Windows menyala (--tray)
        public bool Notifikasi = true;           // v1.1: balon notifikasi saat layanan berhenti sendiri
        public bool AutoPulih = false;           // v1.1: nyalakan ulang layanan yang berhenti sendiri (maks 1x / 10 menit)
        public bool RotasiLog = true;            // v1.1: rapikan log > 5 MB, hapus arsip > 14 hari
        public bool Hotkey = false;              // v1.1: Ctrl+Alt+I menampilkan / menyembunyikan launcher

        public static string FilePath()
        {
            string b = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            if (string.IsNullOrEmpty(b)) b = Path.GetTempPath();
            return Path.Combine(Path.Combine(b, "IrisLauncher"), "settings.ini");
        }

        public static bool IsProject(string dir)
        {
            return !string.IsNullOrEmpty(dir) && Directory.Exists(dir) && File.Exists(Path.Combine(dir, "server.py"));
        }

        static bool B(string v, bool d)
        {
            if (v == null) return d;
            v = v.Trim().ToLowerInvariant();
            if (v == "1" || v == "true" || v == "ya") return true;
            if (v == "0" || v == "false" || v == "tidak") return false;
            return d;
        }

        public static Settings Load()
        {
            Settings s = new Settings();
            try
            {
                string p = FilePath();
                if (File.Exists(p))
                {
                    foreach (string line in File.ReadAllLines(p, Encoding.UTF8))
                    {
                        int i = line.IndexOf('=');
                        if (i <= 0) continue;
                        string k = line.Substring(0, i).Trim().ToLowerInvariant();
                        string v = line.Substring(i + 1).Trim();
                        switch (k)
                        {
                            case "proyek": s.Proyek = v; break;
                            case "distro": if (v.Length > 0) s.Distro = v; break;
                            case "tunggudetik": { int n; if (int.TryParse(v, out n) && n >= 10 && n <= 900) s.TungguDetik = n; break; }
                            case "penjaga": s.Penjaga = B(v, s.Penjaga); break;
                            case "overlay": s.Overlay = B(v, s.Overlay); break;
                            case "stopsemua": s.StopSemua = B(v, s.StopSemua); break;
                            case "konfirmasistop": s.KonfirmasiStop = B(v, s.KonfirmasiStop); break;
                            case "autostart": s.AutoStart = B(v, s.AutoStart); break;
                            case "tutupmatikan": s.TutupMatikan = B(v, s.TutupMatikan); break;
                            case "vvgpu": s.VoiceGpu = B(v, s.VoiceGpu); break;
                            case "cekupdate": s.CekUpdate = B(v, s.CekUpdate); break;
                            case "launcherrepo": s.LauncherRepo = v; break;
                            case "minimalketray": s.MinimalKeTray = B(v, s.MinimalKeTray); break;
                            case "tutupketray": s.TutupKeTray = B(v, s.TutupKeTray); break;
                            case "mulaidenganwindows": s.MulaiDenganWindows = B(v, s.MulaiDenganWindows); break;
                            case "notifikasi": s.Notifikasi = B(v, s.Notifikasi); break;
                            case "autopulih": s.AutoPulih = B(v, s.AutoPulih); break;
                            case "rotasilog": s.RotasiLog = B(v, s.RotasiLog); break;
                            case "hotkey": s.Hotkey = B(v, s.Hotkey); break;
                        }
                    }
                }
            }
            catch { }

            if (!IsProject(s.Proyek))
            {
                string exeDir = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\', '/');
                if (IsProject(exeDir)) s.Proyek = exeDir;
            }
            return s;
        }

        public void Save()
        {
            string p = FilePath();
            Directory.CreateDirectory(Path.GetDirectoryName(p));
            List<string> l = new List<string>();
            l.Add("proyek=" + Proyek);
            l.Add("distro=" + Distro);
            l.Add("tunggudetik=" + TungguDetik);
            l.Add("penjaga=" + (Penjaga ? "1" : "0"));
            l.Add("overlay=" + (Overlay ? "1" : "0"));
            l.Add("stopsemua=" + (StopSemua ? "1" : "0"));
            l.Add("konfirmasistop=" + (KonfirmasiStop ? "1" : "0"));
            l.Add("autostart=" + (AutoStart ? "1" : "0"));
            l.Add("tutupmatikan=" + (TutupMatikan ? "1" : "0"));
            l.Add("vvgpu=" + (VoiceGpu ? "1" : "0"));
            l.Add("cekupdate=" + (CekUpdate ? "1" : "0"));
            l.Add("launcherrepo=" + LauncherRepo);
            l.Add("minimalketray=" + (MinimalKeTray ? "1" : "0"));
            l.Add("tutupketray=" + (TutupKeTray ? "1" : "0"));
            l.Add("mulaidenganwindows=" + (MulaiDenganWindows ? "1" : "0"));
            l.Add("notifikasi=" + (Notifikasi ? "1" : "0"));
            l.Add("autopulih=" + (AutoPulih ? "1" : "0"));
            l.Add("rotasilog=" + (RotasiLog ? "1" : "0"));
            l.Add("hotkey=" + (Hotkey ? "1" : "0"));
            File.WriteAllLines(p, l.ToArray(), Encoding.UTF8);
        }

        // Argumen iris-stop.ps1 (sama dengan tombol Stop): StopSemua=false -> hanya overlay + server.py
        public string StopArgs()
        {
            string a = "-Proyek \"" + Proyek + "\" -Distro " + Distro;
            if (!StopSemua) a += " -TanpaWSL";
            return a;
        }

        public Settings Clone() { return (Settings)MemberwiseClone(); }
    }

    class SettingsForm : Form
    {
        public Settings Result;

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            AppInfo.Chrome(Handle);
        }
        TextBox tbProyek, tbDistro, tbRepo;
        NumericUpDown nudTunggu;
        CheckBox cbPenjaga, cbOverlay, cbKonfirm, cbAuto, cbTutup;
        CheckBox cbTray, cbXTray, cbWin, cbNotif, cbPulih, cbRotasi, cbHotkey, cbCekUpd;
        RadioButton rbSemua, rbSebagian, rbGpu, rbCpu;
        Label lblCek;

        public SettingsForm(Settings s)
        {
            Text = "Pengaturan Iris Launcher";
            AutoScaleMode = AutoScaleMode.Dpi;
            AutoScaleDimensions = new SizeF(96F, 96F);
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false; MinimizeBox = false;
            StartPosition = FormStartPosition.CenterParent;
            ClientSize = new Size(600, 632);
            BackColor = Theme.Bg; ForeColor = Theme.Text;
            Font = new Font("Segoe UI", 9.5F);
            try { Icon = Res.AppIcon(); } catch { }

            int y = 16;
            Controls.Add(L("Folder proyek Iris (berisi server.py)", 20, y)); y += 24;
            tbProyek = T(s.Proyek, 20, y, 440);
            tbProyek.TextChanged += delegate { Cek(); };
            Button bp = new RBtn(); bp.Text = "Pilih..."; bp.SetBounds(470, y - 1, 110, 28);
            Flat(bp, Theme.BtnDoctor); bp.Click += Pilih;
            Controls.Add(tbProyek); Controls.Add(bp); y += 34;
            lblCek = L("", 20, y); lblCek.AutoSize = false; lblCek.Size = new Size(560, 20); Controls.Add(lblCek); y += 34;

            Controls.Add(L("Nama distro WSL", 20, y));
            tbDistro = T(s.Distro, 300, y - 3, 280); Controls.Add(tbDistro); y += 36;

            Controls.Add(L("Batas tunggu layanan (detik)", 20, y));
            nudTunggu = new NumericUpDown(); nudTunggu.Minimum = 10; nudTunggu.Maximum = 900;
            nudTunggu.Value = Math.Max(10, Math.Min(900, s.TungguDetik));
            nudTunggu.SetBounds(300, y - 3, 100, 28);
            nudTunggu.BackColor = Theme.Panel; nudTunggu.ForeColor = Theme.Text;
            Controls.Add(nudTunggu); y += 40;

            cbPenjaga = C("Buka sesi penjaga WSL saat Start (supaya WSL tidak mati sendiri)", s.Penjaga, 20, y); y += 28;
            cbOverlay = C("Jalankan overlay Iris saat Start", s.Overlay, 20, y); y += 36;

            GroupBox g = new GroupBox(); g.Text = "Tombol Stop"; g.ForeColor = Theme.Muted;
            g.SetBounds(20, y, 560, 84);
            rbSemua = new RadioButton(); rbSemua.Text = "Matikan semuanya, termasuk WSL (RAM lepas)";
            rbSemua.SetBounds(14, 24, 520, 24); rbSemua.ForeColor = Theme.Text; rbSemua.Checked = s.StopSemua;
            rbSebagian = new RadioButton(); rbSebagian.Text = "Hanya overlay dan server.py (WSL dan Hermes tetap hidup)";
            rbSebagian.SetBounds(14, 50, 520, 24); rbSebagian.ForeColor = Theme.Text; rbSebagian.Checked = !s.StopSemua;
            g.Controls.Add(rbSemua); g.Controls.Add(rbSebagian); Controls.Add(g); y += 98;

            GroupBox gv = new GroupBox(); gv.Text = "Mesin suara VOICEVOX (berlaku saat VOICEVOX dinyalakan berikutnya)"; gv.ForeColor = Theme.Muted;
            gv.SetBounds(20, y, 560, 84);
            rbGpu = new RadioButton(); rbGpu.Text = "GPU (DirectML), lebih cepat; otomatis ke CPU bila GPU gagal";
            rbGpu.SetBounds(14, 24, 520, 24); rbGpu.ForeColor = Theme.Text; rbGpu.Checked = s.VoiceGpu;
            rbCpu = new RadioButton(); rbCpu.Text = "CPU saja, lebih hemat daya (tanpa --use_gpu)";
            rbCpu.SetBounds(14, 50, 520, 24); rbCpu.ForeColor = Theme.Text; rbCpu.Checked = !s.VoiceGpu;
            gv.Controls.Add(rbGpu); gv.Controls.Add(rbCpu); Controls.Add(gv); y += 98;

            cbKonfirm = C("Tanya konfirmasi sebelum mematikan (Stop dan Hermes)", s.KonfirmasiStop, 20, y); y += 28;
            cbAuto = C("Jalankan Start otomatis saat launcher dibuka", s.AutoStart, 20, y); y += 28;
            cbTutup = C("Saat launcher ditutup, matikan juga semua layanan Iris (sesuai pilihan Stop)", s.TutupMatikan, 20, y); y += 36;

            Label hdr = L("Tray, notifikasi, dan otomatisasi", 20, y); hdr.ForeColor = Theme.Muted; Controls.Add(hdr); y += 26;
            cbTray = C("Minimalkan ke tray (ikon dekat jam), bukan ke taskbar", s.MinimalKeTray, 20, y); y += 28;
            cbXTray = C("Tombol X hanya menyembunyikan ke tray (layanan tidak dimatikan)", s.TutupKeTray, 20, y); y += 28;
            cbWin = C("Buka launcher saat Windows menyala (langsung ke tray)", s.MulaiDenganWindows, 20, y); y += 28;
            cbNotif = C("Notifikasi saat layanan berhenti sendiri", s.Notifikasi, 20, y); y += 28;
            cbPulih = C("Nyalakan ulang otomatis layanan yang berhenti (maks 1x / 10 menit)", s.AutoPulih, 20, y); y += 28;
            cbRotasi = C("Rapikan log besar (> 5 MB) dan hapus arsip log > 14 hari", s.RotasiLog, 20, y); y += 28;
            cbHotkey = C("Pintasan global Ctrl+Alt+I: tampilkan / sembunyikan launcher", s.Hotkey, 20, y); y += 28;
            cbCekUpd = C("Cek update komponen otomatis saat launcher dibuka (butuh internet)", s.CekUpdate, 20, y); y += 32;
            Label lrepo = L("Repo GitHub rilis Iris Launcher untuk update sendiri (contoh: namamu/IrisLauncher; kosongkan bila tidak dipakai)", 20, y);
            lrepo.MaximumSize = new Size(560, 0); Controls.Add(lrepo); y += 44;
            tbRepo = T(s.LauncherRepo, 20, y, 440); Controls.Add(tbRepo); y += 44;

            Button ok = new RBtn(); ok.Text = "Simpan"; ok.SetBounds(360, y, 110, 34);
            Flat(ok, Theme.BtnStart); ok.Click += Simpan;
            Button cancel = new RBtn(); cancel.Text = "Batal"; cancel.SetBounds(480, y, 100, 34);
            Flat(cancel, Theme.BtnDoctor); cancel.DialogResult = DialogResult.Cancel;
            Controls.Add(ok); Controls.Add(cancel);
            AcceptButton = ok; CancelButton = cancel;
            Cek();

            // Isi lebih panjang dari layar kecil: aktifkan gulir.
            int contentH = y + 34 + 24;
            float sc = 1F;
            try { using (Graphics gr = CreateGraphics()) sc = gr.DpiX / 96F; } catch { }
            if (sc < 1F) sc = 1F;
            int maxH = (int)(Screen.PrimaryScreen.WorkingArea.Height / sc) - 100;   // tinggi layar dalam satuan 96 dpi
            AutoScroll = true;
            AutoScrollMinSize = new Size(0, contentH);
            ClientSize = new Size(600, Math.Min(contentH, Math.Max(420, maxH)));
        }

        // Pengaman terakhir: jangan pernah lebih tinggi dari area kerja layar (mis. layar kecil atau skala DPI besar).
        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);
            Rectangle wa = Screen.FromControl(this).WorkingArea;
            if (Height > wa.Height - 16) Height = wa.Height - 16;
            int top = wa.Top + Math.Max(0, (wa.Height - Height) / 2);
            int left = Math.Max(wa.Left, Math.Min(Left, wa.Right - Width));
            Location = new Point(left, top);
        }

        Label L(string t, int x, int y)
        {
            Label l = new Label(); l.Text = t; l.AutoSize = true; l.Location = new Point(x, y);
            l.ForeColor = Theme.Text; return l;
        }

        TextBox T(string t, int x, int y, int w)
        {
            TextBox b = new TextBox(); b.Text = t; b.SetBounds(x, y, w, 26);
            b.BackColor = Theme.Panel; b.ForeColor = Theme.Text; b.BorderStyle = BorderStyle.FixedSingle;
            return b;
        }

        CheckBox C(string t, bool v, int x, int y)
        {
            CheckBox c = new CheckBox(); c.Text = t; c.Checked = v; c.AutoSize = true;
            c.Location = new Point(x, y); c.ForeColor = Theme.Text; Controls.Add(c); return c;
        }

        static void Flat(Button b, Color c)
        {
            b.FlatStyle = FlatStyle.Flat; b.FlatAppearance.BorderSize = 0;
            b.BackColor = c; b.ForeColor = Color.White; b.Cursor = Cursors.Hand;
        }

        void Cek()
        {
            string d = tbProyek.Text.Trim();
            if (d.Length == 0) { lblCek.Text = "Belum diisi."; lblCek.ForeColor = Theme.Red; }
            else if (Settings.IsProject(d)) { lblCek.Text = "OK: server.py ditemukan di folder ini."; lblCek.ForeColor = Theme.Green; }
            else { lblCek.Text = "server.py tidak ditemukan di folder ini."; lblCek.ForeColor = Theme.Red; }
        }

        void Pilih(object sender, EventArgs e)
        {
            using (FolderBrowserDialog f = new FolderBrowserDialog())
            {
                f.Description = "Pilih folder proyek Iris (yang berisi server.py)";
                if (Directory.Exists(tbProyek.Text)) f.SelectedPath = tbProyek.Text;
                if (f.ShowDialog(this) == DialogResult.OK) tbProyek.Text = f.SelectedPath;
            }
        }

        void Simpan(object sender, EventArgs e)
        {
            string proyek = tbProyek.Text.Trim();
            if (proyek.Length > 3) proyek = proyek.TrimEnd('\\', '/');
            string distro = tbDistro.Text.Trim();
            if (proyek.Contains("\"")) { MessageBox.Show(this, "Folder proyek tidak boleh berisi tanda kutip.", "Pengaturan"); return; }
            if (!Regex.IsMatch(distro, @"^[A-Za-z0-9._-]+$")) { MessageBox.Show(this, "Nama distro hanya boleh huruf, angka, titik, minus, dan garis bawah (contoh: Ubuntu).", "Pengaturan"); return; }
            string repo = tbRepo.Text.Trim();
            if (repo.Length > 0 && !Regex.IsMatch(repo, @"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")) { MessageBox.Show(this, "Repo GitHub harus berbentuk pemilik/nama-repo (contoh: namamu/IrisLauncher).", "Pengaturan"); return; }
            if (!Settings.IsProject(proyek))
            {
                DialogResult r = MessageBox.Show(this, "server.py tidak ditemukan di folder itu. Tetap simpan?", "Pengaturan", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
                if (r != DialogResult.Yes) return;
            }
            Settings s = new Settings();
            s.Proyek = proyek; s.Distro = distro; s.TungguDetik = (int)nudTunggu.Value;
            s.Penjaga = cbPenjaga.Checked; s.Overlay = cbOverlay.Checked;
            s.StopSemua = rbSemua.Checked; s.KonfirmasiStop = cbKonfirm.Checked; s.AutoStart = cbAuto.Checked; s.TutupMatikan = cbTutup.Checked;
            s.VoiceGpu = rbGpu.Checked;
            s.MinimalKeTray = cbTray.Checked; s.TutupKeTray = cbXTray.Checked; s.MulaiDenganWindows = cbWin.Checked;
            s.Notifikasi = cbNotif.Checked; s.AutoPulih = cbPulih.Checked; s.RotasiLog = cbRotasi.Checked; s.Hotkey = cbHotkey.Checked; s.CekUpdate = cbCekUpd.Checked; s.LauncherRepo = repo;
            Result = s;
            DialogResult = DialogResult.OK;
            Close();
        }
    }

    // ---------------------------------------------------------------- v1.1: jalankan bersama Windows
    static class Startup
    {
        const string RunKey = @"Software\Microsoft\Windows\CurrentVersion\Run";
        const string ValName = "IrisLauncher";

        // Menulis / menghapus entri HKCU\...\Run (tanpa hak admin). Peluncur dibuka dengan --tray (langsung ke tray).
        public static void Set(bool on)
        {
            try
            {
                using (RegistryKey k = Registry.CurrentUser.OpenSubKey(RunKey, true))
                {
                    if (k == null) return;
                    if (on) k.SetValue(ValName, "\"" + Application.ExecutablePath + "\" --tray");
                    else if (k.GetValue(ValName) != null) k.DeleteValue(ValName, false);
                }
            }
            catch { }
        }
    }

    // ---------------------------------------------------------------- v1.1: menu gelap (tray, Alat, Preset)
    class DarkColors : ProfessionalColorTable
    {
        public override Color ToolStripDropDownBackground { get { return Theme.Panel; } }
        public override Color ImageMarginGradientBegin { get { return Theme.Panel; } }
        public override Color ImageMarginGradientMiddle { get { return Theme.Panel; } }
        public override Color ImageMarginGradientEnd { get { return Theme.Panel; } }
        public override Color MenuBorder { get { return Theme.Border; } }
        public override Color MenuItemBorder { get { return Theme.Accent; } }
        public override Color MenuItemSelected { get { return Theme.BtnDoctor; } }
        public override Color MenuItemSelectedGradientBegin { get { return Theme.BtnDoctor; } }
        public override Color MenuItemSelectedGradientEnd { get { return Theme.BtnDoctor; } }
        public override Color MenuItemPressedGradientBegin { get { return Theme.BtnDoctor; } }
        public override Color MenuItemPressedGradientMiddle { get { return Theme.BtnDoctor; } }
        public override Color MenuItemPressedGradientEnd { get { return Theme.BtnDoctor; } }
        public override Color SeparatorDark { get { return Theme.Border; } }
        public override Color SeparatorLight { get { return Theme.Border; } }
    }

    // ---------------------------------------------------------------- v1.1: ikon tray berwarna sesuai status
    static class TrayIcons
    {
        static readonly Dictionary<int, Icon> cache = new Dictionary<int, Icon>();

        // 0 = abu-abu (semua mati), 1 = kuning (sebagian hidup), 2 = hijau (semua hidup)
        public static Icon Get(int level)
        {
            Icon ic;
            if (cache.TryGetValue(level, out ic)) return ic;
            ic = null;
            try
            {
                Color dot = level == 2 ? Theme.Green : (level == 1 ? Theme.Amber : Theme.Gray);
                using (Icon src = Res.AppIcon())
                using (Icon big = new Icon(src, new Size(32, 32)))
                using (Bitmap bmp = new Bitmap(32, 32))
                using (Graphics g = Graphics.FromImage(bmp))
                {
                    g.SmoothingMode = SmoothingMode.AntiAlias;
                    g.DrawIcon(big, new Rectangle(0, 0, 32, 32));
                    Rectangle r = new Rectangle(17, 17, 14, 14);
                    using (Brush b = new SolidBrush(dot)) g.FillEllipse(b, r);
                    using (Pen p = new Pen(Theme.Bg, 2F)) g.DrawEllipse(p, r);
                    // Handle sengaja tidak dibebaskan: hanya 3 ikon, dipakai selama proses hidup.
                    ic = Icon.FromHandle(bmp.GetHicon());
                }
            }
            catch { ic = null; }
            if (ic == null) { try { ic = Res.AppIcon(); } catch { } }
            cache[level] = ic;
            return ic;
        }
    }

    // ---------------------------------------------------------------- v1.1: penampil log layanan
    class LogForm : Form
    {
        readonly string dir;
        ComboBox cb;
        RichTextBox rt;
        CheckBox cbLive;
        System.Windows.Forms.Timer tm;
        string lastText = null;

        static readonly string[] Names = new string[] {
            "iris-start.log", "iris-server.out.log", "iris-server.err.log",
            "iris-voicevox.out.log", "iris-voicevox.err.log",
            "iris-overlay.out.log", "iris-overlay.err.log" };

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            AppInfo.Chrome(Handle);
        }

        public LogForm(string proyek)
        {
            dir = proyek;
            Text = "Log layanan Iris";
            AutoScaleMode = AutoScaleMode.Dpi;
            AutoScaleDimensions = new SizeF(96F, 96F);
            ClientSize = new Size(820, 520);
            MinimumSize = new Size(600, 360);
            StartPosition = FormStartPosition.CenterParent;
            BackColor = Theme.Bg; ForeColor = Theme.Text;
            Font = new Font("Segoe UI", 9.5F);
            try { Icon = Res.AppIcon(); } catch { }

            Panel top = new Panel(); top.Dock = DockStyle.Top; top.Height = 46; top.BackColor = Theme.Bg;
            cb = new ComboBox(); cb.DropDownStyle = ComboBoxStyle.DropDownList; cb.SetBounds(14, 10, 250, 26);
            cb.BackColor = Theme.Panel; cb.ForeColor = Theme.Text; cb.FlatStyle = FlatStyle.Flat;
            bool any = false;
            foreach (string n in Names)
                if (File.Exists(Path.Combine(dir, n))) { cb.Items.Add(n); any = true; }
            if (!any) foreach (string n in Names) cb.Items.Add(n);
            cb.SelectedIndex = 0;
            cb.SelectedIndexChanged += delegate { lastText = null; LoadLog(); };

            cbLive = new CheckBox(); cbLive.Text = "Ikuti otomatis"; cbLive.Checked = true; cbLive.AutoSize = true;
            cbLive.Location = new Point(278, 13); cbLive.ForeColor = Theme.Text;

            Button bRe = new RBtn(); bRe.Text = "Muat ulang"; bRe.SetBounds(410, 9, 110, 28);
            bRe.FlatStyle = FlatStyle.Flat; bRe.FlatAppearance.BorderSize = 0; bRe.BackColor = Theme.BtnDoctor; bRe.ForeColor = Color.White; bRe.Cursor = Cursors.Hand;
            bRe.Click += delegate { lastText = null; LoadLog(); };

            Button bOpen = new RBtn(); bOpen.Text = "Buka di Notepad"; bOpen.SetBounds(530, 9, 140, 28);
            bOpen.FlatStyle = FlatStyle.Flat; bOpen.FlatAppearance.BorderSize = 0; bOpen.BackColor = Theme.BtnDoctor; bOpen.ForeColor = Color.White; bOpen.Cursor = Cursors.Hand;
            bOpen.Click += delegate
            {
                string n = cb.SelectedItem as string;
                if (n == null) return;
                string p = Path.Combine(dir, n);
                try { if (File.Exists(p)) Process.Start("notepad.exe", "\"" + p + "\""); } catch { }
            };
            top.Controls.Add(cb); top.Controls.Add(cbLive); top.Controls.Add(bRe); top.Controls.Add(bOpen);

            Label warn = new Label(); warn.Dock = DockStyle.Bottom; warn.Height = 26;
            warn.Text = "Catatan: log server memuat teks chat. Jangan dibagikan sembarangan. Yang ditampilkan: 64 KB terakhir.";
            warn.ForeColor = Theme.Amber; warn.Font = new Font("Segoe UI", 8.75F); warn.Padding = new Padding(14, 6, 0, 0);

            rt = new RichTextBox(); rt.ReadOnly = true; rt.Dock = DockStyle.Fill; rt.BorderStyle = BorderStyle.None;
            rt.BackColor = ColorTranslator.FromHtml("#0C0919"); rt.ForeColor = ColorTranslator.FromHtml("#DDD4FF");
            rt.Font = new Font("Consolas", 9.5F); rt.WordWrap = false; rt.DetectUrls = false;

            Controls.Add(rt); Controls.Add(warn); Controls.Add(top);

            tm = new System.Windows.Forms.Timer(); tm.Interval = 2000;
            tm.Tick += delegate { if (cbLive.Checked) LoadLog(); };
            Shown += delegate { LoadLog(); tm.Start(); };
            FormClosed += delegate { tm.Stop(); tm.Dispose(); };
        }

        static string Tail(string path, int maxBytes)
        {
            using (FileStream fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
            {
                long len = fs.Length;
                long start = Math.Max(0L, len - maxBytes);
                fs.Seek(start, SeekOrigin.Begin);
                byte[] buf = new byte[len - start];
                int read = 0;
                while (read < buf.Length)
                {
                    int r = fs.Read(buf, read, buf.Length - read);
                    if (r <= 0) break;
                    read += r;
                }
                string s = Encoding.UTF8.GetString(buf, 0, read);
                if (start > 0) { int nl = s.IndexOf('\n'); if (nl >= 0) s = s.Substring(nl + 1); }
                return s;
            }
        }

        void LoadLog()
        {
            string name = cb.SelectedItem as string;
            if (name == null) return;
            string path = Path.Combine(dir, name);
            string s;
            try { s = File.Exists(path) ? Tail(path, 65536) : "(berkas ini belum ada: layanan terkait belum pernah dijalankan dari launcher)"; }
            catch (Exception ex) { s = "(tidak bisa dibaca: " + ex.Message + ")"; }
            if (s == lastText) return;
            lastText = s;
            rt.Text = s;
            rt.SelectionStart = rt.TextLength; rt.ScrollToCaret();
        }
    }

    class UpdInfo
    {
        public string Key = "", Ins = "", Lat = "", Status = "", Note = "";
    }

    // Daftar komponen + versi terpasang/terbaru; pengguna mencentang yang mau di-update.
    class UpdateForm : Form
    {
        public List<string> Selected = new List<string>();
        public bool Pulihkan;
        CheckBox[] cbs;
        string[] keys;

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            AppInfo.Chrome(Handle);
        }

        static UpdInfo Find(List<UpdInfo> l, string key)
        {
            foreach (UpdInfo u in l) if (u.Key == key) return u;
            return null;
        }

        static string Headline(UpdInfo u)
        {
            if (u == null) return "Belum dicek";
            string v = "";
            if (u.Ins.Length > 0 && u.Lat.Length > 0) v = "   " + u.Ins + "  \u2192  " + u.Lat;
            else if (u.Ins.Length > 0) v = "   terpasang " + u.Ins;
            else if (u.Lat.Length > 0) v = "   terbaru " + u.Lat;
            switch (u.Status)
            {
                case "update": return "Update tersedia" + v;
                case "terbaru": return "Sudah terbaru" + v;
                case "unknown": return "Versi terpasang tidak terbaca" + v;
                case "major": return "Ada versi mayor (tidak otomatis)";
                case "tidakada": return "Tidak terpasang / tidak ditemukan";
                case "skip": return "Dilewati";
                default: return "Gagal dicek";
            }
        }

        static void Flat(Button b, Color c)
        {
            b.FlatStyle = FlatStyle.Flat; b.FlatAppearance.BorderSize = 0;
            b.BackColor = c; b.ForeColor = Color.White; b.Cursor = Cursors.Hand;
        }

        public UpdateForm(List<UpdInfo> infos, string[] keyList, string[] names, DateTime checkedAt, bool adaBackup)
        {
            keys = keyList;
            Text = "Update komponen Iris";
            AutoScaleMode = AutoScaleMode.Dpi;
            AutoScaleDimensions = new SizeF(96F, 96F);
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false; MinimizeBox = false;
            StartPosition = FormStartPosition.CenterParent;
            int rowH = 56;
            ClientSize = new Size(740, 106 + keys.Length * rowH + 64);
            BackColor = Theme.Bg; ForeColor = Theme.Text;
            Font = new Font("Segoe UI", 9.5F);
            try { Icon = Res.AppIcon(); } catch { }

            Label h1 = new Label(); h1.AutoSize = true; h1.Location = new Point(20, 14);
            h1.Font = new Font("Segoe UI Semibold", 12F); h1.ForeColor = Theme.Text;
            h1.Text = "Pilih komponen yang mau di-update";
            Controls.Add(h1);
            Label h2 = new Label(); h2.AutoSize = false; h2.SetBounds(20, 42, 700, 40);
            h2.ForeColor = Theme.Muted;
            h2.Text = "Layanan yang sedang hidup dimatikan sebentar lalu dinyalakan lagi. Tugas /agen Hermes yang sedang jalan bisa terputus."
                + (checkedAt == DateTime.MinValue ? "" : "  Terakhir dicek " + checkedAt.ToString("HH:mm") + ".");
            Controls.Add(h2);

            cbs = new CheckBox[keys.Length];
            for (int i = 0; i < keys.Length; i++)
            {
                UpdInfo u = Find(infos, keys[i]);
                string st = u == null ? "none" : u.Status;
                bool can = st == "update" || st == "unknown";
                Color c = st == "update" ? Theme.Amber
                    : st == "terbaru" ? Theme.Green
                    : (st == "galat" || st == "tidakada") ? Theme.Red : Theme.Muted;
                int y = 92 + i * rowH;

                CheckBox cb = new CheckBox(); cb.Text = ""; cb.AutoSize = false;
                cb.SetBounds(22, y + 4, 22, 22); cb.Enabled = can; cb.Checked = st == "update";
                cb.BackColor = Theme.Bg; cbs[i] = cb; Controls.Add(cb);

                Label n = new Label(); n.AutoSize = false; n.SetBounds(52, y + 3, 150, 24);
                n.Font = new Font("Segoe UI Semibold", 10.5F); n.ForeColor = can || st == "terbaru" ? Theme.Text : Theme.Muted;
                n.Text = names[i]; Controls.Add(n);

                Label hl = new Label(); hl.AutoSize = false; hl.SetBounds(206, y + 4, 520, 22);
                hl.ForeColor = c; hl.Text = Headline(u); Controls.Add(hl);

                Label nt = new Label(); nt.AutoSize = false; nt.SetBounds(52, y + 28, 674, 22);
                nt.ForeColor = Theme.Muted; nt.Font = new Font("Segoe UI", 8.75F);
                nt.Text = u == null ? "" : u.Note; Controls.Add(nt);
            }

            int by = ClientSize.Height - 50;
            Button ok = new RBtn(); ok.Text = "Update terpilih"; ok.SetBounds(20, by, 170, 36);
            Flat(ok, Theme.BtnStart); ok.Click += delegate { Pilih(); };
            Button re = new RBtn(); re.Text = "Cek ulang"; re.SetBounds(200, by, 110, 36);
            Flat(re, Theme.BtnDoctor); re.DialogResult = DialogResult.Retry;
            Button rw = new RBtn(); rw.Text = "Riwayat"; rw.SetBounds(320, by, 90, 36);
            Flat(rw, Theme.BtnDoctor); rw.Click += delegate { BukaRiwayat(); };
            Button tutup = new RBtn(); tutup.Text = "Tutup"; tutup.SetBounds(630, by, 90, 36);
            Flat(tutup, Theme.BtnDoctor); tutup.DialogResult = DialogResult.Cancel;
            Controls.Add(ok); Controls.Add(re); Controls.Add(rw); Controls.Add(tutup);
            if (adaBackup)
            {
                Button pv = new RBtn(); pv.Text = "Pulihkan VOICEVOX lama"; pv.SetBounds(420, by, 200, 36);
                Flat(pv, Theme.BtnStop); pv.Click += delegate { Pulihkan = true; DialogResult = DialogResult.Abort; Close(); };
                Controls.Add(pv);
            }
            CancelButton = tutup;
        }

        void BukaRiwayat()
        {
            string f = Res.HistoryFile();
            if (!File.Exists(f))
            {
                MessageBox.Show(this, "Belum ada riwayat update.", "Riwayat", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            try { Process.Start("notepad.exe", "\"" + f + "\""); }
            catch (Exception ex) { MessageBox.Show(this, ex.Message, "Riwayat"); }
        }

        void Pilih()
        {
            Selected.Clear();
            for (int i = 0; i < cbs.Length; i++)
                if (cbs[i].Enabled && cbs[i].Checked) Selected.Add(keys[i]);
            if (Selected.Count == 0)
            {
                MessageBox.Show(this, "Belum ada komponen yang dicentang.", "Update", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            DialogResult = DialogResult.OK;
            Close();
        }
    }

    class Probe
    {
        public bool Wsl, Voice, Router, Hermes, Server, Overlay;
        public long WslMB, OverlayMB;
        public int RamPct = -1;
    }

    class MainForm : Form
    {
        Settings cfg;
        ServiceChip[] chips = new ServiceChip[6];
        static readonly string[] ChipKey = new string[] { "wsl", "voicevox", "router", "hermes", "server", "overlay" };
        static readonly string[] ChipName = new string[] { "WSL", "VOICEVOX", "9Router", "Hermes", "server.py", "Overlay" };
        static readonly string[] UpdKey = new string[] { "wsl", "voicevox", "router", "hermes", "server", "overlay", "apt", "launcher" };
        static readonly string[] UpdName = new string[] { "WSL", "VOICEVOX", "9Router", "Hermes", "server.py", "Overlay", "Paket Ubuntu (apt)", "Iris Launcher" };
        System.Windows.Forms.Timer updTimer;
        string lastNotified = "";
        int busyChip = -1, errChip = -1;
        string busyCaption = "";
        ToolTip tip = new ToolTip();
        Button btnStart, btnStop, btnDoctor, btnCancel, btnSet, btnUpdate;
        List<UpdInfo> updInfos = new List<UpdInfo>();
        DateTime updChecked = DateTime.MinValue;
        int updCount;
        bool bgChecking;
        string[] chipTips;
        RichTextBox log;
        SummaryPill pill;
        static readonly Color LogBg = ColorTranslator.FromHtml("#0C0919");
        [DllImport("uxtheme.dll", CharSet = CharSet.Unicode)]
        static extern int SetWindowTheme(IntPtr hwnd, string app, string idlist);
        StatusText lblStatus;
        System.Windows.Forms.Timer timer;
        volatile bool probing;
        bool busy;
        Process current;
        Probe last = new Probe();
        bool inRun;
        DateTime lastLine = DateTime.Now;
        bool closeNow, pendingCloseStop;   // closeNow: penutupan sudah diputuskan; pendingCloseStop: Stop-lalu-tutup menunggu proses yang sedang jalan
        string runTitle = "";
        EventWaitHandle stopEvt;           // sinyal dari 'IrisLauncher.exe --stop-all' (menu Keluar overlay)

        // ---- v1.1
        readonly bool startTray;           // dibuka dengan --tray (mis. dari Windows Startup)
        NotifyIcon tray;
        ContextMenuStrip trayMenu;
        bool trayHinted, seeded, exitRequested, chainCancel, hotkeyOn;
        int trayLevel = -1, hiddenTick;
        bool[] stable = new bool[6];
        int[] offCount = new int[6];
        DateTime[] lastRecover = new DateTime[6];
        DateTime lastRunEnd = DateTime.MinValue;
        List<string> doctorLines = new List<string>();
        Color doctorColor = Theme.BtnDoctor;
        Label lblRam;
        Button btnPreset;
        LogForm logForm;
        EventWaitHandle showEvt;
        const int HotkeyId = 0x1215;
        [DllImport("user32.dll")]
        static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);
        [DllImport("user32.dll")]
        static extern bool UnregisterHotKey(IntPtr hWnd, int id);

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            AppInfo.Chrome(Handle);
            ApplyHotkey();
        }

        protected override void OnHandleDestroyed(EventArgs e)
        {
            UnregHotkey();
            base.OnHandleDestroyed(e);
        }

        public MainForm(bool startTray)
        {
            this.startTray = startTray;
            cfg = Settings.Load();
            if (startTray) WindowState = FormWindowState.Minimized;

            Text = "Iris Launcher " + AppInfo.Version;
            AutoScaleMode = AutoScaleMode.Dpi;
            AutoScaleDimensions = new SizeF(96F, 96F);
            ClientSize = new Size(800, 660);
            MinimumSize = new Size(720, 540);
            StartPosition = FormStartPosition.CenterScreen;
            BackColor = Theme.Bg; ForeColor = Theme.Text;
            Font = new Font("Segoe UI", 9.5F);
            try { Icon = Res.AppIcon(); } catch { }

            TableLayoutPanel t = new TableLayoutPanel();
            t.Dock = DockStyle.Fill; t.ColumnCount = 1; t.RowCount = 6;
            t.BackColor = Theme.Bg; t.Padding = new Padding(0);
            t.RowStyles.Add(new RowStyle(SizeType.Absolute, 100));
            t.RowStyles.Add(new RowStyle(SizeType.Absolute, 88));
            t.RowStyles.Add(new RowStyle(SizeType.Absolute, 76));
            t.RowStyles.Add(new RowStyle(SizeType.Absolute, 28));
            t.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            t.RowStyles.Add(new RowStyle(SizeType.Absolute, 44));
            Controls.Add(t);

            // 1. header
            Panel head = new GradPanel(); head.Dock = DockStyle.Fill; head.BackColor = Theme.Panel;
            PictureBox pb = new PictureBox(); pb.SetBounds(20, 14, 72, 72); pb.SizeMode = PictureBoxSizeMode.Zoom;
            try { pb.Image = Res.Logo(); } catch { }
            pb.BackColor = Color.Transparent;
            pb.Paint += delegate (object o, PaintEventArgs pe)
            {
                Rectangle rr = new Rectangle(1, 1, pb.Width - 3, pb.Height - 3);
                pe.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
                using (Pen ring = new Pen(Color.FromArgb(200, Theme.Accent), 2F)) pe.Graphics.DrawEllipse(ring, rr);
            };
            Label title = new Label(); title.Text = "Iris Launcher"; title.AutoSize = true;
            title.Font = new Font("Segoe UI Semibold", 19F); title.ForeColor = Theme.Text; title.Location = new Point(104, 12);
            title.BackColor = Color.Transparent;
            Label sub = new Label(); sub.Text = "Overlay  +  Hermes  +  WSL    \u2022    v" + AppInfo.Version; sub.AutoSize = true;
            sub.ForeColor = Theme.Accent; sub.Location = new Point(107, 58);
            sub.BackColor = Color.Transparent;
            btnSet = new RBtn(); btnSet.Text = "Pengaturan"; btnSet.Size = new Size(120, 34);
            btnSet.Location = new Point(head.Width - 120 - 20, 30);
            Style(btnSet, Theme.BtnDoctor); btnSet.Click += delegate { OpenSettings(); };
            pill = new SummaryPill(); pill.Size = new Size(150, 30); pill.Location = new Point(head.Width - 120 - 20 - 150 - 12, 32);
            lblRam = new Label(); lblRam.AutoSize = false; lblRam.Size = new Size(420, 20);
            lblRam.TextAlign = ContentAlignment.MiddleRight; lblRam.ForeColor = Theme.Muted;
            lblRam.Font = new Font("Segoe UI", 8.75F); lblRam.BackColor = Color.Transparent;
            lblRam.Location = new Point(head.Width - 420 - 20, 70);
            head.Controls.Add(pb); head.Controls.Add(title); head.Controls.Add(sub); head.Controls.Add(btnSet); head.Controls.Add(pill); head.Controls.Add(lblRam);
            head.Resize += delegate { btnSet.Left = head.Width - btnSet.Width - 20; pill.Left = btnSet.Left - pill.Width - 12; lblRam.Left = head.Width - lblRam.Width - 20; };
            t.Controls.Add(head, 0, 0);

            // 2. status: tiap chip bisa diklik (nyalakan / matikan hanya layanan itu)
            Panel stWrap = new Panel(); stWrap.Dock = DockStyle.Fill; stWrap.BackColor = Theme.Bg;
            TableLayoutPanel st = new TableLayoutPanel(); st.Dock = DockStyle.Fill; st.BackColor = Theme.Bg;
            st.ColumnCount = 6; st.RowCount = 1; st.Padding = new Padding(8, 0, 8, 6);
            for (int i = 0; i < 6; i++) st.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100F / 6F));
            st.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
            chipTips = new string[] {
                "WSL. Mati = semua layanan di dalamnya ikut mati.",
                "VOICEVOX :50021 (Windows, vv-engine + GPU; bila folder vv-engine tidak ada, di dalam WSL)", "9Router :20128 (di dalam WSL)", "Hermes :8642 (di dalam WSL)",
                "server.py :8765 (Windows)", "Overlay Electron (Windows)" };
            for (int i = 0; i < 6; i++)
            {
                ServiceChip c = new ServiceChip(); c.Title = ChipName[i]; c.Dock = DockStyle.Fill;
                c.Margin = new Padding(4); c.Caption = "Mati";
                int idx = i;
                c.Click += delegate { Toggle(idx); };
                tip.SetToolTip(c, chipTips[i] + "\r\nKlik untuk menyalakan / mematikan.");
                chips[i] = c; st.Controls.Add(c, i, 0);
            }
            Label hint = new Label(); hint.Dock = DockStyle.Top; hint.Height = 26;
            hint.Text = "Klik salah satu status untuk menyalakan atau mematikan hanya layanan itu.";
            hint.ForeColor = Theme.Muted; hint.Font = new Font("Segoe UI", 8.75F);
            hint.Padding = new Padding(16, 7, 0, 0);
            stWrap.Controls.Add(st); stWrap.Controls.Add(hint);
            t.Controls.Add(stWrap, 0, 1);

            // 3. tombol aksi
            TableLayoutPanel bp = new TableLayoutPanel(); bp.Dock = DockStyle.Fill; bp.ColumnCount = 5; bp.RowCount = 1;
            bp.Padding = new Padding(8, 4, 8, 10);
            float[] bw = new float[] { 23F, 23F, 22F, 16F, 16F };
            for (int i = 0; i < 5; i++) bp.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, bw[i]));
            btnStart = ActionBtn("\u25B6  Start semua", Theme.BtnStart); btnStart.Click += delegate { DoStart(); };
            btnStop = ActionBtn("\u25A0  Stop semua", Theme.BtnStop); btnStop.Click += delegate { DoStop(); };
            btnDoctor = ActionBtn("\u2695  Doctor", Theme.BtnDoctor); btnDoctor.Click += delegate { DoDoctor(); };
            bp.Controls.Add(btnStart, 0, 0); bp.Controls.Add(btnStop, 1, 0);
            bp.Controls.Add(btnDoctor, 2, 0);
            btnPreset = ActionBtn("Preset  \u25BE", Theme.BtnDoctor);
            ContextMenuStrip presetMenu = NewMenu(); AddPresets(presetMenu.Items);
            btnPreset.Click += delegate { presetMenu.Show(btnPreset, new Point(0, btnPreset.Height)); };
            bp.Controls.Add(btnPreset, 3, 0);
            btnUpdate = ActionBtn("\u2191  Update", Theme.BtnDoctor); btnUpdate.Click += delegate { DoUpdate(); };
            bp.Controls.Add(btnUpdate, 4, 0);
            tip.SetToolTip(btnUpdate, "Cek dan pasang update WSL, VOICEVOX, 9Router, Hermes, paket server.py, overlay, paket Ubuntu, dan launcher");
            tip.SetToolTip(btnPreset, "Nyalakan sebagian layanan saja (Chat saja, Hemat RAM)");
            tip.SetToolTip(btnStart, "Nyalakan semuanya sekaligus");
            tip.SetToolTip(btnStop, "Matikan semuanya sekaligus");
            tip.SetToolTip(btnDoctor, "Periksa kondisi semua komponen");
            t.Controls.Add(bp, 0, 2);

            // 4. log
            log = new RichTextBox(); log.ReadOnly = true; log.ScrollBars = RichTextBoxScrollBars.Vertical;
            log.Dock = DockStyle.Fill; log.BackColor = LogBg; log.ForeColor = ColorTranslator.FromHtml("#DDD4FF");
            log.Font = new Font("Consolas", 9.5F); log.BorderStyle = BorderStyle.None; log.DetectUrls = false;
            log.HandleCreated += delegate { try { SetWindowTheme(log.Handle, "DarkMode_Explorer", null); } catch { } };
            Panel logPad = new Panel(); logPad.Dock = DockStyle.Fill; logPad.BackColor = LogBg;
            logPad.Padding = new Padding(10, 8, 4, 8); logPad.Controls.Add(log);
            Panel logWrap = new Panel(); logWrap.Dock = DockStyle.Fill; logWrap.BackColor = Theme.Border;
            logWrap.Padding = new Padding(1); logWrap.Margin = new Padding(14, 0, 14, 0);
            logWrap.Controls.Add(logPad);
            Label logTitle = new Label(); logTitle.Dock = DockStyle.Fill; logTitle.Text = "Log aktivitas";
            logTitle.Font = new Font("Segoe UI Semibold", 9.5F); logTitle.ForeColor = Theme.Accent;
            logTitle.Padding = new Padding(16, 6, 0, 0); logTitle.BackColor = Theme.Bg;
            log.SelectionColor = Theme.Muted;
            log.AppendText("Siap. Tekan \u25B6 Start semua untuk menyalakan layanan,\r\natau klik salah satu status di atas untuk satu layanan saja.\r\n");
            log.SelectionColor = log.ForeColor;
            t.Controls.Add(logTitle, 0, 3);
            t.Controls.Add(logWrap, 0, 4);

            // 5. bawah
            Panel bottom = new Panel(); bottom.Dock = DockStyle.Fill; bottom.BackColor = Theme.Bg;
            lblStatus = new StatusText(); lblStatus.SetBounds(18, 0, 300, 44);
            btnCancel = new RBtn(); btnCancel.Text = "Batalkan"; btnCancel.Size = new Size(100, 28);
            btnCancel.Location = new Point(0, 8);
            Style(btnCancel, Theme.BtnStop); btnCancel.Visible = false; btnCancel.Click += delegate { CancelRun(); };
            Button bFolder = new RBtn(); bFolder.Text = "Alat  \u25BE"; bFolder.Size = new Size(110, 28);
            bFolder.Location = new Point(0, 8);
            Style(bFolder, Theme.BtnDoctor);
            ContextMenuStrip toolsMenu = BuildToolsMenu();
            bFolder.Click += delegate { toolsMenu.Show(bFolder, new Point(0, 0), ToolStripDropDownDirection.AboveRight); };
            Button bClear = new RBtn(); bClear.Text = "Bersihkan log"; bClear.Size = new Size(140, 28);
            bClear.Location = new Point(0, 8);
            Style(bClear, Theme.BtnDoctor); bClear.Click += delegate { log.Clear(); };
            bottom.Controls.Add(lblStatus); bottom.Controls.Add(btnCancel); bottom.Controls.Add(bFolder); bottom.Controls.Add(bClear);
            EventHandler place = delegate
            {
                bClear.Left = bottom.Width - bClear.Width - 16;
                bFolder.Left = bClear.Left - bFolder.Width - 10;
                btnCancel.Left = bFolder.Left - btnCancel.Width - 10;
            };
            bottom.Resize += place; place(null, EventArgs.Empty);
            t.Controls.Add(bottom, 0, 5);

            Shown += OnShown;
            FormClosing += OnClosing;
            FormClosed += delegate
            {
                try { if (tray != null) { tray.Visible = false; tray.Dispose(); } } catch { }
                UnregHotkey();
            };
            WatchStopSignal();
            WatchShowSignal();

            timer = new System.Windows.Forms.Timer(); timer.Interval = 5000;
            timer.Tick += delegate
            {
                // Saat disembunyikan / diminimalkan cek tiap ~10 detik (tetap perlu untuk ikon tray dan notifikasi).
                bool hidden = !Visible || WindowState == FormWindowState.Minimized;
                if (hidden && (++hiddenTick % 2) != 0) return;
                Refresh2();
            };
            Resize += delegate
            {
                if (WindowState == FormWindowState.Minimized)
                {
                    AppInfo.TrimMemory();
                    if (cfg.MinimalKeTray && IsHandleCreated && Visible)
                        BeginInvoke((Action)delegate { if (WindowState == FormWindowState.Minimized) HideToTray(); });
                }
            };
            BuildTray();
        }

        static void Style(Button b, Color c)
        {
            b.FlatStyle = FlatStyle.Flat; b.FlatAppearance.BorderSize = 0;
            b.BackColor = c; b.ForeColor = Color.White; b.Cursor = Cursors.Hand;
            b.FlatAppearance.MouseOverBackColor = ControlPaint.Light(c, 0.15F);
        }

        static Button ActionBtn(string text, Color c)
        {
            Button b = new RBtn(); b.Text = text; b.Dock = DockStyle.Fill; b.Margin = new Padding(6);
            b.Font = new Font("Segoe UI Semibold", 11F); Style(b, c); return b;
        }

        void UI(Action a)
        {
            if (IsDisposed || !IsHandleCreated) return;
            try { if (InvokeRequired) BeginInvoke(a); else a(); } catch { }
        }

        void Log(string s)
        {
            if (s != null && s.StartsWith("@@UPD|", StringComparison.Ordinal)) { ParseUpd(s); return; }
            if (inRun && runTitle == "Doctor" && !string.IsNullOrEmpty(s) && !s.StartsWith("===") && !s.StartsWith("---")) doctorLines.Add(s);
            if (log.TextLength > 200000) { log.Select(0, log.TextLength - 100000); log.SelectedText = ""; }
            Color c = log.ForeColor;
            string u = s ?? "";
            if (u.StartsWith("===")) c = Theme.Accent;
            else if (u.StartsWith("---")) c = Theme.Muted;
            else if (u.IndexOf("GAGAL", StringComparison.OrdinalIgnoreCase) >= 0 || u.IndexOf(" ERROR", StringComparison.OrdinalIgnoreCase) >= 0
                || u.IndexOf(" ERR ", StringComparison.OrdinalIgnoreCase) >= 0) c = Theme.Red;
            else if (u.IndexOf(" WARN", StringComparison.OrdinalIgnoreCase) >= 0 || u.IndexOf("Dibatalkan", StringComparison.OrdinalIgnoreCase) >= 0
                || u.IndexOf("berhenti sendiri", StringComparison.OrdinalIgnoreCase) >= 0) c = Theme.Amber;
            else if (u.IndexOf("Selesai", StringComparison.OrdinalIgnoreCase) >= 0 || u.IndexOf("sudah menjawab", StringComparison.OrdinalIgnoreCase) >= 0
                || u.IndexOf("naik", StringComparison.OrdinalIgnoreCase) >= 0 || u.IndexOf("hidup", StringComparison.OrdinalIgnoreCase) >= 0) c = Theme.Green;
            // Cap waktu otomatis untuk semua baris yang belum punya (keluaran Stop, "selesai", pesan launcher, dll).
            // Dilewati untuk baris kosong, judul "=== ... ===" (sudah memuat jam), dan baris yang sudah berawalan [HH:mm:ss].
            DateTime now = DateTime.Now;
            bool isStep = u.Length > 0 && !u.StartsWith("===") && !u.StartsWith("---");
            // Selama proses jalan: tulis lama langkah (selisih dari baris sebelumnya) bila >= 1 detik, mis. "(+4 dtk)".
            if (inRun && isStep)
            {
                int dt = (int)Math.Round((now - lastLine).TotalSeconds);
                if (dt >= 1) u += "  (+" + dt + " dtk)";
                lastLine = now;
            }
            if (u.Length > 0 && !u.StartsWith("===") && !Regex.IsMatch(u, @"^\[\d{2}:\d{2}:\d{2}\]"))
                u = "[" + now.ToString("HH:mm:ss") + "] " + u;
            log.SelectionStart = log.TextLength; log.SelectionLength = 0;
            log.SelectionColor = c;
            log.AppendText(u + "\r\n");
            log.SelectionColor = log.ForeColor;
            log.SelectionStart = log.TextLength; log.ScrollToCaret();
        }

        // ------------------------------------------------------------ mulai / tutup
        void OnShown(object sender, EventArgs e)
        {
            if (startTray && cfg.MinimalKeTray) DoHide(false);   // dibuka dari Windows Startup: langsung ke tray
            Startup.Set(cfg.MulaiDenganWindows);                 // sinkronkan entri Run (juga memperbarui jalur exe)

            try { Res.ExtractScripts(); }
            catch (Exception ex) { Log("[GAGAL] Tidak bisa menyiapkan skrip: " + ex.Message); }

            if (!Settings.IsProject(cfg.Proyek) && !startTray)
            {
                Log("Folder proyek belum diatur. Buka Pengaturan dan pilih folder yang berisi server.py.");
                OpenSettings();
            }
            RotateLogs(false);
            Refresh2();
            timer.Start();
            CleanOldExe();
            if (cfg.CekUpdate && Settings.IsProject(cfg.Proyek)) BackgroundCheck();
            StartUpdTimer();
            if (cfg.AutoStart)
            {
                if (Settings.IsProject(cfg.Proyek)) DoStart();
                else if (startTray) WaitProjectThenStart();
            }
        }

        bool AnyAlive() { return last.Wsl || last.Voice || last.Router || last.Hermes || last.Server || last.Overlay; }

        // Menutup launcher = mematikan semua layanan Iris dulu (kecuali dimatikan di Pengaturan atau Windows sedang shutdown).
        void OnClosing(object sender, FormClosingEventArgs e)
        {
            bool keluar = exitRequested; exitRequested = false;
            if (closeNow || e.CloseReason == CloseReason.WindowsShutDown) { timer.Stop(); return; }
            if (cfg.TutupKeTray && !keluar && e.CloseReason == CloseReason.UserClosing) { e.Cancel = true; HideToTray(); return; }
            bool perluStop = cfg.TutupMatikan && Settings.IsProject(cfg.Proyek) && (busy || AnyAlive());
            if (perluStop)
            {
                if (cfg.KonfirmasiStop)
                {
                    DialogResult q = MessageBox.Show(this,
                        "Menutup launcher akan ikut mematikan Overlay, server.py" + (cfg.StopSemua ? ", Hermes, 9Router, VOICEVOX, dan WSL" : "") + ".\r\n\r\n"
                        + "Tugas /agen yang sedang dikerjakan Hermes akan terputus.\r\n\r\n"
                        + "Ya = matikan semua lalu tutup\r\nTidak = tutup launcher saja (layanan tetap hidup)\r\nBatal = jangan tutup",
                        "Tutup Iris Launcher", MessageBoxButtons.YesNoCancel, MessageBoxIcon.Warning);
                    if (q == DialogResult.Cancel) { e.Cancel = true; return; }
                    if (q == DialogResult.No) { timer.Stop(); return; }
                }
                e.Cancel = true;
                StopAndClose();
                return;
            }
            if (busy)
            {
                DialogResult r = MessageBox.Show(this, "Masih ada proses yang berjalan. Tutup launcher saja? (proses yang sudah jalan di belakang tidak ikut berhenti)",
                    "Iris Launcher", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
                if (r != DialogResult.Yes) { e.Cancel = true; return; }
            }
            timer.Stop();
        }

        void OpenSettings()
        {
            using (SettingsForm f = new SettingsForm(cfg))
            {
                if (f.ShowDialog(this) == DialogResult.OK && f.Result != null)
                {
                    cfg = f.Result;
                    try { cfg.Save(); Log("Pengaturan disimpan."); }
                    catch (Exception ex) { Log("[GAGAL] Pengaturan tidak bisa disimpan: " + ex.Message); }
                    Startup.Set(cfg.MulaiDenganWindows);
                    ApplyHotkey();
                    Refresh2();
                }
            }
        }

        void OpenFolder()
        {
            try
            {
                if (Directory.Exists(cfg.Proyek)) Process.Start("explorer.exe", "\"" + cfg.Proyek + "\"");
                else Log("Folder proyek belum diatur.");
            }
            catch (Exception ex) { Log("[GAGAL] " + ex.Message); }
        }

        // ------------------------------------------------------------ v1.1: tray, pintasan, notifikasi
        void ApplyHotkey()
        {
            UnregHotkey();
            if (cfg == null || !cfg.Hotkey || !IsHandleCreated) return;
            // Ctrl+Alt+I  (0x1 = Alt, 0x2 = Ctrl, 0x4000 = tanpa pengulangan)
            hotkeyOn = RegisterHotKey(Handle, HotkeyId, 0x4003, (uint)Keys.I);
            if (!hotkeyOn && log != null) Log("GAGAL memasang pintasan Ctrl+Alt+I (sudah dipakai program lain).");
        }

        void UnregHotkey()
        {
            if (hotkeyOn && IsHandleCreated) { try { UnregisterHotKey(Handle, HotkeyId); } catch { } }
            hotkeyOn = false;
        }

        protected override void WndProc(ref Message m)
        {
            if (m.Msg == 0x0312 && m.WParam.ToInt32() == HotkeyId) { ToggleVisible(); return; }
            base.WndProc(ref m);
        }

        static ContextMenuStrip NewMenu()
        {
            ContextMenuStrip m = new ContextMenuStrip();
            m.Renderer = new ToolStripProfessionalRenderer(new DarkColors());
            m.BackColor = Theme.Panel; m.ForeColor = Theme.Text;
            m.Font = new Font("Segoe UI", 9.5F);
            m.ShowImageMargin = false;
            return m;
        }

        static ToolStripMenuItem Item(string text, Action a)
        {
            ToolStripMenuItem i = new ToolStripMenuItem(text);
            i.ForeColor = Theme.Text;
            i.Click += delegate { a(); };
            return i;
        }

        void AddPresets(ToolStripItemCollection c)
        {
            c.Add(Item("Penuh (semua layanan)", delegate { DoStart(); }));
            c.Add(Item("Chat saja (9Router + server.py + overlay)", delegate { StartChain("Chat saja", new int[] { 2, 4, 5 }); }));
            c.Add(Item("Hemat RAM (tanpa Hermes)", delegate { StartChain("Hemat RAM", new int[] { 1, 2, 4, 5 }); }));
        }

        void BuildTray()
        {
            trayMenu = NewMenu();
            ToolStripMenuItem open = Item("Buka Iris Launcher", delegate { RestoreFromTray(); });
            open.Font = new Font(trayMenu.Font, FontStyle.Bold);
            trayMenu.Items.Add(open);
            trayMenu.Items.Add(new ToolStripSeparator());
            trayMenu.Items.Add(Item("\u25B6  Start semua", delegate { DoStart(); }));
            trayMenu.Items.Add(Item("\u25A0  Stop semua", delegate { RestoreFromTray(); DoStop(); }));

            ToolStripMenuItem pre = new ToolStripMenuItem("Preset");
            pre.ForeColor = Theme.Text;
            ToolStripDropDownMenu dd = (ToolStripDropDownMenu)pre.DropDown;
            dd.Renderer = new ToolStripProfessionalRenderer(new DarkColors());
            dd.BackColor = Theme.Panel; dd.ForeColor = Theme.Text; dd.ShowImageMargin = false;
            AddPresets(pre.DropDownItems);
            trayMenu.Items.Add(pre);

            trayMenu.Items.Add(Item("\u2695  Doctor", delegate { DoDoctor(); }));
            trayMenu.Items.Add(Item("Log layanan...", delegate { RestoreFromTray(); OpenLogViewer(); }));
            trayMenu.Items.Add(new ToolStripSeparator());
            trayMenu.Items.Add(Item("Keluar", delegate { exitRequested = true; RestoreFromTray(); Close(); }));

            tray = new NotifyIcon();
            tray.ContextMenuStrip = trayMenu;
            tray.Icon = TrayIcons.Get(0);
            tray.Text = "Iris Launcher";
            tray.MouseClick += delegate (object s, MouseEventArgs e) { if (e.Button == MouseButtons.Left) RestoreFromTray(); };
            tray.Visible = true;
        }

        void UpdateTray(int cnt)
        {
            if (tray == null) return;
            int level = cnt == 0 ? 0 : (cnt == 6 ? 2 : 1);
            if (level != trayLevel)
            {
                trayLevel = level;
                Icon ic = TrayIcons.Get(level);
                if (ic != null) tray.Icon = ic;
            }
            tray.Text = "Iris Launcher: " + cnt + " dari 6 hidup";   // batas 63 karakter
        }

        void Notify(string title, string text, ToolTipIcon icon)
        {
            if (tray == null) return;
            try { tray.ShowBalloonTip(6000, title, text, icon); } catch { }
        }

        void DoHide(bool hint)
        {
            Hide();
            if (hint && !trayHinted)
            {
                trayHinted = true;
                Notify("Iris Launcher", "Masih berjalan di tray. Klik ikonnya untuk membuka lagi.", ToolTipIcon.Info);
            }
        }

        void HideToTray() { DoHide(true); }

        [DllImport("user32.dll")]
        static extern bool SetForegroundWindow(IntPtr hWnd);
        [DllImport("user32.dll")]
        static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

        void RestoreFromTray()
        {
            if (!Visible) Show();
            if (WindowState == FormWindowState.Minimized) ShowWindow(Handle, 9);   // SW_RESTORE
            bool top = TopMost;
            TopMost = true;      // trik agar lolos dari foreground lock Windows
            TopMost = top;
            Activate(); BringToFront();
            SetForegroundWindow(Handle);
            Refresh2();
        }

        void ToggleVisible()
        {
            if (Visible && WindowState != FormWindowState.Minimized) DoHide(false);
            else RestoreFromTray();
        }

        // Peluncur kedua (klik ganda exe saat yang pertama tersembunyi di tray) cukup memunculkan yang pertama.
        void WatchShowSignal()
        {
            try
            {
                showEvt = new EventWaitHandle(false, EventResetMode.AutoReset, "IrisLauncher.Show");
                Thread th = new Thread(delegate ()
                {
                    while (true)
                    {
                        try { showEvt.WaitOne(); } catch { return; }
                        UI(delegate { RestoreFromTray(); });
                    }
                });
                th.IsBackground = true; th.Start();
            }
            catch { }
        }

        // Dipakai saat Windows baru menyala: drive proyek (mis. USB) bisa belum siap.
        void WaitProjectThenStart()
        {
            Log("Folder proyek belum terbaca (drive belum siap?). Menunggu sampai 90 detik...");
            int tries = 0;
            System.Windows.Forms.Timer w = new System.Windows.Forms.Timer();
            w.Interval = 3000;
            w.Tick += delegate
            {
                tries++;
                if (Settings.IsProject(cfg.Proyek))
                {
                    w.Stop(); w.Dispose();
                    Log("Folder proyek ditemukan.");
                    DoStart();
                }
                else if (tries >= 30)
                {
                    w.Stop(); w.Dispose();
                    Log("GAGAL: folder proyek tidak ditemukan. Start otomatis dibatalkan.");
                    Notify("Iris Launcher", "Folder proyek tidak ditemukan; Start otomatis dibatalkan.", ToolTipIcon.Warning);
                }
            };
            w.Start();
        }

        // Layanan yang tadinya hidup lalu mati sendiri (dua pemeriksaan berturut-turut, di luar proses yang kita jalankan sendiri).
        void CheckTransitions(Probe p)
        {
            bool[] on = new bool[] { p.Wsl, p.Voice, p.Router, p.Hermes, p.Server, p.Overlay };
            bool quiet = !seeded || busy || (DateTime.Now - lastRunEnd).TotalSeconds < 25;
            seeded = true;
            List<int> turun = new List<int>();
            for (int i = 0; i < 5; i++)   // overlay (5) tidak dipantau: bisa ditutup sengaja lewat menunya
            {
                if (on[i]) { stable[i] = true; offCount[i] = 0; continue; }
                if (quiet) { stable[i] = false; offCount[i] = 0; continue; }
                if (!stable[i]) continue;
                offCount[i]++;
                if (offCount[i] >= 2) { stable[i] = false; turun.Add(i); }
            }
            if (turun.Count == 0) return;

            List<string> names = new List<string>();
            foreach (int i in turun)
            {
                if ((i == 2 || i == 3) && turun.Contains(0)) continue;   // ikut mati bersama WSL
                names.Add(ChipName[i]);
            }
            string msg = string.Join(", ", names.ToArray()) + " berhenti sendiri.";

            List<int> pulih = new List<int>();
            if (cfg.AutoPulih && Settings.IsProject(cfg.Proyek))
            {
                foreach (int i in turun)
                {
                    if (i == 0) continue;                       // WSL yang mati tidak dibangunkan otomatis
                    if ((i == 2 || i == 3) && !p.Wsl) continue; // 9Router dan Hermes butuh WSL hidup
                    if ((DateTime.Now - lastRecover[i]).TotalMinutes < 10) continue;
                    lastRecover[i] = DateTime.Now;
                    pulih.Add(i);
                }
            }
            if (pulih.Count > 0) msg += " Mencoba menyalakan ulang otomatis.";
            Log(msg);
            if (cfg.Notifikasi) Notify("Iris Launcher", msg, ToolTipIcon.Warning);
            if (pulih.Count > 0) StartChain("Pulih otomatis", pulih.ToArray());
        }

        // ------------------------------------------------------------ v1.1: RAM di header
        static string FmtMB(long mb)
        {
            return mb >= 1024 ? (mb / 1024.0).ToString("0.0") + " GB" : mb + " MB";
        }

        void UpdateRam(Probe p)
        {
            if (lblRam == null) return;
            List<string> parts = new List<string>();
            if (p.Wsl && p.WslMB > 0) parts.Add("WSL " + FmtMB(p.WslMB));
            if (p.Overlay && p.OverlayMB > 0) parts.Add("Overlay " + FmtMB(p.OverlayMB));
            if (p.RamPct >= 0) parts.Add("RAM sistem " + p.RamPct + "%");
            lblRam.Text = string.Join("   \u2022   ", parts.ToArray());
        }

        static long ProcMB(string name)
        {
            long total = 0;
            try
            {
                Process[] ps = Process.GetProcessesByName(name);
                foreach (Process x in ps)
                {
                    try { total += x.WorkingSet64; } catch { }
                    x.Dispose();
                }
            }
            catch { }
            return total / (1024 * 1024);
        }

        static long OverlayMB(string proyek)
        {
            long total = 0;
            try
            {
                string prefix = (proyek ?? "").TrimEnd('\\', '/') + "\\";
                Process[] ps = Process.GetProcessesByName("electron");
                foreach (Process x in ps)
                {
                    try
                    {
                        if (x.MainModule.FileName.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)) total += x.WorkingSet64;
                    }
                    catch { }
                    x.Dispose();
                }
            }
            catch { }
            return total / (1024 * 1024);
        }

        // ------------------------------------------------------------ v1.1: alat (menu "Alat")
        static string HomeDir() { return Environment.GetFolderPath(Environment.SpecialFolder.UserProfile); }
        static string HomeEnv() { return Path.Combine(HomeDir(), ".env"); }
        static string WslConfig() { return Path.Combine(HomeDir(), ".wslconfig"); }
        string ProjEnv() { return string.IsNullOrEmpty(cfg.Proyek) ? "" : Path.Combine(cfg.Proyek, ".env"); }

        void OpenText(string path)
        {
            if (string.IsNullOrEmpty(path) || !File.Exists(path)) { Log("Berkas tidak ditemukan: " + path); return; }
            try
            {
                Process.Start("notepad.exe", "\"" + path + "\"");
                if (path.EndsWith(".env", StringComparison.OrdinalIgnoreCase)) Log("Membuka .env di Notepad (berisi kunci rahasia; jangan dibagikan).");
            }
            catch (Exception ex) { Log("GAGAL: " + ex.Message); }
        }

        ContextMenuStrip BuildToolsMenu()
        {
            ContextMenuStrip m = NewMenu();
            m.Items.Add(Item("Buka folder proyek", delegate { OpenFolder(); }));
            ToolStripMenuItem envHome = Item("Buka .env (profil pengguna)", delegate { OpenText(HomeEnv()); });
            ToolStripMenuItem envProj = Item("Buka .env (folder proyek)", delegate { OpenText(ProjEnv()); });
            ToolStripMenuItem wslc = Item("Buka .wslconfig", delegate { OpenText(WslConfig()); });
            m.Items.Add(envHome); m.Items.Add(envProj); m.Items.Add(wslc);
            m.Items.Add(new ToolStripSeparator());
            m.Items.Add(Item("Log layanan...", delegate { OpenLogViewer(); }));
            m.Items.Add(Item("Salin laporan Doctor", delegate { CopyDoctor(); }));
            m.Items.Add(Item("Rapikan log lama sekarang", delegate { RotateLogs(true); }));
            m.Opening += delegate
            {
                envHome.Enabled = File.Exists(HomeEnv());
                envProj.Enabled = File.Exists(ProjEnv());
                wslc.Enabled = File.Exists(WslConfig());
            };
            return m;
        }

        void OpenLogViewer()
        {
            if (string.IsNullOrEmpty(cfg.Proyek) || !Directory.Exists(cfg.Proyek)) { Log("Folder proyek belum diatur."); return; }
            if (logForm != null && !logForm.IsDisposed) { logForm.Activate(); return; }
            logForm = new LogForm(cfg.Proyek);
            logForm.Show(this);
        }

        // Log besar (> 5 MB) dipindah ke *.log.old (satu generasi); arsip .old yang lebih dari 14 hari dihapus.
        // Berkas yang sedang dipakai proses lain (mis. log server yang sedang jalan) dilewati.
        void RotateLogs(bool manual)
        {
            if (!manual && !cfg.RotasiLog) return;
            if (string.IsNullOrEmpty(cfg.Proyek) || !Directory.Exists(cfg.Proyek)) { if (manual) Log("Folder proyek belum diatur."); return; }
            long batas = manual ? 1024L * 1024L : 5L * 1024L * 1024L;
            int dirotasi = 0, dihapus = 0, dilewati = 0;
            try
            {
                foreach (string f in Directory.GetFiles(cfg.Proyek, "iris-*.log"))
                {
                    try
                    {
                        if (new FileInfo(f).Length <= batas) continue;
                        string arsip = f + ".old";
                        if (File.Exists(arsip)) File.Delete(arsip);
                        File.Move(f, arsip);
                        dirotasi++;
                    }
                    catch { dilewati++; }
                }
                foreach (string f in Directory.GetFiles(cfg.Proyek, "iris-*.log.old"))
                {
                    try
                    {
                        if ((DateTime.Now - File.GetLastWriteTime(f)).TotalDays > 14) { File.Delete(f); dihapus++; }
                    }
                    catch { }
                }
            }
            catch { }
            if (dirotasi > 0 || dihapus > 0 || manual)
                Log("Rapikan log: " + dirotasi + " dipindah ke arsip (.old), " + dihapus + " arsip lama dihapus"
                    + (dilewati > 0 ? ", " + dilewati + " sedang dipakai (dilewati)" : "") + ".");
        }

        // ------------------------------------------------------------ v1.1: hasil Doctor
        void ApplyDoctorBadge()
        {
            int warn = 0, gagal = 0;
            foreach (string l in doctorLines)
            {
                if (l.StartsWith("[WARN")) warn++;
                else if (l.StartsWith("[GAGAL")) gagal++;
            }
            string baseText = "\u2695  Doctor";
            if (doctorLines.Count == 0) { doctorColor = Theme.BtnDoctor; btnDoctor.Text = baseText; }
            else if (gagal > 0) { doctorColor = ColorTranslator.FromHtml("#8A2A4D"); btnDoctor.Text = baseText + "  (" + gagal + " GAGAL)"; }
            else if (warn > 0) { doctorColor = ColorTranslator.FromHtml("#7A5E12"); btnDoctor.Text = baseText + "  (" + warn + " WARN)"; }
            else { doctorColor = ColorTranslator.FromHtml("#1F6B43"); btnDoctor.Text = baseText + "  \u2713"; }
            btnDoctor.BackColor = busy ? Theme.BtnOff : doctorColor;
            btnDoctor.FlatAppearance.MouseOverBackColor = ControlPaint.Light(doctorColor, 0.15F);
        }

        static string Mask(string t, string what, string repl)
        {
            if (string.IsNullOrEmpty(what)) return t;
            what = what.TrimEnd('\\', '/');
            if (what.Length < 4) return t;
            return Regex.Replace(t, Regex.Escape(what), repl, RegexOptions.IgnoreCase);
        }

        void CopyDoctor()
        {
            if (doctorLines.Count == 0) { Log("Belum ada hasil Doctor. Jalankan Doctor dulu."); return; }
            string t = string.Join("\r\n", doctorLines.ToArray());
            t = Mask(t, cfg.Proyek, "<PROYEK>");
            t = Mask(t, HomeDir(), "<HOME>");
            try
            {
                Clipboard.SetText(t);
                Log("Laporan Doctor disalin (" + doctorLines.Count + " baris; jalur proyek dan profil Windows disamarkan).");
            }
            catch (Exception ex) { Log("GAGAL menyalin: " + ex.Message); }
        }

        // ------------------------------------------------------------ v1.1: preset / rantai layanan
        void StartChain(string nama, int[] urut)
        {
            if (busy || !Ready()) return;
            chainCancel = false;
            Log("");
            Log("Preset: " + nama);
            ChainStep(urut, 0);
        }

        void ChainStep(int[] urut, int k)
        {
            if (chainCancel) return;
            if (k >= urut.Length) { Log("Preset selesai."); return; }
            RunService(urut[k], true, delegate (int code)
            {
                // BeginInvoke: Run() baru boleh dipanggil setelah SetBusy(false) selesai
                try { BeginInvoke((Action)delegate { ChainStep(urut, k + 1); }); } catch { }
            });
        }

        void RunService(int i, bool nyala, Action<int> after)
        {
            string a = "-Nama " + ChipKey[i] + " -Aksi " + (nyala ? "nyala" : "mati")
                + " -Distro " + cfg.Distro + " -TungguDetik " + cfg.TungguDetik;
            if (!string.IsNullOrEmpty(cfg.Proyek)) a += " -Proyek " + Q(cfg.Proyek);
            if (!cfg.Penjaga) a += " -TanpaPenjaga";
            if (!cfg.VoiceGpu) a += " -TanpaGPU";

            busyChip = i; errChip = -1;
            busyCaption = nyala ? "Menyalakan..." : "Mematikan...";
            UpdateChips();
            Run(ChipName[i] + ": " + (nyala ? "nyalakan" : "matikan"), "iris-service.ps1", a,
                delegate (int code)
                {
                    busyChip = -1;
                    if (code != 0) errChip = i;
                    UpdateChips();
                    if (after != null) after(code);
                });
            if (!busy) { busyChip = -1; UpdateChips(); }
        }

        // ------------------------------------------------------------ status
        static bool Alive(string url)
        {
            try
            {
                HttpWebRequest r = (HttpWebRequest)WebRequest.Create(url);
                r.Method = "GET"; r.Timeout = 1500; r.ReadWriteTimeout = 1500;
                r.AllowAutoRedirect = false; r.Proxy = null;
                using (WebResponse w = r.GetResponse()) { return true; }
            }
            catch (WebException ex) { return ex.Response != null; }
            catch { return false; }
        }

        static bool AnyProc(string name)
        {
            try
            {
                Process[] ps = Process.GetProcessesByName(name);
                bool any = ps.Length > 0;
                foreach (Process x in ps) x.Dispose();
                return any;
            }
            catch { return false; }
        }

        static bool OverlayUp(string proyek)
        {
            try
            {
                string prefix = (proyek ?? "").TrimEnd('\\', '/') + "\\";
                Process[] ps = Process.GetProcessesByName("electron");
                if (ps.Length == 0) return false;
                bool unknown = false;
                bool found = false;
                foreach (Process p in ps)
                {
                    try
                    {
                        if (!found)
                        {
                            string f = p.MainModule.FileName;
                            if (f.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)) found = true;
                        }
                    }
                    catch { unknown = true; }
                    p.Dispose();
                }
                return found || unknown;
            }
            catch { return false; }
        }

        Probe DoProbe(string proyek)
        {
            Probe p = new Probe();
            Thread[] th = new Thread[4];
            th[0] = new Thread(delegate () { p.Voice = Alive("http://127.0.0.1:50021/version"); });
            th[1] = new Thread(delegate () { p.Router = Alive("http://127.0.0.1:20128/"); });
            th[2] = new Thread(delegate () { p.Hermes = Alive("http://127.0.0.1:8642/health"); });
            // /ping, bukan /health: /health ikut memeriksa Hermes dll., jadi lambat saat Hermes mati dan melewati batas 1,5 detik
            // (server.py lama tanpa /ping membalas 404, itu tetap dihitung hidup)
            th[3] = new Thread(delegate () { p.Server = Alive("http://127.0.0.1:8765/ping"); });
            foreach (Thread x in th) { x.IsBackground = true; x.Start(); }
            p.Wsl = AnyProc("vmmemWSL") || AnyProc("vmmem");
            p.Overlay = OverlayUp(proyek);
            foreach (Thread x in th) x.Join(4000);
            p.RamPct = AppInfo.RamPercent();
            if (p.Wsl) p.WslMB = ProcMB("vmmemWSL") + ProcMB("vmmem");
            if (p.Overlay) p.OverlayMB = OverlayMB(proyek);
            return p;
        }

        void Refresh2()
        {
            if (probing || IsDisposed) return;
            probing = true;
            string proyek = cfg.Proyek;
            ThreadPool.QueueUserWorkItem(delegate
            {
                Probe p = null;
                try { p = DoProbe(proyek); } catch { }
                UI(delegate { if (p != null) Apply(p); probing = false; });
            });
        }

        void UpdateChips()
        {
            bool[] on = new bool[] { last.Wsl, last.Voice, last.Router, last.Hermes, last.Server, last.Overlay };
            for (int i = 0; i < 6; i++)
            {
                ServiceChip c = chips[i];
                if (on[i] && errChip == i) errChip = -1;
                if (busyChip == i) { c.Caption = busyCaption; c.State = ChipState.Busy; }
                else if (on[i]) { c.Caption = "Hidup"; c.State = ChipState.On; }
                else if (errChip == i) { c.Caption = "Gagal (lihat log)"; c.State = ChipState.Err; }
                else { c.Caption = "Mati"; c.State = ChipState.Off; }
            }
            int cnt = 0; for (int k = 0; k < 6; k++) if (on[k]) cnt++;
            pill.SetCount(cnt, 6);
            UpdateTray(cnt);
        }

        void Apply(Probe p)
        {
            last = p;
            UpdateChips();
            UpdateRam(p);
            CheckTransitions(p);
        }

        // ------------------------------------------------------------ menjalankan skrip
        void SetBusy(bool b, string status)
        {
            busy = b;
            btnStart.Enabled = !b; btnStop.Enabled = !b; btnDoctor.Enabled = !b; btnPreset.Enabled = !b; btnUpdate.Enabled = !b;
            Color off = Theme.BtnOff;
            btnStart.BackColor = b ? off : Theme.BtnStart; btnStop.BackColor = b ? off : Theme.BtnStop;
            btnDoctor.BackColor = b ? off : doctorColor; btnPreset.BackColor = b ? off : Theme.BtnDoctor;
            btnUpdate.BackColor = b ? off : UpdColor();
            btnCancel.Visible = b;
            lblStatus.Set(b ? StatusKind.Busy : (status != null && status.IndexOf("peringatan", StringComparison.OrdinalIgnoreCase) >= 0 ? StatusKind.Warn : (string.IsNullOrEmpty(status) || status.StartsWith("Siap") ? StatusKind.Idle : StatusKind.Ok)), status);
            Cursor = b ? Cursors.AppStarting : Cursors.Default;
        }

        bool Ready()
        {
            if (Settings.IsProject(cfg.Proyek)) return true;
            MessageBox.Show(this, "Folder proyek belum benar (server.py tidak ditemukan). Atur dulu di Pengaturan.",
                "Iris Launcher", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            OpenSettings();
            return Settings.IsProject(cfg.Proyek);
        }

        string P(string name) { return "\"" + Path.Combine(Res.ScriptDir(), name) + "\""; }
        string Q(string v) { return "\"" + v + "\""; }

        void Run(string title, string script, string args) { Run(title, script, args, null); }

        void Run(string title, string script, string args, Action<int> done)
        {
            if (busy) return;
            if (!File.Exists(Path.Combine(Res.ScriptDir(), script)))
            {
                try { Res.ExtractScripts(); } catch (Exception ex) { Log("[GAGAL] " + ex.Message); return; }
            }
            Log("");
            runTitle = title;
            if (title == "Doctor") doctorLines.Clear();
            DateTime mulai = DateTime.Now;
            Log("=== " + title + "  (" + mulai.ToString("HH:mm:ss") + ") ===");
            lastLine = mulai; inRun = true;
            SetBusy(true, title + " ...");

            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = "powershell.exe";
            psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File " + P(script) + " " + args;
            psi.UseShellExecute = false; psi.CreateNoWindow = true;
            psi.RedirectStandardOutput = true; psi.RedirectStandardError = true;
            psi.EnvironmentVariables["IRIS_LAUNCHER_EXE"] = Application.ExecutablePath;   // diwarisi overlay: menu Keluar memanggil launcher ini
            psi.StandardOutputEncoding = Encoding.UTF8; psi.StandardErrorEncoding = Encoding.UTF8;

            Thread th = new Thread(delegate ()
            {
                int code = -1;
                try
                {
                    Process p = new Process(); p.StartInfo = psi;
                    p.OutputDataReceived += delegate (object s, DataReceivedEventArgs e) { if (e.Data != null) { string d = e.Data; UI(delegate { Log(d); }); } };
                    p.ErrorDataReceived += delegate (object s, DataReceivedEventArgs e) { if (e.Data != null) { string d = e.Data; UI(delegate { Log(d); }); } };
                    p.Start();
                    current = p;
                    p.BeginOutputReadLine(); p.BeginErrorReadLine();
                    // Sengaja pakai batas waktu terbatas: proses anak (server.py, overlay) bisa memegang pipa,
                    // dan WaitForExit() tanpa argumen akan menunggu pipa itu tertutup.
                    while (!p.WaitForExit(500)) { }
                    Thread.Sleep(400);
                    code = p.ExitCode;
                }
                catch (Exception ex) { string m = ex.Message; UI(delegate { Log("[GAGAL] Tidak bisa menjalankan PowerShell: " + m); }); }
                current = null;
                int c = code;
                UI(delegate
                {
                    inRun = false;
                    lastRunEnd = DateTime.Now;
                    Log("--- selesai (kode " + c + ", " + (int)Math.Round((DateTime.Now - mulai).TotalSeconds) + " detik) ---");
                    if (done != null) { try { done(c); } catch { } }
                    SetBusy(false, c == 0 ? "Selesai." : "Selesai dengan peringatan atau galat (lihat log).");
                    Refresh2();
                    if (pendingCloseStop) { pendingCloseStop = false; StopAndClose(); }
                });
            });
            th.IsBackground = true; th.Start();
        }

        void CancelRun()
        {
            chainCancel = true;
            Process p = current;
            if (p == null) return;
            try
            {
                Process k = Process.Start(new ProcessStartInfo("taskkill.exe", "/PID " + p.Id + " /T /F") { CreateNoWindow = true, UseShellExecute = false });
                Log("Dibatalkan oleh pengguna.");
            }
            catch (Exception ex) { Log("[GAGAL] " + ex.Message); }
        }

        void DoStart()
        {
            if (busy || !Ready()) return;
            if (!last.Server) RotateLogs(false);
            string a = "-Proyek " + Q(cfg.Proyek) + " -Distro " + cfg.Distro + " -TungguDetik " + cfg.TungguDetik;
            if (!cfg.Penjaga) a += " -TanpaPenjaga";
            if (!cfg.Overlay) a += " -TanpaOverlay";
            if (!cfg.VoiceGpu) a += " -TanpaGPU";
            Run("Start", "iris-start.ps1", a);
        }

        void DoStop()
        {
            if (busy || !Ready()) return;
            if (cfg.StopSemua && cfg.KonfirmasiStop)
            {
                DialogResult r = MessageBox.Show(this,
                    "Overlay, server.py, Hermes, 9Router, VOICEVOX, dan WSL akan dimatikan.\r\n\r\nTugas /agen yang sedang dikerjakan Hermes akan terputus. Lanjutkan?",
                    "Stop", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
                if (r != DialogResult.Yes) return;
            }
            Run("Stop", "iris-stop.ps1", cfg.StopArgs());
        }

        // Jalankan iris-stop.ps1, lalu tutup jendela. Dipakai saat launcher ditutup dan saat overlay meminta Keluar.
        void StopAndClose()
        {
            if (busy && runTitle.StartsWith("Stop (launcher")) return;   // penutupan sudah berjalan
            if (busy)
            {
                pendingCloseStop = true;
                if (!runTitle.StartsWith("Stop")) CancelRun();   // Stop yang sedang jalan dibiarkan selesai, jangan dipotong
                return;
            }
            Run("Stop (launcher ditutup)", "iris-stop.ps1", cfg.StopArgs(), delegate (int c)
            {
                closeNow = true;
                try { BeginInvoke((Action)delegate { Close(); }); } catch { }
            });
            if (!busy) { closeNow = true; Close(); }   // Run menolak mulai (skrip tidak bisa disiapkan): jangan terjebak
        }

        // Menu Keluar di overlay memanggil "IrisLauncher.exe --stop-all": instance ini menerima sinyalnya dan mematikan semuanya.
        void WatchStopSignal()
        {
            try
            {
                stopEvt = new EventWaitHandle(false, EventResetMode.AutoReset, "IrisLauncher.StopAll");
                Thread th = new Thread(delegate ()
                {
                    while (true)
                    {
                        try { stopEvt.WaitOne(); } catch { return; }
                        UI(delegate
                        {
                            Log("Overlay meminta keluar: mematikan semua layanan.");
                            if (Settings.IsProject(cfg.Proyek)) StopAndClose();
                            else { closeNow = true; Close(); }
                        });
                    }
                });
                th.IsBackground = true; th.Start();
            }
            catch { }
        }

        // Klik chip: nyalakan atau matikan HANYA layanan itu.
        void Toggle(int i)
        {
            if (busy) return;
            bool[] on = new bool[] { last.Wsl, last.Voice, last.Router, last.Hermes, last.Server, last.Overlay };
            bool nyala = !on[i];
            if (i >= 4 && !Ready()) return;

            if (!nyala && cfg.KonfirmasiStop && (i == 0 || i == 3))
            {
                string msg = i == 0
                    ? "WSL akan dimatikan. 9Router dan Hermes ikut mati karena berjalan di dalam WSL (VOICEVOX ikut mati hanya bila masih dijalankan di WSL).\r\n\r\nTugas /agen yang sedang jalan akan terputus. Lanjutkan?"
                    : "Hermes akan dimatikan (WSL, 9Router, dan VOICEVOX tidak disentuh).\r\n\r\nTugas /agen yang sedang jalan akan terputus. Lanjutkan?";
                DialogResult r = MessageBox.Show(this, msg, ChipName[i], MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
                if (r != DialogResult.Yes) return;
            }

            RunService(i, nyala, null);
        }

        // ------------------------------------------------------------ update komponen
        Color UpdColor() { return updCount > 0 ? Theme.BtnHermes : Theme.BtnDoctor; }

        string UpdArgs(string aksi, string nama)
        {
            string a = "-Aksi " + aksi + " -Nama " + nama + " -Proyek " + Q(cfg.Proyek) + " -Distro " + cfg.Distro
                + " -TungguDetik " + cfg.TungguDetik;
            if (!cfg.VoiceGpu) a += " -TanpaGPU";
            a += " -Launcher " + Q(Application.ExecutablePath) + " -LauncherVersion " + Q(AppInfo.Version);
            if (!string.IsNullOrEmpty(cfg.LauncherRepo)) a += " -LauncherRepo " + Q(cfg.LauncherRepo);
            return a;
        }

        void ParseUpd(string line)
        {
            string[] p = line.Split(new char[] { '|' }, 6);
            if (p.Length < 5) return;
            UpdInfo u = new UpdInfo();
            u.Key = p[1]; u.Ins = p[2]; u.Lat = p[3]; u.Status = p[4]; u.Note = p.Length > 5 ? p[5] : "";
            for (int i = updInfos.Count - 1; i >= 0; i--)
                if (updInfos[i].Key == u.Key) updInfos.RemoveAt(i);
            updInfos.Add(u);
        }

        // Hitung ulang jumlah update, pasang lencana di chip dan warna tombol.
        void ApplyUpd()
        {
            updCount = 0;
            foreach (UpdInfo q in updInfos) if (q.Status == "update") updCount++;
            for (int i = 0; i < chips.Length; i++)
            {
                UpdInfo f = null;
                foreach (UpdInfo u in updInfos) if (u.Key == ChipKey[i]) { f = u; break; }
                bool has = f != null && f.Status == "update";
                chips[i].HasUpdate = has;
                string t = chipTips[i] + "\r\nKlik untuk menyalakan / mematikan.";
                if (has)
                {
                    string v = f.Ins.Length > 0 && f.Lat.Length > 0 ? f.Ins + " -> " + f.Lat : f.Note;
                    t += "\r\nUpdate tersedia: " + v;
                }
                tip.SetToolTip(chips[i], t);
            }
            btnUpdate.Text = "\u2191  Update" + (updCount > 0 ? " (" + updCount + ")" : "");
            if (!busy) btnUpdate.BackColor = UpdColor();
        }

        string UpdNames()
        {
            List<string> n = new List<string>();
            for (int i = 0; i < UpdKey.Length; i++)
                foreach (UpdInfo u in updInfos) if (u.Key == UpdKey[i] && u.Status == "update") n.Add(UpdName[i]);
            return string.Join(", ", n.ToArray());
        }

        // Cek diam-diam saat launcher dibuka: tidak membangunkan WSL, tidak mengisi log kecuali ada update.
        void BackgroundCheck()
        {
            if (bgChecking) return;
            bgChecking = true;
            string args = UpdArgs("cek", "semua") + " -Diam";
            string ps1 = Path.Combine(Res.ScriptDir(), "iris-update.ps1");
            ThreadPool.QueueUserWorkItem(delegate
            {
                List<string> lines = new List<string>();
                try
                {
                    ProcessStartInfo psi = new ProcessStartInfo();
                    psi.FileName = "powershell.exe";
                    psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File " + Q(ps1) + " " + args;
                    psi.UseShellExecute = false; psi.CreateNoWindow = true;
                    psi.RedirectStandardOutput = true;
                    psi.StandardOutputEncoding = Encoding.UTF8;
                    using (Process p = new Process())
                    {
                        p.StartInfo = psi;
                        p.OutputDataReceived += delegate (object so, DataReceivedEventArgs ev)
                        {
                            if (ev.Data != null && ev.Data.StartsWith("@@UPD|", StringComparison.Ordinal))
                                lock (lines) { lines.Add(ev.Data); }
                        };
                        p.Start();
                        p.BeginOutputReadLine();
                        if (!p.WaitForExit(240000)) { try { p.Kill(); } catch { } }
                        else Thread.Sleep(300);
                    }
                }
                catch { }
                string[] got;
                lock (lines) { got = lines.ToArray(); }
                UI(delegate
                {
                    bgChecking = false;
                    if (got.Length == 0) return;
                    foreach (string g in got) ParseUpd(g);
                    updChecked = DateTime.Now;
                    ApplyUpd();
                    if (updCount > 0)
                    {
                        string nm = UpdNames();
                        if (nm != lastNotified)
                        {
                            lastNotified = nm;
                            Log("Update tersedia: " + nm + ". Klik tombol Update.");
                            if (cfg.Notifikasi && !Visible) Notify("Iris Launcher", "Update tersedia: " + nm, ToolTipIcon.Info);
                        }
                    }
                    else lastNotified = "";
                });
            });
        }

        static string StatusWord(string st)
        {
            switch (st)
            {
                case "update": return "update tersedia";
                case "terbaru": return "sudah terbaru";
                case "unknown": return "versi terpasang tidak terbaca";
                case "major": return "ada versi mayor (tidak otomatis)";
                case "tidakada": return "tidak ditemukan";
                case "skip": return "dilewati";
                default: return "gagal dicek";
            }
        }

        void LogUpdSummary()
        {
            for (int i = 0; i < UpdKey.Length; i++)
                foreach (UpdInfo u in updInfos)
                {
                    if (u.Key != UpdKey[i]) continue;
                    string v = u.Ins.Length > 0 && u.Lat.Length > 0 ? u.Ins + " -> " + u.Lat : (u.Ins.Length > 0 ? u.Ins : u.Lat);
                    Log(UpdName[i] + ": " + StatusWord(u.Status) + (v.Length > 0 ? " (" + v + ")" : "") + (u.Note.Length > 0 ? " - " + u.Note : ""));
                }
        }

        void CheckUpdates(bool openAfter)
        {
            if (busy || !Ready()) return;
            updInfos.Clear();
            Run("Cek update", "iris-update.ps1", UpdArgs("cek", "semua"), delegate (int c)
            {
                updChecked = DateTime.Now;
                ApplyUpd();
                LogUpdSummary();
                if (openAfter) BeginInvoke((Action)delegate { ShowUpdateDialog(); });
            });
        }

        void DoUpdate()
        {
            if (busy || !Ready()) return;
            if (updInfos.Count == 0 || (DateTime.Now - updChecked).TotalMinutes > 30) { CheckUpdates(true); return; }
            ShowUpdateDialog();
        }

        void ShowUpdateDialog()
        {
            if (busy || IsDisposed) return;
            using (UpdateForm f = new UpdateForm(updInfos, UpdKey, UpdName, updChecked, HasVvBackup()))
            {
                DialogResult r = f.ShowDialog(this);
                if (r == DialogResult.Retry) { CheckUpdates(true); return; }
                if (r == DialogResult.Abort && f.Pulihkan) { RunRollback(); return; }
                if (r == DialogResult.OK && f.Selected.Count > 0) RunUpdate(f.Selected);
            }
        }

        void RunUpdate(List<string> keys)
        {
            List<string> names = new List<string>();
            foreach (string k in keys)
                for (int i = 0; i < UpdKey.Length; i++) if (UpdKey[i] == k) names.Add(UpdName[i]);
            string msg = "Akan di-update: " + string.Join(", ", names.ToArray()) + ".\r\n\r\n"
                + "Layanan yang sedang hidup dimatikan sebentar lalu dinyalakan lagi."
                + (keys.Contains("wsl") ? " Update WSL mematikan WSL beserta isinya." : "")
                + (keys.Contains("voicevox") ? " Update VOICEVOX mengunduh ribuan MB dan butuh beberapa menit." : "")
                + (keys.Contains("apt") ? " Update paket Ubuntu bisa makan beberapa menit." : "")
                + (keys.Contains("launcher") ? " Launcher mengganti exe-nya sendiri, lalu kamu ditawari mulai ulang." : "")
                + "\r\nTugas /agen Hermes yang sedang jalan bisa terputus. Lanjutkan?";
            if (MessageBox.Show(this, msg, "Update", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
            Run("Update: " + string.Join(", ", names.ToArray()), "iris-update.ps1", UpdArgs("update", string.Join(",", keys.ToArray())),
                delegate (int c)
                {
                    // setelah SetBusy(false) selesai: tawarkan mulai ulang bila launcher baru terpasang, kalau tidak cek ulang
                    BeginInvoke((Action)delegate
                    {
                        if (keys.Contains("launcher") && File.Exists(Application.ExecutablePath + ".old")) AskRestart();
                        else CheckUpdates(false);
                    });
                });
        }

        bool HasVvBackup()
        {
            try
            {
                if (string.IsNullOrEmpty(cfg.Proyek) || !Directory.Exists(cfg.Proyek)) return false;
                return Directory.GetDirectories(cfg.Proyek, "vv-engine.bak-*").Length > 0;
            }
            catch { return false; }
        }

        void RunRollback()
        {
            if (busy || !Ready()) return;
            string msg = "VOICEVOX akan dikembalikan ke folder cadangan terakhir (vv-engine.bak-...). Versi yang sekarang dibuang.\r\n\r\nVOICEVOX dimatikan sebentar. Lanjutkan?";
            if (MessageBox.Show(this, msg, "Pulihkan VOICEVOX", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes) return;
            Run("Pulihkan VOICEVOX", "iris-update.ps1", UpdArgs("pulihkan", "voicevox"),
                delegate (int c) { BeginInvoke((Action)delegate { CheckUpdates(false); }); });
        }

        // Cek berkala saat launcher dibiarkan hidup (mis. di tray): paling sering sekali per 4 jam.
        void StartUpdTimer()
        {
            if (updTimer != null) return;
            updTimer = new System.Windows.Forms.Timer();
            updTimer.Interval = 30 * 60 * 1000;
            updTimer.Tick += delegate
            {
                if (!cfg.CekUpdate || busy || bgChecking || !Settings.IsProject(cfg.Proyek)) return;
                if ((DateTime.Now - updChecked).TotalHours < 4) return;
                BackgroundCheck();
            };
            updTimer.Start();
        }

        // Sisa exe lama setelah update launcher (diganti nama jadi .old oleh iris-update.ps1).
        void CleanOldExe()
        {
            try
            {
                string old = Application.ExecutablePath + ".old";
                if (File.Exists(old)) File.Delete(old);
            }
            catch { }
        }

        void AskRestart()
        {
            DialogResult r = MessageBox.Show(this,
                "Iris Launcher sudah diganti ke versi baru. Mulai ulang sekarang?\r\n\r\nLayanan yang sedang hidup tidak dimatikan.",
                "Update launcher", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
            if (r == DialogResult.Yes) RestartSelf(); else CheckUpdates(false);
        }

        void RestartSelf()
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo("cmd.exe", "/c ping -n 3 127.0.0.1 >nul & start \"\" " + Q(Application.ExecutablePath));
                psi.CreateNoWindow = true; psi.UseShellExecute = false;
                Process.Start(psi);
            }
            catch (Exception ex) { Log("[GAGAL] Tidak bisa memulai ulang otomatis: " + ex.Message + ". Buka IrisLauncher.exe sendiri."); return; }
            closeNow = true;
            Close();
        }

        void DoDoctor()
        {
            if (busy || !Ready()) return;
            Run("Doctor", "iris-doctor.ps1", "-Proyek " + Q(cfg.Proyek) + " -Distro " + cfg.Distro,
                delegate (int c) { try { BeginInvoke((Action)ApplyDoctorBadge); } catch { } });
        }
    }

    static class Program
    {
        // Launcher tidak terbuka tapi overlay minta Keluar: jalankan iris-stop.ps1 tanpa jendela.
        static void HeadlessStop()
        {
            try
            {
                Settings s = Settings.Load();
                if (!Settings.IsProject(s.Proyek)) return;
                Res.ExtractScripts();
                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = "powershell.exe";
                psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File \"" + Path.Combine(Res.ScriptDir(), "iris-stop.ps1") + "\" " + s.StopArgs();
                psi.UseShellExecute = false; psi.CreateNoWindow = true;
                using (Process p = Process.Start(psi)) { p.WaitForExit(180000); }
            }
            catch { }
        }

        [STAThread]
        static void Main(string[] args)
        {
            bool stopAll = args != null && Array.IndexOf(args, "--stop-all") >= 0;
            bool startTray = args != null && Array.IndexOf(args, "--tray") >= 0;
            bool created;
            using (Mutex m = new Mutex(true, "IrisLauncher.SingleInstance", out created))
            {
                if (!created)
                {
                    if (stopAll)
                    {
                        try { using (EventWaitHandle ev = EventWaitHandle.OpenExisting("IrisLauncher.StopAll")) { ev.Set(); } } catch { }
                        return;
                    }
                    if (startTray) return;   // Windows Startup saat launcher sudah jalan: diam saja
                    try { using (EventWaitHandle ev = EventWaitHandle.OpenExisting("IrisLauncher.Show")) { ev.Set(); return; } } catch { }
                    MessageBox.Show("Iris Launcher sudah terbuka.", "Iris Launcher");
                    return;
                }
                if (stopAll) { HeadlessStop(); return; }
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new MainForm(startTray));
            }
        }
    }
}
