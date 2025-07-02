
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PIL import Image
import threading, time, math, sys, os, traceback
import pygame

# ---------- Parámetros globales ----------
WINDOW_W, WINDOW_H = 1920, 1080
FPS              = 26
ERROR_MARGIN_PX  = 15                  # Margen de error para mover vertices

SEQ_PREFIX       = "Image_"           # Image_0.png … Image_N.png
ANIM_START_FRAME = 5

AUDIO_FILE       = "minecraft-footsteps.wav"
EDGE_THICKNESS   = 4
EDGE_COLOR       = (1.0, 1.0, 0.0)
# ----------------------------------------

# ---------- Config-caras ----------
faces_cfg = {
    "front": {"idxs": [0, 1, 2, 3], "flipx": True,  "flipy": False, "rot": 0},
    "right": {"idxs": [1, 4, 5, 2], "flipx": False, "flipy": True,  "rot": 270},
    "top":   {"idxs": [3, 2, 5, 6], "flipx": False, "flipy": True,  "rot": 90},
}
face_order = ["front", "top", "right"]
# ----------------------------------
cube_vertices = [
    [-1, -1,  1],
    [ 1, -1,  1],
    [ 1,  1,  1],
    [-1,  1,  1],
    [ 1, -1, -1],
    [ 1,  1, -1],
    [-1,  1, -1],
    [-1, -1, -1],
]

face_textures   = {name: [] for name in faces_cfg}
face_frame      = {}
active_index    = 0
animating       = False
selected_vertex = None
FRAME_COUNT     = 0

def init_audio():
    pygame.mixer.init()
    global sound, channel
    sound = pygame.mixer.Sound(AUDIO_FILE)
    channel = pygame.mixer.Channel(0)  # usa canal 0 para reproducir

def play_sound():
    if not pygame.mixer.get_init():
        init_audio()
    channel.play(sound)

def stop_sound():
    if pygame.mixer.get_init():
        channel.stop()

def project_vertex(v):
    m = glGetDoublev(GL_MODELVIEW_MATRIX)
    p = glGetDoublev(GL_PROJECTION_MATRIX)
    vp = glGetIntegerv(GL_VIEWPORT)
    return gluProject(v[0], v[1], v[2], m, p, vp)

def unproject(x, y, depth):
    m = glGetDoublev(GL_MODELVIEW_MATRIX)
    p = glGetDoublev(GL_PROJECTION_MATRIX)
    vp = glGetIntegerv(GL_VIEWPORT)
    return gluUnProject(x, y, depth, m, p, vp)


def load_sequence(prefix):
    frames = []
    i = 0
    while True:
        fname = f"{prefix}{i}.png"
        if not os.path.exists(fname):
            break
        try:
            img = Image.open(fname).transpose(Image.FLIP_TOP_BOTTOM)
        except Exception as e:
            print(f"Error cargando {fname}: {e}")
            break
        data = img.convert("RGBA").tobytes()
        tid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tid)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, data)
        frames.append(tid)
        i += 1
    return frames


def transform_uv(u, v, rot, fx, fy):
    if rot % 360 ==  90:
        u, v = v, 1 - u
    elif rot % 360 == 180:
        u, v = 1 - u, 1 - v
    elif rot % 360 == 270:
        u, v = 1 - v, u
    if fx: u = 1 - u
    if fy: v = 1 - v
    return u, v


# ---------- Render y Display ----------
def draw_faces():
    base_uv = [(0,0), (1,0), (1,1), (0,1)]
    for name, cfg in faces_cfg.items():
        idxs, rot, fx, fy = cfg['idxs'], cfg['rot'], cfg['flipx'], cfg['flipy']
        # Textura
        glColor3f(1, 1, 1)
        count = len(face_textures[name])
        frame_idx = min(face_frame.get(name, 0), count - 1)
        glBindTexture(GL_TEXTURE_2D, face_textures[name][frame_idx])
        glBegin(GL_QUADS)
        for i, vi in enumerate(idxs):
            u, v = transform_uv(*base_uv[i], rot, fx, fy)
            glTexCoord2f(u, v)
            glVertex3f(*cube_vertices[vi])
        glEnd()

        # Borde
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
    draw_faces()
    glutSwapBuffers()


def safe_display():
    try:
        display()
    except Exception:
        traceback.print_exc()
# ---------------------------------------

# ---------- Callbacks ----------
def timer_cb(value):
    global animating, active_index
    try:
        if animating:
            face = face_order[active_index]
            face_frame[face] += 1
            if face_frame[face] >= FRAME_COUNT:
                face_frame[face] = FRAME_COUNT - 1
                animating = False
                stop_sound()
                active_index = (active_index + 1) % len(face_order)
                next_face = face_order[active_index]
                face_frame[next_face] = ANIM_START_FRAME
        glutPostRedisplay()
    except Exception:
        traceback.print_exc()
    finally:
        glutTimerFunc(int(1000/FPS), timer_cb, 0)


def key_cb(key, x, y):
    global animating
    try:
        if key == b'\x1b':
            stop_sound()
            sys.exit(0)
        if key == b' ' and not animating:
            animating = True
            play_sound()
    except Exception:
        traceback.print_exc()


def mouse_cb(button, state, x, y):
    global selected_vertex
    print(f"Mouse: button={button}, {state=}, {x=}, {y=}")
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        sx, sy = x, glutGet(GLUT_WINDOW_HEIGHT) - y
        for idx, v in enumerate(cube_vertices):
            win = project_vertex(v)
            if math.hypot(win[0] - sx, win[1] - sy) <= ERROR_MARGIN_PX:
                selected_vertex = (idx, win[2])
                print(f"Selected vertex: {selected_vertex}")
                break
    elif button == GLUT_LEFT_BUTTON and state == GLUT_UP:
        selected_vertex = None
        print("Deselected vertex")


def motion_cb(x, y):
    try:
        if selected_vertex is None:
            return
        idx, depth = selected_vertex
        sx, sy = x, glutGet(GLUT_WINDOW_HEIGHT) - y
        cube_vertices[idx][:] = unproject(sx, sy, depth)
        glutPostRedisplay()
    except Exception:
        traceback.print_exc()
# ---------------------------------------

# ---------- Init & Main ----------
def init():
    global FRAME_COUNT, face_frame
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glClearColor(0.15, 0.15, 0.15, 1)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, WINDOW_W/WINDOW_H, 0.1, 100)

    seq = load_sequence(SEQ_PREFIX)
    FRAME_COUNT = len(seq)
    print(f"Frames cargados: {FRAME_COUNT}")
    if FRAME_COUNT == 0:
        print("No se encontraron imágenes.")
        sys.exit(1)
    for name in faces_cfg:
        face_textures[name] = seq
    face_frame = {name: (ANIM_START_FRAME if name == "front" else FRAME_COUNT - 1)
                  for name in faces_cfg}
    return face_frame


def main():
    global face_frame
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutCreateWindow(b"Cubo computacion grafica")
    glutFullScreen()
    face_frame = init()
    glutDisplayFunc(safe_display)
    glutMouseFunc(mouse_cb)
    glutMotionFunc(motion_cb)
    glutKeyboardFunc(key_cb)
    glutTimerFunc(int(1000/FPS), timer_cb, 0)
    try:
        glutMainLoop()
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    main()
