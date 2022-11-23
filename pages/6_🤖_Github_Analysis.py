import re
import streamlit as st
import plotly.express as px

from github import Github
import pandas as pd
import CONFIG




@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def get_all_issues_df():
    g = Github()
    repo = g.get_repo("hummingbot/hummingbot")
    open_issues = repo.get_issues(state='open')
    processed_issues = []
    priority_values = ["P1", "P2", "P3"]

    for issue in open_issues:
        priority = None
        bug = False
        labels = [label.name for label in issue.labels]
        for label in labels:
            if label in priority_values:
                priority = label
            if label == "bug":
                bug = True

        processed_issues.append({
            "title": issue.title,
            "number": issue.number,
            "labels": [label for label in labels if label not in priority_values + ["bug"]],
            "created_at": issue.created_at,
            "priority": priority,
            "is_bug": bug,
            "url": issue.html_url
        })

    df = pd.DataFrame(processed_issues)
    return df


st.set_page_config(layout='wide')
st.title("🤖 GitHub Analysis")

with st.spinner(text='In progress'):
    issues_df = get_all_issues_df()

st.write("### Exchanges Filter 🦅")
exchanges_filter = st.multiselect(
    "Select the exchanges to filter:",
    options=CONFIG.CERTIFIED_EXCHANGES,
    default=CONFIG.CERTIFIED_EXCHANGES)
exchanges_issues = issues_df[issues_df['title'].str.contains("|".join(exchanges_filter), regex=True, case=False)]
st.dataframe(exchanges_issues)
issues_by_exchange = {}
for exchange in exchanges_filter:
    issues_by_exchange[exchange] = exchanges_issues.title.str.count(exchange, flags=re.IGNORECASE).sum()
fig = px.bar(pd.Series(issues_by_exchange), orientation='h')

st.plotly_chart(fig)

st.write("### Strategies Filter 🦅")
strategies_filter = st.multiselect(
    "Select the strategies to filter:",
    options=CONFIG.CERTIFIED_STRATEGIES,
    default=CONFIG.CERTIFIED_STRATEGIES)
strategies_issues = issues_df[issues_df['title'].str.contains("|".join(strategies_filter), regex=True, case=False)]
st.dataframe(strategies_issues)
issues_by_strategy = {}
for strategy in strategies_filter:
    issues_by_strategy[strategy] = exchanges_issues.title.str.count(exchange, flags=re.IGNORECASE).sum()
fig = px.bar(pd.Series(issues_by_strategy), orientation='h')

st.plotly_chart(fig)
