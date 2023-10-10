# -*- coding: utf-8 -*-
# vispy: gallery 2
# Copyright (c) 2015, Vispy Development Team.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

"""
Multiple real-time digital signals with GLSL-based clipping.
"""


import bsl
import matplotlib.pyplot as plt
import numpy as np
from vispy import app, gloo, visuals

VERT_SHADER = """
#version 120
// y coordinate of the position.
attribute float a_position;
// row, col, and time index.
attribute vec3 a_index;
varying vec3 v_index;
// 2D scaling factor (zooming).
uniform vec2 u_scale;
// Size of the table.
uniform vec2 u_size;
// Number of samples per signal.
uniform float u_n;
// Color.
attribute vec3 a_color;
varying vec4 v_color;
// Varying variables used for clipping in the fragment shader.
varying vec2 v_position;
varying vec4 v_ab;
void main() {
    float n_rows = u_size.x;
    float n_cols = u_size.y;
    // Compute the x coordinate from the time index.
    float x = -1 + 2*a_index.z / (u_n-1);
    vec2 position = vec2(x - (1 - 1 / u_scale.x), a_position);
    // Find the affine transformation for the subplots.
    vec2 a = vec2(1./n_cols, 1./n_rows)*.9;
    vec2 b = vec2(-1 + 2*(a_index.x+.5) / n_cols,
                    -1 + 2*(a_index.y+.5) / n_rows);
    // Apply the static subplot transformation + scaling.
    gl_Position = vec4(a*u_scale*position+b, 0.0, 1.0);
    v_color = vec4(a_color, 1.);
    v_index = a_index;
    // For clipping test in the fragment shader.
    v_position = gl_Position.xy;
    v_ab = vec4(a, b);
}
"""

FRAG_SHADER = """
#version 120
varying vec4 v_color;
varying vec3 v_index;
varying vec2 v_position;
varying vec4 v_ab;
void main() {
    gl_FragColor = v_color;
    // Discard the fragments between the signals (emulate glMultiDrawArrays).
    if ((fract(v_index.x) > 0.) || (fract(v_index.y) > 0.))
        discard;
    // Clipping test.
    vec2 test = abs((v_position.xy-v_ab.zw)/v_ab.xy);
    if ((test.x > 1))
        discard;
}
"""


def view():
    print("Looking for a stream...")
    eeg = bsl.lsl.resolve_streams(stype="EEG", timeout=5)
    ppg = bsl.lsl.resolve_streams(stype="PPG", timeout=5)

    if len(eeg) == 0:
        raise RuntimeError("Can't find EEG stream.")
    else:
        eeg = bsl.lsl.StreamInlet(eeg[0])
    if len(ppg) == 0:
        ppg = None
    else:
        ppg = bsl.lsl.StreamInlet(ppg[0])

    print("Start acquiring data.")

    Canvas(eeg=eeg, ppg=ppg)
    app.run()


