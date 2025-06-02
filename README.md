# Scrapped-games-on-metacritic
Retrieves interesting information about games from [metacritic](https://www.metacritic.com/browse/game/all/all/all-time/new/?releaseYearMin=1958&releaseYearMax=2025&page=1)

# 1. games.csv
This file contains all the games's relevant informations (Title + Initial Release + User Rating + Number of Ratings)

It contains all the games on this site until 6/01/2025. Here's what it looks like:

<img src="https://github.com/user-attachments/assets/b78a02bb-fd1c-4caf-98a7-517ae523a34e" width="500" />

# 2. requirements.txt
You need to install some special packages to be able to run the python scripts, here's the command:
```
pip install -r requirements.txt
```

# 3. scrap.py
```
python scrap.py
```
- This is the script used to scrap the games and put all the information into a CSV file (games.csv).

<img src="https://github.com/user-attachments/assets/009535a6-1105-4bf2-a323-4a176de2ce06" width="500" />

# 4. plot.py
```
python plot.py
```
This is an optional python script that can be used to visualize games through a scatter plot:
- It will create a file named ```interactive_plot_metacritic.html```
- It will open that file

# 5. interactive_plot_metacritic.html
This file can be opened with a browser such as Google Chrome or Firefox, and will look like this:

<img src="https://github.com/user-attachments/assets/e0d9b11e-fe3f-4284-a7b2-e2cd965b69b7" width="700" />

- You'll be able to see which game is on each point by hovering your mouse over it.
- If you feel there are too many points, you can filter a little by using a slider that will activate a threshold based on the number of user ratings.
