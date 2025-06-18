import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import random
import threading
import time
import asyncio
import websockets
import json


app = dash.Dash(__name__)
app.title = "Radar Tracker UI"

# Simulated track storage
live_tracks = {}

def generate_fake_radar_data():
    """ Simulate radar detections updating every second """
    while True:
        frame_tracks = {}
        for i in range(random.randint(2, 6)):
            track_id = random.randint(1, 10)
            azimuth = random.uniform(-75, 75)
            distance = random.uniform(5, 100)
            frame_tracks[track_id] = (azimuth, distance)
        # Replace global
        global live_tracks
        live_tracks = frame_tracks
        time.sleep(1)

# Start the radar simulation in a background thread
threading.Thread(target=generate_fake_radar_data, daemon=True).start()

app.layout = html.Div([
    html.H3("Real-Time Radar Tracker"),
    dcc.Graph(id='radar-plot', style={"height": "90vh"}),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0)
])

@app.callback(
    Output('radar-plot', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_radar_plot(n):
    # Clean up and format data
    thetas = []
    rs = []
    labels = []

    for track_id, (azimuth, distance) in live_tracks.items():
        thetas.append(azimuth)
        rs.append(distance)
        labels.append(f"Track {track_id}")

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=rs,
        theta=thetas,
        mode='markers+text',
        marker=dict(size=12, color='lime'),
        text=labels,
        textposition="top center"
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[0, 150], showgrid=True),
            angularaxis=dict(
                direction="clockwise",
                rotation=90,
                tickmode="array",
                tickvals=[-75, -45, 0, 45, 75],
                ticktext=["-75°", "-45°", "0°", "45°", "75°"]
            )
        ),
        showlegend=False,
        template="plotly_dark",
        margin=dict(t=20, l=0, r=0, b=0)
    )
    return fig

if __name__ == '__main__':
    app.run(debug=True)