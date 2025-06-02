import pandas as pd
import plotly.express as px
import webbrowser
from bs4 import BeautifulSoup
import json

# Read the CSV file
data = pd.read_csv('games.csv')

# Filter the data to keep only rows with ratings
data = data.dropna(subset=['User Rating'])

# Convert Initial Release Dates to datetime format
data['Initial Release Date'] = pd.to_datetime(data['Initial Release Date'])

# Filter the data to keep only rows with valid dates
data = data.dropna(subset=['Initial Release Date'])

# Sort the data by Initial Release Date
data = data.sort_values('Initial Release Date')

# Add an index column to track original positions
data = data.reset_index(drop=True)
data['_index'] = data.index

# Determine the min and max values for x and y axes from the overall data
min_date_overall = data['Initial Release Date'].min()
max_date_overall = data['Initial Release Date'].max()
min_rating_overall = data['User Rating'].min()
max_rating_overall = data['User Rating'].max()

# Calculate margins for x and y axes
x_margin_seconds = (max_date_overall - min_date_overall).total_seconds() * 0.025
y_margin_value = (max_rating_overall - min_rating_overall) * 0.06

# Convert x_margin from seconds to timedelta
x_margin_timedelta = pd.Timedelta(seconds=x_margin_seconds)

# Calculate ranges for x and y axes
x_range_overall = [min_date_overall - x_margin_timedelta, max_date_overall + x_margin_timedelta]
y_range_overall = [min_rating_overall - y_margin_value, max_rating_overall + y_margin_value]

# --- Step and Data Preparation ---
indices_for_each_step = []  # Store only indices instead of full datasets
annotation_text_list = []
common_text = "Ratings<br>Count<br>"
unique_ratings = sorted(data['Number of Ratings'].astype(int).unique())
steps = []
num = 20  # Number of initial steps to take directly from unique_ratings

def update_title(filtered_data_df):
    game_count = len(filtered_data_df)
    game_text = "game" if game_count == 1 else "games"
    return f'Game Ratings by Release Date ({game_count} {game_text})'

for i, rating_count_threshold in enumerate(unique_ratings):
    # Determine if this rating_count_threshold should be a slider step
    is_selected_step = False
    if i < num:  # Select the first 'num' unique rating counts
        is_selected_step = True
    elif i == len(unique_ratings) - 1:  # Always select the last unique rating count
        is_selected_step = True
    elif i >= num:  # For ratings after the first 'num'
        num_initial_ratings_for_calc = len(unique_ratings[:num])
        divisor_for_outer_floor_division_float = num_initial_ratings_for_calc / 1.5
        
        if divisor_for_outer_floor_division_float >= 1 and len(unique_ratings[num:]) > 0:
            calculated_interval = len(unique_ratings[num:]) // int(divisor_for_outer_floor_division_float)
            modulo_divisor = max(1, calculated_interval)
            
            if i % modulo_divisor == 0:
                is_selected_step = True

    if is_selected_step:
        # Store only the indices of games that meet the threshold
        indices = data[data['Number of Ratings'] >= rating_count_threshold]['_index'].tolist()
        indices_for_each_step.append(indices)
        
        annotation_text = f'<span style="display: block; text-align: center;">{common_text}<b>({rating_count_threshold})</b></span>'
        annotation_text_list.append(annotation_text)

        step = dict(
            method='skip',
            args=[],
            label=str(rating_count_threshold)
        )
        steps.append(step)

