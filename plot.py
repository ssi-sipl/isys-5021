import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import threading
import asyncio
import websockets
import json
import time

app = dash.Dash(__name__)
app.title = "Radar Tracker UI"

# Stores live tracks with last seen timestamp
live_tracks = {}

# Replace with your actual RPi IP
RASPBERRY_PI_IP = "192.168.1.42"
WS_PORT = 8765
WS_URI = f"ws://{RASPBERRY_PI_IP}:{WS_PORT}"

# --- WebSocket Client ---
def start_ws_client():
    async def listen():
        global live_tracks
        while True:
            try:
                async with websockets.connect(WS_URI) as ws:
                    print(f"✅ Connected to radar at {WS_URI}")
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)

                        track_id = data.get("track_id")
                        azimuth = data.get("aizmuth_angle")
                        distance = data.get("distance")

                        if track_id and azimuth is not None and distance is not None:
                            live_tracks[track_id] = {
                                "azimuth": azimuth,
                                "distance": distance,
                                "last_seen": time.time()
                            }

            except Exception as e:
                print("🔁 Reconnecting to radar...", e)
                await asyncio.sleep(2)

    asyncio.run(listen())

# Start WebSocket client thread
threading.Thread(target=start_ws_client, daemon=True).start()

# --- Dash Layout ---
app.layout = html.Div([
    html.H3("Real-Time Radar Tracker"),
    dcc.Graph(id='radar-plot', style={"height": "90vh"}),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0)
])

# --- Dash Callback to Update Plot ---
@app.callback(
    Output('radar-plot', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_radar_plot(n):
    now = time.time()
    thetas = []
    rs = []
    labels = []

    # Remove stale tracks older than 3 seconds
    expired = [tid for tid, info in live_tracks.items() if now - info["last_seen"] > 3]
    for tid in expired:
        del live_tracks[tid]

    for tid, info in live_tracks.items():
        thetas.append(info["azimuth"])
        rs.append(info["distance"])
        labels.append(f"{tid[:6]}")  # Shorten track_id for display

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

# --- Run Server ---
if __name__ == '__main__':
    app.run(debug=True)
