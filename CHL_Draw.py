import pandas as pd
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

from pyomo.environ import *
import logging
logging.getLogger('pyomo.core').setLevel(logging.ERROR)

########################################################## DATA ################################################################

teamData = pd.read_csv('TeamData.csv')
potData = pd.read_csv('PotData.csv')

class team():
  def __init__(self,id,Name,Country,League,Pot,OQ,Group=0):
    self.id = id                                                        # for mapping with model variables
    self.Name = Name
    self.Country =Country
    self.League = League
    self.Pot = Pot
    self.OQ = OQ
    self.Group = Group

Teams = {}

for indx in range(teamData.shape[0]):
  Name = teamData.loc[indx,'Team']
  Country = teamData.loc[indx,'Country']
  League = teamData.loc[indx,'League']
  OQf = teamData.loc[indx,'Olympic Qualified']

  for col in potData.columns:
    if Name in list(potData[col]):
      Pot = col

  Teams.update({Name:team(indx,Name,Country,League,Pot,OQf)})

G = int(len(Teams.keys())/3)
Groups = {}
for i in range(G):
  Groups.update({i+1:[]})

teamList = list(Teams.keys())
groupList = list(Groups.keys())

######################################################### FUNCTIONS ##################################################################

def give_feasible(model,team):
    feasible_groups = []

    for g in range(1,G+1):
        model.test_constraints = ConstraintList()
        model.test_constraints.add(model.x[Teams[team].id,g] == 1)
        res = minotaur.solve(model)
        if res.Solver.Status.value == 'ok':
            feasible_groups.append(g)
        model.del_component(model.test_constraints)
        model.del_component(model.test_constraints_index)

    return feasible_groups

########################################################## LP MODEL ################################################################

model = ConcreteModel()

N = len(Teams)               # Number of teams
G = int(N/3)                 # Number of Groups

model.x = Var(np.arange(N),np.arange(1,G+1),domain=Binary)

model.constraint = ConstraintList()

# Team-group constraints

for i in range(N):
    varsum = 0
    for g in range(1,G+1):
        varsum += model.x[i,g]
    model.constraint.add(expr = varsum == 1)

# pot constraints

for g in range(1,G+1):
    for pot in potData.columns:
        varsum = 0
        for Name in Teams.keys():
            if Teams[Name].Pot == pot:
                varsum += model.x[Teams[Name].id,g]
        model.constraint.add(expr = varsum == 1)

# olympic qualified constraints

for g in range(1,G+1):
    varsum = 0
    for Name in Teams.keys():
        if Teams[Name].OQ == True:
            varsum += model.x[Teams[Name].id,g]
    model.constraint.add(expr = varsum <= 1)

# league constraints

leagues = teamData['League'].unique()

for g in range(1,G+1):
    for league in leagues:
        varsum = 0
        for Name in Teams.keys():
            if Teams[Name].League == league:
                varsum += model.x[Teams[Name].id,g]
        model.constraint.add(expr = varsum <= 1)

model.selection_constraints = ConstraintList()

minotaur = SolverFactory("mbnb", executable='./mbin/mbnb')


########################################################## APP ################################################################

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    html.H1("CHL Draw",style={'textAlign':'center'}),
    html.Br(),
    
    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id='team-dropdown',
                options=[{'label': team , 'value': team} for team in teamList],
                placeholder="Select a team",
            ),
            width=3
        ),
        dbc.Col(
            dcc.Dropdown(
                id='group-dropdown',
                options=[{'label': f'Group {group}', 'value': group} for group in groupList],
                placeholder="Select a group",
            ),
            width=3
        ),
    ]),

    html.Div(id='feasible-groups'),
    
    html.Button('Show Feasible', id='show-feasible', n_clicks=0, className='mt-3 mb-3'),

    html.Div([],style={'display':'inline-block','width':'1000px'}),

    html.Button('Assign', id='assign-button', n_clicks=0, className='mt-3 mb-3'),

    dbc.Row(id='group-boxes')
])

@app.callback(
    Output('group-boxes', 'children'),
    Output('team-dropdown','options'),
    Output('group-dropdown','options'),
    Input('assign-button', 'n_clicks'),
    State('team-dropdown', 'value'),
    State('group-dropdown', 'value')
)
def update_assignments(n_clicks, selected_team, selected_group):
    if n_clicks > 0 and selected_team and selected_group:

        Groups[selected_group].append(selected_team)
        teamList.remove(selected_team)
        model.selection_constraints.add(model.x[Teams[selected_team].id,selected_group] == 1)

        if len(Groups[selected_group]) == 3:
           groupList.remove(selected_group)

    return generate_group_boxes(),[{'label': team , 'value': team} for team in teamList],[{'label': f'Group {group}', 'value': group} for group in groupList]

@app.callback(
      Output('feasible-groups','children'),
      Input('show-feasible','n_clicks'),
      State('team-dropdown','value')
)
def ListFeasibleGroups(n_clicks,selected_team):
    if n_clicks > 0:
        fes_groups = give_feasible(model,selected_team)
        if len(fes_groups) != 0:
            return html.P(f'Feasible groups are {fes_groups}')
        else:
            return html.P('Sorry, No feasible solutions are now possible')
            


def generate_group_boxes():
    # Create a list of group divs
    group_boxes = []
    for group, assigned_teams in Groups.items():
        box = dbc.Col(
            html.Div(
                [
                    html.H5(f'Group {group}', className='card-title'),
                    html.Ul([html.Li(team) for team in assigned_teams], className='list-unstyled'),
                ],
                className='border p-3 mb-3',
                style={'height': '150px', 'overflowY': 'auto'}
            ),
            width=3
        )
        group_boxes.append(box)
    return group_boxes

app.run_server(debug=True)