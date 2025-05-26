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

# Determine the min and max values for x and y axes
min_date = data['Initial Release Date'].min()
max_date = data['Initial Release Date'].max()
min_rating = data['User Rating'].min()
max_rating = data['User Rating'].max()

# Calculate margins for x and y axes
x_margin = (max_date - min_date).total_seconds() * 0.025
y_margin = (max_rating - min_rating) * 0.06

# Convert x_margin from seconds to timedelta
x_margin = pd.Timedelta(seconds=x_margin)

# Calculate ranges for x and y axes
x_range = [min_date - x_margin, max_date + x_margin]
y_range = [min_rating - y_margin, max_rating + y_margin]

# Create the scatter plot using Plotly
scatter = px.scatter(data, x='Initial Release Date', y='User Rating', hover_name='Title', hover_data={'Initial Release Date': False, 'User Rating': False})

def update_title(filtered_data_df):
    game_count = len(filtered_data_df)
    game_text = "game" if game_count == 1 else "games"
    return f'Game Ratings by Release Date ({game_count} {game_text})'

# Update the marker properties
scatter.update_traces(marker=dict(
    size=5,
    line=dict(width=1, color='black'),
    opacity=0.8
))

python_filtered_data_list_for_js = []
annotation_text_list = []
common_text = "Ratings<br>Count<br>"
unique_ratings = sorted(data['Number of Ratings'].astype(int).unique())
steps = []
num = 20

for i, rating in enumerate(unique_ratings):
    if i < num or (i >= num and i % (len(unique_ratings[num:]) // (len(unique_ratings[:num])/1.5)) == 0) or i == len(unique_ratings) - 1:
        filtered_data_for_step = data.loc[data['Number of Ratings'] >= rating]
        annotation_text = f'<span style="display: block; text-align: center;">{common_text}<b>({rating})</b></span>'
        
        python_filtered_data_list_for_js.append(filtered_data_for_step)
        annotation_text_list.append(annotation_text)

        step = dict(
            method='relayout',
            args=[
                {'x': [filtered_data_for_step['Initial Release Date']], 'y': [filtered_data_for_step['User Rating']], 'hovertext': [filtered_data_for_step['Title']]},
                {
                    'title': {
                        'text': update_title(filtered_data_for_step),
                        'x': 0.5, 'y': 0.98, 'xanchor': 'center', 'yanchor': 'top'
                    },
                    'annotations': [{
                        'text': annotation_text, 'x': 1.0725, 'y': 1.02,
                        'xref': "paper", 'yref': "paper",
                        'font': {'size': 13, 'color': "black"}, 'showarrow': False
                    }]
                }
            ],
            label=f'{rating}'
        )
        steps.append(step)

serializable_filtered_data_list_for_js = []
for df_item in python_filtered_data_list_for_js:
    df_copy = df_item[['Title', 'Initial Release Date', 'User Rating']].copy()
    df_copy['Initial Release Date'] = df_copy['Initial Release Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    serializable_filtered_data_list_for_js.append(df_copy.to_json(orient='records'))

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

initial_title_data_source = data
if python_filtered_data_list_for_js:
    initial_title_data_source = python_filtered_data_list_for_js[0]

initial_annotation_text = f'<span style="display: block; text-align: center;">{common_text}<b>(All)</b></span>'
if annotation_text_list:
    initial_annotation_text = annotation_text_list[0]

scatter.update_layout(
    height=600,
    title={
        'text': update_title(initial_title_data_source),
        'x': 0.5, 'y': 0.98, 'xanchor': 'center', 'yanchor': 'top'
    },
    xaxis_title=dict(text='Initial Release Date', font=dict(size=14)),
    yaxis_title=dict(text='Rating', font=dict(size=14)),
    xaxis=dict(range=x_range, automargin=True),
    yaxis=dict(range=y_range, automargin=True),
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
            let original_slider_values = {json.dumps([str(rating) for i, rating in enumerate(unique_ratings) if i < num or (i >= num and i % (len(unique_ratings[num:]) // (len(unique_ratings[:num])/1.5)) == 0) or i == len(unique_ratings) - 1])};
            
            if (datasets_for_slider_steps_str_el && datasets_for_slider_steps_str_el.textContent) {{
                try {{
                    datasets_for_slider_steps = JSON.parse(datasets_for_slider_steps_str_el.textContent).map(s => JSON.parse(s));
                }} catch (e) {{
                    console.error('Error parsing filteredDataListJson:', e);
                    datasets_for_slider_steps = null; 
                }}
            }} else {{
                console.error('filteredDataListJson script tag not found or empty.');
                datasets_for_slider_steps = null;
            }}
            if (datasets_for_slider_steps) {{
                {js_title_update_logic}
                function updatePlotWithFilters() {{
                    if (!graphDiv.layout || !graphDiv.layout.sliders || graphDiv.layout.sliders.length === 0 || typeof graphDiv.layout.sliders[0].active === 'undefined') {{
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
                    
                    // Update the annotation with the current slider's rating count
                    let current_annotation_text = original_annotation_texts[activeSliderIndex] || original_annotation_texts[0];
                    
                    Plotly.restyle(graphDiv, {{
                        x: [new_x], y: [new_y], hovertext: [new_hovertext]
                    }}, [0]);
                    
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
        }} else {{
            // console.warn("Slider group '.slider-group' not found for transform adjustments.");
        }}
        
        document.addEventListener('touchmove', function(event) {{ event.preventDefault(); }}, {{ passive: false }});
        document.addEventListener('wheel', function(event) {{ event.preventDefault(); }}, {{ passive: false }});
        document.body.style.overflow = 'hidden';
        
        var style = document.createElement('style');
        style.innerHTML = `.slider-group:hover {{ cursor: ns-resize; }}`;
        document.head.appendChild(style);

        {search_and_update_js_logic}
    }};
"""

existing_script = soup.find('script', string=lambda t: t and 'window.onload' in t and 'sliderGroup' in t)
if existing_script:
    existing_script.replace_with(new_script_tag)
else:
    soup.body.append(new_script_tag)

with open(file_path, 'w', encoding='utf-8') as file:
    file.write(str(soup))

webbrowser.open(file_path)
