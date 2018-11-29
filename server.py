#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver
To run locally
    python server.py
Go to http://localhost:8111 in your browser
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, flash, session, abort

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)



# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "jm4456"
DB_PASSWORD = "yfrrdp47"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request
  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


  """
 Brings up login page or homepage
  """
@app.route('/')
def home():
  if not session.get('logged_in'):
      return render_template('login.html')
  else:
      return homepage()

@app.route('/login', methods=['POST'])
def login():
  '''
Login page
  '''
  if request.form['password'] == 'password' and request.form['username'] == 'Abraham':
        session['logged_in'] = True
        return homepage(1, 1)
  else:
      flash('wrong password!')
  return home()


  """
 Goes to homepage
  """
@app.route('/home/uid=<int:uid>/lid=<int:lid>')
def homepage(uid, lid):
  print request.args

  # get my username
  get_username = text("SELECT name FROM users WHERE uid = :x")
  cursor = g.conn.execute(get_username, x=uid)
  username = ""
  for result in cursor:
    username = result['name']
  cursor.close()

  # get my fantasy team
  get_fantasyteam = text("SELECT fantasy_name FROM manage WHERE uid=:x LIMIT 1")
  cursor = g.conn.execute(get_fantasyteam, x=uid)
  fantasy_team = ""
  for result in cursor:
    fantasy_team = result['fantasy_name']
  cursor.close()

  # get my record
  s = text("SELECT wins, losses FROM fantasyteam_in WHERE name= :x")
  cursor = g.conn.execute(s, x=fantasy_team)
  wins = ""
  losses = ""
  for result in cursor:
    wins = result['wins']
    losses = result['losses']
  cursor.close()


  return render_template("home.html", uid=uid, lid=lid, username=username, fantasy_team=fantasy_team, wins=wins, losses=losses)


'''
Information about my team
'''
@app.route('/myteam/uid=<int:uid>/lid=<int:lid>')
def myteam(uid, lid):

  print request.args

  # get my fantasy team
  get_fantasyteam = text("SELECT fantasy_name FROM manage WHERE uid=:x AND lid=:y")
  cursor = g.conn.execute(get_fantasyteam, x=uid, y=lid)
  fantasy_team = ""
  for result in cursor:
    fantasy_team = result['fantasy_name']
  cursor.close()

  # get players in my team
  get_players = text("SELECT P.number, P.player_name, P.team_name FROM players_play as P, draft as D WHERE lid=:x and fantasy_name=:y and P.number=D.number and P.team_name=D.team_name")
  cursor = g.conn.execute(get_players, x=lid, y=fantasy_team)
  numbers = []
  names = []
  team = []
  for result in cursor:
    numbers.append(result['number'])
    names.append(result['player_name'])
    team.append(result['team_name'])
  cursor.close()

  # get my username
  cursor = g.conn.execute("SELECT name FROM users LIMIT 1")
  username = ""
  for result in cursor:
    username = result['name']
  cursor.close()

  player_dict = {}
  for i in range(len(numbers)):
    player_dict[(numbers[i],team[i])] = names[i]

  return render_template("myteam.html", player_dict = player_dict, username=username, uid=uid, lid=lid)


'''
Information about the league I am in
'''
@app.route('/league/uid=<int:uid>/lid=<int:lid>')
def league(uid, lid):
  # get team records from the league
  get_records = text("SELECT name, wins, losses FROM fantasyteam_in WHERE lid=:x")
  cursor = g.conn.execute(get_records, x=lid)
  team = {}
  for result in cursor:
    team[result['name']] = (result['wins'] , result['losses'])
  cursor.close()

  # get my fantasy team
  get_fantasyteam = text("SELECT DISTINCT fantasy_name FROM manage WHERE uid=:x AND lid=:y LIMIT 1")
  cursor = g.conn.execute(get_fantasyteam, x=uid, y=lid)
  fantasy_team = ""
  for result in cursor:
    fantasy_team = result['fantasy_name']
  cursor.close()

  
  return render_template("league.html", team=team, fantasy_team=fantasy_team, uid=uid, lid=lid)

'''
Opens players tab
'''
@app.route('/players/uid=<int:uid>/lid=<int:lid>')
def players(uid, lid):

  return render_template("players.html", uid=uid, lid=lid)

