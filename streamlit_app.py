import altair as alt
import pandas as pd
import streamlit as st

from src.consts.strategy import StrategyMode
from src.schemas.strategy import StrategyParams
from src.schemas.targeting_report import KeywordPerformance
from src.services import insights_service, targeting_report_service


def _fmt_currency(value: float | None) -> str:
    return "—" if value is None else f"${value:,.2f}"


def _fmt_percent(value: float | None) -> str:
    return "—" if value is None else f"{value:.1%}"


def _fmt_number(value: float | None) -> str:
    return "—" if value is None else f"{value:,.2f}"


def _to_table_row(row: KeywordPerformance) -> dict:
    return {
        "Keyword": row.keyword,
        "Match Type": row.match_type,
        "Bid": _fmt_currency(row.bid),
        "Impressions": row.impressions,
        "Clicks": row.clicks,
        "CTR": _fmt_percent(row.ctr),
        "CPC": _fmt_currency(row.cpc),
        "Cost": _fmt_currency(row.cost),
        "Sales": _fmt_currency(row.sales),
        "Purchases": row.purchases,
        "ACOS": _fmt_percent(row.acos),
    }


KEYWORD_AXIS = alt.Axis(labelLimit=280, title=None)


def _hover_selection() -> alt.Parameter:
    return alt.selection_point(on="pointerover", fields=["Keyword"], empty=False)


def _spend_chart(performances: list[KeywordPerformance]) -> alt.Chart:
    data = pd.DataFrame(
        {"Keyword": row.keyword, "Cost": row.cost, "Sales": row.sales}
        for row in performances
    )
    data = data.sort_values("Cost", ascending=False).head(20)
    data = data.melt("Keyword", var_name="Metric", value_name="Amount")

    hover = _hover_selection()
    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X("Amount:Q", title="Amount ($)"),
            y=alt.Y("Keyword:N", sort="-x", axis=KEYWORD_AXIS),
            color=alt.Color("Metric:N", scale=alt.Scale(range=["#d62728", "#2ca02c"])),
            opacity=alt.condition(hover, alt.value(1.0), alt.value(0.55)),
            tooltip=["Keyword", "Metric", "Amount"],
        )
        .add_params(hover)
        .properties(height=alt.Step(24))
    )


def _acos_chart(performances: list[KeywordPerformance], target_acos: float) -> alt.Chart | None:
    rows = [row for row in performances if row.acos is not None]
    if not rows:
        return None

    data = pd.DataFrame({"Keyword": row.keyword, "ACOS": row.acos} for row in rows)
    data["Status"] = data["ACOS"].apply(
        lambda acos: "Above target" if acos > target_acos else "At or below target"
    )

    hover = _hover_selection()
    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X("ACOS:Q", axis=alt.Axis(format="%")),
            y=alt.Y("Keyword:N", sort="-x", axis=KEYWORD_AXIS),
            color=alt.Color(
                "Status:N",
                scale=alt.Scale(
                    domain=["Above target", "At or below target"],
                    range=["#d62728", "#2ca02c"],
                ),
            ),
            opacity=alt.condition(hover, alt.value(1.0), alt.value(0.55)),
            tooltip=["Keyword", alt.Tooltip("ACOS:Q", format=".1%")],
        )
        .add_params(hover)
        .properties(height=alt.Step(24))
    )


def _ctr_chart(performances: list[KeywordPerformance]) -> alt.Chart | None:
    rows = [row for row in performances if row.impressions > 0 and row.ctr is not None]
    if not rows:
        return None

    data = pd.DataFrame(
        {
            "Keyword": row.keyword,
            "Impressions": row.impressions,
            "CTR": row.ctr,
            "Cost": row.cost,
        }
        for row in rows
    )

    hover = _hover_selection()
    return (
        alt.Chart(data)
        .mark_circle(size=140)
        .encode(
            x=alt.X("Impressions:Q"),
            y=alt.Y("CTR:Q", axis=alt.Axis(format="%")),
            size=alt.Size("Cost:Q", legend=alt.Legend(title="Cost ($)")),
            opacity=alt.condition(hover, alt.value(1.0), alt.value(0.6)),
            tooltip=[
                "Keyword",
                "Impressions",
                alt.Tooltip("CTR:Q", format=".1%"),
                alt.Tooltip("Cost:Q", format="$.2f"),
            ],
        )
        .add_params(hover)
        .properties(height=350)
    )


