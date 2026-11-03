import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from database import seed_if_empty, read_table, save_frame
from analytics import validate_data, build_product_metrics, forecast_product, reorder_recommendations, slow_stock, make_insights
from reports import build_pdf_report

ROOT=Path(__file__).parent
st.set_page_config(page_title="StockSense AI",page_icon="📦",layout="wide",initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--ink:#10182d;--muted:#8b9ab7;--panel:#17233d;--line:rgba(255,255,255,.09);--lime:#c7f36b;--cyan:#61d7e8}
.stApp{background:radial-gradient(circle at 78% 4%,rgba(72,112,173,.28),transparent 28%),linear-gradient(135deg,#0b1224 0%,#101b33 52%,#172440 100%);color:#f5f7ff;font-family:'DM Sans',sans-serif}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#111d35,#0d1629);border-right:1px solid var(--line)}
.block-container{padding-top:1.5rem;padding-bottom:3rem;max-width:1500px}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;color:#f7f9ff!important}
p, label, .stMarkdown{color:#d5deef}
.hero{padding:28px 32px;border:1px solid rgba(255,255,255,.12);border-radius:24px;background:linear-gradient(110deg,rgba(33,57,94,.96),rgba(24,42,70,.78));box-shadow:0 18px 60px rgba(0,0,0,.22);position:relative;overflow:hidden;animation:rise .7s ease both}
.hero:after{content:'✦';position:absolute;right:8%;top:-48px;font-size:190px;color:rgba(199,243,107,.10);transform:rotate(12deg)}
.eyebrow{color:var(--lime);font-size:11px;font-weight:800;letter-spacing:2.4px;text-transform:uppercase}
.hero h1{font-size:36px;margin:8px 0 5px}
.hero p{color:#b8c7df;margin:0;max-width:680px}
.kpi{background:linear-gradient(145deg,rgba(34,52,83,.95),rgba(21,34,58,.95));border:1px solid var(--line);border-radius:18px;padding:18px 20px;min-height:122px;box-shadow:0 12px 30px rgba(0,0,0,.12);animation:rise .55s ease both}
.kpi-label{font-size:12px;color:#9eacc6;font-weight:700;letter-spacing:.6px;text-transform:uppercase}
.kpi-value{font-family:'Space Grotesk';font-size:27px;font-weight:700;color:white;margin:7px 0}
.kpi-foot{font-size:11px;color:#8d9bb6}
.panel{background:rgba(22,35,60,.78);border:1px solid var(--line);border-radius:20px;padding:20px 22px}
.insight{border:1px solid rgba(199,243,107,.22);border-left:4px solid var(--lime);background:rgba(199,243,107,.07);border-radius:12px;padding:13px 16px;margin:9px 0;color:#e8f4d1}
.tag{display:inline-block;background:rgba(97,215,232,.12);color:#83e7f2;padding:5px 9px;border-radius:20px;font-size:11px;font-weight:700}
div[data-testid="stMetric"]{background:rgba(255,255,255,.04);padding:12px;border-radius:12px}
.stButton>button{background:linear-gradient(90deg,#c7f36b,#9edb4c);color:#142034;border:0;border-radius:10px;font-weight:800;min-height:42px}
.stButton>button:hover{filter:brightness(1.08);color:#142034;border:0;transform:translateY(-1px)}
.stDownloadButton>button{background:#243858;color:#f7f9ff;border:1px solid #405579;border-radius:10px}
.stTabs [data-baseweb="tab"]{color:#c7d2e6}
.stTabs [aria-selected="true"]{color:#c7f36b!important}
div[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:12px;overflow:hidden}
[data-testid="stSelectbox"] label,[data-testid="stSlider"] label{color:#c9d5e9}
@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
@keyframes pulse{0%,100%{opacity:.65}50%{opacity:1}}
.pulse{animation:pulse 2.3s infinite}
</style>
""",unsafe_allow_html=True)

seed_if_empty(ROOT/"data")
if "datasets" not in st.session_state:
    st.session_state.datasets={t:read_table(t) for t in ["sales","products","inventory","suppliers"]}

def fmt_rs(v): return f"Rs. {v:,.0f}"
def chart_theme(fig,height=330):
    fig.update_layout(height=height,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#d7e1f2",family="DM Sans"),margin=dict(l=10,r=10,t=35,b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),xaxis=dict(gridcolor="rgba(255,255,255,.07)"),
        yaxis=dict(gridcolor="rgba(255,255,255,.07)"))
    return fig

def kpi(label,value,foot):
    st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-foot">{foot}</div></div>',unsafe_allow_html=True)

d=st.session_state.datasets
errors=validate_data(d["sales"],d["products"],d["inventory"])
if errors:
    st.error("Data validation needs attention: "+" | ".join(errors))
    st.stop()
metrics=build_product_metrics(d["sales"],d["products"],d["inventory"],d["suppliers"])
slow=slow_stock(metrics)
metrics["movement_class"]=slow["movement_class"]
metrics["cash_trapped_value"]=slow["cash_trapped_value"]
insights=make_insights(metrics)

with st.sidebar:
    st.markdown("## 📦 StockSense **AI**")
    st.caption("INVENTORY INTELLIGENCE")
    page=st.radio("WORKSPACE",["Overview","Demand Forecast","Reorder Planner","Cash Trapped","Product Analytics","Data Studio","Reports"],label_visibility="visible")
    st.markdown("---")
    st.markdown('<span class="tag">● SYSTEM ONLINE</span>',unsafe_allow_html=True)
    st.caption("Local demo database · SQLite")
    st.markdown("---")
    st.caption("DATA CONTROLS")
    if st.button("↻ Restore sample data",use_container_width=True):
        for table in ["sales","products","inventory","suppliers"]:
            frame=pd.read_csv(ROOT/"data"/f"{table}.csv")
            st.session_state.datasets[table]=frame
            save_frame(table,frame)
        st.rerun()
    st.caption("StockSense AI • v1.0")

st.markdown('<div class="hero"><div class="eyebrow">PREDICTIVE INVENTORY INTELLIGENCE</div><h1>Make every unit count.</h1><p>See demand before it happens, protect working capital, and turn inventory decisions into a competitive advantage.</p><br><span class="tag">✦ AI-ASSISTED DECISION SUPPORT</span> &nbsp; <span class="tag">LIVE DATA WORKSPACE</span></div>',unsafe_allow_html=True)
st.write("")

# Shared filters
f1,f2,f3=st.columns([1,1,1])
with f1: cat_filter=st.selectbox("Category",["All"]+sorted(metrics.category.dropna().unique().tolist()))
with f2: supplier_filter=st.selectbox("Supplier",["All"]+sorted(metrics.supplier.dropna().unique().tolist()))
with f3: lookback=st.select_slider("Sales analysis window",options=[30,60,90,180,365],value=90,format_func=lambda x:f"Last {x} days")
filtered=metrics.copy()
if cat_filter!="All": filtered=filtered[filtered.category==cat_filter]
if supplier_filter!="All": filtered=filtered[filtered.supplier==supplier_filter]
latest=pd.to_datetime(d["sales"].date,errors="coerce").max()
sales_recent=d["sales"].copy(); sales_recent["date"]=pd.to_datetime(sales_recent.date,errors="coerce")
sales_recent=sales_recent[sales_recent.date>latest-pd.Timedelta(days=lookback)]
total_sales=int(sales_recent.units_sold.sum())
revenue=float(sales_recent.revenue.sum()) if "revenue" in sales_recent else float(total_sales)
inventory_value=float(filtered.inventory_cost_value.sum())
trapped=float(filtered.cash_trapped_value.sum())
stock_risk=int((filtered.stock_status!="Healthy").sum())

if page=="Overview":
    st.markdown("### Executive snapshot")
    cols=st.columns(4)
    with cols[0]: kpi("Units sold",f"{total_sales:,.0f}",f"Across selected {lookback}-day window")
    with cols[1]: kpi("Inventory at cost",fmt_rs(inventory_value),"Current on-hand stock valuation")
    with cols[2]: kpi("Capital at risk",fmt_rs(trapped),"Slow-moving + dead stock estimate")
    with cols[3]: kpi("SKUs needing attention",f"{stock_risk}", "Reorder now or at-risk products")
    st.write("")
    left,right=st.columns([1.5,1])
    with left:
        st.markdown("### Sales momentum")
        daily=sales_recent.groupby("date").agg(units=("units_sold","sum")).reset_index()
        daily["7-day average"]=daily.units.rolling(7,min_periods=1).mean()
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=daily.date,y=daily.units,name="Daily units",mode="lines",line=dict(color="#61d7e8",width=1.5),opacity=.55))
        fig.add_trace(go.Scatter(x=daily.date,y=daily["7-day average"],name="7-day trend",mode="lines",line=dict(color="#c7f36b",width=3)))
        st.plotly_chart(chart_theme(fig),use_container_width=True)
    with right:
        st.markdown("### Inventory health")
        status=filtered.stock_status.value_counts().rename_axis("Status").reset_index(name="Products")
        fig=px.pie(status,names="Status",values="Products",hole=.68,color="Status",color_discrete_map={"Healthy":"#c7f36b","At risk":"#f7b955","Reorder now":"#ff6b7a"})
        fig.update_traces(textinfo="label+value")
        st.plotly_chart(chart_theme(fig,330),use_container_width=True)
    st.markdown("### AI business signals")
    for item in make_insights(filtered): st.markdown(f'<div class="insight">✦ &nbsp;{item}</div>',unsafe_allow_html=True)
    st.markdown("### Products to watch")
    watch=filtered.sort_values(["days_of_cover","on_hand"]).head(8)[["product_name","category","on_hand","units_30d","days_of_cover","lead_time_days","stock_status"]].copy()
    watch["days_of_cover"]=watch.days_of_cover.replace(np.inf,np.nan).round(1)
    st.dataframe(watch,use_container_width=True,hide_index=True)

elif page=="Demand Forecast":
    st.markdown("### Demand forecast")
    st.write("Select a SKU to estimate demand for the next 7–90 days. The model uses daily sales lags and calendar patterns.")
    names=metrics[["product_id","product_name"]].drop_duplicates()
    selected=st.selectbox("Product",names.product_id.tolist(),format_func=lambda x:names.loc[names.product_id==x,"product_name"].iloc[0])
    horizon=st.slider("Forecast horizon (days)",7,90,30,step=7)
    result,error=forecast_product(d["sales"],selected,horizon)
    if error: st.warning(error)
    else:
        fc=result["forecast"]
        fig=go.Figure()
        hist=result["history"].tail(120)
        fig.add_trace(go.Scatter(x=hist.date,y=hist.actual_units,name="Historical daily sales",mode="lines",line=dict(color="#61d7e8")))
        fig.add_trace(go.Scatter(x=fc.date,y=fc.forecast_units,name="Forecast",mode="lines+markers",line=dict(color="#c7f36b",width=3)))
        fig.add_trace(go.Scatter(x=list(fc.date)+list(fc.date[::-1]),y=list(fc.upper_bound)+list(fc.lower_bound[::-1]),fill="toself",fillcolor="rgba(199,243,107,.12)",line=dict(color="rgba(0,0,0,0)"),name="Indicative error band"))
        st.plotly_chart(chart_theme(fig,400),use_container_width=True)
        c1,c2,c3=st.columns(3)
        c1.metric("Forecast units",f"{fc.forecast_units.sum():,.0f}")
        c2.metric("Daily average",f"{fc.forecast_units.mean():.1f}")
        c3.metric("Validation MAE",f"{result['mae']:.2f}" if result["mae"] is not None else "N/A")
        st.caption("Method: "+result["model"]+". The shaded band is based on a chronological holdout MAE; it is indicative, not a formal confidence interval. Forecasts are not guarantees.")
        st.dataframe(fc.round(2),use_container_width=True,hide_index=True)
        st.download_button("Download forecast CSV",fc.to_csv(index=False).encode(),f"forecast_{selected}.csv","text/csv")

elif page=="Reorder Planner":
    st.markdown("### Purchase planning workspace")
    a,b=st.columns(2)
    with a: cover=st.slider("Target stock coverage (days)",7,120,30)
    with b: safety=st.slider("Safety buffer (days)",0,30,7)
    plan=reorder_recommendations(filtered,cover,safety)
    plan=plan[plan.suggested_order_qty>0]
    total_cost=plan.estimated_order_cost.sum()
    c1,c2,c3=st.columns(3)
    c1.metric("SKUs to replenish",len(plan))
    c2.metric("Estimated purchase spend",fmt_rs(total_cost))
    c3.metric("Units to order",f"{plan.suggested_order_qty.sum():,.0f}")
    st.caption("Formula: max(0, average daily demand × (target coverage + safety buffer + supplier lead time) − on-hand units). Average demand uses the trailing 90 days.")
    st.dataframe(plan[["product_name","supplier","on_hand","avg_daily_demand","lead_time_days","suggested_order_qty","estimated_order_cost","stock_status"]].round(2),use_container_width=True,hide_index=True)
    st.download_button("Download purchase plan CSV",plan.to_csv(index=False).encode(),"purchase_plan.csv","text/csv")

elif page=="Cash Trapped":
    st.markdown("### Cash trapped in inventory")
    st.write("Estimate the cost value of stock that has very low movement or no recorded sales in the supplied history.")
    c1,c2,c3=st.columns(3)
    c1.metric("Potential capital tied up",fmt_rs(trapped))
    c2.metric("Slow / dead SKUs",int(filtered.movement_class.isin(["Slow moving","Very slow","Dead stock"]).sum()))
    c3.metric("Share of inventory cost",f"{(trapped/inventory_value*100 if inventory_value else 0):.1f}%")
    st.markdown('<div class="insight">Calculation: on-hand quantity × unit cost. Included products have average daily demand below 0.75 units, or zero recorded units across the available sales history. This is an estimate of inventory cost value, not cash recoverable or guaranteed savings.</div>',unsafe_allow_html=True)
    breakdown=filtered.groupby("movement_class",as_index=False).agg(products=("product_id","count"),capital=("cash_trapped_value","sum"))
    fig=px.bar(breakdown,x="movement_class",y="capital",color="movement_class",text_auto=".2s",color_discrete_sequence=["#ff7185","#f7b955","#c7f36b","#61d7e8"])
    st.plotly_chart(chart_theme(fig),use_container_width=True)
    st.markdown("#### Product-level capital exposure")
    exposure=filtered[filtered.cash_trapped_value>0].sort_values("cash_trapped_value",ascending=False)
    st.dataframe(exposure[["product_name","category","supplier","on_hand","total_units","avg_daily_demand","inventory_cost_value","movement_class","cash_trapped_value"]].round(2),use_container_width=True,hide_index=True)
    st.download_button("Download exposure CSV",exposure.to_csv(index=False).encode(),"cash_trapped_analysis.csv","text/csv")

elif page=="Product Analytics":
    st.markdown("### Product performance & profitability")
    product=st.selectbox("Inspect product",filtered.product_id.tolist(),format_func=lambda x:filtered.loc[filtered.product_id==x,"product_name"].iloc[0])
    row=filtered[filtered.product_id==product].iloc[0]
    a,b,c,dcol=st.columns(4)
    a.metric("Lifetime units",f"{row.total_units:,.0f}")
    b.metric("Revenue",fmt_rs(row.total_revenue))
    c.metric("Gross profit",fmt_rs(row.gross_profit))
    dcol.metric("Gross margin",f"{row.gross_margin_pct:.1f}%")
    st.markdown("#### Revenue and demand by month")
    tmp=d["sales"][d["sales"].product_id.astype(str)==str(product)].copy()
    tmp["date"]=pd.to_datetime(tmp.date,errors="coerce")
    monthly=tmp.set_index("date").resample("MS").agg(units=("units_sold","sum"),revenue=("revenue","sum") if "revenue" in tmp else ("units_sold","sum")).reset_index()
    fig=px.bar(monthly,x="date",y="units",color_discrete_sequence=["#61d7e8"])
    st.plotly_chart(chart_theme(fig),use_container_width=True)
    st.markdown("#### Product facts")
    st.json({"SKU":row.product_id,"Product":row.product_name,"Supplier":row.supplier,"On hand":int(row.on_hand),"Reorder point":int(row.reorder_point),"Lead time days":int(row.lead_time_days),"Days of cover":None if not np.isfinite(row.days_of_cover) else round(float(row.days_of_cover),1),"Status":row.stock_status})

elif page=="Data Studio":
    st.markdown("### Data studio")
    st.write("Upload replacement datasets. CSV and Excel (.xlsx) are supported. Required columns are validated before the workspace is updated.")
    st.info("Required files: sales (date, product_id, units_sold), products (product_id, product_name, category, supplier, selling_price, unit_cost, reorder_point, lead_time_days), inventory (product_id, on_hand). Supplier data is optional.")
    uploaded={}
    for table in ["sales","products","inventory","suppliers"]:
        up=st.file_uploader(f"Upload {table}.csv or .xlsx",type=["csv","xlsx"],key=f"upload_{table}")
        if up:
            uploaded[table]=pd.read_excel(up) if up.name.lower().endswith(".xlsx") else pd.read_csv(up)
    if st.button("Validate & apply uploaded data",type="primary"):
        candidate={**d,**uploaded}
        check=validate_data(candidate["sales"],candidate["products"],candidate["inventory"])
        if check: st.error(" | ".join(check))
        else:
            for table,frame in uploaded.items():
                st.session_state.datasets[table]=frame
                save_frame(table,frame)
            st.success("Validated successfully. Updated data is now active and saved in SQLite.")
            st.rerun()
    st.markdown("#### Current dataset summary")
    for table,frame in d.items():
        with st.expander(f"{table.title()} · {len(frame):,} rows"):
            st.dataframe(frame.head(100),use_container_width=True,hide_index=True)
    st.caption("Data stays in the local SQLite database on this machine. Uploading new files replaces that table in the current workspace.")

elif page=="Reports":
    st.markdown("### Reports & exports")
    st.write("Generate a PDF snapshot for management review.")
    report=build_pdf_report(filtered,make_insights(filtered))
    st.download_button("⬇ Download inventory intelligence report (PDF)",report,"stocksense_inventory_report.pdf","application/pdf",type="primary")
    st.download_button("Download complete product metrics (CSV)",filtered.to_csv(index=False).encode(),"product_metrics.csv","text/csv")
    st.markdown("#### Methodology & assumptions")
    st.markdown("""
    - **Demand baseline:** trailing 90-day units sold divided by 90 calendar days.
    - **Days of cover:** on-hand stock divided by average daily demand. No recorded demand is displayed as unlimited cover, not as proof of future demand.
    - **Reorder quantity:** demand during target coverage + safety buffer + listed supplier lead time, less on-hand stock, floored at zero.
    - **Cash trapped:** on-hand units × unit cost for SKUs classified as slow, very slow, or dead by historical average movement.
    - **Gross profit estimate:** recorded sales revenue less units sold × current unit cost. Historical cost changes are not modelled.
    - **Forecast:** Random Forest regression with lag and calendar features. Forecasting is disabled when there is insufficient history.
    - **Limitations:** forecasts assume the uploaded sales history is representative. Promotions, returns, stockout-censored demand, supplier disruptions, and price changes are not inferred unless present in the data.
    """)
