from f1_analyzer_2 import F1Analysis as f1
import pandas as pd
import streamlit as st

# streamlit run app.py

def df_format(df, x):
    x.dataframe(
            df, 
            hide_index=True, height='content', width='stretch',
            column_config={col: st.column_config.Column(alignment='center') for col in df.columns},
        )
    
def get_tracks(year):
    df = pd.read_csv('./events/finished.csv')
    return df[df['Year'] == year]['EventName'].to_list()

def get_sessions(year, track):
    df = pd.read_csv('./events/finished.csv')
    df = df[df['Year'] == year]
    df = df[df['EventName'] == track].reset_index(drop=True)
    df_list = []
    for x in list(range(1,6)):
        session = str(df[f'Session{x}'].item())
        if session in ['Race', 'Sprint', 'Qualifying', 'Sprint Qualifying']:
            df_list.append(session)
    return df_list

def df_format(df, x):
    x.dataframe(
            df, 
            hide_index=True, height='content', width='stretch',
            column_config={col: st.column_config.Column(alignment='center') for col in df.columns},
        )

st.set_page_config(layout="wide")

if 'race' not in st.session_state:
    st.session_state['race'] = f1(2026, 'Australian Grand Prix', 'Race')
    year = 2026
    track = 'Australian Grand Prix'
    session = 'Race'

year = st.sidebar.slider('Year', 2019, 2026)
track = st.sidebar.selectbox('Track', get_tracks(year))
session = st.sidebar.selectbox('Session', get_sessions(year,track))

done = st.sidebar.button('Done')

if done:
    st.session_state['race'] = f1(year, track, session)

if 'race' in st.session_state:
    race = st.session_state['race']
    year = race.year
    track = race.track
    session = race.session

    st.header(f'{race.year} {race.track} {race.session}', text_alignment='center')
    col1, col2 = st.columns(2)
    col1.header('Results', text_alignment='center')
    df_format(race.clean_results, col1)
    col2.header(f'Weather Conditions', text_alignment='center')
    df_format(race.weather_data[1], col2)
    col2.plotly_chart(race.weather_plot)

    if race.session in ['Race','Sprint']:
        laps_1, laps_2 = st.columns(2)

        laps_1.plotly_chart(race.strategies_plot)
        laps_2.plotly_chart(race.positions_plot)
    else:
        for qs in ['Q1', 'Q2', 'Q3']:
            st.header(f'{qs} Analysis', text_alignment='center')

            st.session_state[f'{qs}_1'],st.session_state[f'{qs}_2'] = st.columns(2)
            st.session_state[f'{qs}_3'],st.session_state[f'{qs}_4'], st.session_state[f'{qs}_5'] = st.columns(3)
           

            for n, p in zip([1,2], ['Lap Time', 'Speed Trap']):
                st.session_state[f'{qs}_{n}'].text(p, text_alignment='center')
                st.session_state[f'{qs}_{n}'].plotly_chart(race.quali_plots[qs][n - 1])

            for n, p in zip([3,4,5], ['Sector 1', 'Sector 2', 'Sector 3']):
                st.session_state[f'{qs}_{n}'].text(p, text_alignment='center')
                st.session_state[f'{qs}_{n}'].plotly_chart(race.quali_plots[qs][n - 1])




        
