
import plotly.express as px
import streamlit as st
import pandas as pd
from general_functions import *
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# on the command prompt run: streamlit run C:\noam\dogs\pythonProject\main_stream.py
def load_data(uploaded_files):
    """Load and combine the content of selected files into a DataFrame."""
    all_files = []
    for uploaded_file in uploaded_files:
        lines = uploaded_file.readlines()
        file_name = uploaded_file.name.split("_")[0]
        lines = [file_name + '; ' + line.decode('utf-8') for line in lines]
        all_files += lines

    data = [line.strip().split(';') for line in all_files]
    df = pd.DataFrame(data)#, columns=["Filename", "Content"]
    return df

def groupping(df,group_by_lst):
    v_count = df.groupby(group_by_lst)['score (Hit/miss)'].apply('value_counts')
    hit_rate = df.groupby(group_by_lst)['score (Hit/miss)'].apply(lambda x: hit_rate_cal(x))
    hit_rate.rename("hit_rate", inplace=True)
    fa_rate = df.groupby(group_by_lst)['score (Hit/miss)'].apply(lambda x: fa_rate_cal(x))
    fa_rate.rename("fa_rate", inplace=True)
    all_data = pd.merge(v_count, hit_rate, left_on=group_by_lst, right_index=True, how='left')
    all_data = pd.merge(all_data, fa_rate, left_on=group_by_lst, right_index=True, how='left')
    all_data['d_prime'] = calculate_d(all_data['hit_rate'], all_data['fa_rate'])

    all_data = all_data.reset_index()
    #st.write(all_data)
    all_data_remove_duplicates = all_data.drop_duplicates(subset=group_by_lst, keep='last')
    all_data_remove_duplicates = all_data_remove_duplicates.reset_index()

    return all_data_remove_duplicates, all_data

def plot_line(df,y_axis,x_axis_tlt,y_axis_tlt,title,if_sessions = False):
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

                fig.add_vline(x=x_position, line_dash='dash', line_color='rgb(211, 215, 222)')#annotation_text=f'{date}'
                fig.add_annotation(
                    x=x_position-0.3,
                    y=y_position+0.5,
                    text=date,
                    showarrow=False,
                    textangle=270,  # Angle of the text

                    font=dict(color='rgb(97, 98, 99)')
                )#                    xanchor='left',,
                   # yanchor='bottom',  # Position the annotation text at the top of the plot


    # # Customize the layout of the plot (optional)
    # fig.update_layout(
    #     xaxis_title=x_axis_tlt,
    #     yaxis_title=y_axis_tlt,
    #     title_x=0.5  # Center the chart title
    # )
    # Customize the layout of the plot
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
    # fig.update_xaxes(range=[0, selected_dog.shape[0]])
    fig.update_xaxes(
        range=[0, df.shape[0]+1],
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
                             text=dog_data['count'], textposition='auto'), row=1, col=i+1)

    # Update x-axis and y-axis titles
    fig.update_xaxes(title_text='Score', row=1, col=len(dog_names) // 2 + 1)
    fig.update_yaxes(title_text='Count', row=1, col=1)

    # Update figure layout
    fig.update_layout(showlegend=False)

    st.plotly_chart(fig)

def main():
    st.title('Text Files Viewer and Combiner')

    st.sidebar.title("Upload Text Files")
    uploaded_files = st.sidebar.file_uploader("Choose text file(s)", accept_multiple_files=True, type="txt")


    if uploaded_files:
        df = load_data(uploaded_files)
        #""" pre-processed data """
        # set columns name
        df.columns = df.iloc[0]
        df.drop(columns=df.columns[0], axis=1, inplace=True)  # drop first col
        df = df.rename(columns=lambda
            x: x.strip() if x is not None else x)  # Remove leading and trailing spaces from all columns names
        df = df.map(
            lambda x: x.strip() if isinstance(x, str) else x)  # Remove leading and trailing spaces from all values
        df = df.loc[
            df['date'] != "date"]  # filter the wrong rows (that is actually names of the columns of the text files)
        st.subheader("Data After pre-processing")
        st.write(df)


        #""" choose how to display the data """
        option = st.sidebar.radio(
            "Display Options",
            ("By Sessions", "All Together", "By Bin Size")
        )
        res = []
        with_duplicates = []
        tlt_x_axis = ''
        if_sessions = False
        if option == "By Sessions":
            res, with_duplicates = groupping(df,['dog_name', 'date', 'num_session'])
            tlt_x_axis = 'session'
            if_sessions = True
        elif option == "All Together":
            res, with_duplicates = groupping(df,['dog_name'])
            tlt_x_axis = ''
        elif option == "By Bin Size":
            bin_size = st.sidebar.number_input("Bin Size", min_value=1, value=10)
            tlt_x_axis = 'Bins: bin size=' + str(bin_size)
            df_sorted = df.sort_values(by=['dog_name', 'date', 'Time stamp of trial initiation'])
            df_sorted['bin'] = df_sorted.groupby('dog_name').cumcount() // bin_size + 1
            """ by_bins """
            #st.write(df_sorted)
            res, with_duplicates = groupping(df_sorted, ['dog_name','bin'])

        unique_names = res["dog_name"].unique()
        selected_name = st.sidebar.selectbox("Select a Name", unique_names)

        # Display data for the selected name
        if selected_name:
            # plot total score dist
            score_dist = with_duplicates.groupby(['dog_name','score (Hit/miss)'])['count'].sum()
            #st.write(score_dist)
            score_dist = score_dist.reset_index()
            plot_score_dist(score_dist)
            st.subheader(f"Data for {selected_name}:")
            selected_dog = res[res["dog_name"] == selected_name]
            selected_dog.reset_index(inplace=True)
            selected_dog.index = selected_dog.index + 1
            #st.subheader("Data After analysis and grouping")
            selected_dog=selected_dog.drop(columns=['level_0','index','score (Hit/miss)'])
            st.write(selected_dog)

            #plot d_prime
            plot_line(selected_dog, 'd_prime',tlt_x_axis, 'D prime','D-Prime over time',if_sessions)
            # plot hit_rate and fa_rate
            plot_line(selected_dog, ['hit_rate','fa_rate'], tlt_x_axis, 'Rate','Hit and FA rates over time',if_sessions)

    else:
        st.write("Please upload at least one text file to display")

if __name__ == "__main__":
    main()

