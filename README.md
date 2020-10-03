# flask_riotAPI_leaguestats
Proof-of-concept website inspired by op.gg, written by myself from scratch


# What is this?
A website that you can run locally or on a server which takes a summoner name and server as input and gives you stats for your League of Legends account. 

# How do I set it up?
After installing all dependencies open a CMD or shell in the folder where flask_app.py is located and use the following commands:

Windows:
set FLASK_ENV=production
set FLASK_APP=flask_app.py
python -m flask run

Linux:
export FLASK_ENV=development
export FLASK_APP=flask_app.py
python3 -m flask run

Then open a browser and open the URL shown in the terminal.
I also host this website on Pythonanywhere, it was pretty easy to set up.

# Stats
- Account overview stuff like acc lvl, current rank, amount games played, winrate, ...
- Mastery list that includes every champ and if you still can get a chest for it this season
- Overview of the last 5 games played with information such as cs, avg cs / min, cs / min compared to lane opponent, items bought, wards placed / killed, ...
- Live Game overview if you are currently ingame (shows all champions picked, their talents, mastery, acc levels, ranks, ...)

The live game overview is a bit buggy it doesn't throw errors but sometimes even though a summoner is currently ingame it shows that he is not ingame.
Might fix it someday but my code became one huge mess and I really hate every second I spend debugging it lmao.
