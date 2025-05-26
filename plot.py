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

# Determine the min and max values for x and y axes from the overall data
# This ensures consistent axis ranges regardless of initially plotted subset
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
python_filtered_data_list_for_js = []
annotation_text_list = []
common_text = "Ratings<br>Count<br>"
unique_ratings = sorted(data['Number of Ratings'].astype(int).unique())
steps = []
num = 20 # Number of initial steps to take directly from unique_ratings

def update_title(filtered_data_df):
    game_count = len(filtered_data_df)
    game_text = "game" if game_count == 1 else "games"
    return f'Game Ratings by Release Date ({game_count} {game_text})'

for i, rating_count_threshold in enumerate(unique_ratings):
    # Determine if this rating_count_threshold should be a slider step
    is_selected_step = False
    if i < num: # Select the first 'num' unique rating counts
        is_selected_step = True
    elif i == len(unique_ratings) - 1: # Always select the last unique rating count
        is_selected_step = True
    elif i >= num: # For ratings after the first 'num'
        # This logic aims to select a subset of remaining ratings to keep slider manageable
        # It calculates an interval based on how many initial ratings were taken vs. remaining
        # Guard against division by zero or ineffective interval
        num_initial_ratings_for_calc = len(unique_ratings[:num]) # Actually used initial ratings count
        
        # Divisor for the outer floor division, derived from the number of initial ratings
        # e.g., if num_initial_ratings_for_calc is 20, 20/1.5 = 13.33
        divisor_for_outer_floor_division_float = num_initial_ratings_for_calc / 1.5
        
        if divisor_for_outer_floor_division_float >= 1 and len(unique_ratings[num:]) > 0:
            # Interval for selecting steps from the ratings_after_num part
            # e.g. len(unique_ratings[num:]) = 980, int(13.33) = 13.  980 // 13 = 75.
            calculated_interval = len(unique_ratings[num:]) // int(divisor_for_outer_floor_division_float)
            modulo_divisor = max(1, calculated_interval) # Ensure divisor for % is at least 1
            
            # We need to check the index `i` relative to the start of the `unique_ratings[num:]` segment.
            # The condition `i % modulo_divisor == 0` is applied to the global index `i`.
            # This might not distribute as intended. A simpler way is np.linspace or fixed number of steps.
            # Given the existing code, let's keep it, assuming it works for the user's data distribution.
            if i % modulo_divisor == 0:
                 is_selected_step = True
        # If the above conditions for interval calculation aren't met, this rating_count_threshold is not selected by this rule.
        # It might have been selected by i < num or i == len(unique_ratings) - 1.

    if is_selected_step:
        filtered_data_for_step = data.loc[data['Number of Ratings'] >= rating_count_threshold]
        annotation_text = f'<span style="display: block; text-align: center;">{common_text}<b>({rating_count_threshold})</b></span>'
        
        python_filtered_data_list_for_js.append(filtered_data_for_step)
        annotation_text_list.append(annotation_text)

        # MODIFICATION 1: Make step args lightweight.
        # Only update title and annotation text directly. Data (x, y, hovertext)
        # will be updated by the JavaScript `plotly_sliderchange` event.
        step = dict(
            method='relayout', # Use 'relayout' as we are only changing layout properties here
            args=[{
                'title.text': update_title(filtered_data_for_step),
                'annotations[0].text': annotation_text # Update text of the first annotation
            }],
            label=str(rating_count_threshold)
        )
        steps.append(step)

