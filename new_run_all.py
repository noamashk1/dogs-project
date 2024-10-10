import socket
import subprocess
import time
import logging
import sys
import pandas as pd
import os
from scipy.stats import norm
import plotly.express as px
import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go

#to executable- navigate to the directory by  "cd C:\noam\dogs\pythonProject" and the use: C:\Users\Owner\AppData\Local\Programs\Python\Python312\python.exe -m PyInstaller --onefile --hidden-import=streamlit --hidden-import=importlib_metadata --collect-all streamlit new_run_all.py

# # Increase the timeout for the Streamlit server to start
os.environ['STREAMLIT_SERVER_STARTUP_TIMEOUT'] = '300'  # Increase to 300 seconds
# Set up logging
logging.basicConfig(filename='app_log.txt', level=logging.DEBUG)


def find_chrome_path():
    # Common Chrome installation paths for Windows
    common_paths = [
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Users\<username>\AppData\Local\Google\Chrome\Application\chrome.exe"  # User-specific path
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    logging.error("Chrome not found in expected locations.")
    return None

def is_server_running(host='localhost', port=8501):
    """Check if the Streamlit server is running."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) == 0

# === Your original run_all_in_one_manof() function goes here ===
def run_all_in_one_manof():
    # Simulating what was in the 'all_in_one_manof.py'
    # This is just an example; replace it with actual code from 'all_in_one_manof.py'
    logging.info("Running logic.py")
    # Add the actual functions and logic from 'all_in_one_manof.py' here

    def hit_rate_cal(trials_score):
        # 0 = hit, 1 = FA, 2 = miss, 3 = CR.
        hit = trials_score.eq("HIT").sum()
        miss = trials_score.eq("MISS").sum()
        hit_rate = hit / (hit + miss)
        if hit == 0:
            hit_rate = 0
        if hit_rate == 1:
            hit_rate = 0.99
        if hit_rate == 0:
            hit_rate = 0.01
        return hit_rate

    def fa_rate_cal(mice_trails):
        # 0 = hit, 1 = FA, 2 = miss, 3 = CR.
        fa = mice_trails.eq("FA").sum()
        cr = mice_trails.eq("CR").sum()
        fa_rate = fa / (fa + cr)
        if fa == 0:
            fa_rate = 0
        if fa_rate == 1:
            fa_rate = 0.99
        if fa_rate == 0:
            fa_rate = 0.01
        return fa_rate

    def calculate_d(hit_rate_col, fa_rate_col):
        d = norm.ppf(hit_rate_col) - norm.ppf(fa_rate_col)
        # if np.isnan(d):
        #     print(d)
        return d

    def groupping(df, group_by_lst):
        v_count = df.groupby(group_by_lst)['score (Hit/miss)'].apply('value_counts')
        hit_rate = df.groupby(group_by_lst)['score (Hit/miss)'].apply(lambda x: hit_rate_cal(x))
        hit_rate.rename("hit_rate", inplace=True)
        fa_rate = df.groupby(group_by_lst)['score (Hit/miss)'].apply(lambda x: fa_rate_cal(x))
        fa_rate.rename("fa_rate", inplace=True)
        all_data = pd.merge(v_count, hit_rate, left_on=group_by_lst, right_index=True, how='left')
        all_data = pd.merge(all_data, fa_rate, left_on=group_by_lst, right_index=True, how='left')
        all_data['d_prime'] = calculate_d(all_data['hit_rate'], all_data['fa_rate'])

        all_data = all_data.reset_index()
        # st.write(all_data)
        all_data_remove_duplicates = all_data.drop_duplicates(subset=group_by_lst, keep='last')
        all_data_remove_duplicates = all_data_remove_duplicates.reset_index()

        return all_data_remove_duplicates, all_data

    def plot_line(df, y_axis, x_axis_tlt, y_axis_tlt, title, if_sessions=False):
        # st.scatter_chart(selected_dog,y=['hit_rate','fa_rate'],use_container_width=True)

        if df.shape[0] < 2:
            fig = px.scatter(df, y=y_axis, title=title)
        else:
            fig = px.line(df, y=y_axis, title=title)
            if if_sessions:
                # Identify the index positions of the first occurrences of each date
                df['date_id'] = df['date'].factorize()[0]
                if isinstance(y_axis, list):
                    y_position = max([df[i].max() for i in y_axis])
                    st.write('list')
                else:
                    st.write('not_list')
                    y_position = df[y_axis].max()
                for date_id in df['date_id'].unique():
                    date = df.loc[df['date_id'] == date_id, 'date'].values[0]
                    x_position = df.loc[df['date_id'] == date_id].iloc[0].name
                    fig.add_vline(x=x_position, line_dash='dash',
                                  line_color='rgb(211, 215, 222)')  # annotation_text=f'{date}'
                    fig.add_annotation(
                        x=x_position - 0.3,
                        y=y_position + 0.5,
                        text=date,
                        showarrow=False,
                        textangle=270,  # Angle of the text

                        font=dict(color='rgb(97, 98, 99)')
                    )

        fig.update_layout(
            xaxis_title=x_axis_tlt,
            yaxis_title=y_axis_tlt,
            title_x=0.5,  # Center the chart title
            height=600,  # Make the plot height adjustable
            xaxis=dict(
                rangeslider=dict(visible=True),  # Add an x-axis range slider for better navigation
                type='linear'
            )
        )

        # Set the x-axis range
        fig.update_xaxes(
            range=[0, df.shape[0] + 1],
            tickmode='linear',
            tick0=0,
            dtick=1
        )

        # Display the interactive plot in Streamlit
        st.plotly_chart(fig, use_container_width=True)

    def plot_score_dist(df):
        dog_names = df['dog_name'].unique()

        # Create a single figure to hold all the plots
        fig = make_subplots(rows=1, cols=len(dog_names), subplot_titles=dog_names)
        for i, dog in enumerate(dog_names):
            dog_data = df[df['dog_name'] == dog]

            fig.add_trace(go.Bar(x=dog_data['score (Hit/miss)'], y=dog_data['count'], name=dog,
                                 text=dog_data['count'], textposition='auto'), row=1, col=i + 1)

        # Update x-axis and y-axis titles
        fig.update_xaxes(title_text='Score', row=1, col=len(dog_names) // 2 + 1)
        fig.update_yaxes(title_text='Count', row=1, col=1)

        # Update figure layout
        fig.update_layout(showlegend=False)

        st.plotly_chart(fig)

    def combine_excel_files():
        st.sidebar.title("Upload Excel Files")
        uploaded_files = st.sidebar.file_uploader("Choose Excel file(s)", accept_multiple_files=True, type="xlsx")

        if uploaded_files:
            dataframes = []
            for uploaded_file in uploaded_files:
                try:
                    df = pd.read_excel(uploaded_file)
                    dataframes.append(df)
                    st.write(f"Loaded {uploaded_file.name}")
                except Exception as e:
                    st.error(f"Failed to load {uploaded_file.name}: {e}")

            if dataframes:
                combined_df = pd.concat(dataframes, ignore_index=True)
                st.write("Combined DataFrame:")
                st.write(combined_df)
                return combined_df
            else:
                st.write("No valid files to combine.")
        else:
            st.write("No files uploaded.")

    df = combine_excel_files()
    if not isinstance(df, type(None)):
        df.drop(columns=['area', 'dog_ID', 'target_bin', 'trial_ID', 'trial_total', 'target_ID', 'click_time',
                         'choice_time', 'tester'], axis=1, inplace=True)  # drop first col
        df = df.rename(columns={'dog': 'dog_name', 'session': 'num_session', 'score': 'score (Hit/miss)'})
        df['score (Hit/miss)'] = df['score (Hit/miss)'].replace('cr', 'CR')
        df['score (Hit/miss)'] = df['score (Hit/miss)'].replace('hit', 'HIT')
        df['score (Hit/miss)'] = df['score (Hit/miss)'].replace('fp', 'FA')
        df['score (Hit/miss)'] = df['score (Hit/miss)'].replace('miss', 'MISS')
        df['date'] = df['date'].astype(str).str.zfill(6)
        df['date'] = pd.to_datetime(df['date'], format='%d%m%y')
        df.sort_values(by='date', ascending=True, inplace=True)
        df['date_str'] = df['date'].dt.strftime('%d/%m/%Y')
        st.subheader("Combined Data")

        # """ pre-processed data """
        # filter the wrong rows (that is actually names of the columns of the text files)
        st.subheader("Data After pre-processing")
        st.write(df)

        # """ choose how to display the data """
        option = st.sidebar.radio(
            "Display Options",
            ("By Sessions", "All Together", "By Bin Size")
        )
        res = []
        with_duplicates = []
        tlt_x_axis = ''
        if_sessions = False
        if option == "By Sessions":
            res, with_duplicates = groupping(df, ['dog_name', 'date', 'num_session'])
            tlt_x_axis = 'session'
            if_sessions = True
        elif option == "All Together":
            res, with_duplicates = groupping(df, ['dog_name'])
            tlt_x_axis = ''
        elif option == "By Bin Size":
            bin_size = st.sidebar.number_input("Bin Size", min_value=1, value=10)
            tlt_x_axis = 'Bins: bin size=' + str(bin_size)
            df_sorted = df.sort_values(by=['dog_name', 'date'])  # , 'Time stamp of trial initiation'
            df_sorted['bin'] = df_sorted.groupby('dog_name').cumcount() // bin_size + 1
            """ by_bins """
            # st.write(df_sorted)
            res, with_duplicates = groupping(df_sorted, ['dog_name', 'bin'])

        unique_names = res["dog_name"].unique()
        selected_name = st.sidebar.selectbox("Select a Name", unique_names)

        # Display data for the selected name
        if selected_name:
            # st.write(f"Data for {selected_name}:")
            selected_dog = res[res["dog_name"] == selected_name]
            selected_dog.reset_index(inplace=True)
            selected_dog.index = selected_dog.index + 1
            if 'date' in selected_dog.columns:
                selected_dog['date'] = selected_dog['date'].dt.strftime('%d/%m/%y')
            st.subheader("Data After analysis and grouping")
            selected_dog = selected_dog.drop(columns=['level_0', 'index', 'score (Hit/miss)'])
            st.write(selected_dog)
            # plot total score dist
            score_dist = with_duplicates.groupby(['dog_name', 'score (Hit/miss)'])['count'].sum()
            st.write(score_dist)
            score_dist = score_dist.reset_index()
            plot_score_dist(score_dist)
            # plot d_prime
            plot_line(selected_dog, 'd_prime', tlt_x_axis, 'D prime', 'D-Prime over time', if_sessions)
            # plot hit_rate and fa_rate
            plot_line(selected_dog, ['hit_rate', 'fa_rate'], tlt_x_axis, 'Rate', 'Hit and FA rates over time',
                      if_sessions)

    print("All-in-one Manof logic executed.")

def main():
    try:
        logging.info('Starting the application...')

        # Run the code from 'all_in_one_manof.py'
        run_all_in_one_manof()  # <== This is the missing call

        # Find the Chrome path
        chrome_path = find_chrome_path()
        if chrome_path is None:
            logging.error("Chrome could not be found. Make sure it is installed.")
            return

        # Check if the Streamlit server is already running
        if not is_server_running():
            # Start the Streamlit server only if it is not running
            command = [sys.executable, '-m', 'streamlit', 'run', sys.argv[0]]  # Running current script itself
            server = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.info('Started the Streamlit server.')
        else:
            logging.info('Streamlit server is already running.')

        # Wait for the Streamlit server to start
        logging.info('Waiting for Streamlit server to start...')
        for _ in range(300):  # Wait up to 300 seconds
            if is_server_running():
                logging.info('Streamlit server is running.')
                break
            time.sleep(1)
        else:
            logging.error('Streamlit server did not start in time.')
            return

        # Open Chrome only if it's not already open
        if 'BROWSER_OPENED' not in os.environ:
            try:
                subprocess.Popen([chrome_path, 'http://localhost:8501'])
                logging.info('Opened Chrome at http://localhost:8501')
                os.environ['BROWSER_OPENED'] = '1'  # Set environment variable to prevent reopening
            except Exception as e:
                logging.exception('Failed to open Chrome')

    except Exception as e:
        logging.exception('An error occurred during execution')
        sys.exit(1)  # Exit with an error code

if __name__ == '__main__':
    main()
