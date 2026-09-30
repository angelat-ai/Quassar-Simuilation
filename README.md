# Quasar Simulation: A 3D Black Hole in Python

A real-time, rotatable 3D simulation of a quasar (a supermassive black hole feeding on gas and dust), written in pure Python with NumPy and Pygame. No game engine and no 3D library: every particle, rotation, and glow is calculated by hand with math.

![Quasar simulation main view](assets/quasar-main.png)

## Demo Video

[Watch the demo video](assets/demo.mp4)

## Gallery

| Edge-on view | Zoomed out | Close-up |
| :---: | :---: | :---: |
| ![Edge-on view](assets/quasar-edge-on.png) | ![Zoomed out](assets/quasar-zoom-out.png) | ![Close-up](assets/quasar-close-up.png) |

## Features

1. About 100,000 particles rendered in real time using NumPy (no per-particle Python loops).
2. Fully rotatable in 3D with the mouse, plus zoom.
3. Accretion disc with two spiral arms and a hot-to-cool color gradient.
4. Thin glowing rings around the disc.
5. Relativistic polar jets with a slight wobble and outward-moving pulses.
6. Doppler beaming: the side of the disc moving toward you is brighter.
7. Gravitational lensing halo and arcs around the core.
8. Cinematic look: tone mapping, multi-layer bloom, lens streak, and vignette.
9. Procedural nebula background with a star band, and 1,000 twinkling 3D stars that shift with parallax as you rotate.

## Controls

| Input | Action |
| :--- | :--- |
| Left mouse drag | Rotate freely in any direction |
| Mouse wheel | Zoom in and out |
| Arrow keys | Rotate |
| A | Toggle auto-rotate |
| SPACE | Toggle disc orbit motion |
| H | Hide or show the on-screen hint |
| R | Reset the view |
| ESC | Quit |

## Installation

Requirements: Python 3.9 or newer.

```bash
git clone https://github.com/angelat-ai/quasar-simulation.git
cd quasar-simulation
pip install -r requirements.txt
python black_hole.py
```

If the animation runs slowly on your computer, lower `N_DISC` (default 50000) and `N_JET` (default 16000) in `black_hole.py`.

## How It Works

This section explains the math and logic behind the simulation so it is easy to follow.

### 1. Everything is a particle in 3D space

Every glowing dot is a point with coordinates (x, y, z). The scene is made of several groups of points: the disc, the rings, the jet, floating embers, and background stars.

### 2. Building the disc and rings with polar coordinates

A circle is created from an angle and a radius:

$$x = r\cos\theta, \qquad y = r\sin\theta$$

Each disc particle gets a random radius and angle. The z value is a tiny random number, which gives the disc a slight thickness. The thin rings use a nearly constant radius, so they look like sharp glowing lines. Two spiral arms are made by tying the angle to the radius:

$$\theta = k\ln\!\left(\frac{r}{r_0}\right) + \text{arm offset} + \text{noise}$$

### 3. Orbiting motion

Material closer to the black hole orbits faster. Each particle's angle changes over time as:

$$\theta(t) = \theta_0 + \omega\,t, \qquad \omega \propto \frac{1}{r}$$

Real orbits follow Kepler's law (omega proportional to r to the power of negative 1.5). This simulation uses a gentler version so the spiral arms stay visible for longer.

### 4. Rotation with matrices

To rotate the whole scene, every point is multiplied by a rotation matrix. For a rotation by angle a around the X axis:

$$y' = y\cos a - z\sin a, \qquad z' = y\sin a + z\cos a$$

Rotations around Y and Z work the same way. The three are stored as matrices and combined into one matrix M. When you drag the mouse, a small rotation is multiplied onto M every frame (a trackball style control):

$$M \leftarrow R_x(\Delta y \cdot k)\; R_y(-\Delta x \cdot k)\; M, \qquad p' = M\,p$$