'''
Displays NFL teams
'''
@app.route('/nfl/uid=<int:uid>/lid=<int:lid>')
def nfl(uid, lid):

#get nfl teams
  get_nfl = text("SELECT name, location FROM team")
  cursor = g.conn.execute(get_nfl)
  nfl_teams = {}
  for result in cursor:
    nfl_teams[result['name']] = result['location']
  cursor.close()

  return render_template("nfl.html", uid=uid, lid=lid, nfl_teams=nfl_teams)


'''
Statistics for a given team
'''
@app.route('/teamsplayers/uid=<int:uid>/lid=<int:lid>', methods=['POST'])
def teamsplayers(uid, lid):

  # get players in team
  get_players = text("SELECT number, player_name, height, weight FROM players_play WHERE team_name=:t")
  cursor = g.conn.execute(get_players, t=request.form['team'])
  players = []
  for result in cursor:
    players.append((result['number'],result['player_name'],result['height'],result['weight']))
  cursor.close()

  return render_template("teamsplayers.html", uid=uid, lid=lid, players=players)


'''
Statistics for a given player
'''
@app.route('/playerstats/uid=<int:uid>/lid=<int:lid>', methods=['POST'])
def playerstats(uid, lid):

  team = request.form['team']
  number = request.form['number']
  #get player name
  get_name = text("SELECT DISTINCT player_name FROM players_play WHERE team_name=:t AND number=:n")
  cursor = g.conn.execute(get_name, t=team, n=number)
  for result in cursor:
    name = result['player_name']
  cursor.close()

  # get stats of player
  get_stats = text("SELECT catching_all, rushing_all, passing_all, touchdowns_all FROM offensive WHERE team_name=:t AND number=:n")
  cursor = g.conn.execute(get_stats, t=request.form['team'], n=request.form['number'])
  stats = []
  for result in cursor:
    stats.append(result['catching_all'])
    stats.append(result['rushing_all'])
    stats.append(result['passing_all'])
    stats.append(result['touchdowns_all'])
  cursor.close()

  return render_template("playerstats.html", uid=uid, lid=lid, team=team, number=number, name=name, stats=stats)

'''
Top 5 statistics
'''
@app.route('/td/uid=<int:uid>/lid=<int:lid>', methods=['GET'])
def td(uid, lid):

  # get stats of top 5 players
  top_stats = text("SELECT P.player_name, P.team_name, P.number, O.touchdowns_all FROM offensive as O, players_play as P WHERE P.team_name=O.team_name AND P.number=O.number ORDER BY O.touchdowns_all DESC LIMIT 5")
  cursor = g.conn.execute(top_stats)
  topstats = {}
  for result in cursor:
    topstats[(result['team_name'], result['number'])] = (result['player_name'], result['touchdowns_all'])
  cursor.close()

  return render_template("td.html", uid=uid, lid=lid, topstats=topstats)

@app.route('/passing/uid=<int:uid>/lid=<int:lid>', methods=['GET'])
def passing(uid, lid):

  # get stats of top 5 players
  top_stats = text("SELECT P.player_name, P.team_name, P.number, O.passing_all FROM offensive as O, players_play as P WHERE P.team_name=O.team_name AND P.number=O.number ORDER BY O.passing_all DESC LIMIT 5")
  cursor = g.conn.execute(top_stats)
  topstats = {}
  for result in cursor:
    topstats[(result['team_name'], result['number'])] = (result['player_name'], result['passing_all'])
  cursor.close()

  return render_template("passing.html", uid=uid, lid=lid, topstats=topstats)

@app.route('/catching/uid=<int:uid>/lid=<int:lid>', methods=['GET'])
def catching(uid, lid):

  # get stats of top 5 players
  top_stats = text("SELECT P.player_name, P.team_name, P.number, O.catching_all FROM offensive as O, players_play as P WHERE P.team_name=O.team_name AND P.number=O.number ORDER BY O.catching_all DESC LIMIT 5")
  cursor = g.conn.execute(top_stats)
  topstats = {}
  for result in cursor:
    topstats[(result['team_name'], result['number'])] = (result['player_name'], result['catching_all'])
  cursor.close()

  return render_template("catching.html", uid=uid, lid=lid, topstats=topstats)

