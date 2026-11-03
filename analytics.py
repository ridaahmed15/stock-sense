import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

REQUIRED = {
    "sales": {"date", "product_id", "units_sold"},
    "products": {"product_id", "product_name", "category", "supplier", "selling_price", "unit_cost", "reorder_point", "lead_time_days"},
    "inventory": {"product_id", "on_hand"},
}

def validate_data(sales, products, inventory):
    errors=[]
    for label, frame in [("sales",sales),("products",products),("inventory",inventory)]:
        missing=REQUIRED[label]-set(frame.columns)
        if missing: errors.append(f"{label.title()} file is missing: {', '.join(sorted(missing))}")
    if errors: return errors
    if sales.empty or products.empty or inventory.empty: errors.append("Sales, products, and inventory datasets must not be empty.")
    if not errors:
        if (pd.to_numeric(sales.units_sold,errors="coerce").fillna(-1)<0).any(): errors.append("units_sold must be zero or greater.")
        if (pd.to_numeric(inventory.on_hand,errors="coerce").fillna(-1)<0).any(): errors.append("on_hand must be zero or greater.")
        if products.product_id.duplicated().any(): errors.append("products.product_id must be unique.")
    return errors

def clean_inputs(sales, products, inventory):
    s=sales.copy(); p=products.copy(); i=inventory.copy()
    s["date"]=pd.to_datetime(s["date"],errors="coerce")
    s["units_sold"]=pd.to_numeric(s["units_sold"],errors="coerce")
    s=s.dropna(subset=["date","product_id","units_sold"])
    p["selling_price"]=pd.to_numeric(p["selling_price"],errors="coerce").fillna(0)
    p["unit_cost"]=pd.to_numeric(p["unit_cost"],errors="coerce").fillna(0)
    p["reorder_point"]=pd.to_numeric(p["reorder_point"],errors="coerce").fillna(0)
    p["lead_time_days"]=pd.to_numeric(p["lead_time_days"],errors="coerce").fillna(14)
    i["on_hand"]=pd.to_numeric(i["on_hand"],errors="coerce").fillna(0)
    return s,p,i

def build_product_metrics(sales, products, inventory, suppliers=None):
    s,p,i=clean_inputs(sales,products,inventory)
    today=s.date.max().normalize()
    last30=s[s.date>today-pd.Timedelta(days=30)].groupby("product_id").units_sold.sum()
    prev30=s[(s.date<=today-pd.Timedelta(days=30))&(s.date>today-pd.Timedelta(days=60))].groupby("product_id").units_sold.sum()
    last90=s[s.date>today-pd.Timedelta(days=90)].groupby("product_id").units_sold.sum()
    alltime=s.groupby("product_id").agg(total_units=("units_sold","sum"),total_revenue=("units_sold",lambda x: 0)).drop(columns=["total_revenue"],errors="ignore")
    rev=s.groupby("product_id").agg(total_units=("units_sold","sum"), total_revenue=("revenue","sum") if "revenue" in s.columns else ("units_sold","sum"))
    m=p.merge(i,on="product_id",how="left").merge(rev,on="product_id",how="left")
    m["on_hand"]=m.on_hand.fillna(0)
    m["total_units"]=m.total_units.fillna(0)
    m["total_revenue"]=m.total_revenue.fillna(0)
    m["units_30d"]=m.product_id.map(last30).fillna(0)
    m["units_prev30d"]=m.product_id.map(prev30).fillna(0)
    m["units_90d"]=m.product_id.map(last90).fillna(0)
    m["avg_daily_demand"]=m.units_90d/90
    m["days_of_cover"]=np.where(m.avg_daily_demand>0,m.on_hand/m.avg_daily_demand,np.inf)
    m["gross_profit"]=m.total_revenue-(m.total_units*m.unit_cost)
    m["gross_margin_pct"]=np.where(m.total_revenue>0,m.gross_profit/m.total_revenue*100,0)
    m["inventory_cost_value"]=m.on_hand*m.unit_cost
    m["stock_status"]=np.where(m.on_hand<=m.reorder_point,"Reorder now",np.where(m.days_of_cover<=m.lead_time_days,"At risk","Healthy"))
    m["sales_change_pct"]=np.where(m.units_prev30d>0,(m.units_30d-m.units_prev30d)/m.units_prev30d*100,np.nan)
    if suppliers is not None and not suppliers.empty:
        m=m.merge(suppliers[["supplier","avg_lead_time_days","on_time_rate"]],on="supplier",how="left")
    return m

