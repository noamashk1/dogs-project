import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import tkinter.font as tkFont
import pandas as pd
import os
from scipy.stats import norm
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

def hit_rate_cal(trials_score):
    hit = trials_score.eq("HIT").sum()
    miss = trials_score.eq("MISS").sum()
    hit_rate = hit / (hit + miss) if (hit + miss) > 0 else 0
    hit_rate = min(max(hit_rate, 0.01), 0.99)  # Clamp values between 0.01 and 0.99
    return hit_rate

def fa_rate_cal(mice_trails):
    fa = mice_trails.eq("FA").sum()
    cr = mice_trails.eq("CR").sum()
    fa_rate = fa / (fa + cr) if (fa + cr) > 0 else 0
    fa_rate = min(max(fa_rate, 0.01), 0.99)  # Clamp values between 0.01 and 0.99
    return fa_rate

def calculate_d(hit_rate_col, fa_rate_col):
    return norm.ppf(hit_rate_col) - norm.ppf(fa_rate_col)

def groupping(df, group_by_lst):
    if df.empty:  # Check if the DataFrame is empty
        return pd.DataFrame(), pd.DataFrame()  # Return empty DataFrames if there's no data

    v_count = df.groupby(group_by_lst)['score (Hit/miss)'].apply('value_counts')
    hit_rate = df.groupby(group_by_lst)['score (Hit/miss)'].apply(hit_rate_cal)
    hit_rate.rename("hit_rate", inplace=True)
    fa_rate = df.groupby(group_by_lst)['score (Hit/miss)'].apply(fa_rate_cal)
    fa_rate.rename("fa_rate", inplace=True)

    all_data = pd.merge(v_count, hit_rate, left_on=group_by_lst, right_index=True, how='left')
    all_data = pd.merge(all_data, fa_rate, left_on=group_by_lst, right_index=True, how='left')
    all_data['d_prime'] = calculate_d(all_data['hit_rate'], all_data['fa_rate'])
    all_data = all_data.reset_index()
    all_data_remove_duplicates = all_data.drop_duplicates(subset=group_by_lst, keep='last').reset_index()

    return all_data_remove_duplicates, all_data

def plot_line(df, y_axis, x_axis_tlt, y_axis_tlt, title, if_sessions=False):
    if df.shape[0] < 2:
        fig = px.scatter(df, y=y_axis, title=title)
    else:
        fig = px.line(df, y=y_axis, title=title)
        if y_axis=='d_prime':
            fig.update_traces(line=dict(color='green'))
        if if_sessions:
            df['date_id'] = df['date'].factorize()[0]
            y_position = df[y_axis].max()
            annotations = []  # List to store annotations
            for date_id in df['date_id'].unique():
                x_position = df.loc[df['date_id'] == date_id].iloc[0].name
                date = df.loc[df['date_id'] == date_id, 'date'].dt.strftime('%d/%m/%Y').iloc[0]
                try:
                    fig.add_vline(x=x_position, line_dash='dash', line_color='rgb(150, 160, 165)')
                except:
                    print("mono")
                annotation = dict(x=x_position - 0.1, y=y_position + 0.1, text=date, showarrow=False, textangle=270,
                                  font=dict(color='rgb(97, 98, 99)'))
                annotations.append(annotation)

            # Add all annotations to the figure
            for annotation in annotations:
                fig.add_annotation(**annotation)

    fig.update_layout(xaxis_title=x_axis_tlt, yaxis_title=y_axis_tlt, title_x=0.5, height=600,
                      xaxis=dict(rangeslider=dict(visible=True), type='linear'))
    fig.update_xaxes(range=[0, df.shape[0] + 1], tickmode='linear', tick0=0, dtick=1)
    return fig

