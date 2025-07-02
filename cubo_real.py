from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PIL import Image
import math

WINDOW_WIDTH = 1920 
WINDOW_HEIGHT = 1080

texture_ids = {}

# Cada cuadrado tiene: [vertices, textura o secuencia]
squares = [
    {
        "vertices": [[300,100], [400, 100], [400, 200], [300, 200]],
        "texture_sequence": "Image_",
        "frame_count": 26,
        "is_sequence": True,
        "current_frame": 0,
        "frame_textures": [],
        "rotation": 0,
        "flipx": True,
        "flipy": False
    },
    {
        "vertices": [[500,300],[700, 300], [700, 400], [500, 400]],
        "texture_sequence": "Image_",
        "frame_count": 26,
        "is_sequence": True,
        "current_frame": 0,
        "frame_textures": [],
        "rotation": 90,
        "flipx": False,
        "flipy": False
    },
    {
        "vertices": [[800, 400], [900, 400], [900, 500], [800, 500]],
        "texture_sequence": "Image_",
        "frame_count": 26,
        "is_sequence": True,
        "current_frame": 0,
        "frame_textures": [],
        "rotation": 90,
        "flipx": False,
        "flipy": False
    }
]

error_margin = 50
selected_vertex = None
is_left_button_pressed = False

def transform_and_draw_square(square):
    original_vertices = square["vertices"]
    angle = math.radians(square["rotation"])
    flipx = -1 if square["flipx"] else 1
    flipy = -1 if square["flipy"] else 1

    # Calcular centro del cuadrado
    cx = sum([v[0] for v in original_vertices]) / 4
    cy = sum([v[1] for v in original_vertices]) / 4

    dx = [0.0, 1.0, 1.0, 0.0]
    dy = [0.0, 0.0, 1.0, 1.0]

    glBindTexture(GL_TEXTURE_2D, square["texture_id"])
    glBegin(GL_QUADS)
    for i in range(4):
        # Posición relativa al centro
        x, y = original_vertices[i]
        rel_x = x - cx
        rel_y = y - cy

        # Aplicar flip
        rel_x *= flipx
        rel_y *= flipy

        # Aplicar rotación
        rot_x = rel_x * math.cos(angle) - rel_y * math.sin(angle)
        rot_y = rel_x * math.sin(angle) + rel_y * math.cos(angle)

        # Regresar al sistema global
        final_x = cx + rot_x
        final_y = cy + rot_y

        glTexCoord2f(dx[i], dy[i])
        glVertex2f(final_x, final_y)
    glEnd()

def calcular_distancia(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def mouse_callback(button, state, x, y):
    global is_left_button_pressed, selected_vertex
    opengl_x = x
    opengl_y = WINDOW_HEIGHT - y
    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            is_left_button_pressed = True
            for i, square in enumerate(squares):
                for j, vertex in enumerate(square["vertices"]):
                    dist = calcular_distancia(opengl_x, opengl_y, vertex[0], vertex[1])
                    if dist <= error_margin:
                        selected_vertex = (i, j)
                        return
        elif state == GLUT_UP:
            is_left_button_pressed = False
            selected_vertex = None

def motion_callback(x, y):
    global is_left_button_pressed, selected_vertex
    if is_left_button_pressed and selected_vertex is not None:
        opengl_x = x
        opengl_y = WINDOW_HEIGHT - y
        square_index, vertex_index = selected_vertex
        squares[square_index]["vertices"][vertex_index] = [opengl_x, opengl_y]
        glutPostRedisplay()

def load_texture(filename):
    if filename in texture_ids:
        return texture_ids[filename]

    image = Image.open(filename)
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    img_data = image.convert("RGBA").tobytes()

    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.width, image.height, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, img_data)

    texture_ids[filename] = texture_id
    return texture_id

def load_image_sequence(prefix, count):
    frames = []
    for i in range(count):
        filename = f"{prefix}{i}.png"
        image = Image.open(filename).transpose(Image.FLIP_TOP_BOTTOM)
        img_data = image.convert("RGBA").tobytes()
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.width, image.height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        frames.append(texture_id)
    return frames

def init():    
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glEnable(GL_TEXTURE_2D)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)

    for square in squares:
        if square.get("is_sequence"):
            square["frame_textures"] = load_image_sequence(square["texture_sequence"], square["frame_count"])
            square["texture_id"] = square["frame_textures"][0]
        else:
            square["texture_id"] = load_texture(square["texture"])

def update_animation(value):
    for square in squares:
        if square.get("is_sequence"):
            square["current_frame"] = (square["current_frame"] + 1) % square["frame_count"]
            square["texture_id"] = square["frame_textures"][square["current_frame"]]
    glutPostRedisplay()
    glutTimerFunc(100, update_animation, 0)

def draw_textured_squares():
    for square in squares:
        transform_and_draw_square(square)


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    draw_textured_squares()
    glFlush()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Cuadrado con Textura Animada")
    init()
    glutDisplayFunc(display)
    glutMouseFunc(mouse_callback)
    glutMotionFunc(motion_callback)
    glutTimerFunc(100, update_animation, 0)
    glutMainLoop()

if __name__ == "__main__":
    main()