@app.route('/rushing/uid=<int:uid>/lid=<int:lid>', methods=['GET'])
def rushing(uid, lid):

  # get stats of top 5 players
  top_stats = text("SELECT P.player_name, P.team_name, P.number, O.rushing_all FROM offensive as O, players_play as P WHERE P.team_name=O.team_name AND P.number=O.number ORDER BY O.rushing_all DESC LIMIT 5")
  cursor = g.conn.execute(top_stats)
  topstats = {}
  for result in cursor:
    topstats[(result['team_name'], result['number'])] = (result['player_name'], result['rushing_all'])
  cursor.close()

  return render_template("rushing.html", uid=uid, lid=lid, topstats=topstats)


@app.route('/comparetd/uid=<int:uid>/lid=<int:lid>', methods=['GET'])
def comparetd(uid, lid):

  team = request.args.get('team')
  number = request.args.get('number')

  #get player name
  get_name = text("SELECT DISTINCT player_name FROM players_play WHERE team_name=:t AND number=:n")
  cursor = g.conn.execute(get_name, t=team, n=number)
  for result in cursor:
    name = result['player_name']
  cursor.close()

  # get stats of player
  get_stats = text("SELECT catching_all, rushing_all, passing_all, touchdowns_all FROM offensive WHERE team_name=:t AND number=:n")
  cursor = g.conn.execute(get_stats, t=team, n=number)
  stats = []
  for result in cursor:
    stats.append(result['catching_all'])
    stats.append(result['rushing_all'])
    stats.append(result['passing_all'])
    stats.append(result['touchdowns_all'])
  cursor.close()

  # get stats of top 5 players
  top_stats = text("SELECT P.player_name, P.team_name, P.number, O.touchdowns_all FROM offensive as O, players_play as P WHERE P.team_name=O.team_name AND P.number=O.number ORDER BY O.touchdowns_all DESC LIMIT 5")
  cursor = g.conn.execute(top_stats)
  topstats = {}
  for result in cursor:
    topstats[(result['team_name'], result['number'])] = (result['player_name'], result['touchdowns_all'])
  cursor.close()

  return render_template("comparetd.html", uid=uid, lid=lid, team=team, number=number, name=name, stats=stats, topstats=topstats)

@app.route('/comparepass/uid=<int:uid>/lid=<int:lid>', methods=['GET'])
def comparepass(uid, lid):

  team = request.args.get('team')
  number = request.args.get('number')

  #get player name
  get_name = text("SELECT DISTINCT player_name FROM players_play WHERE team_name=:t AND number=:n")
  cursor = g.conn.execute(get_name, t=team, n=number)
  for result in cursor:
    name = result['player_name']
  cursor.close()

  # get stats of player
  get_stats = text("SELECT catching_all, rushing_all, passing_all, touchdowns_all FROM offensive WHERE team_name=:t AND number=:n")
  cursor = g.conn.execute(get_stats, t=team, n=number)
  stats = []
  for result in cursor:
    stats.append(result['catching_all'])
    stats.append(result['rushing_all'])
    stats.append(result['passing_all'])
    stats.append(result['touchdowns_all'])
  cursor.close()

  # get stats of top 5 players
  top_stats = text("SELECT P.player_name, P.team_name, P.number, O.passing_all FROM offensive as O, players_play as P WHERE P.team_name=O.team_name AND P.number=O.number ORDER BY O.passing_all DESC LIMIT 5")
  cursor = g.conn.execute(top_stats)
  topstats = {}
  for result in cursor:
    topstats[(result['team_name'], result['number'])] = (result['player_name'], result['passing_all'])
  cursor.close()

  return render_template("comparepass.html", uid=uid, lid=lid, team=team, number=number, name=name, stats=stats, topstats=topstats)

