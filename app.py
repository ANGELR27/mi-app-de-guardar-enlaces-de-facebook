import ttkbootstrap as tb
from ttkbootstrap.constants import *
import mysql.connector
from mysql.connector import Error
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import requests
from bs4 import BeautifulSoup

# Función para conectar a la base de datos
def conectar_bd():
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="2705",  # Cambia por tu contraseña de MySQL
            database="gestor_enlaces"
        )
        if conexion.is_connected():
            return conexion
    except Error as e:
        messagebox.showerror("Error", f"No se pudo conectar a la base de datos: {e}")
        return None

# Función para extraer metadatos del enlace (título y miniatura)
def obtener_datos_enlace(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Obtener el título de la página
        titulo = soup.title.string if soup.title else 'Sin título'

        # Buscar la imagen de miniatura (usualmente está en etiquetas meta)
        miniatura = None
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            miniatura = og_image['content']
        
        return titulo, miniatura
    except Exception as e:
        print(f"Error al obtener datos del enlace: {e}")
        return 'Sin título', None  # Valor predeterminado si hay un error

# Función para guardar un enlace en la base de datos con título y miniatura
def guardar_enlace():
    categoria = combo_categoria.get().strip()
    enlace = entry_enlace.get().strip()

    if not categoria or not enlace:
        messagebox.showwarning("Advertencia", "Por favor, selecciona una categoría y escribe un enlace.")
        return

    # Extraer el título y la miniatura del enlace
    titulo, miniatura = obtener_datos_enlace(enlace)
    
    conexion = conectar_bd()
    if conexion is None:
        return

    try:
        cursor = conexion.cursor()
        sql = "INSERT INTO enlaces (categoria, enlace, titulo, miniatura) VALUES (%s, %s, %s, %s)"
        valores = (categoria, enlace, titulo, miniatura)
        cursor.execute(sql, valores)
        conexion.commit()
        messagebox.showinfo("Éxito", f"Enlace guardado con título: {titulo}")
    except Error as e:
        messagebox.showerror("Error", f"No se pudo guardar el enlace: {e}")
    finally:
        cursor.close()
        conexion.close()

# Función para redirigir al enlace al hacer clic en él
def abrir_enlace(event):
    item = treeview.selection()[0]
    enlace = treeview.item(item, "values")[2]
    webbrowser.open(enlace)

# Función para eliminar el enlace seleccionado
def eliminar_enlace():
    item = treeview.selection()
    if not item:
        messagebox.showwarning("Advertencia", "Por favor, selecciona un enlace para eliminar.")
        return

    enlace = treeview.item(item[0], "values")[2]  # Columna del enlace

    if not enlace:
        messagebox.showwarning("Advertencia", "No puedes eliminar un separador de categoría.")
        return

    conexion = conectar_bd()
    if conexion is None:
        return

    try:
        cursor = conexion.cursor()
        sql = "DELETE FROM enlaces WHERE enlace = %s"
        cursor.execute(sql, (enlace,))
        conexion.commit()
        treeview.delete(item[0])  # Eliminar de la vista también
        messagebox.showinfo("Éxito", "¡Enlace eliminado exitosamente!")
    except Error as e:
        messagebox.showerror("Error", f"No se pudo eliminar el enlace: {e}")
    finally:
        cursor.close()
        conexion.close()

# Función para mostrar los enlaces agrupados por categoría
def mostrar_enlaces():
    conexion = conectar_bd()
    if conexion is None:
        return

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT categoria, titulo, enlace, fecha_agregado FROM enlaces ORDER BY categoria, fecha_agregado DESC")
        resultados = cursor.fetchall()

        ventana_enlaces = tb.Toplevel(window)
        ventana_enlaces.title("Enlaces Guardados")
        ventana_enlaces.geometry("600x500")

        global treeview
        treeview = ttk.Treeview(ventana_enlaces, columns=("Categoria", "Título", "Enlace", "Fecha"), show="headings")
        treeview.heading("Categoria", text="Categoría")
        treeview.heading("Título", text="Título")
        treeview.heading("Enlace", text="Enlace")
        treeview.heading("Fecha", text="Fecha Agregado")
        treeview.pack(fill="both", expand=True)

        # Añadir los enlaces al Treeview
        categoria_actual = None
        for categoria, titulo, enlace, fecha in resultados:
            if categoria != categoria_actual:
                treeview.insert("", "end", values=(f"--- {categoria} ---", "", "", ""))
                categoria_actual = categoria
            treeview.insert("", "end", values=(categoria, titulo, enlace, fecha))

        treeview.bind("<Double-1>", abrir_enlace)

        # Añadir botón de eliminar enlace en la ventana de enlaces
        tb.Button(ventana_enlaces, text="Eliminar Enlace Seleccionado", bootstyle="danger outline", command=eliminar_enlace).pack(pady=10)

    except Error as e:
        messagebox.showerror("Error", f"No se pudieron recuperar los enlaces: {e}")
    finally:
        cursor.close()
        conexion.close()

# Función para crear una nueva categoría
def crear_categoria():
    def guardar_categoria():
        nueva_categoria = nueva_categoria_entry.get().strip()
        if nueva_categoria:
            combo_categoria['values'] = tuple(list(combo_categoria['values']) + [nueva_categoria])
            messagebox.showinfo("Éxito", f"Categoría '{nueva_categoria}' creada.")
            ventana_categoria.destroy()
        else:
            messagebox.showwarning("Advertencia", "El nombre de la categoría no puede estar vacío.")

    ventana_categoria = tb.Toplevel(window)
    ventana_categoria.title("Crear Nueva Categoría")
    ventana_categoria.geometry("300x200")

    tb.Label(ventana_categoria, text="Nombre de la Nueva Categoría:", bootstyle="info").pack(pady=10)
    nueva_categoria_entry = tb.Entry(ventana_categoria)
    nueva_categoria_entry.pack(pady=10)

    tb.Button(ventana_categoria, text="Guardar Categoría", bootstyle="success", command=guardar_categoria).pack(pady=10)

# Configuración de la ventana principal
def main():
    global window
    window = tb.Window(themename="darkly")
    window.title("Gestor de Enlaces de Facebook")
    window.geometry("400x400")

    tb.Label(window, text="Categoría:", bootstyle="info").pack(pady=10)
    global combo_categoria
    combo_categoria = tb.Combobox(window, values=["Entretenimiento", "Educación", "Deportes", "Noticias", "Música"], bootstyle="primary")
    combo_categoria.pack(pady=5)
    combo_categoria.set("Entretenimiento")

    tb.Label(window, text="Enlace de Video:", bootstyle="info").pack(pady=10)
    global entry_enlace
    entry_enlace = tb.Entry(window, bootstyle="secondary")
    entry_enlace.pack(pady=5)

    tb.Button(window, text="Guardar Enlace", bootstyle="success outline", command=guardar_enlace).pack(pady=10)
    tb.Button(window, text="Mostrar Enlaces Guardados", bootstyle="primary outline", command=mostrar_enlaces).pack(pady=10)
    tb.Button(window, text="Crear Nueva Categoría", bootstyle="info outline", command=crear_categoria).pack(pady=10)

    window.mainloop()

# Ejecutamos la aplicación
if __name__ == "__main__":
    main()
