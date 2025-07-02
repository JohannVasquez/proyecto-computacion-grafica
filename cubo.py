from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PIL import Image
import math

WINDOW_WIDTH = 1920 
WINDOW_HEIGHT = 1080

texture_id = None

"""
bottom left, bottom right, top right, top left

"""

# Cada cuadrado tiene: [vertices, textura]
squares = [
    {
        "vertices": [[300,100], [400, 100], [400, 200], [300, 200]],
        "texture": "image1.jpg"
    },
    {
        "vertices": [[500,300],[700, 300], [700, 400], [500, 400]],
        "texture": "image1.jpg"
    },
    {
        "vertices": [[800, 400], [900, 400], [900, 500], [800, 500]],
        "texture": "image1.jpg"
    }
]

texture_ids = {}

# squares = [
#     [[300,100], [400, 100], [400, 200], [300, 200]],
#     [[500,300],[700, 300], [700, 400], [500, 400]],
#     [[800, 400], [900, 400], [900, 500], [800, 500]]
    
# ]

# Definir un margen de error en píxeles
error_margin = 50  # Puedes ajustarlo según tus necesidades
selected_vertex = None  # Para almacenar el índice del vértice seleccionado

# Función para calcular la distancia entre dos puntos (x1, y1) y (x2, y2)
def calcular_distancia(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


is_left_button_pressed = False  # Variable para almacenar si el botón izquierdo está presionado

def mouse_callback(button, state, x, y):
    global is_left_button_pressed, selected_vertex

    opengl_x = x
    opengl_y = WINDOW_HEIGHT - y  # Invertir coordenada Y

    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            is_left_button_pressed = True
            print(f"🖱 Botón IZQUIERDO PRESIONADO en ({opengl_x}, {opengl_y})")

            for i, square in enumerate(squares):
                for j, vertex in enumerate(square["vertices"]):  # ⚠️ ahora accedés a square["vertices"]
                    dist = calcular_distancia(opengl_x, opengl_y, vertex[0], vertex[1])
                    if dist <= error_margin:
                        selected_vertex = (i, j)
                        print(f"✔ Clic cerca del vértice {j} del cuadrado {i} en {vertex}")
                        return  # Salimos después de encontrar el primero
        elif state == GLUT_UP:
            is_left_button_pressed = False
            selected_vertex = None
            print(f"🖱 Botón IZQUIERDO LIBERADO en ({opengl_x}, {opengl_y})")


def motion_callback(x, y):
    global is_left_button_pressed, selected_vertex

    if is_left_button_pressed and selected_vertex is not None:
        opengl_x = x
        opengl_y = WINDOW_HEIGHT - y

        square_index, vertex_index = selected_vertex
        squares[square_index]["vertices"][vertex_index] = [opengl_x, opengl_y]  # 👈 actualizamos vértice
        print(f"✔ Vértice {vertex_index} del cuadrado {square_index} movido a ({opengl_x}, {opengl_y})")
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


def init():    
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glEnable(GL_TEXTURE_2D)  # Habilita texturas
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    # Cargar texturas para cada cuadrado
    for square in squares:
        square["texture_id"] = load_texture(square["texture"])

def draw_textured_squares():
    dx = [0.0, 1.0, 1.0, 0.0]
    dy = [0.0, 0.0, 1.0, 1.0]

    for square in squares:
        glBindTexture(GL_TEXTURE_2D, square["texture_id"])
        glBegin(GL_QUADS)
        for i in range(4):
            glTexCoord2f(dx[i], dy[i])
            x, y = square["vertices"][i]
            glVertex2f(x, y)
        glEnd()


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    draw_textured_squares()
    glFlush()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Cuadrado con Textura")
    
    # glutFullScreen()
    init()
    glutDisplayFunc(display)
    # threading.Thread(target=modificar_vertice, daemon=True).start()
    glutMouseFunc(mouse_callback)
    glutMotionFunc(motion_callback) # Callback para el movimiento
    glutMainLoop()

if __name__ == "__main__":
    main()