# --- Prepare minimal dataset for JavaScript ---
# Only include necessary columns and convert dates to strings
minimal_data = data[['Title', 'Initial Release Date', 'User Rating', '_index']].copy()
minimal_data['Initial Release Date'] = minimal_data['Initial Release Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
minimal_data_json = minimal_data.to_json(orient='records')

# --- Determine initial data for the plot ---
if indices_for_each_step:
    initial_indices = indices_for_each_step[0]
    initial_plot_data = data.iloc[initial_indices]
    initial_annotation_text = annotation_text_list[0]
else:
    initial_plot_data = data
    initial_annotation_text = f'<span style="display: block; text-align: center;">{common_text}<b>(All)</b></span>'

# --- Create the scatter plot ---
scatter = px.scatter(initial_plot_data, x='Initial Release Date', y='User Rating', hover_name='Title', 
                    hover_data={'Initial Release Date': False, 'User Rating': False})

# Update the marker properties
scatter.update_traces(marker=dict(
    size=5,
    line=dict(width=1, color='black'),
    opacity=0.8
))

# Update layout with sliders if steps were generated
if steps:
    scatter.update_layout(
        sliders=[
            dict(
                active=0, pad={"t": -60}, steps=steps,
                x=0.5, xanchor='left', y=0.5, yanchor='top',
                len=0.4, tickcolor='rgba(0, 0, 0, 0)', ticklen=0,
                font={'color': 'rgba(0, 0, 0, 0)'}
            )
        ]
    )

# Update general layout properties
scatter.update_layout(
    height=600,
    title={
        'text': update_title(initial_plot_data),
        'x': 0.5, 'y': 0.98, 'xanchor': 'center', 'yanchor': 'top'
    },
    xaxis_title=dict(text='Initial Release Date', font=dict(size=14)),
    yaxis_title=dict(text='Rating', font=dict(size=14)),
    xaxis=dict(range=x_range_overall, automargin=True),
    yaxis=dict(range=y_range_overall, automargin=True),
    font=dict(size=18),
    hoverlabel=dict(font_size=16, bgcolor='yellow'),
    margin=dict(t=50),
    annotations=[
        dict(
            text=initial_annotation_text,
            x=1.0725, y=1.02, xref="paper", yref="paper",
            font=dict(size=13, color="black"), showarrow=False
        )
    ],
)

# --- HTML Generation and JavaScript Injection ---
file_path = 'interactive_plot_metacritic.html'
plot_div_id = 'gameScatterPlot'
scatter.write_html(file_path, div_id=plot_div_id, full_html=True, include_plotlyjs='cdn')

with open(file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()
soup = BeautifulSoup(html_content, 'html.parser')

search_input_html = '<input type="text" id="searchInput" placeholder="Search by title..." style="position: fixed; top: 10px; left: 10px; z-index: 1000; padding: 8px; font-size: 14px; width: 250px; border: 1px solid #ccc; border-radius: 4px;">'
soup.body.insert(0, BeautifulSoup(search_input_html, 'html.parser'))

# Embed the full dataset once
full_data_script_tag = soup.new_tag('script', id='fullDatasetJson', type='application/json')
full_data_script_tag.string = minimal_data_json
soup.head.append(full_data_script_tag)

# Embed the indices for each step (much smaller than full datasets)
indices_script_tag = soup.new_tag('script', id='indicesForStepsJson', type='application/json')
indices_script_tag.string = json.dumps(indices_for_each_step)
soup.head.append(indices_script_tag)

js_title_update_logic = """
                function js_update_plot_title(game_count) {
                    const game_text = game_count === 1 ? "game" : "games";
                    return 'Game Ratings by Release Date (' + game_count + ' ' + game_text + ')';
                }
"""

search_and_update_js_logic = f"""
        // --- Search Bar Functionality START ---
        const plotDivId = '{plot_div_id}';
        const graphDiv = document.getElementById(plotDivId);
        const searchInput = document.getElementById('searchInput');
        if (!graphDiv) {{
            console.error('Plotly graph div (#' + plotDivId + ') not found for search functionality.');
        }} else if (!searchInput) {{
            console.error('Search input element not found.');
        }} else {{
            let fullDatasetEl = document.getElementById('fullDatasetJson');
            let indicesForStepsEl = document.getElementById('indicesForStepsJson');
            let fullDataset = [];
            let indicesForSteps = [];
            let original_annotation_texts = {json.dumps(annotation_text_list)};

            // Parse the full dataset
            if (fullDatasetEl && fullDatasetEl.textContent) {{
                try {{
                    fullDataset = JSON.parse(fullDatasetEl.textContent);
                }} catch (e) {{
                    console.error('Error parsing fullDatasetJson:', e);
                }}
            }}

            // Parse the indices for each step
            if (indicesForStepsEl && indicesForStepsEl.textContent) {{
                try {{
                    indicesForSteps = JSON.parse(indicesForStepsEl.textContent);
                }} catch (e) {{
                    console.error('Error parsing indicesForStepsJson:', e);
                }}
            }}

            if (fullDataset.length > 0 && indicesForSteps.length > 0) {{
                {js_title_update_logic}
                
                function updatePlotWithFilters() {{
                    if (!graphDiv.layout || !graphDiv.layout.sliders || graphDiv.layout.sliders.length === 0 || typeof graphDiv.layout.sliders[0].active === 'undefined') {{
                        return;
                    }}
                    
                    const searchTerm = searchInput.value.toLowerCase().trim();
                    const activeSliderIndex = graphDiv.layout.sliders[0].active;

                    if (activeSliderIndex < 0 || activeSliderIndex >= indicesForSteps.length) {{
                        console.error('Active slider index is out of bounds.');
                        return;
                    }}

                    // Get the indices for the current slider position
                    const currentIndices = indicesForSteps[activeSliderIndex];
                    
                    // Filter the full dataset using the indices
                    let games_to_display = fullDataset.filter(game => currentIndices.includes(game._index));

                    // Apply search filter if search term exists
                    if (searchTerm) {{
                        games_to_display = games_to_display.filter(game =>
                            game.Title && typeof game.Title === 'string' && game.Title.toLowerCase().includes(searchTerm)
                        );
                    }}

                    const new_x = games_to_display.map(g => g['Initial Release Date']);
                    const new_y = games_to_display.map(g => g['User Rating']);
                    const new_hovertext = games_to_display.map(g => g.Title);
                    const new_plot_title_text = js_update_plot_title(games_to_display.length);
                    
                    let current_annotation_text = original_annotation_texts[activeSliderIndex] || (original_annotation_texts.length > 0 ? original_annotation_texts[0] : "Info");
                    
                    // Update the plot with filtered data
                    Plotly.restyle(graphDiv, {{
                        x: [new_x], 
                        y: [new_y], 
                        hovertext: [new_hovertext]
                    }}, [0]);
                    
                    Plotly.relayout(graphDiv, {{
                        'title.text': new_plot_title_text,
                        'annotations[0].text': current_annotation_text
                    }});
                }}
                
                // Event listeners
                searchInput.addEventListener('input', function() {{
                    updatePlotWithFilters();
                }});
                
                // Handle slider changes
                graphDiv.on('plotly_sliderchange', function() {{
                    setTimeout(function() {{
                        updatePlotWithFilters();
                    }}, 50);
                }});
                
                let initialFilterCallPending = true;
                function initialFilter() {{
                    if (initialFilterCallPending && graphDiv.layout && graphDiv.layout.sliders && graphDiv.layout.sliders.length > 0 && typeof graphDiv.layout.sliders[0].active !== 'undefined') {{
                        updatePlotWithFilters();
                        initialFilterCallPending = false;
                    }} else if (initialFilterCallPending) {{
                        setTimeout(initialFilter, 100);
                    }}
                }}

                if (graphDiv._fullLayout) {{
                    initialFilter();
                }} else {{
                     graphDiv.on('plotly_afterplot', initialFilter);
                }}
            }}
        }}
        // --- Search Bar Functionality END ---
"""

new_script_tag = soup.new_tag('script')
new_script_tag.string = f"""
    window.onload = function() {{
        var sliderGroup = document.querySelector('.slider-group');
        if (sliderGroup) {{
            sliderGroup.setAttribute('transform', 'rotate(270)translate(-529,1177.5)');
            var observer = new MutationObserver(function(mutations) {{
                if (sliderGroup.getAttribute('transform') !== 'rotate(270)translate(-529,1177.5)') {{
                    sliderGroup.setAttribute('transform', 'rotate(270)translate(-529,1177.5)');
                    setTimeout(function() {{ sliderGroup.style.opacity = 1; }}, 10);
                }}
            }});
            observer.observe(sliderGroup, {{ attributes: true }});
        }}
        
        var style = document.createElement('style');
        style.innerHTML = `.slider-group:hover {{ cursor: ns-resize; }}`;
        document.head.appendChild(style);

        {search_and_update_js_logic}
    }};
"""

# Replace existing onload script if present, otherwise append
existing_script = soup.find('script', string=lambda t: t and 'window.onload' in t and 'sliderGroup' in t)
if existing_script:
    existing_script.replace_with(new_script_tag)
else:
    soup.body.append(new_script_tag)

with open(file_path, 'w', encoding='utf-8') as file:
    file.write(str(soup))

webbrowser.open(file_path)
