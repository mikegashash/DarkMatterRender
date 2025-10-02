# Three-Panel View - Optimized for smooth rotation with fixed layout
import numpy as np
import scipy.fft as fft
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots

print("Building Optimized Three-Panel Comparison...")

G = 4.30091e-6
ln2 = math.log(2.0)

def fftfreq_3d(nx, ny, nz, L):
    kx = 2*np.pi*fft.fftfreq(nx, d=L/nx)
    ky = 2*np.pi*fft.fftfreq(ny, d=L/ny)
    kz = 2*np.pi*fft.fftfreq(nz, d=L/nz)
    return np.meshgrid(kx, ky, kz, indexing='ij')

def create_galaxy(nx=28, ny=28, nz=28, L=40.0):  # Reduced from 35 to 28
    dx = L/nx
    x = (np.arange(nx) - nx//2) * dx
    y = (np.arange(ny) - ny//2) * dx
    z = (np.arange(nz) - nz//2) * dx
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    R = np.sqrt(X**2 + Y**2)
    rho = np.exp(-R/3.0) * np.exp(-np.abs(Z)/0.5)
    rho = rho / (rho.sum() + 1e-30)
    return rho, L, (x, y, z)

def compute_info_density(rho_b, L, ell=5.0, strength=2.0):
    nx, ny, nz = rho_b.shape
    kx, ky, kz = fftfreq_3d(nx, ny, nz, L)
    k2 = kx**2 + ky**2 + kz**2
    
    rho_k = fft.fftn(rho_b)
    eps = 1e-20
    mask = k2 > eps
    Phi_k = np.zeros_like(rho_k, dtype=complex)
    Phi_k[mask] = -4*np.pi*G * rho_k[mask] / (k2[mask] + eps)
    
    K_k = 1.0 / (k2 + (1.0/(ell**2)) + eps)
    response_k = K_k * k2 * Phi_k
    response = np.real(fft.ifftn(response_k))
    
    rho_info = np.maximum(response * strength * 1e-7, 0.0)
    rho_info = np.nan_to_num(rho_info, nan=0.0, posinf=0.0, neginf=0.0)
    return rho_info

# Create galaxy
print("Creating galaxy...")
rho_b, L, (x, y, z) = create_galaxy()
X_flat = np.repeat(x, len(y)*len(z))
Y_flat = np.tile(np.repeat(y, len(z)), len(x))
Z_flat = np.tile(z, len(x)*len(y))
print(f"Grid: {len(x)}×{len(y)}×{len(z)}, Box: {L} kpc")

def visualize_three_panel(ell_kpc=6.0, strength=2.0):
    """Three-panel view with fixed layout and smoother rotation"""
    
    print(f"\nComputing: ℓ={ell_kpc} kpc, ζ={strength}")
    
    # Compute densities
    rho_info = compute_info_density(rho_b, L, ell=ell_kpc, strength=strength)
    
    # Normalize
    def norm(vals):
        vals_flat = vals.flatten()
        if np.any(vals_flat > 0):
            vmin, vmax = np.percentile(vals_flat[vals_flat > 0], [5, 95])
            return np.clip((vals_flat - vmin) / (vmax - vmin + 1e-30), 0, 1)
        return vals_flat
    
    rho_b_norm = norm(rho_b)
    rho_info_norm = norm(rho_info)
    
    # Create three-panel subplots
    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{'type': 'volume'}, {'type': 'volume'}, {'type': 'volume'}]],
        subplot_titles=(
            '<b>Normal Matter</b><br><sub>Stars & Gas</sub>',
            '<b>Information Field</b><br><sub>Emergent Halo</sub>',
            '<b>Combined</b><br><sub>Total Distribution</sub>'
        ),
        horizontal_spacing=0.05
    )
    
    # Panel 1: Baryonic matter (Blue)
    fig.add_trace(go.Volume(
        x=X_flat, y=Y_flat, z=Z_flat, value=rho_b_norm,
        isomin=0.2, isomax=1.0, opacity=0.35, surface_count=6,  # Reduced surfaces
        colorscale='Blues', showscale=False,
        caps=dict(x_show=False, y_show=False, z_show=False),
    ), row=1, col=1)
    
    # Panel 2: Information halo (Hot)
    fig.add_trace(go.Volume(
        x=X_flat, y=Y_flat, z=Z_flat, value=rho_info_norm,
        isomin=0.1, isomax=1.0, opacity=0.25, surface_count=8,  # Reduced surfaces
        colorscale='Hot', showscale=False,
        caps=dict(x_show=False, y_show=False, z_show=False),
    ), row=1, col=2)
    
    # Panel 3: OVERLAY - Blue disk
    fig.add_trace(go.Volume(
        x=X_flat, y=Y_flat, z=Z_flat, value=rho_b_norm,
        isomin=0.2, isomax=1.0, opacity=0.3, surface_count=6,
        colorscale='Blues', showscale=False,
        caps=dict(x_show=False, y_show=False, z_show=False),
    ), row=1, col=3)
    
    # Panel 3: OVERLAY - Orange halo (25% more transparent = 0.2 * 0.75 = 0.15)
    fig.add_trace(go.Volume(
        x=X_flat, y=Y_flat, z=Z_flat, value=rho_info_norm,
        isomin=0.1, isomax=1.0, opacity=0.15,  # Reduced from 0.2 to 0.15
        surface_count=8,
        colorscale='Hot', 
        colorbar=dict(title="Density", x=1.01),
        caps=dict(x_show=False, y_show=False, z_show=False),
    ), row=1, col=3)
    
    # Initial camera
    initial_camera = dict(eye=dict(x=1.5, y=1.5, z=1.2), center=dict(x=0, y=0, z=0))
    
    scene_settings = dict(
        xaxis=dict(title="X [kpc]", range=[-L/2, L/2]),
        yaxis=dict(title="Y [kpc]", range=[-L/2, L/2]),
        zaxis=dict(title="Z [kpc]", range=[-L/2, L/2]),
        camera=initial_camera,
        aspectmode='cube'
    )
    
    # Rotation frames - Fewer frames for smoother performance
    frames = []
    n_frames = 60  # Reduced from 72
    
    for i in range(n_frames):
        angle = i * 6  # 6 degrees per frame
        rad = np.radians(angle)
        eye_x = 1.5 * np.cos(rad)
        eye_y = 1.5 * np.sin(rad)
        
        frames.append(go.Frame(
            layout=dict(
                scene=dict(camera=dict(eye=dict(x=eye_x, y=eye_y, z=1.2))),
                scene2=dict(camera=dict(eye=dict(x=eye_x, y=eye_y, z=1.2))),
                scene3=dict(camera=dict(eye=dict(x=eye_x, y=eye_y, z=1.2)))
            ),
            name=str(i)
        ))
    
    fig.frames = frames
    
    # Layout with title moved up
    fig.update_layout(
        scene=scene_settings,
        scene2=scene_settings,
        scene3=scene_settings,
        title=dict(
            text=f"<b>Information-Gravity Coupling: Three-Panel View</b> | ℓ={ell_kpc} kpc, ζ={strength}<br>" +
                 "<sub>Blue = Visible Matter | Red/Orange = Information Field | Right = Overlay</sub>",
            x=0.5,
            xanchor='center',
            y=0.98,  # Moved higher
            yanchor='top',
            font=dict(size=14)
        ),
        width=2100,
        height=600,  # Reduced height
        margin=dict(l=0, r=0, b=80, t=80),  # Reduced top margin
        showlegend=False,
        updatemenus=[{
            'type': 'buttons',
            'showactive': True,
            'buttons': [
                {
                    'label': '▶ Play',
                    'method': 'animate',
                    'args': [None, {
                        'frame': {'duration': 100, 'redraw': True},  # Slightly slower for smoothness
                        'fromcurrent': True,
                        'mode': 'immediate',
                        'transition': {'duration': 50, 'easing': 'linear'}
                    }]
                },
                {
                    'label': '⏸ Pause',
                    'method': 'animate',
                    'args': [[None], {
                        'frame': {'duration': 0, 'redraw': False},
                        'mode': 'immediate'
                    }]
                },
                {
                    'label': '↻ Reset',
                    'method': 'animate',
                    'args': [[frames[0].name], {
                        'frame': {'duration': 0, 'redraw': True},
                        'mode': 'immediate'
                    }]
                }
            ],
            'x': 0.5,
            'xanchor': 'center',
            'y': -0.1,
            'yanchor': 'top'
        }],
        sliders=[{
            'active': 0,
            'yanchor': 'top',
            'y': -0.18,
            'xanchor': 'left',
            'currentvalue': {
                'prefix': 'Rotation: ',
                'visible': True,
                'xanchor': 'center'
            },
            'pad': {'b': 10, 't': 10},
            'len': 0.9,
            'x': 0.05,
            'steps': [
                {
                    'args': [[f.name], {
                        'frame': {'duration': 0, 'redraw': True},
                        'mode': 'immediate'
                    }],
                    'method': 'animate',
                    'label': f'{i*6}°'
                } for i, f in enumerate(frames[::5])  # Every 30 degrees
            ]
        }]
    )
    
    # Annotation at bottom
    fig.add_annotation(
        text="<b>Notice:</b> Blue disk (visible matter) sits within extended red/orange halo (information field)",
        xref="paper", yref="paper",
        x=0.5, y=-0.05,
        showarrow=False,
        font=dict(size=11),
        align="center",
        bgcolor="rgba(255,255,200,0.8)",
        bordercolor="orange",
        borderwidth=2
    )
    
    fig.show()
    
    # Auto-play
    from IPython.display import display, Javascript
    display(Javascript("""
        setTimeout(function() {
            var buttons = document.querySelectorAll('.modebar-btn');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].getAttribute('data-title') === 'Play') {
                    buttons[i].click();
                    break;
                }
            }
        }, 500);
    """))
    
    print(f"\n✓ Optimized three-panel visualization complete!")
    print(f"  Smoother rotation with reduced grid size (28³)")
    print(f"  Overlay transparency increased for better blue visibility")
    print(f"  Mass ratio (Minfo/Mbary): {rho_info.sum()/rho_b.sum():.3f}")

# Run visualization
print("\n" + "="*60)
print("CREATING OPTIMIZED THREE-PANEL COMPARISON")
print("="*60)
visualize_three_panel(ell_kpc=6.0, strength=2.0)

print("\n" + "="*60)
print("Try different parameters:")
print("  visualize_three_panel(ell_kpc=8.0, strength=1.5)")
print("  visualize_three_panel(ell_kpc=5.0, strength=3.0)")
print("="*60)