def plot_score_dist(df):
    dog_names = df['dog_name'].unique()

    # Define a color map for the bars
    color_map = ['blue', 'green', 'red', 'purple', 'orange', 'pink', 'brown', 'cyan']  # Add more colors if needed

    # Create subplots
    fig = make_subplots(rows=1, cols=len(dog_names), subplot_titles=dog_names)

    # Add a bar trace for each dog
    for i, dog in enumerate(dog_names):
        dog_data = df[df['dog_name'] == dog]

        # Assign different color from the color map
        color = color_map[i % len(color_map)]  # Cycle through colors if there are more dogs than colors

        fig.add_trace(go.Bar(x=dog_data['score (Hit/miss)'], y=dog_data['count'], name=dog,
                             marker=dict(color=color),  # Set the color for each dog
                             text=dog_data['count'], textposition='auto'),
                      row=1, col=i + 1)

    # Update layout to set the background to white
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='white',  # Set the plot area background color to white
        paper_bgcolor='white'  # Set the overall background color to white
    )

    return fig
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Data Analysis App")

        # Set window size
        window_width = 400
        window_height = 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calculate the position to center the window
        x_position = (screen_width // 2) - (window_width // 2)
        y_position = (screen_height // 2) - (window_height // 2)

        # Set the geometry of the window (width x height + x_position + y_position)
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        # Increase font size
        font_style = tkFont.Font(family="Helvetica", size=13)

        # Button to select files
        self.select_button = tk.Button(root, text="Select Excel Files", command=self.combine_excel_files, font=font_style)
        self.select_button.pack(pady=10)

        # Radiobuttons for display options
        self.display_option = tk.StringVar(value='1')  # Default to "By Sessions"
        self.radiobuttons_frame = tk.Frame(root)
        self.radiobuttons_frame.pack(pady=10)

        tk.Radiobutton(self.radiobuttons_frame, text="By Sessions", variable=self.display_option, value='1', font=font_style).pack(anchor=tk.W)
        tk.Radiobutton(self.radiobuttons_frame, text="All Together", variable=self.display_option, value='2', font=font_style).pack(anchor=tk.W)
        tk.Radiobutton(self.radiobuttons_frame, text="By Bin Size", variable=self.display_option, value='3', font=font_style).pack(anchor=tk.W)

        # OK button to run analysis
        self.ok_button = tk.Button(root, text="OK", command=self.run_analysis, font=font_style)
        self.ok_button.pack(pady=20)

        self.df = None  # DataFrame to store combined data

    def combine_excel_files(self):
        file_paths = filedialog.askopenfilenames(title="Select Excel Files", filetypes=[("Excel files", "*.xlsx")])
        if not file_paths:
            return

        dataframes = []
        for file_path in file_paths:
            try:
                df = pd.read_excel(file_path)
                dataframes.append(df)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load {file_path}: {e}")

        if dataframes:
            self.df = pd.concat(dataframes, ignore_index=True)
            print(self.df.head())
            messagebox.showinfo("Success", "Excel files loaded successfully!")
            self.update_dog_names()
            self.Data_preprocessing()
        else:
            messagebox.showwarning("Warning", "No valid files to combine.")

    def update_dog_names(self):
        if self.df is not None:
            dog_names = self.df['dog'].unique()  # Update with the correct column name for dog names
            #self.dog_name_dropdown['values'] = dog_names.tolist()

    def Data_preprocessing(self):
        self.df.drop(columns=['area', 'dog_ID', 'target_bin', 'trial_ID', 'trial_total', 'target_ID', 'click_time',
                         'choice_time', 'tester'], axis=1, inplace=True)
        self.df = self.df.rename(columns={'dog': 'dog_name', 'session': 'num_session', 'score': 'score (Hit/miss)'})
        self.df['score (Hit/miss)'] = self.df['score (Hit/miss)'].replace({'cr': 'CR', 'hit': 'HIT', 'fp': 'FA', 'miss': 'MISS'})
        self.df['date'] = self.df['date'].astype(str).str.zfill(6)
        self.df['date'] = pd.to_datetime(self.df['date'], format='%d%m%y')
        self.df.sort_values(by='date', ascending=True, inplace=True)
        self.df['date_str'] = self.df['date'].dt.strftime('%d/%m/%Y')

    def run_analysis(self):
        if self.df is None:
            messagebox.showwarning("Warning", "No data loaded.")
            return
        option = self.display_option.get()

        res = []
        with_duplicates = []
        tlt_x_axis = ''
        if_sessions = False
        if option == '1':  # By Sessions
            res, with_duplicates = groupping(self.df, ['dog_name', 'date', 'num_session'])
            tlt_x_axis = 'session'
            if_sessions = True
        elif option == '2':  # All Together
            res, with_duplicates = groupping(self.df, 'dog_name')
            tlt_x_axis = ''
        elif option == '3':  # By Bin Size
            bin_size = simpledialog.askinteger("Input", "Bin Size (default=10)", initialvalue=10)
            df_sorted = self.df.sort_values(by=['dog_name', 'date'])
            df_sorted['bin'] = df_sorted.groupby('dog_name').cumcount() // bin_size + 1
            res, with_duplicates = groupping(df_sorted, ['dog_name', 'bin'])

        # Check if res is empty before proceeding
        if res.empty:
            messagebox.showwarning("Warning", "No data to display for the selected option.")
            return

        # Get all unique dog names
        all_dogs = res["dog_name"].unique()

        # Create a combined figure with enough rows for all dogs
        # Add one additional row for the score distribution
        fig_combined = make_subplots(
            rows=len(all_dogs) * 2 + 1,  # Add one extra row for the score distribution plot
            cols=1,
            subplot_titles=["Score Distribution"] +  # Title for the score distribution
                           [f"{dog}: D-Prime over time" if i % 2 == 0 else f"{dog}: Hit and FA rates over time" for dog
                            in all_dogs for i in range(2)],
            vertical_spacing = 0.05  # Adjust vertical spacing between plots
        )

        # Add the score distribution graph
        score_dist = with_duplicates.groupby(['dog_name', 'score (Hit/miss)'])['count'].sum().reset_index()
        fig_score_dist = plot_score_dist(score_dist)
        # Add traces for score distribution
        for trace in fig_score_dist.data:
            fig_combined.add_trace(trace, row=1, col=1)  # Add to the first row

        row_counter = 2  # Start row counter for subsequent subplots after the score distribution

        # Loop through each dog and add their D-Prime and Hit/FA rates graphs consecutively
        for dog in all_dogs:
            # Filter data for the current dog
            selected_dog = res[res["dog_name"] == dog]
            selected_dog.reset_index(inplace=True)

            # Add the D-prime figure with annotations for this dog
            fig_d_prime = plot_line(selected_dog, 'd_prime', tlt_x_axis, 'D prime', f"{dog}: D-Prime over time",
                                    if_sessions)

            # Add traces for D-prime
            for trace in fig_d_prime.data:
                fig_combined.add_trace(trace, row=row_counter, col=1)

            # Add vertical lines (vlines) from the D-prime figure to the combined figure
            for shape in fig_d_prime.layout.shapes:
                if shape['type'] == 'line':  # Ensure it's a line (which can represent a vline)
                    fig_combined.add_shape(
                        type=shape['type'],
                        x0=shape['x0'],
                        x1=shape['x1'],
                        y0=shape['y0'],
                        y1=shape['y1'],
                        line=dict(color=shape['line']['color'], width=shape['line']['width'],dash='dash'),
                        xref=f'x{row_counter}',  # Reference for this subplot's x-axis
                        yref=f'y{row_counter}'  # Reference for this subplot's y-axis
                    )
            # Add annotations from the D-prime figure
            for annotation in fig_d_prime.layout.annotations:
                fig_combined.add_annotation(
                    x=annotation.x,
                    y=annotation.y,
                    text=annotation.text,
                    showarrow=annotation.showarrow,
                    textangle=annotation.textangle,
                    font=dict(color=annotation.font.color),
                    xref=f'x{row_counter}',  # Reference for this subplot
                    yref=f'y{row_counter}'  # Reference for this subplot
                )


            # Increment row counter for Hit and FA rates
            row_counter += 1

            # Add the hit_rate and fa_rate figure with annotations for this dog
            fig_hit_fa = plot_line(selected_dog, ['hit_rate', 'fa_rate'], tlt_x_axis, 'Rate',
                                   f"{dog}: Hit and FA rates over time", if_sessions)
            # Add traces for Hit and FA rates
            for trace in fig_hit_fa.data:
                fig_combined.add_trace(trace, row=row_counter, col=1)

            for shape in fig_hit_fa.layout.shapes:
                if shape['type'] == 'line':  # Ensure it's a line (which can represent a vline)
                    fig_combined.add_shape(
                        type=shape['type'],
                        x0=shape['x0'],
                        x1=shape['x1'],
                        y0=shape['y0'],
                        y1=shape['y1'],
                        line=dict(color=shape['line']['color'], width=shape['line']['width'],dash='dash'),
                        xref=f'x{row_counter}',  # Reference for this subplot's x-axis
                        yref=f'y{row_counter}'  # Reference for this subplot's y-axis
                    )

            # for annotation in fig_hit_fa.layout.annotations:
            #     fig_combined.add_annotation(
            #         x=annotation.x,
            #         y=annotation.y,
            #         text=annotation.text,
            #         showarrow=annotation.showarrow,
            #         textangle=annotation.textangle,
            #         font=dict(color=annotation.font.color),
            #         xref=f'x{row_counter}',  # Reference for this subplot
            #         yref=f'y{row_counter}'  # Reference for this subplot
            #     )
            # Increment row counter for the next dog's graphs
            row_counter += 1

        fig_combined.update_layout(
            height=300 * (len(all_dogs) * 2 + 1),
            width=800,
            title={
                "text": "<b>Analysis Results</b>",  # Wrap the title in <b> tags for bold
                "font": {
                    "size": 24,
                    "family": "Arial, sans-serif"  # Optional: set a font family
                },
                "yanchor": "top",  # Anchor the title to the top
                "y": 0.95  # Adjust this value to increase the space between the title and the figure
            },
            legend=dict(
                orientation="v",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            showlegend=True,
            margin=dict(l=20, r=20, t=100, b=50),  # Adjust the top margin (t) for more space
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        # Configure x and y axes to show the axis lines and grid
        fig_combined.update_xaxes(
            showline=True,
            linewidth=2,
            linecolor='grey',
            showgrid=True,
            gridcolor='lightgrey'
        )

        fig_combined.update_yaxes(
            showline=True,
            linewidth=2,
            linecolor='grey',
            showgrid=True,
            gridcolor='lightgrey'
        )

        # Save and open the HTML file as before
        html_content = f"""
        <html>
        <head>
            <style>
                body {{
                    display: flex;
                    justify-content: center;  /* Center horizontally */
                    align-items: center;  /* Center vertically */
                    height: 100vh;  /* Full height of the viewport */
                    margin: 0;  /* Remove default body margin */
                    overflow: hidden;  /* Hide overflow */
                }}
                .scroll-container {{
                    width: 100%;  /* Set the container to use full width of the viewport */
                    height: 800px;  /* Set the visible height */
                    overflow-y: scroll;  /* Enable vertical scrolling */
                    box-sizing: border-box;  /* Ensure padding is included in width */
                    padding: 20px 0;  /* Add padding at the top and bottom */
                    display: flex;  /* Use flexbox to center the graphs */
                    flex-direction: column;  /* Stack the graphs vertically */
                    align-items: center;  /* Center the graphs horizontally */
                }}
                .plotly-graph {{
                    width: 100% !important;  /* Ensure each graph takes the full width */
                    max-width: 800px;  /* Optional: Limit max width for large screens */
                }}
            </style>
        </head>
        <body>
            <div class="scroll-container">
                {fig_combined.to_html(full_html=False)}
            </div>
        </body>
        </html>
        """

        # Write the HTML content to a file using UTF-8 encoding
        with open("combined_analysis.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        # Open the HTML file
        os.startfile("combined_analysis.html")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()