class Canvas(app.Canvas):
    def __init__(self, eeg, ppg=None):
        app.Canvas.__init__(self, title="Muse - Use your wheel to zoom!", keys="interactive")

        # Get info from stream
        eeg_info = _view_info(eeg)
        self.ch_names = eeg_info["ch_names"]
        self.n_channels = eeg_info["n_channels"]

        # Channel colors
        colors = [
            (255 / 255, 87 / 255, 34 / 255),  # Orange
            (103 / 255, 58 / 255, 183 / 255),  # Dark Purple
            (33 / 255, 150 / 255, 243 / 255),  # Dark blue
            (3 / 255, 169 / 255, 244 / 255),  # Blue
            (142 / 255, 39 / 255, 176 / 255),  # Purple
        ]
        # Colors for impedence
        self.colors_quality = plt.get_cmap("RdYlGn")(np.linspace(0, 1, 11))[::-1]

        # ppg = None
        ppg_info = None
        if ppg is not None:
            ppg_info = _view_info(ppg)
            self.ch_names += ppg_info["ch_names"]
            self.n_channels += ppg_info["n_channels"]
            colors += [
                (244 / 255, 67 / 255, 54 / 255),  # Red
                (244 / 255, 67 / 255, 54 / 255),  # Red
                (244 / 255, 67 / 255, 54 / 255),  # Red
            ]

        # Number of cols and rows in the table.
        n_rows = len(colors)
        n_cols = 1

        # Initialize data to zero
        self.data = np.zeros((eeg_info["n_samples"], n_rows))

        colors = np.repeat(colors, eeg_info["n_samples"], axis=0).astype(np.float32)
        # Signal 2D index of each vertex (row and col) and x-index (sample index
        # within each signal).
        index = np.c_[
            np.repeat(np.repeat(np.arange(n_cols), n_rows), eeg_info["n_samples"]),
            np.repeat(np.tile(np.arange(n_rows), n_cols), eeg_info["n_samples"]),
            np.tile(np.arange(eeg_info["n_samples"]), n_rows),
        ].astype(np.float32)

        self.program = gloo.Program(VERT_SHADER, FRAG_SHADER)
        self.program["a_position"] = self.data.T.astype(np.float32).reshape(-1, 1)
        self.program["a_index"] = index
        self.program["a_color"] = colors
        self.program["u_scale"] = (1.0, 1.0)
        self.program["u_size"] = (n_rows, n_cols)
        self.program["u_n"] = eeg_info["n_samples"]

        # Text
        self.font_size = 48.0
        self.display_names = []
        self.display_quality = []
        for channel in self.ch_names:
            text = visuals.TextVisual(channel, bold=True, color="white")
            self.display_names.append(text)
            text = visuals.TextVisual("", bold=True, color="white")
            self.display_quality.append(text)

        # Store
        self.eeg = eeg_info["inlet"]
        self.ppg = False if ppg is None else ppg_info["inlet"]
        self.n_samples = eeg_info["n_samples"]
        self.sfreq = eeg_info["sfreq"]

        # View
        self._timer = app.Timer("auto", connect=self.on_timer, start=True)
        gloo.set_viewport(0, 0, *self.physical_size)
        gloo.set_state(
            clear_color="white",
            blend=True,
            blend_func=("src_alpha", "one_minus_src_alpha"),
        )

        self.show()

    def on_timer(self, event):
        """Add some data at the end of each signal (real-time signals)."""

        # EEG ------------------------------------------------
        samples, time = self.eeg.pull_chunk(timeout=0, max_samples=100)
        samples = np.array(samples)[:, ::-1]  # Reverse (newest on the right)

        # PPG ------------------------------------------------
        if self.ppg:
            samples = np.hstack([np.zeros((len(samples), 3)), samples])

            # ppg_samples, ppg_time = self.ppg.pull_chunk(timeout=0, max_samples=100)
            # if len(ppg_samples) > 0:
            #     ppg_samples = np.array(ppg_samples)[:, ::-1]
            #     # For each eeg timestamp, find closest ppg timestamp
            #     ppg_samples = np.array([ppg_samples[np.argmin(np.abs(ppg_time - t)), :] for t in time])
            #     # Concat with samples
            #     samples = np.hstack([ppg_samples, samples])
            # else:
            #     # Concat with samples
            #     samples = np.hstack([np.zeros((len(samples), 3)), samples])

        self.data = np.vstack([self.data, samples])  # Concat
        self.data = self.data[-self.n_samples :]  # Keep only last window length

        # Rescaling
        plot_data = self.data.copy()

        # Normalize EEG (last 5 channels)
        plot_data[:, -5:] = (plot_data[:, -5:] - plot_data[:, -5:].mean(axis=0)) / 500

        # Compute Impedence
        sd = np.std(plot_data[-int(self.sfreq) :, -5:], axis=0)[::-1] * 500
        # Discretize the impedence into 11 levels for coloring
        co = np.int32(np.tanh((sd - 30) / 15) * 5 + 5)

        # Loop through the 5 last channels indices (EEG channels)
        for i in range(5):
            self.display_quality[i].text = f"{sd[i]:.2f}"
            self.display_quality[i].color = self.colors_quality[co[i]]
            self.display_quality[i].font_size = 12 + co[i]

            self.display_names[i].font_size = 12 + co[i]
            self.display_names[i].color = self.colors_quality[co[i]]

        self.program["a_position"].set_data(plot_data.T.ravel().astype(np.float32))
        self.update()

    def on_key_press(self, event):
        # increase time scale
        if event.key.name in ["+", "-"]:
            if event.key.name == "+":
                dx = -0.05
            else:
                dx = 0.05
            scale_x, scale_y = self.program["u_scale"]
            scale_x_new, scale_y_new = (
                scale_x * np.exp(1.0 * dx),
                scale_y * np.exp(0.0 * dx),
            )
            self.program["u_scale"] = (max(1, scale_x_new), max(1, scale_y_new))
            self.update()

    def on_mouse_wheel(self, event):
        dx = np.sign(event.delta[1]) * 0.05
        scale_x, scale_y = self.program["u_scale"]
        scale_x_new, scale_y_new = (
            scale_x * np.exp(0.0 * dx),
            scale_y * np.exp(2.0 * dx),
        )
        self.program["u_scale"] = (max(1, scale_x_new), max(0.01, scale_y_new))
        self.update()

    def on_resize(self, event):
        # Set canvas viewport and reconfigure visual transforms to match.
        vp = (0, 0, self.physical_size[0], self.physical_size[1])
        self.context.set_viewport(*vp)

        # Text position
        for i, t in enumerate(self.display_names):
            t.transforms.configure(canvas=self, viewport=vp)
            t.pos = (
                self.size[0] * 0.075,
                ((i + 0.5) / self.n_channels) * self.size[1],
            )

        for i, t in enumerate(self.display_quality):
            t.transforms.configure(canvas=self, viewport=vp)
            t.pos = (
                self.size[0] * 0.925,
                ((i + 0.5) / self.n_channels) * self.size[1],
            )

    def on_draw(self, event):
        gloo.clear()
        gloo.set_viewport(0, 0, *self.physical_size)
        self.program.draw("line_strip")
        [t.draw() for t in self.display_names + self.display_quality]


def _view_info(inlet):
    """Get info from stream"""
    inlet.open_stream()

    info = {}  # Initialize a container
    info["info"] = inlet.get_sinfo()
    info["description"] = info["info"].desc

    info["window"] = 10  # 10-second window showing the data.
    info["sfreq"] = info["info"].sfreq
    info["n_samples"] = int(info["sfreq"] * info["window"])
    info["ch_names"] = info["info"].get_channel_names()
    info["n_channels"] = len(info["ch_names"])
    info["inlet"] = inlet
    return info
