from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

M = ['Januari','Februari','Mac','April','Mei','Jun','Julai','Ogos','September','Oktober','November','Disember']
meta25=[49312.74,17565.41,2488.90,23315.19,21050.11,32978.84,42851.39,41417.13,18086.44,18911.44,21049.30,29143.03]
meta26=[7983.12,7301.32,7717.98,34999.19,44014.02,44292.30,56294.02,24660.47,33532.85,48558.65]
tt25=[0,0,0,164.44,443.19,0,0,2385.09,583.12,674.26,704.45,2227.87]
tt26=[1665.11,1515.29,804.09,6177.44,10997.16,2255.97,1140.43,0,0,0]
g25=[2096.14,1703.30,1210.35,1493.40,1752.29,1759.65,2057.50,1590.69,356.64,40.22,0,1244.81]
g26=[2030.21,1327.07,796.85,1459.73,1068.13,1089.51,1106.64,975.02,1062.70,1166.86]

f = lambda x: f'{x:,.2f}'
NAVY = colors.HexColor('#1f3a5f'); LIGHT = colors.HexColor('#eef2f7'); GRID = colors.HexColor('#c8d1dc')

ss = getSampleStyleSheet()
H1 = ParagraphStyle('h1', parent=ss['Title'], fontSize=18, textColor=NAVY, spaceAfter=2)
SUB = ParagraphStyle('sub', parent=ss['Normal'], fontSize=9, textColor=colors.grey, alignment=1, spaceAfter=10)
H2 = ParagraphStyle('h2', parent=ss['Heading2'], fontSize=12, textColor=NAVY, spaceBefore=10, spaceAfter=5)
NOTE = ParagraphStyle('n', parent=ss['Normal'], fontSize=8.5, leading=11, textColor=colors.HexColor('#444444'))

def table(rows, widths, total_rows=1):
    t = Table(rows, colWidths=widths, repeatRows=1)
    st = [('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),
          ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),
          ('ALIGN',(1,0),(-1,-1),'RIGHT'),('GRID',(0,0),(-1,-1),0.4,GRID),
          ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
          ('ROWBACKGROUNDS',(0,1),(-1,-1-total_rows),[colors.white,LIGHT])]
    for i in range(total_rows):
        r = -1 - i
        st += [('FONTNAME',(0,r),(-1,r),'Helvetica-Bold'),('BACKGROUND',(0,r),(-1,r),colors.HexColor('#d9e2ee'))]
    t.setStyle(TableStyle(st)); return t

def single(title, vals):
    rows = [['Bulan','Total Spend (RM)']] + [[M[i], f(v)] for i, v in enumerate(vals)] + [['JUMLAH', f(sum(vals))]]
    return [Paragraph(title, H2), table(rows, [60*mm, 50*mm])]

def combined(title, a, b, c):
    rows = [['Bulan','Meta','TikTok','Google','Jumlah']]
    for i in range(len(a)):
        rows.append([M[i], f(a[i]), f(b[i]), f(c[i]), f(a[i]+b[i]+c[i])])
    rows.append(['JUMLAH', f(sum(a)), f(sum(b)), f(sum(c)), f(sum(a)+sum(b)+sum(c))])
    return [Paragraph(title, H2), table(rows, [32*mm, 33*mm, 30*mm, 30*mm, 35*mm])]

doc = SimpleDocTemplate('/home/user/Testing/Ads_Spend_Minda_Optima_Jan2025-Okt2026.pdf', pagesize=A4,
                        leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm,
                        title='Ads Spend Minda Optima', author='Minda Optima')
s = [Paragraph('Laporan Ads Spend - Minda Optima', H1),
     Paragraph('Tempoh: Januari 2025 - Oktober 2026 | Semua jumlah dalam RM', SUB)]

tm, tt, tg = sum(meta25)+sum(meta26), sum(tt25)+sum(tt26), sum(g25)+sum(g26)
grand = tm+tt+tg
sumrows = [['Platform','2025','2026 (Jan-Okt)','Jumlah','%'],
           ['Meta Ads', f(sum(meta25)), f(sum(meta26)), f(tm), f'{tm/grand*100:.1f}%'],
           ['TikTok Ads', f(sum(tt25)), f(sum(tt26)), f(tt), f'{tt/grand*100:.1f}%'],
           ['Google Ads', f(sum(g25)), f(sum(g26)), f(tg), f'{tg/grand*100:.1f}%'],
           ['JUMLAH', f(sum(meta25)+sum(tt25)+sum(g25)), f(sum(meta26)+sum(tt26)+sum(g26)), f(grand), '100%']]
s += [Paragraph('Ringkasan', H2), table(sumrows, [38*mm, 36*mm, 38*mm, 38*mm, 20*mm]), Spacer(1,6),
      Paragraph('<b>Nota:</b> TikTok dan Google ialah jumlah termasuk cukai (DST dan Service Tax 8%), '
                'dikira daripada invois dalam Google Drive. Angka Meta diberi oleh pengguna dan tidak disahkan '
                'dengan sumber asal. Bulan TikTok 0.00 bermaksud tiada invois dalam folder; Google Nov 2025 juga '
                'tiada invois. TikTok Apr-Mei 2025 termasuk invois atas nama "Pusat Tuisyen Minda Optima" '
                '(tanpa Sdn Bhd), RM607.63.', NOTE), PageBreak()]
s += single('Meta Ads 2025', meta25) + single('Meta Ads 2026 (Jan-Okt)', meta26) + [PageBreak()]
s += single('TikTok Ads 2025', tt25) + single('TikTok Ads 2026 (Jan-Okt)', tt26) + [PageBreak()]
s += single('Google Ads 2025', g25) + single('Google Ads 2026 (Jan-Okt)', g26) + [PageBreak()]
s += combined('Gabungan 2025', meta25, tt25, g25) + combined('Gabungan 2026 (Jan-Okt)', meta26, tt26, g26)
doc.build(s)