def forecast_product(sales, product_id, horizon=30):
    s=sales.copy()
    s["date"]=pd.to_datetime(s["date"],errors="coerce")
    daily=s[s.product_id.astype(str)==str(product_id)].groupby("date").units_sold.sum().asfreq("D",fill_value=0)
    if len(daily)<21:
        return None, "Not enough history: at least 21 dated observations are required."
    y=daily.values.astype(float)
    # Lag and calendar features; chronological holdout for a basic quality check
    frame=pd.DataFrame({"y":y})
    for lag in [1,7,14]:
        frame[f"lag_{lag}"]=frame.y.shift(lag)
    frame["dow"]=daily.index.dayofweek
    frame["month"]=daily.index.month
    frame=frame.dropna()
    if len(frame)<15:
        return None, "Not enough usable history to train a forecast model."
    X=frame.drop(columns="y"); target=frame.y
    split=max(10,int(len(frame)*0.8))
    model=RandomForestRegressor(n_estimators=160,max_depth=6,min_samples_leaf=2,random_state=42)
    model.fit(X.iloc[:split],target.iloc[:split])
    validation=model.predict(X.iloc[split:]) if split<len(frame) else np.array([])
    mae=float(mean_absolute_error(target.iloc[split:],validation)) if len(validation) else None
    # Refit on all observations, recursively predict future days
    model.fit(X,target)
    history=list(y)
    future=[]
    last_date=daily.index.max()
    for step in range(1,horizon+1):
        date=last_date+pd.Timedelta(days=step)
        row=pd.DataFrame([{
            "lag_1":history[-1],
            "lag_7":history[-7] if len(history)>=7 else np.mean(history),
            "lag_14":history[-14] if len(history)>=14 else np.mean(history),
            "dow":date.dayofweek,"month":date.month
        }])
        pred=max(0,float(model.predict(row)[0]))
        future.append((date,pred)); history.append(pred)
    result=pd.DataFrame(future,columns=["date","forecast_units"])
    result["lower_bound"]=np.maximum(0,result.forecast_units-(mae or 0)*1.28)
    result["upper_bound"]=result.forecast_units+(mae or 0)*1.28
    return {"history":daily.reset_index().rename(columns={"index":"date","units_sold":"actual_units"}),
            "forecast":result,"mae":mae,"model":"Random Forest regression with 1/7/14-day lags and calendar features"}, None

def reorder_recommendations(metrics, cover_days=30, safety_days=7):
    m=metrics.copy()
    target=m.avg_daily_demand*(cover_days+safety_days+m.lead_time_days)
    m["suggested_order_qty"]=np.maximum(0,np.ceil(target-m.on_hand)).astype(int)
    m["estimated_order_cost"]=m.suggested_order_qty*m.unit_cost
    return m.sort_values(["suggested_order_qty","avg_daily_demand"],ascending=False)

def slow_stock(metrics, slow_days=60):
    m=metrics.copy()
    # Slow: positive stock but <= 1 unit/day average; dead: no sales in supplied history.
    m["movement_class"]=np.select(
        [m.total_units<=0,(m.avg_daily_demand<0.15)&(m.on_hand>0),(m.avg_daily_demand<0.75)&(m.on_hand>0)],
        ["Dead stock","Very slow","Slow moving"],default="Active")
    m["cash_trapped_value"]=np.where(m.movement_class.isin(["Dead stock","Very slow","Slow moving"]),m.inventory_cost_value,0)
    return m

def make_insights(metrics, forecast=None):
    insights=[]
    trapped=metrics.cash_trapped_value.sum() if "cash_trapped_value" in metrics else 0
    if trapped>0:
        insights.append(f"Rs. {trapped:,.0f} is potentially tied up in slow-moving or dead inventory. Review these SKUs before placing new orders.")
    reorder=metrics[metrics.stock_status=="Reorder now"]
    if len(reorder):
        insights.append(f"{len(reorder)} products are at or below their reorder points. Prioritise items with the shortest days of cover.")
    at_risk=metrics[metrics.stock_status=="At risk"]
    if len(at_risk):
        insights.append(f"{len(at_risk)} products may run out before replenishment based on current 90-day average demand and listed lead time.")
    low_margin=metrics[(metrics.total_revenue>0)&(metrics.gross_margin_pct<20)]
    if len(low_margin):
        insights.append(f"{len(low_margin)} products have gross margin below 20%. Review supplier cost, pricing, or discounting.")
    if not insights: insights.append("No critical inventory signals were detected from the supplied data. Continue monitoring demand and supplier lead times.")
    return insights
