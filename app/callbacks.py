"""
Dash callbacks: wire dropdowns → all panels + PDF export.
"""

import io
import pandas as pd
from dash import Input, Output, callback, dcc
from dash.exceptions import PreventUpdate

# analytics
from analytics.pnl_decomposition import daily_book_pnl
from analytics.hedge_efficiency   import compute_hedge_efficiency
from analytics.basis_analysis     import basis_alerts

# components
from app.components.kpi_cards    import build_kpi_row
from app.components.pnl_charts   import actual_vs_explained, hedged_vs_unhedged
from app.components.basis_charts import basis_time_series, sector_hedge_ratio_chart
from app.components.alerts_panel import build_alerts, alerts_table
from app.components.hedge_tables import hedge_summary_table


def register_callbacks(app, data: dict):
    pnl_df   = data["pnl"]
    hedge_df = data["hedge"]
    basis_df = data["basis"]

    @app.callback(
        Output("kpi-row",     "children"),
        Output("pnl-chart",   "figure"),
        Output("hedge-chart", "figure"),
        Output("basis-chart", "figure"),
        Output("sector-chart","figure"),
        Output("alerts-table","children"),
        Input("date-dropdown","value"),
        Input("book-dropdown","value"),
    )
    def update_all(selected_date, selected_book):
        if not selected_date or not selected_book:
            raise PreventUpdate

        dt = pd.Timestamp(selected_date)

        # --- P&L aggregation ---
        daily = daily_book_pnl(pnl_df, book_id=selected_book)

        # --- Hedge efficiency ---
        eff_df = compute_hedge_efficiency(
            pnl_df[pnl_df["book_id"] == selected_book], hedge_df
        )

        # Merge efficiency back into daily for KPI row
        daily = daily.merge(
            eff_df[["date","hedge_efficiency","net_cs01","hedge_ratio"]],
            on="date", how="left"
        )

        # Latest row for KPIs
        latest_row = daily[daily["date"] == dt]
        hedge_row  = None
        if not latest_row.empty:
            latest_row  = latest_row.iloc[0]
            hedge_row   = latest_row

        kpi = build_kpi_row(latest_row if not isinstance(latest_row, pd.DataFrame) else pd.Series(),
                            hedge_row)

        pnl_fig    = actual_vs_explained(daily)
        hedge_fig  = hedged_vs_unhedged(eff_df)
        basis_fig  = basis_time_series(basis_df)
        sector_fig = sector_hedge_ratio_chart(hedge_df, pnl_df)

        alert_df   = build_alerts(daily, eff_df, basis_df, dt)
        alerts     = alerts_table(alert_df)

        return kpi, pnl_fig, hedge_fig, basis_fig, sector_fig, alerts

    @app.callback(
        Output("pdf-download","data"),
        Input("export-btn","n_clicks"),
        Input("date-dropdown","value"),
        Input("book-dropdown","value"),
        prevent_initial_call=True,
    )
    def export_pdf(n_clicks, selected_date, selected_book):
        if not n_clicks or not selected_date:
            raise PreventUpdate

        dt = pd.Timestamp(selected_date)
        daily  = daily_book_pnl(pnl_df, book_id=selected_book)
        eff_df = compute_hedge_efficiency(
            pnl_df[pnl_df["book_id"] == selected_book], hedge_df
        )
        daily  = daily.merge(
            eff_df[["date","hedge_efficiency","net_cs01","hedge_ratio"]],
            on="date", how="left"
        )

        from analytics.pnl_decomposition import top_movers, LABEL_MAP, COMPONENTS
        from analytics.basis_analysis import basis_summary

        latest = daily[daily["date"] == dt].iloc[0] if not daily[daily["date"] == dt].empty else None
        movers = top_movers(pnl_df, dt)
        b_sum  = basis_summary(basis_df, dt)
        alert_df = build_alerts(daily, eff_df, basis_df, dt)

        pdf_bytes = _build_pdf(dt, latest, daily, eff_df, movers, b_sum, alert_df,
                               hedge_df, selected_book)
        return dcc.send_bytes(pdf_bytes, f"credit_risk_{selected_date}.pdf")


