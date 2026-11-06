from f1_analyzer_2 import F1Analysis as f1
import pandas as pd
import streamlit as st

# streamlit run app.py

def get_events():
    df = pd.read_csv('./events/events.csv')
    df = df.loc[df['Complete'] == True].copy()
    return df

def df_format(df, x):
    x.dataframe(
            df, 
            hide_index=True, height='content', width='stretch',
            column_config={col: st.column_config.Column(alignment='center') for col in df.columns},
        )
    
def get_tracks(year):
    df = events.copy()
    return df[df['Year'] == year]['EventName'].to_list()

def get_sessions(year, track):
    df = events.copy()
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

events = get_events()

st.set_page_config(layout="wide")

if 'race' not in st.session_state:
    st.session_state['race'] = f1(2020, 'Sakhir Grand Prix', 'Race')
    year = 2020
    track = 'Sakhir Grand Prix'
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
    
    if race.session in ['Race','Sprint']:
        st.header(f'{race.year} {race.track}', text_alignment='center')
        sum_col_1, sum_col_2, sum_col_3 = st.columns([1,1,9])
        select = sum_col_1.selectbox('', ['Summary', 'Strategies', 'Lap Times', 'Sector Times & Speed Trap','Tyre Performance'])

        if select == 'Summary':
            
            col1, col2 = st.columns(2)
            col1.header('Results', text_alignment='center')
            df_format(race.clean_results, col1)
            col2.header(f'Weather Conditions', text_alignment='center')
            df_format(race.weather_data[1], col2)
            col2.plotly_chart(race.weather_plot)

        if select == 'Strategies':
            laps_1, laps_2 = st.columns(2)

            laps_1.header('Strategies', text_alignment='center')
            laps_2.header('Positions', text_alignment='center')
            
            laps_1.plotly_chart(race.strategies_plot)
            laps_2.plotly_chart(race.positions_plot)
        
        if select == 'Lap Times':
            lap_type = sum_col_2.selectbox('',['Clean', 'Fuel Corrected'], index=0)
        
            if lap_type == 'Clean':
                st.header('Lap Times', text_alignment='center')
                st.plotly_chart(race.race_plots[0])
                st.session_state[f'laps_1'], st.session_state[f'laps_2'] = st.columns([1,2], border=True)
                
                st.session_state[f'laps_1'].text(f'Pace Bar')
                st.session_state[f'laps_1'].plotly_chart(race.race_plots[1])

                st.session_state[f'laps_2'].text(f'Pace Violin')
                st.session_state[f'laps_2'].plotly_chart(race.race_plots[2])

                pass
            if lap_type == 'Fuel Corrected':
                st.header('Lap Times Fuel Corrected', text_alignment='center')
                st.plotly_chart(race.race_plots[3])
                st.session_state[f'laps_1'], st.session_state[f'laps_2'] = st.columns([1,2], border=True)
                
                st.session_state[f'laps_1'].text(f'Pace Bar')
                st.session_state[f'laps_1'].plotly_chart(race.race_plots[4])

                st.session_state[f'laps_2'].text(f'Pace Violin')
                st.session_state[f'laps_2'].plotly_chart(race.race_plots[5])
                pass
        if select == 'Sector Times & Speed Trap':
            st.header('Average Sector Times and Speed Trap', text_alignment='center')
            st.text('Speed Trap')
            st.plotly_chart(race.race_plots[-1])

            st.session_state['r_sector_1'], st.session_state['r_sector_2'], st.session_state['r_sector_3'] = st.columns(3, border=True)

            for s, p in zip([1,2,3], [6,7,8]):
                st.session_state[f'r_sector_{s}'].text(f'Sector {s}')
                st.session_state[f'r_sector_{s}'].plotly_chart(race.race_plots[p])

        if select == 'Tyre Performance':
            for tyre in list(race.tyre_deg_plots.keys()):
                plots = race.tyre_deg_plots[tyre]
                st.header(f'{tyre} Degredation',text_alignment='center')
                tyre_1, tyre_2 = st.columns(2, border=True)
                tyre_1.text('Pace')
                tyre_1.plotly_chart(plots[0])
                tyre_2.text('Deg Per Lap')
                tyre_2.plotly_chart(plots[1])



    else:
        st.header(f'{race.year} {race.track} {race.session}', text_alignment='center')
        sum_col_1, sum_col_2, sum_col_3 = st.columns([1,1,9])
        select = sum_col_1.selectbox('', ['Summary', 'Q1', 'Q2', 'Q3'], index=0)

        if select == 'Summary':
            col1, col2 = st.columns(2, border=True)
            col1.header('Results', text_alignment='center')
            df_format(race.clean_results, col1)
            col2.header(f'Weather Conditions', text_alignment='center')
            df_format(race.weather_data[1], col2)
            col2.plotly_chart(race.weather_plot)

        for qs in ['Q1', 'Q2', 'Q3']:
            if select == qs:
                st.header(f'{qs} Analysis', text_alignment='center')

                st.session_state[f'{qs}_1'],st.session_state[f'{qs}_2'] = st.columns(2, border=True)
                st.header('Personal Best Sectors', text_alignment='center')
                st.session_state[f'{qs}_3'],st.session_state[f'{qs}_4'], st.session_state[f'{qs}_5'] = st.columns(3, border=True)
                
                for n, p in zip([1,2], ['Lap Time', 'Speed Trap']):
                    st.session_state[f'{qs}_{n}'].text(p, text_alignment='center')
                    st.session_state[f'{qs}_{n}'].plotly_chart(race.quali_plots[qs][n - 1])

                for n, p in zip([3,4,5], ['Sector 1', 'Sector 2', 'Sector 3']):
                    st.session_state[f'{qs}_{n}'].text(p, text_alignment='center')
                    st.session_state[f'{qs}_{n}'].plotly_chart(race.quali_plots[qs][n - 1])



    