# --- Serialize data for JavaScript ---
serializable_filtered_data_list_for_js = []
for df_item in python_filtered_data_list_for_js:
    df_copy = df_item[['Title', 'Initial Release Date', 'User Rating']].copy()
    df_copy['Initial Release Date'] = df_copy['Initial Release Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    serializable_filtered_data_list_for_js.append(df_copy.to_json(orient='records'))

# --- Determine initial data for the plot ---
# MODIFICATION 2: Use data for the first slider step for the initial plot view.
if python_filtered_data_list_for_js:
    initial_plot_data = python_filtered_data_list_for_js[0]
    initial_title_data_source = python_filtered_data_list_for_js[0]
    initial_annotation_text = annotation_text_list[0]
else:
    # Fallback if no steps were generated (e.g., unique_ratings was empty)
    initial_plot_data = data # Use the full (NaN-filtered, sorted) data
    initial_title_data_source = data
    initial_annotation_text = f'<span style="display: block; text-align: center;">{common_text}<b>(All)</b></span>'


# --- Create the scatter plot ---
scatter = px.scatter(initial_plot_data, x='Initial Release Date', y='User Rating', hover_name='Title', hover_data={'Initial Release Date': False, 'User Rating': False})

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
        'text': update_title(initial_title_data_source),
        'x': 0.5, 'y': 0.98, 'xanchor': 'center', 'yanchor': 'top'
    },
    xaxis_title=dict(text='Initial Release Date', font=dict(size=14)),
    yaxis_title=dict(text='Rating', font=dict(size=14)),
    xaxis=dict(range=x_range_overall, automargin=True), # Use overall range
    yaxis=dict(range=y_range_overall, automargin=True), # Use overall range
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
file_path = 'interactive_plot.html'
plot_div_id = 'gameScatterPlot'
scatter.write_html(file_path, div_id=plot_div_id, full_html=True, include_plotlyjs='cdn')

