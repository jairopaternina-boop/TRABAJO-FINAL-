"""
Simulador de Autómatas Finitos Deterministas
Estructuras Discretas — Proyecto
Módulo 1: construcción y gráfica | Módulo 2: cinco palabras | Módulo 3: probar palabras
Extras (bonificación): recorrido resaltado sobre la gráfica y guardar/cargar autómata (JSON).
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
import json

MAX_LONG = 10  # longitud máxima de búsqueda en el Módulo 2


# ======================= LÓGICA DEL AUTÓMATA =======================
class Automata:
    def __init__(self, Q, sigma, delta, q0, F):
        self.Q = Q              # lista de estados (en orden de ingreso)
        self.sigma = sigma      # lista de símbolos (en orden de ingreso)
        self.delta = delta      # dict {(estado, simbolo): estado}
        self.q0 = q0
        self.F = F              # lista de estados finales

    def recorrido(self, palabra):
        """Devuelve (lista_de_estados, None) o (None, (simbolo, posicion)) si hay símbolo inválido."""
        estado = self.q0
        pasos = [estado]
        for i, c in enumerate(palabra):
            if c not in self.sigma:
                return None, (c, i + 1)
            estado = self.delta[(estado, c)]
            pasos.append(estado)
        return pasos, None

    def reconoce(self, palabra):
        pasos, error = self.recorrido(palabra)
        return pasos is not None and pasos[-1] in self.F

    def alcanzables(self):
        vistos, pila = {self.q0}, [self.q0]
        while pila:
            q = pila.pop()
            for a in self.sigma:
                d = self.delta[(q, a)]
                if d not in vistos:
                    vistos.add(d)
                    pila.append(d)
        return vistos

    def palabras_reconocidas(self, cantidad=5, max_long=MAX_LONG):
        """Las 'cantidad' palabras reconocidas más cortas, en orden canónico.
        puede[k] = estados desde los que alguna palabra de longitud exacta k llega a F.
        Con eso solo se exploran ramas que sí terminan en una palabra reconocida."""
        puede = [set(self.F)]
        for k in range(1, max_long + 1):
            puede.append({q for q in self.Q
                          if any(self.delta[(q, a)] in puede[k - 1] for a in self.sigma)})
        resultado = []

        def dfs(estado, prefijo, restante):
            if len(resultado) >= cantidad:
                return
            if restante == 0:
                resultado.append(prefijo)
                return
            for a in self.sigma:  # orden del alfabeto ingresado
                sig = self.delta[(estado, a)]
                if sig in puede[restante - 1]:
                    dfs(sig, prefijo + a, restante - 1)
                    if len(resultado) >= cantidad:
                        return

        for L in range(max_long + 1):
            if self.q0 in puede[L]:
                dfs(self.q0, "", L)
            if len(resultado) >= cantidad:
                break
        return resultado

    def tupla(self):
        return f"M = ({conj(self.Q)}, {conj(self.sigma)}, δ, {self.q0}, {conj(self.F)})"

    def tabla(self):
        ancho = max([len(q) for q in self.Q] + [len(a) for a in self.sigma] + [2]) + 2
        lineas = ["δ".ljust(ancho + 3) + "".join(a.ljust(ancho) for a in self.sigma)]
        for q in self.Q:
            marca = ("→" if q == self.q0 else " ") + ("*" if q in self.F else " ")
            fila = marca + " " + q.ljust(ancho)
            fila += "".join(self.delta[(q, a)].ljust(ancho) for a in self.sigma)
            lineas.append(fila)
        lineas.append("\n→ estado inicial    * estado final")
        return "\n".join(lineas)

    def a_dict(self):
        return {"Q": self.Q, "sigma": self.sigma, "q0": self.q0, "F": self.F,
                "delta": {q: {a: self.delta[(q, a)] for a in self.sigma} for q in self.Q}}

    @staticmethod
    def desde_dict(d):
        delta = {(q, a): d["delta"][q][a] for q in d["Q"] for a in d["sigma"]}
        return Automata(d["Q"], d["sigma"], delta, d["q0"], d["F"])


def conj(xs):
    return "{" + ", ".join(xs) + "}"


def parse_lista(texto):
    return [x.strip() for x in texto.split(",") if x.strip()]


def texto_recorrido(pasos, palabra):
    s = pasos[0]
    for c, q in zip(palabra, pasos[1:]):
        s += f" –{c}→ {q}"
    return s


# ======================= DIBUJO DE LA GRÁFICA =======================
def dibujar_automata(canvas, M, resaltar=None):
    """resaltar: dict {(origen, destino): [números de paso]} para la mejora opcional."""
    canvas.delete("all")
    if M is None:
        return
    resaltar = resaltar or {}
    W, H = int(canvas.cget("width")), int(canvas.cget("height"))
    cx, cy, R = W / 2, H / 2, 26
    n = len(M.Q)

    # Posición de los estados: sobre un círculo, empezando por la izquierda
    pos = {}
    radio = min(W, H) / 2 - 90
    for i, q in enumerate(M.Q):
        if n == 1:
            pos[q] = (cx, cy)
        else:
            ang = math.pi + 2 * math.pi * i / n
            pos[q] = (cx + radio * math.cos(ang), cy + radio * math.sin(ang))

    # Agrupar símbolos que van del mismo origen al mismo destino
    grupos = {}
    for q in M.Q:
        for a in M.sigma:
            grupos.setdefault((q, M.delta[(q, a)]), []).append(a)

    fuente = ("Arial", 12, "bold")
    for (o, d), simbolos in grupos.items():
        etiqueta = ", ".join(simbolos)
        pasos = resaltar.get((o, d))
        color = "#E8730C" if pasos else "#333333"
        grosor = 3 if pasos else 1.6
        if pasos:
            etiqueta += "  [" + ",".join(map(str, pasos)) + "]"
        x, y = pos[o]

        if o == d:  # bucle
            if n == 1:
                ux, uy = 0, -1
            else:
                dist = math.hypot(x - cx, y - cy)
                ux, uy = (x - cx) / dist, (y - cy) / dist
                if o == M.q0 and ux < -0.7:  # no chocar con la flecha inicial
                    ux, uy = 0, -1

            def rot(vx, vy, t):
                return vx * math.cos(t) - vy * math.sin(t), vx * math.sin(t) + vy * math.cos(t)
            a1, b1 = rot(ux, uy, -0.5)
            a2, b2 = rot(ux, uy, 0.5)
            c1, e1 = rot(ux, uy, -0.6)
            c2, e2 = rot(ux, uy, 0.6)
            puntos = [x + R * a1, y + R * b1, x + 2.8 * R * c1, y + 2.8 * R * e1,
                      x + 2.8 * R * c2, y + 2.8 * R * e2, x + R * a2, y + R * b2]
            canvas.create_line(*puntos, smooth=True, arrow=tk.LAST, width=grosor,
                               fill=color, arrowshape=(10, 12, 4))
            canvas.create_text(x + 3.2 * R * ux, y + 3.2 * R * uy, text=etiqueta,
                               font=fuente, fill=color)
        else:
            x2, y2 = pos[d]
            dist = math.hypot(x2 - x, y2 - y)
            ux, uy = (x2 - x) / dist, (y2 - y) / dist
            nx, ny = -uy, ux
            curva = 28 if (d, o) in grupos else 0  # dos flechas separadas si hay ida y vuelta
            sx, sy = x + R * ux + 0.4 * curva * nx, y + R * uy + 0.4 * curva * ny
            ex, ey = x2 - R * ux + 0.4 * curva * nx, y2 - R * uy + 0.4 * curva * ny
            mx, my = (x + x2) / 2 + curva * nx, (y + y2) / 2 + curva * ny
            canvas.create_line(sx, sy, mx, my, ex, ey, smooth=True, arrow=tk.LAST,
                               width=grosor, fill=color, arrowshape=(10, 12, 4))
            canvas.create_text(mx + 14 * nx, my + 14 * ny, text=etiqueta, font=fuente, fill=color)

    # Estados
    for q, (x, y) in pos.items():
        final = q in M.F
        relleno = "#D9F2E3" if final else "#EAF1FB"
        canvas.create_oval(x - R, y - R, x + R, y + R, fill=relleno, outline="#1F3B73", width=2)
        if final:  # doble círculo
            canvas.create_oval(x - R + 5, y - R + 5, x + R - 5, y + R - 5,
                               outline="#1F3B73", width=2)
        canvas.create_text(x, y, text=q, font=("Arial", 11, "bold"))

    # Flecha del estado inicial (no sale de ningún estado)
    x, y = pos[M.q0]
    canvas.create_line(x - R - 45, y, x - R, y, arrow=tk.LAST, width=2,
                       fill="#1F3B73", arrowshape=(10, 12, 4))
    canvas.create_text(x - R - 50, y - 12, text="inicio", font=("Arial", 9), fill="#1F3B73")


# ======================= INTERFAZ GRÁFICA =======================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador de Autómatas Finitos — Estructuras Discretas")
        self.geometry("1150x700")
        self.M = None
        self.celdas = {}
        self.Q_tabla, self.S_tabla = [], []

        ttk.Style().configure("TButton", padding=5)
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)
        self.tab1, self.tab2, self.tab3 = ttk.Frame(self.nb), ttk.Frame(self.nb), ttk.Frame(self.nb)
        self.nb.add(self.tab1, text="  Módulo 1: Construir y graficar  ")
        self.nb.add(self.tab2, text="  Módulo 2: Cinco palabras  ")
        self.nb.add(self.tab3, text="  Módulo 3: Probar palabras  ")
        self.nb.bind("<<NotebookTabChanged>>", self.cambio_pestana)

        self.crear_modulo1()
        self.crear_modulo2()
        self.crear_modulo3()

    # ---------------- Módulo 1 ----------------
    def crear_modulo1(self):
        izq = ttk.Frame(self.tab1, padding=10)
        izq.pack(side="left", fill="y")
        der = ttk.Frame(self.tab1, padding=10)
        der.pack(side="right", fill="both", expand=True)

        ttk.Label(izq, text="1. Estados Q (separados por comas):").pack(anchor="w")
        self.e_Q = ttk.Entry(izq, width=40)
        self.e_Q.pack(anchor="w", pady=(0, 6))
        ttk.Label(izq, text="2. Alfabeto Σ (símbolos de un carácter, por comas):").pack(anchor="w")
        self.e_S = ttk.Entry(izq, width=40)
        self.e_S.pack(anchor="w", pady=(0, 6))
        ttk.Button(izq, text="Generar tabla δ  ▶", command=self.generar_tabla).pack(anchor="w")

        ttk.Label(izq, text="3. Función de transición δ:").pack(anchor="w", pady=(8, 0))
        self.f_tabla = ttk.Frame(izq)
        self.f_tabla.pack(anchor="w", pady=4)

        ttk.Label(izq, text="4. Estado inicial q0:").pack(anchor="w")
        self.c_q0 = ttk.Combobox(izq, width=15)
        self.c_q0.pack(anchor="w", pady=(0, 6))
        ttk.Label(izq, text="5. Estados finales F (separados por comas):").pack(anchor="w")
        self.e_F = ttk.Entry(izq, width=40)
        self.e_F.pack(anchor="w", pady=(0, 8))

        botones = ttk.Frame(izq)
        botones.pack(anchor="w")
        ttk.Button(botones, text="Construir autómata", command=self.construir).pack(side="left")
        ttk.Button(botones, text="Cargar ejemplo A2", command=self.ejemplo).pack(side="left", padx=4)
        botones2 = ttk.Frame(izq)
        botones2.pack(anchor="w", pady=4)
        ttk.Button(botones2, text="Guardar (.json)", command=self.guardar).pack(side="left")
        ttk.Button(botones2, text="Abrir (.json)", command=self.cargar).pack(side="left", padx=4)

        self.t_def = tk.Text(izq, width=48, height=11, font=("Consolas", 10))
        self.t_def.pack(anchor="w", pady=6)

        ttk.Label(der, text="Gráfica del autómata", font=("Arial", 12, "bold")).pack()
        self.canvas1 = tk.Canvas(der, width=620, height=560, bg="white",
                                 highlightthickness=1, highlightbackground="#bbb")
        self.canvas1.pack(fill="both", expand=True)

    def generar_tabla(self):
        Q = self.validar_Q()
        S = self.validar_S()
        if Q is None or S is None:
            return
        for w in self.f_tabla.winfo_children():
            w.destroy()
        self.celdas = {}
        ttk.Label(self.f_tabla, text="δ", font=("Arial", 10, "bold")).grid(row=0, column=0)
        for j, a in enumerate(S):
            ttk.Label(self.f_tabla, text=a, font=("Arial", 10, "bold")).grid(row=0, column=j + 1)
        for i, q in enumerate(Q):
            ttk.Label(self.f_tabla, text=q).grid(row=i + 1, column=0, padx=4)
            for j, a in enumerate(S):
                cb = ttk.Combobox(self.f_tabla, values=Q, width=7)
                cb.grid(row=i + 1, column=j + 1, padx=2, pady=1)
                self.celdas[(q, a)] = cb
        self.c_q0["values"] = Q
        self.Q_tabla, self.S_tabla = Q, S

    def validar_Q(self):
        Q = parse_lista(self.e_Q.get())
        if not Q:
            messagebox.showerror("Error en Q", "Debe ingresar al menos un estado.")
            return None
        repetidos = {q for q in Q if Q.count(q) > 1}
        if repetidos:
            messagebox.showerror("Error en Q", f"Estados repetidos: {conj(sorted(repetidos))}. Intente de nuevo.")
            return None
        return Q

    def validar_S(self):
        S = parse_lista(self.e_S.get())
        if not S:
            messagebox.showerror("Error en Σ", "Debe ingresar al menos un símbolo.")
            return None
        largos = [a for a in S if len(a) != 1]
        if largos:
            messagebox.showerror("Error en Σ", f"Cada símbolo debe ser un único carácter: {', '.join(largos)}")
            return None
        repetidos = {a for a in S if S.count(a) > 1}
        if repetidos:
            messagebox.showerror("Error en Σ", f"Símbolos repetidos: {conj(sorted(repetidos))}")
            return None
        return S

    def construir(self):
        Q, S = self.validar_Q(), self.validar_S()
        if Q is None or S is None:
            return
        if Q != self.Q_tabla or S != self.S_tabla:
            messagebox.showerror("Tabla δ", "Q o Σ cambiaron. Presione «Generar tabla δ» y complétela.")
            return
        delta = {}
        for q in Q:
            for a in S:
                valor = self.celdas[(q, a)].get().strip()
                if not valor:
                    messagebox.showerror("Error en δ", f"Falta definir δ({q}, {a}).")
                    return
                if valor not in Q:
                    messagebox.showerror("Error en δ", f"δ({q}, {a}) = {valor}: el estado {valor} "
                                         f"no pertenece a Q = {conj(Q)}. Intente de nuevo.")
                    return
                delta[(q, a)] = valor
        q0 = self.c_q0.get().strip()
        if q0 not in Q:
            messagebox.showerror("Error en q0", f"El estado inicial «{q0}» no pertenece a Q = {conj(Q)}.")
            return
        F = parse_lista(self.e_F.get())
        fuera = [f for f in F if f not in Q]
        if fuera:
            messagebox.showerror("Error en F", f"No pertenecen a Q: {', '.join(fuera)}.")
            return
        F = list(dict.fromkeys(F))
        if not F:
            messagebox.showwarning("Sin estados finales",
                                   "No indicó estados finales: el autómata no reconocerá ninguna palabra.")
        self.establecer_automata(Automata(Q, S, delta, q0, F))

    def establecer_automata(self, M):
        self.M = M  # reemplaza al anterior
        self.t_def.delete("1.0", "end")
        self.t_def.insert("end", "Autómata construido:\n\n" + M.tupla() + "\n\n" + M.tabla())
        dibujar_automata(self.canvas1, M)
        dibujar_automata(self.canvas3, M)
        self.t2.delete("1.0", "end")
        self.t3.delete("1.0", "end")

    def llenar_formulario(self, M):
        self.e_Q.delete(0, "end"); self.e_Q.insert(0, ", ".join(M.Q))
        self.e_S.delete(0, "end"); self.e_S.insert(0, ", ".join(M.sigma))
        self.generar_tabla()
        for (q, a), cb in self.celdas.items():
            cb.set(M.delta[(q, a)])
        self.c_q0.set(M.q0)
        self.e_F.delete(0, "end"); self.e_F.insert(0, ", ".join(M.F))

    def ejemplo(self):
        d = {"Q": ["s0", "s1", "s2"], "sigma": ["a", "b"], "q0": "s0", "F": ["s2"],
             "delta": {"s0": {"a": "s1", "b": "s0"}, "s1": {"a": "s1", "b": "s2"},
                       "s2": {"a": "s1", "b": "s0"}}}
        self.llenar_formulario(Automata.desde_dict(d))

    def guardar(self):
        if self.M is None:
            messagebox.showinfo("Guardar", "Primero construya un autómata.")
            return
        ruta = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(self.M.a_dict(), f, ensure_ascii=False, indent=2)

    def cargar(self):
        ruta = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not ruta:
            return
        try:
            with open(ruta, encoding="utf-8") as f:
                M = Automata.desde_dict(json.load(f))
            self.llenar_formulario(M)
            self.construir()
        except Exception as e:
            messagebox.showerror("Abrir", f"No se pudo leer el archivo: {e}")

    # ---------------- Módulo 2 ----------------
    def crear_modulo2(self):
        f = ttk.Frame(self.tab2, padding=12)
        f.pack(fill="both", expand=True)
        ttk.Label(f, text="Las cinco palabras reconocidas más cortas (orden canónico)",
                  font=("Arial", 12, "bold")).pack(anchor="w")
        ttk.Button(f, text="Calcular", command=self.modulo2).pack(anchor="w", pady=6)
        self.t2 = tk.Text(f, font=("Consolas", 12), height=20)
        self.t2.pack(fill="both", expand=True)

    def modulo2(self):
        M = self.M
        self.t2.delete("1.0", "end")
        self.t2.insert("end", "=== MÓDULO 2: CINCO PALABRAS RECONOCIDAS ===\n\n")
        self.t2.insert("end", f"Autómata: {M.tupla()}\n\n")
        palabras = M.palabras_reconocidas()
        for i, w in enumerate(palabras, 1):
            pasos, _ = M.recorrido(w)
            nombre = w if w else "ε"
            self.t2.insert("end", f"{i}. {nombre:<12} recorrido: {texto_recorrido(pasos, w)}\n")
        if not palabras:
            motivo = ""
            if not M.F:
                motivo = " (no tiene estados finales)"
            elif not (set(M.F) & M.alcanzables()):
                motivo = " (ningún estado final es alcanzable desde el estado inicial)"
            self.t2.insert("end", f"Este autómata no reconoce ninguna palabra{motivo}.\n")
        elif len(palabras) < 5:
            n = len(palabras)
            self.t2.insert("end", f"\nEste autómata solo reconoce {n} palabra{'s' if n > 1 else ''} "
                                  f"de longitud menor o igual que {MAX_LONG}.\n")

    # ---------------- Módulo 3 ----------------
    def crear_modulo3(self):
        izq = ttk.Frame(self.tab3, padding=10)
        izq.pack(side="left", fill="both", expand=True)
        der = ttk.Frame(self.tab3, padding=10)
        der.pack(side="right", fill="both")

        ttk.Label(izq, text="Escriba una palabra (deje vacío para ε) y presione Enter:",
                  font=("Arial", 11, "bold")).pack(anchor="w")
        fila = ttk.Frame(izq)
        fila.pack(anchor="w", pady=6)
        self.e_palabra = ttk.Entry(fila, width=30, font=("Consolas", 12))
        self.e_palabra.pack(side="left")
        self.e_palabra.bind("<Return>", lambda e: self.modulo3())
        ttk.Button(fila, text="Probar", command=self.modulo3).pack(side="left", padx=4)
        ttk.Button(fila, text="Limpiar historial",
                   command=lambda: self.t3.delete("1.0", "end")).pack(side="left")
        self.t3 = tk.Text(izq, font=("Consolas", 11), width=55)
        self.t3.pack(fill="both", expand=True)
        self.t3.tag_config("ok", foreground="#1B7F3B", font=("Consolas", 11, "bold"))
        self.t3.tag_config("no", foreground="#B00020", font=("Consolas", 11, "bold"))

        ttk.Label(der, text="Recorrido resaltado sobre la gráfica",
                  font=("Arial", 11, "bold")).pack()
        self.canvas3 = tk.Canvas(der, width=520, height=520, bg="white",
                                 highlightthickness=1, highlightbackground="#bbb")
        self.canvas3.pack()

    def modulo3(self):
        M = self.M
        w = self.e_palabra.get().strip()
        nombre = w if w else "ε (palabra vacía)"
        self.t3.insert("end", f"Palabra: {nombre}\n")
        pasos, error = M.recorrido(w)
        if error:
            c, p = error
            self.t3.insert("end", f"  ✗ NO RECONOCIDA: el símbolo '{c}' en la posición {p} "
                                  f"no pertenece a Σ = {conj(M.sigma)}.\n", "no")
            dibujar_automata(self.canvas3, M)
        else:
            if not w:
                self.t3.insert("end", f"  No hay símbolos que leer: se queda en {M.q0}.\n")
            else:
                for i, (c, q) in enumerate(zip(w, pasos[1:]), 1):
                    self.t3.insert("end", f"  Paso {i}: δ({pasos[i-1]}, {c}) = {q}\n")
                self.t3.insert("end", f"  Recorrido: {texto_recorrido(pasos, w)}\n")
            fin = pasos[-1]
            if fin in M.F:
                self.t3.insert("end", f"  ✓ RECONOCIDA: termina en {fin}, que es estado final.\n", "ok")
            else:
                self.t3.insert("end", f"  ✗ NO RECONOCIDA: termina en {fin}, que no es estado final.\n", "no")
            resaltar = {}
            for i in range(len(w)):
                resaltar.setdefault((pasos[i], pasos[i + 1]), []).append(i + 1)
            dibujar_automata(self.canvas3, M, resaltar)
        self.t3.insert("end", "¿Desea probar otra palabra? Escríbala arriba y presione Enter.\n\n")
        self.t3.see("end")
        self.e_palabra.delete(0, "end")
        self.e_palabra.focus()

    # ---------------- Navegación ----------------
    def cambio_pestana(self, _evento):
        idx = self.nb.index(self.nb.select())
        if idx > 0 and self.M is None:
            messagebox.showwarning("Falta el autómata",
                                   "Primero debe construir un autómata en el Módulo 1.")
            self.nb.select(0)
        elif idx == 1:
            self.modulo2()
        elif idx == 2:
            self.e_palabra.focus()


if __name__ == "__main__":
    App().mainloop()