def _build_pdf(dt, latest, daily, eff_df, movers, b_sum, alert_df, hedge_df, book_id):
    """Build a 4-section PDF using reportlab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.65*inch, rightMargin=0.65*inch,
                            topMargin=0.65*inch, bottomMargin=0.65*inch)
    styles = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=14,
                         textColor=colors.HexColor("#0078D4"), spaceAfter=4)
    H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=11,
                         textColor=colors.HexColor("#1F2937"), spaceAfter=3)
    BODY = styles["Normal"]
    BODY.fontSize = 9

    def section(title):
        return [Paragraph(title, H1),
                HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E5E7EB")),
                Spacer(1, 6)]

    def kv_table(rows):
        data = [[k, v] for k, v in rows]
        t = Table(data, colWidths=[2.5*inch, 4*inch])
        t.setStyle(TableStyle([
            ("FONTSIZE",    (0,0), (-1,-1), 9),
            ("TEXTCOLOR",   (0,0), (0,-1), colors.HexColor("#6B7280")),
            ("FONTNAME",    (0,0), (0,-1), "Helvetica-Bold"),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, colors.HexColor("#F9FAFB")]),
            ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
            ("PADDING",     (0,0), (-1,-1), 5),
        ]))
        return t

    story = []
    # Title
    story.append(Paragraph(
        f"Credit Risk Daily Report — {book_id} — {dt.strftime('%d %b %Y')}", H1))
    story.append(Spacer(1, 12))

    # ── Section A: Headline ──
    story += section("A  Headline")
    if latest is not None:
        act  = latest.get("actual_pnl", 0)
        expl = latest.get("explained_pct", 0)
        res  = latest.get("residual_pct", 0)
        eff  = latest.get("hedge_efficiency", 0) or 0
        ncs  = latest.get("net_cs01", 0) or 0

        story.append(kv_table([
            ("Actual P&L",       f"${act:,.0f}"),
            ("Explained %",      f"{expl*100:.1f}%"),
            ("Residual %",       f"{res*100:.1f}%"),
            ("Hedge Efficiency", f"{eff*100:.1f}%"),
            ("Net CS01",         f"${ncs:,.0f}"),
        ]))
        story.append(Spacer(1, 8))

    if not movers.empty:
        story.append(Paragraph("Top 3 Movers", H2))
        mv_data = [["Issuer","Sector","Actual P&L","Spread P&L","Event P&L"]]
        for _, r in movers.iterrows():
            mv_data.append([r["issuer"], r["sector"],
                            f"${r['actual_pnl']:,.0f}", f"${r['spread_pnl']:,.0f}",
                            f"${r['event_pnl']:,.0f}"])
        t = Table(mv_data, colWidths=[1.8*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0078D4")),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 9),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#F9FAFB")]),
            ("PADDING",    (0,0), (-1,-1), 5),
        ]))
        story.append(t)
    story.append(Spacer(1, 12))

    # ── Section B: Driver Breakdown ──
    story += section("B  P&L Driver Breakdown")
    from analytics.pnl_decomposition import LABEL_MAP, COMPONENTS
    if latest is not None:
        driver_rows = [(LABEL_MAP[c], f"${latest.get(c,0):,.0f}") for c in COMPONENTS]
        driver_rows.append(("── Total Actual", f"${latest.get('actual_pnl',0):,.0f}"))
        story.append(kv_table(driver_rows))
    story.append(Spacer(1, 12))

    # ── Section C: Hedge Review ──
    story += section("C  Hedge Review")
    h_row = hedge_df[hedge_df["date"] == dt]
    if not h_row.empty:
        hr = h_row.iloc[0]
        story.append(kv_table([
            ("Hedge Instrument", hr["instrument"]),
            ("Notional ($mm)",   f"{hr['notional_mm']:.1f}"),
            ("Gross CS01",       f"${hr['gross_cs01']:,.0f}"),
            ("Hedge CS01",       f"${hr['hedge_cs01']:,.0f}"),
            ("Net CS01",         f"${hr['net_cs01']:,.0f}"),
            ("Hedge Ratio",      f"{hr['hedge_ratio']*100:.1f}%"),
            ("Effective Beta",   f"{hr['effective_beta']:.3f}"),
        ]))
    if not b_sum.empty:
        story.append(Spacer(1, 8))
        story.append(Paragraph("Bond–CDS Basis by Issuer", H2))
        bs_data = [["Issuer","Sector","Bond Spd","CDS Spd","Basis","Status"]]
        for _, r in b_sum.iterrows():
            bs_data.append([r["issuer"], r["sector"],
                            f"{r['bond_spread_bps']:.0f}",
                            f"{r['cds_spread_bps']:.0f}",
                            f"{r['basis_bps']:.0f}", r["status"]])
        t = Table(bs_data, colWidths=[1.7*inch, 1.2*inch, 0.8*inch, 0.8*inch, 0.7*inch, 0.7*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0078D4")),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 8),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#F9FAFB")]),
            ("PADDING",    (0,0), (-1,-1), 4),
        ]))
        story.append(t)
    story.append(Spacer(1, 12))

    # ── Section D: Exceptions ──
    story += section("D  Exceptions")
    if alert_df.empty:
        story.append(Paragraph("No open exceptions.", BODY))
    else:
        exc_data = [list(alert_df.columns)] + alert_df.values.tolist()
        col_w = [0.8*inch, 1.6*inch, 3.4*inch, 0.8*inch]
        t = Table(exc_data, colWidths=col_w)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0078D4")),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 8),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
            ("WORDWRAP",   (0,0), (-1,-1), True),
            ("PADDING",    (0,0), (-1,-1), 4),
        ]))
        story.append(t)

    doc.build(story)
    return buf.getvalue()