with open(file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()
soup = BeautifulSoup(html_content, 'html.parser')

search_input_html = '<input type="text" id="searchInput" placeholder="Search by title..." style="position: fixed; top: 10px; left: 10px; z-index: 1000; padding: 8px; font-size: 14px; width: 250px; border: 1px solid #ccc; border-radius: 4px;">'
soup.body.insert(0, BeautifulSoup(search_input_html, 'html.parser'))

data_list_script_tag = soup.new_tag('script', id='filteredDataListJson', type='application/json')
data_list_script_tag.string = json.dumps(serializable_filtered_data_list_for_js)
soup.head.append(data_list_script_tag)

js_title_update_logic = """
                function js_update_plot_title(game_count) {
                    const game_text = game_count === 1 ? "game" : "games";
                    return 'Game Ratings by Release Date (' + game_count + ' ' + game_text + ')';
                }
"""

# Prepare original_slider_values for JS (ensure it matches the `label` of the steps)
js_original_slider_values = []
if steps: # Only if steps were actually created
    js_original_slider_values = [step['label'] for step in steps]


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
            let datasets_for_slider_steps_str_el = document.getElementById('filteredDataListJson');
            let datasets_for_slider_steps = [];
            let original_annotation_texts = {json.dumps(annotation_text_list)};
            // let original_slider_values = {json.dumps(js_original_slider_values)}; // Not directly used in this JS logic, but good for debugging

            if (datasets_for_slider_steps_str_el && datasets_for_slider_steps_str_el.textContent) {{
                try {{
                    datasets_for_slider_steps = JSON.parse(datasets_for_slider_steps_str_el.textContent).map(s => JSON.parse(s));
                }} catch (e) {{
                    console.error('Error parsing filteredDataListJson:', e);
                    datasets_for_slider_steps = null; 
                }}
            }} else {{
                console.warn('filteredDataListJson script tag not found or empty. Search/slider might not work if datasets are expected.');
                datasets_for_slider_steps = null;
            }}

            if (datasets_for_slider_steps && datasets_for_slider_steps.length > 0) {{ // Check if data is available
                {js_title_update_logic}
                function updatePlotWithFilters() {{
                    if (!graphDiv.layout || !graphDiv.layout.sliders || graphDiv.layout.sliders.length === 0 || typeof graphDiv.layout.sliders[0].active === 'undefined') {{
                        // console.warn('Slider or active index not found, cannot update plot based on slider.');
                        // If no slider, maybe just filter based on search if datasets_for_slider_steps[0] exists?
                        // For now, we assume slider is present if this function is central.
                        return;
                    }}
                    const searchTerm = searchInput.value.toLowerCase();
                    const activeSliderIndex = graphDiv.layout.sliders[0].active;

                    if (activeSliderIndex < 0 || activeSliderIndex >= datasets_for_slider_steps.length) {{
                        console.error('Active slider index (' + activeSliderIndex + ') is out of bounds for datasets_for_slider_steps (len: ' + datasets_for_slider_steps.length + ').');
                        return;
                    }}

                    const current_slider_dataset = datasets_for_slider_steps[activeSliderIndex];
                    let games_to_display = current_slider_dataset;

                    if (searchTerm) {{
                        games_to_display = current_slider_dataset.filter(game =>
                            game.Title && typeof game.Title === 'string' && game.Title.toLowerCase().includes(searchTerm)
                        );
                    }}

                    const new_x = games_to_display.map(g => g['Initial Release Date']);
                    const new_y = games_to_display.map(g => g['User Rating']);
                    const new_hovertext = games_to_display.map(g => g.Title);
                    const new_plot_title_text = js_update_plot_title(games_to_display.length);
                    
                    let current_annotation_text = original_annotation_texts[activeSliderIndex] || (original_annotation_texts.length > 0 ? original_annotation_texts[0] : "Info");
                    
                    Plotly.restyle(graphDiv, {{
                        x: [new_x], y: [new_y], hovertext: [new_hovertext]
                    }}, [0]); // Update data of the first trace
                    
                    Plotly.relayout(graphDiv, {{
                        'title.text': new_plot_title_text,
                        'annotations[0].text': current_annotation_text
                    }});
                }}
                
                searchInput.addEventListener('input', updatePlotWithFilters);
                graphDiv.on('plotly_sliderchange', updatePlotWithFilters);
                
                let initialFilterCallPending = true;
                function initialFilter() {{
                    if (initialFilterCallPending && graphDiv.layout && graphDiv.layout.sliders && graphDiv.layout.sliders.length > 0 && typeof graphDiv.layout.sliders[0].active !== 'undefined') {{
                        updatePlotWithFilters(); // Call it once to sync with initial slider state
                        initialFilterCallPending = false;
                    }} else if (initialFilterCallPending && !(graphDiv.layout && graphDiv.layout.sliders && graphDiv.layout.sliders.length > 0)) {{
                        // No slider, but maybe datasets_for_slider_steps has data for a non-slider view
                        // This part might need adjustment if the plot can exist without a slider but still use datasets_for_slider_steps[0]
                        // For now, assume slider is primary driver if datasets_for_slider_steps is populated
                        // updatePlotWithFilters(); // Or a modified version for no-slider case
                        // initialFilterCallPending = false;
                        // console.log("No slider found, initial filter might not apply as expected.")
                    }}
                     else if (initialFilterCallPending) {{
                        setTimeout(initialFilter, 100); // Wait for layout to be ready
                    }}
                }}

                if (graphDiv._fullLayout) {{ // If layout is already there
                    initialFilter();
                }} else {{
                     graphDiv.on('plotly_afterplot', initialFilter); // Wait for plot to render
                }}
            }} else {{
                 // console.warn("datasets_for_slider_steps is null or empty. Search and slider updates will not function.");
                 // Add basic search for non-slider case if needed, operating on graphDiv.data[0]
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
        }} else {{
            // console.warn("Slider group '.slider-group' not found for transform adjustments.");
        }}
        
        // These prevent scrolling on the page, which might be desired for a full-screen plot
        // document.addEventListener('touchmove', function(event) {{ event.preventDefault(); }}, {{ passive: false }});
        // document.addEventListener('wheel', function(event) {{ event.preventDefault(); }}, {{ passive: false }});
        // document.body.style.overflow = 'hidden';
        
        var style = document.createElement('style');
        style.innerHTML = `.slider-group:hover {{ cursor: ns-resize; }}`; // ns-resize for vertical slider illusion
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
