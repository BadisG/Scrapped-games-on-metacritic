import pandas as pd
import plotly.express as px
import webbrowser
from bs4 import BeautifulSoup

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

def update_title(filtered_data):
    game_count = len(filtered_data)
    game_text = "game" if game_count == 1 else "games"
    return f'Game Ratings by Release Date ({game_count} {game_text})'

# Update the marker properties
scatter.update_traces(marker=dict(
    size=5,  # Increase the size of the points
    line=dict(width=1, color='black'),  # Add a black border around the points
    opacity=0.8  # Make the points more transparent
))

filtered_data_list = []
annotation_text_list = []

common_text = "Ratings<br>Count<br>"

unique_ratings = sorted(data['Number of Ratings'].astype(int).unique())
steps = []
num = 20  # Seems to be the sweet spot

# Create steps for the first 20 values and the remaining values with a finer step size
for i, rating in enumerate(unique_ratings):
    if i < num or (i >= num and i % (len(unique_ratings[num:]) // (len(unique_ratings[:num])/1.5)) == 0) or i == len(unique_ratings) - 1:
        filtered_data = data.loc[data['Number of Ratings'] >= rating]
        annotation_text = f'<span style="display: block; text-align: center;">{common_text}<b>({rating})</b></span>'
        filtered_data_list.append(filtered_data)
        annotation_text_list.append(annotation_text)
        step = dict(
            method='update',
            args=[
                {'x': [filtered_data['Initial Release Date']], 'y': [filtered_data['User Rating']], 'hovertext': [filtered_data['Title']]},
                {
                    'title': {
                        'text': update_title(filtered_data),
                        'x': 0.5,
                        'y': 0.98,
                        'xanchor': 'center',
                        'yanchor': 'top'
                    },
                    'annotations': [{
                        'text': annotation_text,
                        'x': 1.0725,
                        'y': 1.02,
                        'xref': "paper",
                        'yref': "paper",
                        'font': {'size': 13, 'color': "black"},
                        'showarrow': False
                    }]
                }
            ],
            label=f'{rating}'
        )
        steps.append(step)
        

scatter.update_layout(
    sliders=[
        dict(
            active=0,
            pad={"t": -60},  # Adjust the distance between the slider and the plot if needed
            steps=steps,
            x=0.5,  # Position the slider to the left
            xanchor='left',  # Anchor the slider to the left
            y=0.5,  # Position the slider just below the title
            yanchor='top',
            len=0.4,  # Width of the slider
            tickcolor='rgba(0, 0, 0, 0)',  # Make the bar invisible
            ticklen=0,
            font={'color': 'rgba(0, 0, 0, 0)'}  # Make the text color invisible
        )
    ]
)

scatter.update_layout(
    height=600,
    title={
        'text': update_title(data),
        'x': 0.5,
        'y': 0.98,
        'xanchor': 'center',
        'yanchor': 'top'
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
            text=annotation_text_list[0],
            x=1.0725,
            y=1.02,
            xref="paper",
            yref="paper",
            font=dict(size=13, color="black"),
            showarrow=False
        )
    ],
)


# Save the interactive plot as an HTML file
file_path = 'interactive_plot.html'
scatter.write_html(file_path)

# Inject JavaScript code to modify the slider's properties
with open(file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

soup = BeautifulSoup(html_content, 'html.parser')

script_tag = soup.new_tag('script')
script_tag.string = '''
    window.onload = function() {
        var sliderGroup = document.querySelector('.slider-group');
        sliderGroup.setAttribute('transform', 'rotate(270)translate(-529,1177.5)');
        
        var observer = new MutationObserver(function(mutations) {
            if (sliderGroup.getAttribute('transform') !== 'rotate(270)translate(-529,1177.5)') {
                sliderGroup.setAttribute('transform', 'rotate(270)translate(-529,1177.5)');
                setTimeout(function() {
                    sliderGroup.style.opacity = 1;
                }, 10);
            }
        });
        observer.observe(sliderGroup, { attributes: true });
        
        document.addEventListener('touchmove', function(event) {
            event.preventDefault();
        }, { passive: false });
        
        document.addEventListener('wheel', function(event) {
            event.preventDefault();
        }, { passive: false });
        
        document.body.style.overflow = 'hidden';
        
        var style = document.createElement('style');
        style.innerHTML = `
            .slider-group:hover {
                cursor: ns-resize;
            }
        `;
        document.head.appendChild(style);
    };
'''

soup.body.append(script_tag)

# Save the modification in the HTML file
with open(file_path, 'w', encoding='utf-8') as file:
    file.write(str(soup))

# Open the interactive plot in the web browser
webbrowser.open(file_path)