@app.route('/comparecatch/uid=<int:uid>/lid=<int:lid>', methods=['GET'])
def comparecatch(uid, lid):

  team = request.args.get('team')
  number = request.args.get('number')
  
  #get player name
  get_name = text("SELECT DISTINCT player_name FROM players_play WHERE team_name=:t AND number=:n")
  cursor = g.conn.execute(get_name, t=team, n=number)
  for result in cursor:
    name = result['player_name']
  cursor.close()

  # get stats of player
  get_stats = text("SELECT catching_all, rushing_all, passing_all, touchdowns_all FROM offensive WHERE team_name=:t AND number=:n")
  cursor = g.conn.execute(get_stats, t=team, n=number)
  stats = []
  for result in cursor:
    stats.append(result['catching_all'])
    stats.append(result['rushing_all'])
    stats.append(result['passing_all'])
    stats.append(result['touchdowns_all'])
  cursor.close()

  # get stats of top 5 players
  top_stats = text("SELECT P.player_name, P.team_name, P.number, O.catching_all FROM offensive as O, players_play as P WHERE P.team_name=O.team_name AND P.number=O.number ORDER BY O.catching_all DESC LIMIT 5")
  cursor = g.conn.execute(top_stats)
  topstats = {}
  for result in cursor:
    topstats[(result['team_name'], result['number'])] = (result['player_name'], result['catching_all'])
  cursor.close()

  return render_template("comparecatch.html", uid=uid, lid=lid, team=team, number=number, name=name, stats=stats, topstats=topstats)

@app.route('/comparerush/uid=<int:uid>/lid=<int:lid>', methods=['GET'])
def comparerush(uid, lid):

  team = request.args.get('team')
  number = request.args.get('number')
  
  #get player name
  get_name = text("SELECT DISTINCT player_name FROM players_play WHERE team_name=:t AND number=:n")
  cursor = g.conn.execute(get_name, t=team, n=number)
  for result in cursor:
    name = result['player_name']
  cursor.close()

  # get stats of player
  get_stats = text("SELECT catching_all, rushing_all, passing_all, touchdowns_all FROM offensive WHERE team_name=:t AND number=:n")
  cursor = g.conn.execute(get_stats, t=team, n=number)
  stats = []
  for result in cursor:
    stats.append(result['catching_all'])
    stats.append(result['rushing_all'])
    stats.append(result['passing_all'])
    stats.append(result['touchdowns_all'])
  cursor.close()

  # get stats of top 5 players
  top_stats = text("SELECT P.player_name, P.team_name, P.number, O.rushing_all FROM offensive as O, players_play as P WHERE P.team_name=O.team_name AND P.number=O.number ORDER BY O.rushing_all DESC LIMIT 5")
  cursor = g.conn.execute(top_stats)
  topstats = {}
  for result in cursor:
    topstats[(result['team_name'], result['number'])] = (result['player_name'], result['rushing_all'])
  cursor.close()

  return render_template("comparerush.html", uid=uid, lid=lid, team=team, number=number, name=name, stats=stats, topstats=topstats)



# Add player to my fantasy team
@app.route('/add/uid=<int:uid>/lid=<int:lid>', methods=['POST'])
def add(uid, lid):

  # get my fantasy team
  get_fantasyteam = text("SELECT DISTINCT fantasy_name FROM manage WHERE uid=:x AND lid=:y LIMIT 1")
  cursor = g.conn.execute(get_fantasyteam, x=uid, y=lid)
  fantasy_team = ""
  for result in cursor:
    fantasy_team = result['fantasy_name']
  cursor.close()

  tnumber = request.form['number']
  team = request.form['team']
  cmd = 'INSERT INTO draft(number,team_name,fantasy_name,lid) VALUES (:num, :t, :f, :l)';
  g.conn.execute(text(cmd), num = tnumber, t = team, f=fantasy_team, l=lid);
  return myteam(uid,lid)

# Remove player to my fantasy team
@app.route('/remove/uid=<int:uid>/lid=<int:lid>', methods=['POST'])
def remove(uid, lid):

  # get my fantasy team
  get_fantasyteam = text("SELECT DISTINCT fantasy_name FROM manage WHERE uid=:x AND lid=:y LIMIT 1")
  cursor = g.conn.execute(get_fantasyteam, x=uid, y=lid)
  fantasy_team = ""
  for result in cursor:
    fantasy_team = result['fantasy_name']
  cursor.close()

  tnumber = request.form['number']
  team = request.form['team']
  cmd = 'DELETE FROM draft WHERE number=:num AND team_name=:t';
  g.conn.execute(text(cmd), num = tnumber, t = team);
  
  return myteam(uid,lid)

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using
        python server.py
    Show the help text using
        python server.py --help
    """

    app.secret_key = os.urandom(12)
    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


run()