// by: KangJiho
// Iris Launcher v1.0 - satu exe: Start / Stop / Hermes / Doctor + pengaturan.
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

[assembly: AssemblyTitle("Iris Launcher")]
[assembly: AssemblyProduct("Iris Launcher")]
[assembly: AssemblyDescription("Peluncur IRIS desktop companion: Start, Stop, Hermes, Doctor")]
[assembly: AssemblyCompany("KangJiho")]
[assembly: AssemblyCopyright("Copyright (c) 2026 KangJiho. All rights reserved")]
[assembly: AssemblyInformationalVersion("1.0.0")]
[assembly: AssemblyVersion("1.0.0.0")]
[assembly: AssemblyFileVersion("1.0.0.0")]

namespace IrisLauncher
{
    static class AppInfo
    {
        public const string Version = "1.0";

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
            foreach (string n in new string[] { "iris-start.ps1", "iris-stop.ps1", "iris-hermes.ps1", "iris-doctor.ps1", "iris-service.ps1" })
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
        public bool VoiceGpu = true;       // VOICEVOX Windows (vv-engine): true = GPU (DirectML), false = CPU

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
        TextBox tbProyek, tbDistro;
        NumericUpDown nudTunggu;
        CheckBox cbPenjaga, cbOverlay, cbKonfirm, cbAuto, cbTutup;
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
            cbTutup = C("Saat launcher ditutup, matikan juga semua layanan Iris (sesuai pilihan Stop)", s.TutupMatikan, 20, y); y += 44;

