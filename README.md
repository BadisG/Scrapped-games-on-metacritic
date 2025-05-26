# Scrapped-games-on-metacritic
Retrieves interesting information about games from [metacritic](https://www.metacritic.com/browse/game/all/all/all-time/userscore/?releaseYearMin=1958&releaseYearMax=2025&page=1)

# 1. dataset_metacritic_scraper.csv

This raw file contains all the information on all Metacritic games. You can download it here:
https://www.kaggle.com/datasets/zaireali/metacritic-games-scrape/data

# 2. requirements.txt
You need to install some special packages to be able to run the python scripts, here's the command:
```
pip install -r requirements.txt
```

# 3. clean_csv.py
This file simplifies and filters **dataset_metacritic_scraper.csv** to make a file named **games.csv**. 

To use it, both the csv and the python script must be on the same folder:
```
python clean_csv.py
```

# 4. games.csv
This file contains all the games's relevant informations (Title + User Ratings + Number of Ratings + Date of Release + Console)

It contains all the games on this site until 2/15/2025. Here's what it looks like:

<img src="https://github.com/user-attachments/assets/f99181d2-9169-45b1-b219-51277f8a15c4" width="500" />

# 5. plot.py
```
python plot.py
```
This is an optional python script that can be used to visualize games through a scatter plot:
- It will create a file named ```interactive_plot.html```
- It will open that file

# 6. interactive_plot_metacritic.html
This file can be opened with a browser such as Google Chrome or Firefox, and will look like this:

<img src="https://github.com/user-attachments/assets/e0d9b11e-fe3f-4284-a7b2-e2cd965b69b7" width="700" />

- You'll be able to see which game is on each point by hovering your mouse over it.
- If you feel there are too many points, you can filter a little by using a slider that will activate a threshold based on the number of user ratings.
