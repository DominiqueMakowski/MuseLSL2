# -*- coding: utf-8 -*-
# vispy: gallery 2
# Copyright (c) 2015, Vispy Development Team.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

"""
Multiple real-time digital signals with GLSL-based clipping.
"""

import math

import numpy as np
import scipy.signal
from pylsl import StreamInlet, resolve_byprop
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
    streams = resolve_byprop("type", "EEG", timeout=5)  # LSL_SCAN_TIMEOUT

    if len(streams) == 0:
        raise (RuntimeError("Can't find EEG stream."))
    print("Start acquiring data.")

    inlet = StreamInlet(streams[0], max_chunklen=12)  # LSL_EEG_CHUNK
    Canvas(inlet)
    app.run()


class Canvas(app.Canvas):
    def __init__(self, lsl_inlet, scale=500):
        app.Canvas.__init__(
            self, title="EEG - Use your wheel to zoom!", keys="interactive"
        )

        self.inlet = lsl_inlet
        info = self.inlet.info()
        description = info.desc()

        window = 10
        self.sfreq = info.nominal_srate()
        n_samples = int(self.sfreq * window)
        self.n_chans = info.channel_count()

        ch = description.child("channels").first_child()
        ch_names = [ch.child_value("label")]

        for i in range(self.n_chans):
            ch = ch.next_sibling()
            ch_names.append(ch.child_value("label"))

        # Number of cols and rows in the table.
        n_rows = self.n_chans
        n_cols = 1

        # Number of signals.
        m = n_rows * n_cols

        # Number of samples per signal.
        n = n_samples

        # Various signal amplitudes.
        amplitudes = np.zeros((m, n)).astype(np.float32)
        # gamma = np.ones((m, n)).astype(np.float32)
        # Generate the signals as a (m, n) array.
        y = amplitudes

        # color = sns.color_palette("RdBu_r", 5)  # n_rows = 5
        # [tuple(np.round(x, 2)) for x in color]
        color = [
            (0.22, 0.51, 0.73),
            (0.65, 0.81, 0.89),
            (0.97, 0.97, 0.96),
            (0.97, 0.72, 0.6),
            (0.79, 0.28, 0.25),
        ]

        color = np.repeat(color, n, axis=0).astype(np.float32)
        # Signal 2D index of each vertex (row and col) and x-index (sample index
        # within each signal).
        index = np.c_[
            np.repeat(np.repeat(np.arange(n_cols), n_rows), n),
            np.repeat(np.tile(np.arange(n_rows), n_cols), n),
            np.tile(np.arange(n), m),
        ].astype(np.float32)

        self.program = gloo.Program(VERT_SHADER, FRAG_SHADER)
        self.program["a_position"] = y.reshape(-1, 1)
        self.program["a_color"] = color
        self.program["a_index"] = index
        self.program["u_scale"] = (1.0, 1.0)
        self.program["u_size"] = (n_rows, n_cols)
        self.program["u_n"] = n

        # text
        self.font_size = 48.0
        self.names = []
        self.quality = []
        for ii in range(self.n_chans):
            text = visuals.TextVisual(ch_names[ii], bold=True, color="white")
            self.names.append(text)
            text = visuals.TextVisual("", bold=True, color="white")
            self.quality.append(text)

        # A rounding of: sns.color_palette("RdYlGn", 11)[::-1]
        self.quality_colors = [
            (0.08, 0.56, 0.3),
            (0.29, 0.69, 0.36),
            (0.52, 0.79, 0.4),
            (0.72, 0.88, 0.46),
            (0.87, 0.95, 0.58),
            (1.0, 1.0, 0.75),
            (1.0, 0.9, 0.58),
            (0.99, 0.75, 0.44),
            (0.97, 0.56, 0.32),
            (0.92, 0.34, 0.22),
            (0.81, 0.16, 0.15),
        ]

        self.scale = scale
        self.n_samples = n_samples
        self.af = [1.0]

        self.data = np.zeros((n_samples, self.n_chans))

        self._timer = app.Timer("auto", connect=self.on_timer, start=True)
        gloo.set_viewport(0, 0, *self.physical_size)
        gloo.set_state(
            clear_color="black",
            blend=True,
            blend_func=("src_alpha", "one_minus_src_alpha"),
        )

        self.show()

    def on_key_press(self, event):

        # increase time scale
        if event.key.name in ["+", "-"]:
            if event.key.name == "+":
                dx = -0.05
            else:
                dx = 0.05
            scale_x, scale_y = self.program["u_scale"]
            scale_x_new, scale_y_new = (
                scale_x * math.exp(1.0 * dx),
                scale_y * math.exp(0.0 * dx),
            )
            self.program["u_scale"] = (max(1, scale_x_new), max(1, scale_y_new))
            self.update()

    def on_mouse_wheel(self, event):
        dx = np.sign(event.delta[1]) * 0.05
        scale_x, scale_y = self.program["u_scale"]
        scale_x_new, scale_y_new = (
            scale_x * math.exp(0.0 * dx),
            scale_y * math.exp(2.0 * dx),
        )
        self.program["u_scale"] = (max(1, scale_x_new), max(0.01, scale_y_new))
        self.update()

    def on_timer(self, event):
        """Add some data at the end of each signal (real-time signals)."""

        samples, timestamps = self.inlet.pull_chunk(timeout=0.0, max_samples=100)
        if timestamps:
            samples = np.array(samples)[:, ::-1]

            self.data = np.vstack([self.data, samples])
            self.data = self.data[-self.n_samples :]

            plot_data = (self.data - self.data.mean(axis=0)) / self.scale

            sd = np.std(plot_data[-int(self.sfreq) :], axis=0)[::-1] * self.scale
            co = np.int32(np.tanh((sd - 30) / 15) * 5 + 5)
            for ii in range(self.n_chans):
                self.quality[ii].text = "%.2f" % (sd[ii])
                self.quality[ii].color = self.quality_colors[co[ii]]
                self.quality[ii].font_size = 12 + co[ii]

                self.names[ii].font_size = 12 + co[ii]
                self.names[ii].color = self.quality_colors[co[ii]]

            self.program["a_position"].set_data(plot_data.T.ravel().astype(np.float32))
            self.update()

    def on_resize(self, event):
        # Set canvas viewport and reconfigure visual transforms to match.
        vp = (0, 0, self.physical_size[0], self.physical_size[1])
        self.context.set_viewport(*vp)

        for ii, t in enumerate(self.names):
            t.transforms.configure(canvas=self, viewport=vp)
            t.pos = (self.size[0] * 0.025, ((ii + 0.5) / self.n_chans) * self.size[1])

        for ii, t in enumerate(self.quality):
            t.transforms.configure(canvas=self, viewport=vp)
            t.pos = (self.size[0] * 0.975, ((ii + 0.5) / self.n_chans) * self.size[1])

    def on_draw(self, event):
        gloo.clear()
        gloo.set_viewport(0, 0, *self.physical_size)
        self.program.draw("line_strip")
        [t.draw() for t in self.names + self.quality]
