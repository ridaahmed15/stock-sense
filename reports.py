from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

def build_pdf_report(metrics, insights, title="StockSense AI | Inventory Intelligence Report"):
    buffer=BytesIO()
    doc=SimpleDocTemplate(buffer,pagesize=landscape(A4),rightMargin=14*mm,leftMargin=14*mm,topMargin=13*mm,bottomMargin=13*mm)
    styles=getSampleStyleSheet()
    story=[Paragraph(title,styles["Title"]),Spacer(1,5*mm),
           Paragraph("Decision support based on the uploaded or sample data. Forecasts and reorder quantities are estimates, not purchase orders.",styles["BodyText"]),Spacer(1,4*mm)]
    for item in insights: story.append(Paragraph("• "+item,styles["BodyText"]))
    story.append(Spacer(1,5*mm))
    cols=["Product","Category","On hand","30d sold","Days cover","Status","Cash tied (Rs.)"]
    data=[cols]
    for _,r in metrics.sort_values("inventory_cost_value",ascending=False).head(30).iterrows():
        cover="—" if r.days_of_cover==float("inf") else f"{r.days_of_cover:.1f}"
        data.append([str(r.product_name)[:25],str(r.category),f"{r.on_hand:,.0f}",f"{r.units_30d:,.0f}",cover,str(r.stock_status),f"{r.cash_trapped_value:,.0f}"])
    table=Table(data,repeatRows=1,colWidths=[45*mm,30*mm,20*mm,20*mm,22*mm,30*mm,28*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#18233f")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),8),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#d8deea")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f3f6fb")]),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)
    ]))
    story.append(table)
    doc.build(story)
    return buffer.getvalue()