NumPy applies this to all particles at once, which is why it is fast.

### 5. How a flat screen looks 3D (perspective projection)

A monitor is 2D, so depth is an illusion created by perspective. Points that are farther away (larger z) are drawn closer to the center and smaller:

$$s = \frac{f}{f + z}, \qquad x_{screen} = c_x + x\,s\,\text{zoom}, \qquad y_{screen} = c_y + y\,s\,\text{zoom}$$

Here f is the focal length (1400 in the code) and c is the screen center. Near particles are also drawn slightly brighter, which adds to the depth feeling. Because the matrix M changes as you drag, the same 3D points land on different screen positions and the object appears to turn.

### 6. Glow by adding light

Instead of drawing circles, every projected particle adds its color to a pixel buffer using `np.bincount`. Where many particles overlap, the values add up and the area becomes bright, just like real light. Then a tone-mapping curve keeps hot areas golden instead of pure white:

$$I_{out} = 255\left(1 - e^{-I/165}\right)$$

### 7. Bloom

To make the glow soft, the image is shrunk to a low resolution and enlarged again, which blurs it. This is done at several sizes and each blurred copy is added back on top of the original. Small blur gives a sharp glow, and large blur gives the wide halo.

### 8. Doppler beaming

The disc spins, so one side moves toward the camera and the other moves away. The velocity of a particle along its orbit is tangent to the circle, (-sin theta, cos theta). Its component toward the camera comes from the third row of M. Brightness is scaled by:

$$b = \text{clip}\left(1 - k\,v_z\right), \qquad I' = I\,b^2$$

The side coming toward you becomes brighter and the receding side becomes dimmer.

### 9. The jet

The jet is a stream of particles along the z axis, which is the axis the disc spins around. Its width grows with distance, it has a small sine wobble, and a moving sine wave in its brightness creates pulses traveling outward:

$$w(z, t) = w_0\left(0.6 + 0.4\sin(0.05\,|z| - 5t)\right)$$

Since the jet is part of the same 3D model, it rotates together with the disc.

### 10. Gravitational lensing halo

Near a black hole, gravity bends light so the far side of the disc appears to wrap over the top and bottom of the core. This is faked with a ring that always faces the camera, plus two bright arcs. The arcs point along the projected direction of the disc's axis and get stronger when you view the disc edge-on:

$$\varphi = \operatorname{atan2}(M_{12}, M_{02}), \qquad \text{edge} = 1 - |M_{22}|$$

### 11. Procedural background

The nebula is built from layered noise (fractal Brownian motion). Random low-resolution grids are smoothly scaled up at different sizes and blended together, then colored with purple, teal, and warm orange blobs. Thin ridges in a separate noise layer create dark dust lanes. Stars are drawn with cross-shaped flares, and the 3D stars are rotated by the same matrix M, which gives parallax when you rotate.

### 12. Final touches

A pulsing core sprite, a horizontal anamorphic lens streak, and a vignette that darkens the edges of the screen finish the cinematic look.

## Customization

| Variable | What it changes |
| :--- | :--- |
| `N_DISC`, `N_JET` | Particle counts (lower for better performance) |
| `R_RING` | Size of the outer ring |
| `d_w` | Brightness of the orange dust in the disc |
| `j_w0` | Brightness of the jet |
| `halo_w0` | Strength of the lensing halo |
| `M = ry(-0.0028) @ M` | Auto-rotate speed |
| `disc_phase += 0.38 * dt` | Disc orbit speed |
| `rng = np.random.default_rng(11)` | Random seed (change it for a different nebula) |

## Tech Stack

1. Python
2. NumPy for all the math and particle handling
3. Pygame for the window, input, and image blending

## Credits

Inspired by YouTube tutorials on generating galaxies with Python, and by digital space art of a quasar. Built and debugged by [@angelat-ai](https://github.com/angelat-ai).

## License

Released under the MIT License. See the `LICENSE` file for details.
