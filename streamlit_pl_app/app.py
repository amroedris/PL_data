import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Premier League Dashboard", layout="wide")

# Title
st.title("Premier League Data Analysis")

# File uploader
uploaded_file = st.file_uploader("Upload the England CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Clean column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    df['date'] = pd.to_datetime(df['date'], dayfirst=True)

    # Section 1: Red/Yellow Cards by Referee
    st.header("🔴 Referee Discipline Stats (50+ Matches)")
    card_data = df.dropna(subset=['referee', 'h_yellow', 'a_yellow', 'h_red', 'a_red']).copy()
    card_data['total_yellow'] = card_data['h_yellow'] + card_data['a_yellow']
    card_data['total_red'] = card_data['h_red'] + card_data['a_red']
    eligible_refs = card_data['referee'].value_counts()[lambda x: x >= 50].index
    filtered_data = card_data[card_data['referee'].isin(eligible_refs)]

    referee_cards = (
        filtered_data.groupby('referee')[['total_yellow', 'total_red']]
        .mean().reset_index().sort_values(by='total_yellow', ascending=False)
    )

    st.plotly_chart(px.bar(referee_cards, x='referee', y='total_yellow',
                           title='Average Yellow Cards (50+ Matches)',
                           labels={'total_yellow': 'Avg Yellow Cards'},
                           color='total_yellow'))

    st.plotly_chart(px.bar(referee_cards.sort_values(by='total_red', ascending=False),
                           x='referee', y='total_red',
                           title='Average Red Cards (50+ Matches)',
                           labels={'total_red': 'Avg Red Cards'},
                           color='total_red'))

    # Section 2: Correlation - Shots vs Goals
    st.header("📊 Correlation Between Shots and Goals")
    shot_data = df.dropna(subset=['h_shots', 'fth_goals', 'a_shots', 'fta_goals']).copy()
    shot_data['total_goals'] = shot_data['fth_goals'] + shot_data['fta_goals']
    shot_data['total_shots'] = shot_data['h_shots'] + shot_data['a_shots']

    home_corr = shot_data['h_shots'].corr(shot_data['fth_goals'])
    away_corr = shot_data['a_shots'].corr(shot_data['fta_goals'])
    total_corr = shot_data['total_shots'].corr(shot_data['total_goals'])

    st.write(f"📈 Home Shots vs Goals Correlation: `{home_corr:.2f}`")
    st.write(f"📈 Away Shots vs Goals Correlation: `{away_corr:.2f}`")
    st.write(f"📈 Overall Shots vs Goals Correlation: `{total_corr:.2f}`")

    st.plotly_chart(px.scatter(shot_data, x='h_shots', y='fth_goals', title='Home Shots vs Home Goals', trendline='ols'))
    st.plotly_chart(px.scatter(shot_data, x='a_shots', y='fta_goals', title='Away Shots vs Away Goals', trendline='ols'))
    st.plotly_chart(px.scatter(shot_data, x='total_shots', y='total_goals', title='Total Shots vs Total Goals', trendline='ols'))

    # Section 3: Arsenal Fouls
    st.header("⚠️ Arsenal: Fouls Committed vs Suffered")
    arsenal = df[(df['hometeam'] == 'Arsenal') | (df['awayteam'] == 'Arsenal')].copy()
    arsenal['fouls_committed'] = arsenal.apply(lambda r: r['h_fouls'] if r['hometeam'] == 'Arsenal' else r['a_fouls'], axis=1)
    arsenal['fouls_suffered'] = arsenal.apply(lambda r: r['a_fouls'] if r['hometeam'] == 'Arsenal' else r['h_fouls'], axis=1)

    fouls_df = pd.DataFrame({
        'Type': ['Fouls Committed', 'Fouls Suffered'],
        'Average': [arsenal['fouls_committed'].mean(), arsenal['fouls_suffered'].mean()]
    })
    st.plotly_chart(px.bar(fouls_df, x='Type', y='Average', color='Type', title="Arsenal: Average Fouls"))

    # Section 4: Referee Bias - David Coote
    st.header("👨‍⚖️ David Coote: Liverpool Bias?")
    coote = df[df['referee'] == 'D Coote'].copy()
    coote_liv = coote[(coote['hometeam'] == 'Liverpool') | (coote['awayteam'] == 'Liverpool')].copy()
    coote_others = coote[~((coote['hometeam'] == 'Liverpool') | (coote['awayteam'] == 'Liverpool'))].copy()

    coote_liv['liv_yellow'] = coote_liv.apply(lambda r: r['h_yellow'] if r['hometeam'] == 'Liverpool' else r['a_yellow'], axis=1)
    coote_liv['opp_yellow'] = coote_liv.apply(lambda r: r['a_yellow'] if r['hometeam'] == 'Liverpool' else r['h_yellow'], axis=1)
    coote_liv['liv_fouls'] = coote_liv.apply(lambda r: r['h_fouls'] if r['hometeam'] == 'Liverpool' else r['a_fouls'], axis=1)
    coote_liv['opp_fouls'] = coote_liv.apply(lambda r: r['a_fouls'] if r['hometeam'] == 'Liverpool' else r['h_fouls'], axis=1)

    comparison_df = pd.DataFrame({
        'Metric': ['Yellows on Liverpool', 'Yellows on Opponent', 'Avg Yellows (Others)',
                   'Fouls by Liverpool', 'Fouls by Opponent', 'Avg Fouls (Others)'],
        'Average': [
            coote_liv['liv_yellow'].mean(),
            coote_liv['opp_yellow'].mean(),
            (coote_others['h_yellow'].mean() + coote_others['a_yellow'].mean()) / 2,
            coote_liv['liv_fouls'].mean(),
            coote_liv['opp_fouls'].mean(),
            (coote_others['h_fouls'].mean() + coote_others['a_fouls'].mean()) / 2
        ]
    })
    st.plotly_chart(px.bar(comparison_df, x='Metric', y='Average', color='Metric',
                           title="David Coote - Liverpool vs Other Teams"))

    # Section 5: Arsenal vs Big 6
    st.header("⚔️ Arsenal vs Big Six Win Rate")
    big_six = ['Chelsea', 'Liverpool', 'Manchester City', 'Manchester United', 'Tottenham Hotspur']
    arsenal_big6 = df[((df['hometeam'] == 'Arsenal') & (df['awayteam'].isin(big_six))) |
                      ((df['awayteam'] == 'Arsenal') & (df['hometeam'].isin(big_six)))].copy()

    def get_result(row):
        if row['hometeam'] == 'Arsenal':
            return 'Win' if row['ft_result'] == 'H' else 'Loss' if row['ft_result'] == 'A' else 'Draw'
        else:
            return 'Win' if row['ft_result'] == 'A' else 'Loss' if row['ft_result'] == 'H' else 'Draw'

    arsenal_big6['arsenal_result'] = arsenal_big6.apply(get_result, axis=1)
    st.write(f"Total Matches vs Big 6: {len(arsenal_big6)}")
    st.write(arsenal_big6['arsenal_result'].value_counts())

    pie_data = arsenal_big6['arsenal_result'].value_counts().reset_index()
    pie_data.columns = ['Result', 'Count']
    st.plotly_chart(px.pie(pie_data, names='Result', values='Count', title="Arsenal vs Big Six"))

else:
    st.info("👆 Upload your CSV file to begin.")
