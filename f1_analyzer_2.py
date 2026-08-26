import fastf1
from fastf1 import plotting
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import numpy as np


class F1Analysis:
    def __init__(self, year, track, session):
        self.year = year
        self.track = track
        self.session = session
        self.results_df = pd.read_parquet(f'./data/{year}_{track}_{session}_results.parquet'.lower().replace(' ',''))
        self.laps_df = pd.read_parquet(f'./data/{year}_{track}_{session}_laps.parquet'.lower().replace(' ',''))
        self.weather_df = pd.read_parquet(f'./data/{year}_{track}_{session}_weather.parquet'.lower().replace(' ',''))
        self.teams = self._get_teams()
        self.race_distance = self._get_race_distance()
        self.sprint_distance = math.ceil(self.race_distance * 1/3)
        self.tyre_colors = self._tyre_colors()
        self.weather_plot = self._plot_weather()
        
        # self.location = self.session.session_info['Meeting']['Location']
        # self.type_2 = self.session.session_info['Type']
        self.drivers = self._get_all_drivers_names()
        self.valid_drivers = self._get_valid_drivers()
        self.invalid_drivers = self._get_invalid_drivers()
        # self.results = self._get_results_clean()[1]
        # self.results_raw = self._get_results_clean()[0]
        # self.lead_drivers = self._get_lead_driver()
        self.time_loss = self._get_time_loss_per_kg()
        # self.title = self._get_session_title()
        # self.type = self._get_session_type()
        self.fuel_capacity = self._get_fuel_capacity()
        # self.location = self._get_location()
        self.avg_fuel_usage = self._get_avg_fuel_usage()
        self.time_loss_per_lap = self._fuel_time_loss_per_lap()
        self.driver_line_type = self._driver_line_type()
        # self.top_ten_lap_details = self._get_top_ten_laps_details()
        # self.tyre_deg = self._calc_tyre_deg()
        # self.weather_data = self._get_weather_data()
        self.analyzed_stints = self._analyze_race_stints()
        self.strategies_plot = self._strategies_plot()
        self.positions_plot = self._positions_plot()

    def _get_teams(self):
        df = self.results_df
        return df['TeamName'].drop_duplicates().to_list()

    def _get_all_drivers_names(self):
        return self.results_df['Abbreviation'].to_list()

    def _get_time_loss_per_kg(self):
        # get the fastest valid lap time
        df = self.laps_df
        fl = df.loc[df['TrackStatus'] == '1']['LapTime'].min().total_seconds()

        time_loss_per_kg = (fl / 90) * .035
        return time_loss_per_kg

    def _tyre_colors(self):
        tyre_colors = {
            'SOFT':'#FF3333',
            'MEDIUM': '#FFF200',
            'HARD': '#EBEBEB',

            'INTERMEDIATE': '#43B02A',
            'WET': '#0067AD'
        }
        return tyre_colors

    def _get_fuel_capacity(self):
        if self.year in [2019,2020,2021,2022,2023,2024,2025]:
            return 110
        elif self.year == 2026:
            return 75
        elif self.year == 2018:
            return 105

    def _get_race_distance(self):
        df = pd.read_csv('./events/schedule.csv').reset_index(drop=True)
        df = df[df['Year'] == self.year]
        df = df[df['EventName'] == self.track]
        return df['Laps'].item()

    def _get_avg_fuel_usage(self):
        rd = self.race_distance
        cap = self.fuel_capacity
        return cap / (rd - 1)

    def _driver_line_type(self):
        df = self.results_df.copy()
        teams = self.teams
        teams_dfs = [df[df['TeamName'] == team] for team in teams]
        driver_dict = {}

        for team in teams_dfs:
            drivers = team['Abbreviation'].to_list()
            driver_dict[drivers[0]] = 'solid'
            try:
                driver_dict[drivers[1]] = 'dot'
            except:
                continue
        return driver_dict

    def _get_valid_drivers(self):
        if self.session in ['Race', 'Sprint']:
            valid_drivers = []
            laps_min = self.race_distance * .75
            df = self.results_df
            for driver in self.drivers:
                try:
                    driver_laps = df[df['Abbreviation'] == driver]['Laps'].item()
                    if driver_laps >= laps_min:
                        valid_drivers.append(driver)
                except:
                    continue
            return valid_drivers
        else:
            valid_drivers = []
            for driver in self.drivers:
                if pd.isna(self.results_df[self.results_df['Abbreviation'] == driver]['Q1'].item()):
                    continue
                else:
                    valid_drivers.append(driver)
            return valid_drivers

    def _get_invalid_drivers(self):
        invalid_drivers = []
        for driver in self.drivers:
            if driver not in self.valid_drivers:
                invalid_drivers.append(driver)
        return invalid_drivers
           

    def _analyze_race_stints(self):
        if self.session not in ['Race', 'Sprint']: 
            return None
        
        results = self.results_df
        analyzed_dfs = []

        for driver in self.drivers:
            driver_color = f'#{results.loc[results['Abbreviation'] == driver]['TeamColor'].item()}'
            driver_laps = self.laps_df.loc[self.laps_df['Driver'] == driver].reset_index(drop=True)
            driver_laps['Color'] = driver_color
            driver_laps['TimeLoss'] = self.time_loss_per_lap['TimeLoss'].reindex(driver_laps.index)
            driver_laps['LapTime'] = driver_laps['LapTime'].dt.total_seconds()
            driver_laps['TimedLapTime'] = driver_laps['LapTime']
            
            # Instead of using for loops which is rly slow, I can use boolean indexing with pandas
            # it basically works like this:
            # df.loc[df['column_name'] condition, 'column_to_modify'] = new_value
            # this is much faster than the for x in df.index:
            # ` reverses the condition from True to False and vice versa, so it selects all rows where the condition is not met`
            
            driver_laps.loc[driver_laps['TrackStatus'] != '1', 'TimedLapTime'] = pd.NA
            driver_laps.loc[driver_laps['Deleted'] == True, 'TimedLapTime'] = pd.NA
            driver_laps.loc[driver_laps['IsAccurate'] == False, 'TimedLapTime'] = pd.NA

            driver_laps['Roll'] = driver_laps['TimedLapTime'].rolling(window=7).median()
            driver_laps['Roll2'] = driver_laps['TimedLapTime'].rolling(window=2).median()
            driver_laps.loc[driver_laps['Roll'].isna(), 'Roll'] = driver_laps['Roll2']
            driver_laps['Roll'] = driver_laps['Roll'].bfill().ffill()
            driver_laps['Diff'] = driver_laps['TimedLapTime'] - driver_laps['Roll']
            driver_laps.loc[driver_laps['Diff'] < 0, 'Diff'] = pd.NA
            threshold = driver_laps['Diff'].mean() * 2
            driver_laps.loc[driver_laps['TimedLapTime'] - driver_laps['Roll'] > threshold,'TimedLapTime'] = pd.NA
            driver_laps.loc[driver_laps['TimedLapTime'] == driver_laps['TimedLapTime'].max(), 'TimedLapTime'] = pd.NA

            # fuel corrections
            driver_laps['LapTimeFc'] = driver_laps['LapTime'] - driver_laps['TimeLoss']
            driver_laps['TimedLapTimeFc'] = driver_laps['TimedLapTime'] - driver_laps['TimeLoss']

            driver_laps = driver_laps.drop(columns=['Roll', 'Roll2', 'Diff'])
            
                # if not driver_laps.loc[x, 'IsAccurate']:
                #     driver_laps.loc[x,'TimedLapTime'] = pd.NA
                # if driver_laps.loc[x, 'TrackStatus'] != '1':
                #     driver_laps.loc[x, 'TimedLapTime'] = pd.NA
                # if driver_laps.loc[x,'LapNumber'] == 1 or driver_laps.loc[x,'LapNumber'] == 2:
                #     driver_laps.loc[x,'TimedLapTime'] = pd.NA
                # if driver_laps.loc[x,'Deleted']:
                #     driver_laps.loc[x,'TimedLapTime'] = pd.NA
                # if driver_laps.loc[x,'TimedLapTime']  - driver_laps['TimedLapTime'].mean() > 2:
                #     driver_laps.loc[x,'TimedLapTime'] = pd.NA
            
            analyzed_dfs.append(driver_laps)
        return analyzed_dfs


    def _fuel_time_loss_per_lap(self):
        if self.session not in ['Race', 'Sprint']:
            return None
        elif self.session == 'Race':
            distance = self.race_distance
        elif self.session == 'Sprint':
            distance = self.sprint_distance

        time_loss_per_kg = self.time_loss
        avg_fuel_usage = self.avg_fuel_usage

        fuel_per_lap = pd.DataFrame()
        fuel_per_lap['Laps'] = list(range(1, distance + 1))
        fuel_per_lap['Fuel'] = fuel_per_lap['Laps'] * avg_fuel_usage
        fuel_per_lap['Fuel'] = fuel_per_lap['Fuel'].values[::-1]
        fuel_per_lap['TimeLoss'] = fuel_per_lap['Fuel'] * time_loss_per_kg

        return fuel_per_lap

    def _strategies_plot(self):
        if self.session not in ['Race', 'Sprint']:
            return None
        analyzed_dfs = self.analyzed_stints
        stints_dfs = []
        stints_summaries = []

        for df in analyzed_dfs:
            stints = df['Stint'].drop_duplicates().to_list()

            for stint in stints:
                stint_df = df[df['Stint'] == stint].reset_index(drop=True)
                stints_dfs.append(stint_df)

        for df in stints_dfs:
            if df.empty:
                continue

            stint_dict = {
                'Driver': [df['Driver'].iloc[0]],
                'AvgLapTime': [df['TimedLapTime'].mean()],
                'AvgLapTimeFc': [df['TimedLapTimeFc'].mean()],
                'Stint': [df['Stint'].iloc[0]],
                'StintStart': [df['LapNumber'].iloc[0]],
                'StintEnd': [df['LapNumber'].iloc[-1]],
                'StintLength': [df['LapNumber'].iloc[-1] - df['LapNumber'].iloc[0]],
                'Compound': [df['Compound'].iloc[0]],
                'FreshTyre': [df['FreshTyre'].iloc[0]],
                'Color': [self.tyre_colors[df['Compound'].iloc[0]]],
                'Length+1': [(df['LapNumber'].iloc[-1] - df['LapNumber'].iloc[0]) + 1]
            }

            df = pd.DataFrame(stint_dict)
            stints_summaries.append(df)
        
        texts = []

        for df in stints_summaries:
            label = (
                f'{df['Driver'].iloc[0]} | '
                f'AVG: {self.convert_seconds_to_s_ms(df['AvgLapTime'].iloc[0])} | FC: {self.convert_seconds_to_s_ms(df['AvgLapTimeFc'].iloc[0])}<br>' # makes a new line
                f'Tyre: {df['Compound'].iloc[0]} | New Set: {df['FreshTyre'].iloc[0]}<br>'
                f'Stint: {df['Stint'].iloc[0].astype(int)} | '
                f'Length: {df['StintLength'].iloc[0].astype(int) + 1} | '
                f'Range: {df['StintStart'].iloc[0].astype(int)}-{df['StintEnd'].iloc[0].astype(int)} |'
            )    

            texts.append(label)
        
        fig = make_subplots()

        for df, text in zip(stints_summaries, texts):
            fig.add_traces(go.Bar(
                x=df['Length+1'],
                y=df['Driver'],
                name=df['Driver'].iloc[0],
                marker_color=df['Color'].iloc[0],
                orientation='h',
                hovertext=text,
                textposition='none',
                hoverinfo='text'
            ))

        fig.update_layout(
            title=f'{self.year} {self.track} {self.session} Strategies',
            template='plotly_dark',
            width=1200, height=680,
            barmode='stack',
            showlegend=False
        )

        fig.update_yaxes(title_text='Drivers', autorange='reversed')
        fig.update_xaxes(title_text='Laps')

        return fig

    def _positions_plot(self):
        if self.session not in ['Race', 'Sprint']:
            return None
        
        fig = make_subplots()
        results_df = self.results_df

        for df in self.analyzed_stints:
            driver = df['Driver'].iloc[0]
            grid_pos = results_df.loc[results_df['Abbreviation'] == driver]['GridPosition'].item()
            if grid_pos in [0, 0.0]:
                grid_pos = None
            df_2 = df.iloc[0:1].copy()
            df_2['LapNumber'] = 0
            df_2['Position'] = grid_pos

            template = [(
                f'{df_2['Driver'].iloc[0]}<br>'
                f'Grid Pos {df_2['Position'].iloc[0]}'
            )]

            for lap, position, time, tyre, age in zip(df['LapNumber'], df['Position'], df['LapTimeFc'], df['Compound'], df['TyreLife']):
                try:
                    age = int(age)
                except:
                    pass

                text = (
                    f"{df.loc[0, 'Driver']} | Lap {lap:.0f} | Pos {position:.0f}<br>"
                    f"Time: {F1Analysis.convert_seconds_to_m_s_ms(time)}<br>" 
                    f"Tyre: {tyre} ({(age)})"
                )
                template.append(text)
            
            df = pd.concat([df_2, df]).reset_index().copy()
            
            fig.add_trace(go.Scatter(
                x=df['LapNumber'], y=df['Position'],
                name=df.loc[0, 'Driver'],
                hovertext=template,
                mode='lines+markers',
                marker=dict(color=df.loc[0, 'Color']),
                hoverinfo='text',
        
            ))

            fig.update_layout(
                showlegend=True, 
                yaxis=dict(tickformat=','),
                title=f'{self.year} {self.track} {self.session}',
                template='plotly_dark', 
                margin=dict(l=5, r=5, t=30, b=40), 
                width=1200, height=680,
            )

            fig.update_yaxes(title_text='Position', range=[self.results_df['Position'].max() + .5, .5])
            fig.update_xaxes(title_text='Lap', range=[-1, self.results_df['Laps'].max() + 1])

        return fig
    
    def _plot_weather(self):
        def _get_weather_data(df):
            direction_dict = {
                'NE': list(range(24, 67 + 1)),
                'E': list(range(68, 112 + 1)),
                'SE': list(range(113, 157 + 1)),
                'S': list(range(158, 202 + 1)),
                'SW': list(range(203, 247 + 1)),
                'W': list(range(248, 292 + 1)),
                'NW': list(range(293, 337 + 1))
            }
            
            def get_direction(degrees):
                direction = 'N'
                for direct in list(direction_dict.keys()):
                    if degrees in direction_dict[direct]:
                        direction = direct
                    else:
                        pass
                return direction
            
            if self.session in ['Race', 'Sprint']:
                def get_lap(time):
                    lap_number = 'No Lap'
                    for lap in list(lap_ranges.keys()):
                        if time in lap_ranges[lap]:
                            lap_number = lap
                        else:
                            pass
                    return lap_number
                
                # get the time range of each lead lap
                
                lead_lap = self.laps_df[['Time', 'LapTime', 'Position', 'LapNumber']]
                lead_lap = lead_lap[lead_lap['Position'] == 1.0].sort_values(by='LapNumber').reset_index(drop=True)
            
                for x in ['Time', 'LapTime']:
                    lead_lap[x] = lead_lap[x].dt.total_seconds()
                
                lead_lap['TimeEnd'] = lead_lap['Time'].shift(-1)
                lead_lap.loc[lead_lap['LapNumber'] == lead_lap['LapNumber'].iloc[-1], 'TimeEnd'] = lead_lap['Time'].iloc[-1] + 120
                
                for x in ['Time', 'TimeEnd']:
                    lead_lap[x] = lead_lap[x].apply(lambda x: int(x))
                
                lap_ranges = {}

                for lap in lead_lap.index.to_list():
                    lap_ranges[lead_lap.loc[lap, 'LapNumber']] = list(range(lead_lap.loc[lap, 'Time'], lead_lap.loc[lap, 'TimeEnd'] + 1))
                
                # add lap number to weather data

                weather = self.weather_df
                weather['Time'] = weather['Time'].dt.total_seconds().apply(lambda x: int(x))

                weather['LapNumber'] = weather['Time'].apply(get_lap)

                weather = weather[weather['LapNumber'] != 'No Lap'].drop_duplicates(subset='LapNumber').reset_index(drop=True)

                weather['WindComp'] = weather['WindDirection'].apply(get_direction)

                
            else:
                # get the time range of each lead lap
                    
                laps = self.laps_df
                weather = self.weather_df
            
                laps['Time'] = laps['Time'].dt.total_seconds().apply(lambda x: int(x))

                # add lap number to weather data

                weather['Time'] = weather['Time'].dt.total_seconds().apply(lambda x: int(x))
                weather = weather[(weather['Time'] > laps['Time'].min()) & (weather['Time'] < laps['Time'].max())].reset_index(drop=True)
                weather['Time'] = weather['Time'].apply(lambda x: int(x / 60))
                weather['WindComp'] = weather['WindDirection'].apply(get_direction)
            
            if True in weather['Rainfall'].to_list():
                rain = 'True'
            else:
                rain = 'False'

            weather_summary = pd.DataFrame({
                'AirTempAvg': [f"{weather['AirTemp'].mean():.2f}℃"],
                'TrackTempAvg': [f"{weather['TrackTemp'].mean():.2f}℃"],
                'HumidityAvg': [f"{weather['Humidity'].mean():.2f}%"],
                'Rain': [rain],
                'WindSpeedAvg': [f"{weather['WindSpeed'].mean():.2f}km/h"],
                'WindDirectionAvg': [f"{weather['WindDirection'].mean():.2f}°"],
                'WindCompAvg': [get_direction(weather['WindDirection'].mean())],
                'PressureAvg': [f"{weather['Pressure'].mean():.2f}"]

            })

            return [weather, weather_summary]


        df = _get_weather_data(self.weather_df)[0]

        fig = make_subplots()

        if self.session in ['Race', 'Sprint']:

            template = []

            for lap, air, track, rain, hum, wind_s, wind_d, wind_c, press in zip(
                df['LapNumber'], df['AirTemp'], df['TrackTemp'], df['Rainfall'], df['Humidity'],df['WindSpeed'], df['WindDirection'], df['WindComp'], df['Pressure']
            ):

                text = (
                    f"<b>Lap:</b> {int(lap)} <b>Air:</b> {air}℃ <b>Track:</b> {track}℃<br>"
                    f"<b>Wind:</b> {wind_s} km/h <b>Direction:</b> {wind_c} ({wind_d})<br>"
                    f"<b>Humidity:</b> {hum:.1f}% <b>Rain:</b> {rain}<br>"
                    f"<b>Pressure:</b> {press}"
                    )
                
                template.append(text)
            
            for y in ['AirTemp', 'TrackTemp', 'WindSpeed', 'Humidity']:
                
                fig.add_trace(go.Scatter(
                    x=df['LapNumber'], y=df[y],
                    name=y,
                    hovertext=template,
                    mode='lines',
                    hoverinfo='text'  
                ))       

                fig.update_layout(
                    showlegend=True,
                    template='plotly_dark', 
                    margin=dict(l=5, r=5, t=30, b=40), 
                    width=1200, height=680,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02, # Positive values push it above the plot
                        xanchor="center",
                        x=0.5
                    )
                )
        else:

            template = []

            for air, track, rain, hum, wind_s, wind_d, wind_c, press in zip(
                df['AirTemp'], df['TrackTemp'], df['Rainfall'], df['Humidity'],df['WindSpeed'], df['WindDirection'], df['WindComp'], df['Pressure']
            ):

                text = (
                    f"<b>Air:</b> {air}℃ <b>Track:</b> {track}℃<br>"
                    f"<b>Wind:</b> {wind_s} km/h <b>Direction:</b> {wind_c} ({wind_d})<br>"
                    f"<b>Humidity:</b> {hum:.1f}% <b>Rain:</b> {rain}<br>"
                    f"<b>Pressure:</b> {press}"
                    )
                
                template.append(text)
            
            for y in ['AirTemp', 'TrackTemp', 'WindSpeed', 'Humidity']:
                
                fig.add_trace(go.Scatter(
                    x=df['Time'], y=df[y],
                    name=y,
                    hovertext=template,
                    mode='lines',
                    hoverinfo='text'  
                ))       

                fig.update_layout(
                    showlegend=True,
                    template='plotly_dark', 
                    margin=dict(l=5, r=5, t=30, b=40), 
                    width=1200, height=680,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02, # Positive values push it above the plot
                        xanchor="center",
                        x=0.5
                    )
                )
        return fig

    @staticmethod
    def convert_seconds_to_m_s_ms(total_seconds):
        if pd.isna(total_seconds):
            return pd.NA
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        milliseconds = int(round((total_seconds - int(total_seconds)) * 1000))
        return f"{minutes}:{seconds:02d}.{milliseconds:03d}"

    @staticmethod
    def convert_seconds_to_s_ms(total_seconds):
        if pd.isna(total_seconds):
            return pd.NA
        seconds = int(total_seconds % 60)
        milliseconds = int(round((total_seconds - int(total_seconds)) * 1000))
        return f"{seconds:02d}.{milliseconds:03d}"

    @staticmethod
    def convert_seconds_to_s_ms_short(total_seconds):
        if pd.isna(total_seconds):
            return pd.NA
        if total_seconds < 0:
            return f"{total_seconds:.2f}"
        seconds = total_seconds % 60
        return f"{seconds:.2f}"