def _render_insights(insights: list[str]) -> None:
    for insight in insights:
        st.markdown(f"- {insight}")


st.set_page_config(page_title="Amazon Ads Analyzer", layout="wide")

with st.sidebar:
    st.header("Controls")
    target_acos_pct = st.number_input(
        "Target ACOS (%)", min_value=0, max_value=100, value=80, step=1
    )
    strategy_mode_label = st.radio(
        "Strategy mode",
        options=["Growth (build sales velocity)", "Profitability (protect margin)"],
    )
    strategy_mode = (
        StrategyMode.GROWTH
        if strategy_mode_label.startswith("Growth")
        else StrategyMode.PROFITABILITY
    )
    st.divider()
    uploaded_file = st.file_uploader("Upload Amazon Targeting Report (CSV)", type="csv")

st.title("Amazon Ads Analyzer")

strategy = StrategyParams(target_acos=target_acos_pct / 100, mode=strategy_mode)
calendar_insights = insights_service.calendar_insights(strategy)
if calendar_insights:
    with st.container(border=True):
        st.subheader("Upcoming Amazon Events")
        _render_insights(calendar_insights)

if uploaded_file is not None:
    try:
        performances = targeting_report_service.ingest(uploaded_file.getvalue())
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    if not performances:
        st.warning(
            "No keyword rows were found in this file. Double-check it's a Sponsored "
            "Products Targeting report export with at least one enabled keyword."
        )
        st.stop()

    summary = targeting_report_service.summarize(performances)

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Spend", _fmt_currency(summary.total_spend))
        col2.metric("Total Sales", _fmt_currency(summary.total_sales))
        col3.metric("Total Purchases", summary.total_purchases)
        col4.metric("Blended ACOS", _fmt_percent(summary.blended_acos))

    with st.container(border=True):
        st.subheader("Strategic Recommendation")
        _render_insights(insights_service.overall_recommendation(performances, summary, strategy))

    with st.container(border=True):
        st.subheader("Spend vs. Sales by Keyword")
        st.caption("Hover a bar to highlight it and see its exact values.")
        st.altair_chart(_spend_chart(performances), use_container_width=True)
        _render_insights(insights_service.spend_insights(performances, summary, strategy))

    with st.container(border=True):
        st.subheader("ACOS vs. Target ACOS by Keyword")
        acos_chart = _acos_chart(performances, strategy.target_acos)
        if acos_chart is not None:
            st.altair_chart(acos_chart, use_container_width=True)
        else:
            st.caption("No keyword has sales yet, so ACOS isn't defined for any of them.")
        _render_insights(insights_service.acos_insights(performances, summary, strategy))

    with st.container(border=True):
        st.subheader("Impressions vs. CTR by Keyword")
        st.caption(
            "CTR (click-through rate) = clicks ÷ impressions — how often people who saw the "
            "ad actually clicked it."
        )
        ctr_chart = _ctr_chart(performances)
        if ctr_chart is not None:
            st.altair_chart(ctr_chart, use_container_width=True)
        else:
            st.caption("No keyword has impressions yet.")
        _render_insights(insights_service.ctr_insights(performances))

    with st.container(border=True):
        st.subheader("Keyword Performance")
        st.dataframe([_to_table_row(row) for row in performances], use_container_width=True)
else:
    st.info("Upload a Targeting Report CSV to get started.")
