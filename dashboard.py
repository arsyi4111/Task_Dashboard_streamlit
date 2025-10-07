from metrics import get_metrics, load_performance_data
import streamlit as st

def performance_dashboard:
    # ==============================
    # LOAD DATA
    # ==============================
    df = load_performance_data()

    # --- Define Penyaluran Dana categories ---
    penyaluran_cats = [
        "17. PENYALURAN DANA NASIONAL",
        "18. PENYALURAN DANA DAERAH",
        "19. PENYALURAN DANA KORPORASI"
    ]

    df_excl = df[~df["Categori Produk"].isin(penyaluran_cats)].copy()
    df_incl = df.copy()  # keep version with Penyaluran Dana

    # ==============================
    # FILTER BAR
    # ==============================
    st.markdown("### 🔍 Summary Filter")

    sorted_products = sorted(
        df_excl["Categori Produk"].unique(),
        key=lambda x: int(x.split(".")[0]) if x.split(".")[0].isdigit() else 999
    )

    selected_products = st.multiselect(
        label="Select Categories",
        options=sorted_products,
        default=sorted_products,
        placeholder="Select categories...",
    )

    if selected_products:
        df_excl = df_excl[df_excl["Categori Produk"].isin(selected_products)]
        df_incl = df_incl[df_incl["Categori Produk"].isin(selected_products + penyaluran_cats)]

    # ==============================
    # METRICS & COUNTDOWN
    # ==============================
    metrics_excl = get_metrics(df_excl)
    metrics_incl = get_metrics(df_incl)

    today = datetime.date.today()
    end_of_month = (
        datetime.date(today.year, today.month + 1, 1) - datetime.timedelta(days=1)
        if today.month < 12 else datetime.date(today.year, 12, 31)
    )
    end_of_year = datetime.date(today.year, 12, 31)

    total_days_month = (end_of_month - datetime.date(today.year, today.month, 1)).days + 1
    total_days_year = (end_of_year - datetime.date(today.year, 1, 1)).days + 1

    days_to_eom = (end_of_month - today).days
    days_to_eoy = (end_of_year - today).days

    total_workdays_month = np.busday_count(
        datetime.date(today.year, today.month, 1).strftime("%Y-%m-%d"),
        (end_of_month + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    )
    total_workdays_year = np.busday_count(
        datetime.date(today.year, 1, 1).strftime("%Y-%m-%d"),
        (end_of_year + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    )

    workdays_to_eom = np.busday_count(
        today.strftime("%Y-%m-%d"),
        (end_of_month + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    )
    workdays_to_eoy = np.busday_count(
        today.strftime("%Y-%m-%d"),
        (end_of_year + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
            <div class='metric-box'>
                <h3>Days to End of Month</h3>
                <p>{days_to_eom}/{total_days_month}<br>
                <span style="font-size:0.9em; color:gray;">Work days: {workdays_to_eom}/{total_workdays_month}</span></p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class='metric-box'>
                <h4>📅 Monthly Performance</h4>
                <p><b>last update: 18 September 2025</b></p>
                <p><b>Total:</b> {metrics_excl['mtd_total']:,.0f}</p>
                <p><b>Target:</b> {metrics_excl['mtd_target']:,.0f}</p>
                <p><b>Ach:</b> {metrics_excl['mtd_ach']:.1f}%</p>
                <hr>
                <p><b>Total (include Penyaluran Dana):</b> {metrics_incl['mtd_total']:,.0f}</p>
                <p><b>Target:</b> {metrics_incl['mtd_target']:,.0f}</p>
                <p><b>Ach:</b> {metrics_incl['mtd_ach']:.1f}%</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class='metric-box'>
                <h3>Days to End of Year</h3>
                <p>{days_to_eoy}/{total_days_year}<br>
                <span style="font-size:0.9em; color:gray;">Work days: {workdays_to_eoy}/{total_workdays_year}</span></p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class='metric-box'>
                <h4>📊 FY Performance</h4>
                <p><b>last update: 18 September 2025</b></p>
                <p><b>Total:</b> {metrics_excl['ytd_total']:,.0f}</p>
                <p><b>Target:</b> {metrics_excl['ytd_target']:,.0f}</p>
                <p><b>Ach:</b> {metrics_excl['ytd_ach']:.1f}%</p>
                <hr>
                <p><b>Total (include Penyaluran Dana):</b> {metrics_incl['ytd_total']:,.0f}</p>
                <p><b>Target:</b> {metrics_incl['ytd_target']:,.0f}</p>
                <p><b>Ach:</b> {metrics_incl['ytd_ach']:.1f}%</p>
            </div>
        """, unsafe_allow_html=True)

    # ==============================
    # TIMELINE: 2024 + 2025 Forecast
    # ==============================
    st.subheader("📊 Revenue Timeline: 2024 + 2025 (with Forecast, Stable Seasonality, without Penyaluran Dana)")

    monthly_agg = df_excl.groupby("bulan").agg({
        "Kinerja 2024": "sum",
        "Kinerja 2025": "sum",
        "Target Tahun Ini": "sum"
    }).reset_index()

    month_map = {
        1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
        7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"
    }
    monthly_agg["bulan_name"] = monthly_agg["bulan"].map(month_map)

    df_2024 = monthly_agg[["bulan","bulan_name","Kinerja 2024"]].copy()
    df_2024["year"] = 2024
    df_2024.rename(columns={"Kinerja 2024":"Kinerja"}, inplace=True)

    df_2025 = monthly_agg[["bulan","bulan_name","Kinerja 2025","Target Tahun Ini"]].copy()
    df_2025["year"] = 2025
    df_2025.rename(columns={"Kinerja 2025":"Kinerja","Target Tahun Ini":"Target"}, inplace=True)

    timeline_excl = pd.concat([df_2024, df_2025], ignore_index=True)
    timeline_excl["t"] = (timeline_excl["year"] - 2024) * 12 + timeline_excl["bulan"]
    timeline_excl["label"] = timeline_excl["bulan_name"] + " " + timeline_excl["year"].astype(str)

    # --- Train OLS on 2024 + Jan–Aug 2025 ---
    train = timeline_excl[(timeline_excl["year"]==2024) | ((timeline_excl["year"]==2025)&(timeline_excl["bulan"]<=8))].copy()
    month_dummies = pd.get_dummies(train["bulan"], prefix="m", drop_first=True)

    X = pd.concat([train[["t"]].astype(float), month_dummies.astype(float)], axis=1)
    y = train["Kinerja"].astype(float)

    model = sm.OLS(y, sm.add_constant(X)).fit()

    future_months = np.arange(9,13)
    future_t = ((2025-2024)*12 + future_months)
    future_dummies = pd.get_dummies(future_months, prefix="m", drop_first=True)
    future_dummies = future_dummies.reindex(columns=month_dummies.columns, fill_value=0).astype(float)

    X_future = pd.concat([pd.DataFrame({"t":future_t}, dtype=float), future_dummies], axis=1)
    forecast_values = model.predict(sm.add_constant(X_future))

    forecast_df = pd.DataFrame({
        "year":2025,"bulan":future_months,"bulan_name":[month_map[m] for m in future_months],
        "t":future_t,"Forecast":forecast_values
    })
    forecast_df["label"] = forecast_df["bulan_name"] + " 2025"

    timeline_excl = timeline_excl.merge(forecast_df[["t","Forecast"]], on="t", how="left")

    # ==============================
    # PLOT
    # ==============================
    plot_data = timeline_excl.melt(
        id_vars=["label"], value_vars=["Kinerja","Target","Forecast"],
        var_name="Kategori", value_name="Nilai"
    )
    fig = px.bar(
        plot_data, x="label", y="Nilai", color="Kategori",
        barmode="group", text_auto=".2s"
    )
    fig.update_yaxes(title="Revenue (in Millions)", tickformat=".2s")
    fig.update_xaxes(title="Month", tickangle=-45)
    fig.update_layout(
        title="Revenue Timeline: 2024 + 2025 (with Forecast, Stable Seasonality)",
        legend_title="Kategori", bargap=0.2
    )
    fig.add_traces(go.Scatter(
        x=train["label"], y=model.predict(sm.add_constant(X)),
        mode="lines", name="Trend + Seasonality Fit",
        line=dict(color="black", dash="dash")
    ))
    st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # SUMMARY (Projected)
    # ==============================
    monthly_summary_excl = (
        timeline_excl[timeline_excl["year"]==2025]
        .groupby("bulan").agg({"Kinerja":"sum","Target":"sum","Forecast":"sum"}).reset_index()
    )

    real_until_aug_excl = monthly_summary_excl.loc[monthly_summary_excl["bulan"]<=8,"Kinerja"].sum()
    forecast_sept_dec_excl = monthly_summary_excl.loc[monthly_summary_excl["bulan"]>=9,"Forecast"].sum()
    total_proj_excl = real_until_aug_excl + forecast_sept_dec_excl
    target_excl = monthly_summary_excl["Target"].sum()
    ach_excl = (total_proj_excl/target_excl*100) if target_excl>0 else 0

    # --- INCLUDE (manual PD adjustment) ---
    pd_realized_until_aug = df[df["Categori Produk"].isin(penyaluran_cats)]
    pd_realized_until_aug = pd_realized_until_aug[pd_realized_until_aug["bulan"]<=8]["Kinerja 2025"].sum()

    pd_forecast_manual = 38670
    total_proj_incl = total_proj_excl + pd_realized_until_aug + pd_forecast_manual
    target_incl = target_excl + df[df["Categori Produk"].isin(penyaluran_cats)]["Target Tahun Ini"].sum()
    ach_incl = (total_proj_incl/target_incl*100) if target_incl>0 else 0

    # --- DISPLAY ---
    st.markdown(f"""
        <div style="background-color:#1c2d5a;padding:15px;border-radius:10px;
        color:white;font-size:20px;font-weight:bold;text-align:center;margin-top:20px;">
            So the projection until the end of the year is:<br>
            📈 Projected Revenue (2025): {total_proj_excl:,.0f}<br>
            🎯 Projected Achievement (2025): {ach_excl:.1f}%<br><br>
            with projected Penyaluran Dana revenue in Sept - Dec of {pd_forecast_manual:,.0f} M, so that:<br>
            📈 Projected Revenue include Penyaluran Dana (2025): {total_proj_incl:,.0f}<br>
            🎯 Projected Achievement include Penyaluran Dana (2025): {ach_incl:.1f}%
        </div>
    """, unsafe_allow_html=True)