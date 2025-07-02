# cube_anim_drag_fullscreen_edges_flip_rot.py
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PIL import Image
import math, sys

# ---------- Parámetros globales ----------
WINDOW_W, WINDOW_H = 1920, 1080          # se fuerza full-screen igual
FPS                = 30
ERROR_MARGIN_PX    = 15
SEQ_PREFIX         = "Image_"
SEQ_FRAMES         = 26

EDGE_THICKNESS     = 4                   # grosor del borde interior
EDGE_COLOR         = (1.0, 1.0, 0.0)     # amarillo
# ----------------------------------------

# ---------- Config-caras (flip + rot) ----------
#  idxs   → índices de cube_vertices
#  flipx  → invierte textura eje X
#  flipy  → invierte textura eje Y
#  rot    → gira textura 0/90/180/270 (º) sentido horario
faces = {
    "front": {"idxs": [0, 1, 2, 3], "flipx": True, "flipy": False, "rot":   0},
    "right": {"idxs": [1, 4, 5, 2], "flipx": False,  "flipy": True, "rot":  270},
    "top"  : {"idxs": [3, 2, 5, 6], "flipx": False, "flipy": True,  "rot": 90},
}
# -----------------------------------------------

# Vértices del cubo (arista = 2, centrado en el origen)
cube_vertices = [
    [-1, -1,  1], [ 1, -1,  1], [ 1,  1,  1], [-1,  1,  1],
    [ 1, -1, -1], [ 1,  1, -1], [-1,  1, -1], [-1, -1, -1],
]

face_textures   = {name: [] for name in faces}
current_frame   = 0
selected_vertex = None                    # (índice, depth)

# ---------- Utilidades picking ----------
def project_vertex(v):
    model = glGetDoublev(GL_MODELVIEW_MATRIX)
    proj  = glGetDoublev(GL_PROJECTION_MATRIX)
    view  = glGetIntegerv(GL_VIEWPORT)
    return gluProject(*v, model, proj, view)

def unproject(x, y, depth):
    model = glGetDoublev(GL_MODELVIEW_MATRIX)
    proj  = glGetDoublev(GL_PROJECTION_MATRIX)
    view  = glGetIntegerv(GL_VIEWPORT)
    return gluUnProject(x, y, depth, model, proj, view)

# ---------- Carga de texturas ----------
def load_image_sequence(pref, cnt):
    frames = []
    for i in range(cnt):
        fname = f"{pref}{i}.png"
        try:
            img = Image.open(fname).transpose(Image.FLIP_TOP_BOTTOM)
        except FileNotFoundError:
            print(f"[WARN] {fname} no encontrado – se omite.", file=sys.stderr)
            continue
        data = img.convert("RGBA").tobytes()
        tid  = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tid)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, data)
        frames.append(tid)
    return frames

# ---------- Transformación UV ----------
def transform_uv(u, v, rot_deg, flipx, flipy):
    """Aplica rotación (0/90/180/270) y flips a coords (u,v)."""
    if   rot_deg % 360 ==  90: u, v = v, 1 - u
    elif rot_deg % 360 == 180: u, v = 1 - u, 1 - v
    elif rot_deg % 360 == 270: u, v = 1 - v, u
    # rot 0 → sin cambio
    if flipx: u = 1 - u
    if flipy: v = 1 - v
    return u, v

# ---------- Render ----------
def draw_cube_faces():
    global current_frame
    base_uv = [(0,0), (1,0), (1,1), (0,1)]   # orden ccw en quad

    for name, cfg in faces.items():
        idxs   = cfg["idxs"]
        flipx  = cfg["flipx"]
        flipy  = cfg["flipy"]
        rot    = cfg["rot"]

        # Cara texturizada
        glColor3f(1, 1, 1)
        glBindTexture(GL_TEXTURE_2D, face_textures[name][current_frame])
        glBegin(GL_QUADS)
        for i, vi in enumerate(idxs):
            u, v = transform_uv(*base_uv[i], rot, flipx, flipy)
            glTexCoord2f(u, v)
            glVertex3f(*cube_vertices[vi])
        glEnd()

        # Borde interior
        glDisable(GL_TEXTURE_2D)
        glColor3f(*EDGE_COLOR)
        glLineWidth(EDGE_THICKNESS)
        glBegin(GL_LINE_LOOP)
        for vi in idxs:
            glVertex3f(*cube_vertices[vi])
        glEnd()
        glEnable(GL_TEXTURE_2D)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(3, 4, 6, 0, 0, 0, 0, 1, 0)
    draw_cube_faces()
    glutSwapBuffers()

# ---------- Callbacks ----------
def timer(_):
    global current_frame
    current_frame = (current_frame + 1) % SEQ_FRAMES
    glutPostRedisplay()
    glutTimerFunc(int(1000/FPS), timer, 0)

def mouse(btn, state, x, y):
    global selected_vertex
    if btn == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        sx, sy = x, glutGet(GLUT_WINDOW_HEIGHT) - y
        for idx, v in enumerate(cube_vertices):
            win = project_vertex(v)
            if math.hypot(win[0]-sx, win[1]-sy) <= ERROR_MARGIN_PX:
                selected_vertex = (idx, win[2])
                break
    elif btn == GLUT_LEFT_BUTTON and state == GLUT_UP:
        selected_vertex = None

def motion(x, y):
    if selected_vertex is None: return
    idx, depth = selected_vertex
    sx, sy = x, glutGet(GLUT_WINDOW_HEIGHT) - y
    cube_vertices[idx][:] = unproject(sx, sy, depth)
    glutPostRedisplay()

def key(k, *_):
    if k == b'\x1b': sys.exit(0)

# ---------- Init ----------
def init():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glClearColor(0.15, 0.15, 0.15, 1)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, WINDOW_W / WINDOW_H, 0.1, 100)

    seq = load_image_sequence(SEQ_PREFIX, SEQ_FRAMES)
    if not seq:
        print("❌ No hay secuencia. Abortando…")
        sys.exit(1)
    for n in faces:
        face_textures[n] = seq

# ---------- Main ----------
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutCreateWindow(b"Cubo 3 caras - waton")
    glutFullScreen()

    init()
    glutDisplayFunc(display)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    glutKeyboardFunc(key)
    glutTimerFunc(int(1000/FPS), timer, 0)
    glutMainLoop()

if __name__ == "__main__":
    main()