            Button ok = new RBtn(); ok.Text = "Simpan"; ok.SetBounds(360, y, 110, 34);
            Flat(ok, Theme.BtnStart); ok.Click += Simpan;
            Button cancel = new RBtn(); cancel.Text = "Batal"; cancel.SetBounds(480, y, 100, 34);
            Flat(cancel, Theme.BtnDoctor); cancel.DialogResult = DialogResult.Cancel;
            Controls.Add(ok); Controls.Add(cancel);
            AcceptButton = ok; CancelButton = cancel;
            Cek();
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
            Result = s;
            DialogResult = DialogResult.OK;
            Close();
        }
    }

    class Probe
    {
        public bool Wsl, Voice, Router, Hermes, Server, Overlay;
    }

    class MainForm : Form
    {
        Settings cfg;
        ServiceChip[] chips = new ServiceChip[6];
        static readonly string[] ChipKey = new string[] { "wsl", "voicevox", "router", "hermes", "server", "overlay" };
        static readonly string[] ChipName = new string[] { "WSL", "VOICEVOX", "9Router", "Hermes", "server.py", "Overlay" };
        int busyChip = -1, errChip = -1;
        string busyCaption = "";
        ToolTip tip = new ToolTip();
        Button btnStart, btnStop, btnDoctor, btnCancel, btnSet;
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

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            AppInfo.Chrome(Handle);
        }

        public MainForm()
        {
            cfg = Settings.Load();

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
            head.Controls.Add(pb); head.Controls.Add(title); head.Controls.Add(sub); head.Controls.Add(btnSet); head.Controls.Add(pill);
            head.Resize += delegate { btnSet.Left = head.Width - btnSet.Width - 20; pill.Left = btnSet.Left - pill.Width - 12; };
            t.Controls.Add(head, 0, 0);

            // 2. status: tiap chip bisa diklik (nyalakan / matikan hanya layanan itu)
            Panel stWrap = new Panel(); stWrap.Dock = DockStyle.Fill; stWrap.BackColor = Theme.Bg;
            TableLayoutPanel st = new TableLayoutPanel(); st.Dock = DockStyle.Fill; st.BackColor = Theme.Bg;
            st.ColumnCount = 6; st.RowCount = 1; st.Padding = new Padding(8, 0, 8, 6);
            for (int i = 0; i < 6; i++) st.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100F / 6F));
            st.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
            string[] tips = new string[] {
                "WSL. Mati = semua layanan di dalamnya ikut mati.",
                "VOICEVOX (Windows, vv-engine + GPU; bila folder vv-engine tidak ada, di dalam WSL)", "9Router (di dalam WSL)", "Hermes (di dalam WSL)",
                "server.py (Windows)", "Overlay Electron (Windows)" };
            for (int i = 0; i < 6; i++)
            {
                ServiceChip c = new ServiceChip(); c.Title = ChipName[i]; c.Dock = DockStyle.Fill;
                c.Margin = new Padding(4); c.Caption = "Mati";
                int idx = i;
                c.Click += delegate { Toggle(idx); };
                tip.SetToolTip(c, tips[i] + "\r\nKlik untuk menyalakan / mematikan.");
                chips[i] = c; st.Controls.Add(c, i, 0);
            }
            Label hint = new Label(); hint.Dock = DockStyle.Top; hint.Height = 26;
            hint.Text = "Klik salah satu status untuk menyalakan atau mematikan hanya layanan itu.";
            hint.ForeColor = Theme.Muted; hint.Font = new Font("Segoe UI", 8.75F);
            hint.Padding = new Padding(16, 7, 0, 0);
            stWrap.Controls.Add(st); stWrap.Controls.Add(hint);
            t.Controls.Add(stWrap, 0, 1);

            // 3. tombol aksi
            TableLayoutPanel bp = new TableLayoutPanel(); bp.Dock = DockStyle.Fill; bp.ColumnCount = 3; bp.RowCount = 1;
            bp.Padding = new Padding(8, 4, 8, 10);
            for (int i = 0; i < 3; i++) bp.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100F / 3F));
            btnStart = ActionBtn("\u25B6  Start semua", Theme.BtnStart); btnStart.Click += delegate { DoStart(); };
            btnStop = ActionBtn("\u25A0  Stop semua", Theme.BtnStop); btnStop.Click += delegate { DoStop(); };
            btnDoctor = ActionBtn("\u2695  Doctor", Theme.BtnDoctor); btnDoctor.Click += delegate { DoDoctor(); };
            bp.Controls.Add(btnStart, 0, 0); bp.Controls.Add(btnStop, 1, 0);
            bp.Controls.Add(btnDoctor, 2, 0);
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
            Button bFolder = new RBtn(); bFolder.Text = "Buka folder"; bFolder.Size = new Size(110, 28);
            bFolder.Location = new Point(0, 8);
            Style(bFolder, Theme.BtnDoctor); bFolder.Click += delegate { OpenFolder(); };
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
            WatchStopSignal();

            timer = new System.Windows.Forms.Timer(); timer.Interval = 5000;
            timer.Tick += delegate { if (WindowState != FormWindowState.Minimized) Refresh2(); };
            Resize += delegate { if (WindowState == FormWindowState.Minimized) AppInfo.TrimMemory(); };
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
            if (log.TextLength > 200000) { log.Select(0, log.TextLength - 100000); log.SelectedText = ""; }
            Color c = log.ForeColor;
            string u = s ?? "";
            if (u.StartsWith("===")) c = Theme.Accent;
            else if (u.StartsWith("---")) c = Theme.Muted;
            else if (u.IndexOf("GAGAL", StringComparison.OrdinalIgnoreCase) >= 0 || u.IndexOf(" ERROR", StringComparison.OrdinalIgnoreCase) >= 0
                || u.IndexOf(" ERR ", StringComparison.OrdinalIgnoreCase) >= 0) c = Theme.Red;
            else if (u.IndexOf(" WARN", StringComparison.OrdinalIgnoreCase) >= 0 || u.IndexOf("Dibatalkan", StringComparison.OrdinalIgnoreCase) >= 0) c = Theme.Amber;
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
            try { Res.ExtractScripts(); }
            catch (Exception ex) { Log("[GAGAL] Tidak bisa menyiapkan skrip: " + ex.Message); }

            if (!Settings.IsProject(cfg.Proyek))
            {
                Log("Folder proyek belum diatur. Buka Pengaturan dan pilih folder yang berisi server.py.");
                OpenSettings();
            }
            Refresh2();
            timer.Start();
            if (cfg.AutoStart && Settings.IsProject(cfg.Proyek)) DoStart();
        }

        bool AnyAlive() { return last.Wsl || last.Voice || last.Router || last.Hermes || last.Server || last.Overlay; }

        // Menutup launcher = mematikan semua layanan Iris dulu (kecuali dimatikan di Pengaturan atau Windows sedang shutdown).
        void OnClosing(object sender, FormClosingEventArgs e)
        {
            if (closeNow || e.CloseReason == CloseReason.WindowsShutDown) { timer.Stop(); return; }
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
        }

        void Apply(Probe p)
        {
            last = p;
            UpdateChips();
        }

        // ------------------------------------------------------------ menjalankan skrip
        void SetBusy(bool b, string status)
        {
            busy = b;
            btnStart.Enabled = !b; btnStop.Enabled = !b; btnDoctor.Enabled = !b;
            Color off = Theme.BtnOff;
            btnStart.BackColor = b ? off : Theme.BtnStart; btnStop.BackColor = b ? off : Theme.BtnStop;
            btnDoctor.BackColor = b ? off : Theme.BtnDoctor;
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
                });
            if (!busy) { busyChip = -1; UpdateChips(); }
        }

        void DoDoctor()
        {
            if (busy || !Ready()) return;
            Run("Doctor", "iris-doctor.ps1", "-Proyek " + Q(cfg.Proyek) + " -Distro " + cfg.Distro);
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
                    MessageBox.Show("Iris Launcher sudah terbuka.", "Iris Launcher");
                    return;
                }
                if (stopAll) { HeadlessStop(); return; }
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new MainForm());
            }
        }
    }
}
