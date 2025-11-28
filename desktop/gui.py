import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import io
from datetime import datetime

# --- IMPORTACIONES DE BASE DE DATOS ---
from db import (
    SessionLocal,
    init_db,
    Medicamento,
    PerfilPaciente,
    Usuario,
    PerfilMedico
)
# Modelos nuevos para recetas locales
from db_recetas_models import RecetaLocal, MedicamentoRecetaLocal, init_recetas_db

# --- IMPORTACIONES DE LÓGICA DE NEGOCIO ---
# Nota: sync_patients_from_drive se importa dentro de la función para evitar ciclos circulares si los hubiera,
# pero es seguro importarlo aquí si sync_patients.py está limpio.
from sync_patients import sync_patients_from_drive
from sync_prescriptions import sync_prescriptions

# Importamos el flujo nuevo que valida XSD y sube a Drive
from receta_flow import procesar_nueva_receta_local 

# --- IMPORTACIONES DE UTILIDADES ---
# Las variables de config se usan en los otros módulos, pero las importamos aquí por completitud.
from config import DRIVE_FOLDER_ID_RECETAS, DRIVE_FOLDER_ID_PACIENTES
from pdf_generator import generar_pdf_receta_local
from printer_utils import enviar_a_impresora

# ==========================================
# CLASES DE UTILIDAD UI (Tooltips, Placeholders)
# ==========================================

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.tooltip = None

    def enter(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, background="#ffffe0", relief="solid", borderwidth=1, font=("Arial", 8))
        label.pack()

    def leave(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class PlaceholderEntry(ttk.Entry):
    def __init__(self, parent, placeholder, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = 'grey'
        self.default_color = 'black'
        self.has_placeholder = True
        self.bind('<FocusIn>', self.focus_in)
        self.bind('<FocusOut>', self.focus_out)
        self.bind('<Key>', self.on_key)
        self.put_placeholder()

    def put_placeholder(self):
        self.delete(0, 'end')
        self.insert(0, self.placeholder)
        self.config(foreground=self.placeholder_color)
        self.has_placeholder = True

    def focus_in(self, *args):
        if self.has_placeholder:
            self.delete('0', 'end')
            self.config(foreground=self.default_color)
            self.has_placeholder = False

    def focus_out(self, *args):
        if not super().get():
            self.put_placeholder()

    def on_key(self, *args):
        if self.has_placeholder:
            self.delete('0', 'end')
            self.config(foreground=self.default_color)
            self.has_placeholder = False

    def get(self):
        return '' if self.has_placeholder else super().get()

class PlaceholderCombobox(ttk.Combobox):
    def __init__(self, parent, placeholder, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = 'grey'
        self.default_color = 'black'
        self.has_placeholder = True
        self.bind('<FocusIn>', self.focus_in)
        self.bind('<FocusOut>', self.focus_out)
        self.bind('<Key>', self.on_key)
        self.bind('<<ComboboxSelected>>', self.on_select)
        self.put_placeholder()

    def put_placeholder(self):
        self.set(self.placeholder)
        self.config(foreground=self.placeholder_color)
        self.has_placeholder = True

    def focus_in(self, *args):
        if self.has_placeholder:
            self.set('')
            self.config(foreground=self.default_color)
            self.has_placeholder = False

    def focus_out(self, *args):
        if not super().get():
            self.put_placeholder()

    def on_key(self, *args):
        if self.has_placeholder:
            self.set('')
            self.config(foreground=self.default_color)
            self.has_placeholder = False

    def on_select(self, *args):
        if self.has_placeholder:
            self.config(foreground=self.default_color)
            self.has_placeholder = False

    def get(self):
        return '' if self.has_placeholder else super().get()


# ==========================================
# PESTAÑA 1: GENERAR Y SINCRONIZAR
# ==========================================

class RecetasTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.load_medicamentos()
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Top frame
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", pady=(0, 10))

        # --- DATOS PACIENTE ---
        patient_frame = ttk.LabelFrame(top_frame, text="Información del Paciente", padding=10)
        patient_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ttk.Label(patient_frame, text="Núm. Afiliación:").grid(row=0, column=0, sticky="w")
        self.entry_num_afiliacion = PlaceholderEntry(patient_frame, "e.g. 12345678", width=15)
        self.entry_num_afiliacion.grid(row=0, column=1, sticky="w")
        self.entry_num_afiliacion.bind("<FocusOut>", self.on_patient_id_change)
        self.entry_num_afiliacion.bind("<Return>", self.on_patient_id_change)
        ToolTip(self.entry_num_afiliacion, "Número de afiliación del paciente (8 dígitos)")

        self.btn_buscar = ttk.Button(patient_frame, text="Buscar Paciente", command=self.buscar_paciente)
        self.btn_buscar.grid(row=0, column=2, sticky="w", padx=(10, 0))

        self.btn_sync_pacientes = ttk.Button(patient_frame, text="Actualizar Pacientes", command=self.actualizar_pacientes)
        self.btn_sync_pacientes.grid(row=0, column=3, sticky="w", padx=(10, 0))
        ToolTip(self.btn_sync_pacientes, "Descarga los pacientes desde Google Drive y actualiza la base local")

        # Campos ocultos de paciente
        self.lbl_primer_nombre = ttk.Label(patient_frame, text="Primer Nombre:")
        self.entry_primer_nombre = PlaceholderEntry(patient_frame, "e.g. Israel", width=20)
        ToolTip(self.entry_primer_nombre, "Primer nombre del paciente")

        self.lbl_segundo_nombre = ttk.Label(patient_frame, text="Segundo Nombre:")
        self.entry_segundo_nombre = PlaceholderEntry(patient_frame, "e.g. Antonio", width=20)
        ToolTip(self.entry_segundo_nombre, "Segundo nombre del paciente (opcional)")

        self.lbl_primer_apellido = ttk.Label(patient_frame, text="Primer Apellido:")
        self.entry_primer_apellido = PlaceholderEntry(patient_frame, "e.g. Rivera", width=20)
        ToolTip(self.entry_primer_apellido, "Primer apellido del paciente")

        self.lbl_segundo_apellido = ttk.Label(patient_frame, text="Segundo Apellido:")
        self.entry_segundo_apellido = PlaceholderEntry(patient_frame, "e.g. García", width=20)
        ToolTip(self.entry_segundo_apellido, "Segundo apellido del paciente (opcional)")

        self.lbl_edad = ttk.Label(patient_frame, text="Edad:")
        self.entry_edad = PlaceholderEntry(patient_frame, "e.g. 35", width=10)
        ToolTip(self.entry_edad, "Edad del paciente en años (solo números)")

        self.lbl_genero = ttk.Label(patient_frame, text="Género:")
        self.entry_genero = PlaceholderCombobox(patient_frame, "Seleccionar", values=["F", "M", "X"], width=10, state="readonly")
        ToolTip(self.entry_genero, "Seleccione el género del paciente (F=Femenino, M=Masculino, X=Otro)")

        self.lbl_email = ttk.Label(patient_frame, text="Email:")
        self.entry_email = PlaceholderEntry(patient_frame, "e.g. israel@email.com", width=30)
        ToolTip(self.entry_email, "Correo electrónico del paciente")

        self.patient_fields_visible = False

        # --- DATOS DOCTOR ---
        doctor_frame = ttk.LabelFrame(top_frame, text="Información del Doctor", padding=10)
        doctor_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        ttk.Label(doctor_frame, text="Nombre:").grid(row=0, column=0, sticky="w")
        self.entry_medico_nombre = PlaceholderEntry(doctor_frame, "e.g. Ana", width=20)
        self.entry_medico_nombre.grid(row=0, column=1, sticky="w")
        ToolTip(self.entry_medico_nombre, "Nombre del médico")

        ttk.Label(doctor_frame, text="Primer Apellido:").grid(row=1, column=0, sticky="w")
        self.entry_medico_primer_apellido = PlaceholderEntry(doctor_frame, "e.g. López", width=20)
        self.entry_medico_primer_apellido.grid(row=1, column=1, sticky="w")
        ToolTip(self.entry_medico_primer_apellido, "Primer apellido del médico")

        ttk.Label(doctor_frame, text="Segundo Apellido:").grid(row=2, column=0, sticky="w")
        self.entry_medico_segundo_apellido = PlaceholderEntry(doctor_frame, "e.g. García", width=20)
        self.entry_medico_segundo_apellido.grid(row=2, column=1, sticky="w")
        ToolTip(self.entry_medico_segundo_apellido, "Segundo apellido del médico (opcional)")

        ttk.Label(doctor_frame, text="Cédula:").grid(row=3, column=0, sticky="w")
        self.entry_cedula = PlaceholderEntry(doctor_frame, "e.g. 12345678", width=20)
        self.entry_cedula.grid(row=3, column=1, sticky="w")
        ToolTip(self.entry_cedula, "Cédula profesional del médico")

        # --- RECETA ---
        prescription_frame = ttk.LabelFrame(main_frame, text="Receta Médica", padding=10)
        prescription_frame.pack(fill="both", expand=True)

        ttk.Label(prescription_frame, text="Diagnóstico:").grid(row=0, column=0, sticky="w")
        self.entry_diag = PlaceholderEntry(prescription_frame, "e.g. Hipertensión arterial", width=40)
        self.entry_diag.grid(row=0, column=1, sticky="w", pady=(0, 10))
        ToolTip(self.entry_diag, "Diagnóstico médico del paciente")

        # Encabezados de medicamentos
        ttk.Label(prescription_frame, text="Medicamento").grid(row=1, column=0, sticky="w", padx=(0, 2))
        ttk.Label(prescription_frame, text="Dósis").grid(row=1, column=1, sticky="w", padx=(110, 2))
        ttk.Label(prescription_frame, text="Frecuencia").grid(row=1, column=2, sticky="w", padx=2)

        self.meds_frame = ttk.Frame(prescription_frame)
        self.meds_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(5, 10))
        
        self.meds_entries = []
        self.med_row_count = 0

        btn_med_frame = ttk.Frame(prescription_frame)
        btn_med_frame.grid(row=3, column=0, columnspan=3, sticky="ew")

        self.btn_add_med = ttk.Button(btn_med_frame, text="Agregar medicamento", command=self.add_medicine_entry)
        self.btn_add_med.pack(side="left", padx=5)
        self.btn_remove_med = ttk.Button(btn_med_frame, text="Quitar medicamento", command=self.remove_medicine_entry)
        self.btn_remove_med.pack(side="left", padx=5)

        self.add_medicine_entry() # Agregar primera fila por defecto

        # --- BOTONES ACCIÓN ---
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        # Botón 1: Generar Receta Local (Nuevo flujo con XSD)
        self.btn_generar = ttk.Button(btn_frame, text="Generar Receta Local", command=self.generar_receta_local)
        self.btn_generar.grid(row=0, column=0, padx=5)

        # Botón 2: Sincronizar desde Drive
        self.btn_recuperar = ttk.Button(btn_frame, text="Sincronizar y Ver Recetas", command=self.recuperar_recetas)
        self.btn_recuperar.grid(row=0, column=1, padx=5)

        # Área de logs/texto
        self.text_area = tk.Text(self, height=10)
        self.text_area.pack(fill="both", expand=True, padx=10, pady=10)

    # --- FUNCIONES ---

    def add_medicine_entry(self):
        e_nombre = PlaceholderEntry(self.meds_frame, "e.g. Paracetamol", width=23)
        e_dosis = PlaceholderEntry(self.meds_frame, "e.g. 500mg", width=15)
        e_freq = PlaceholderEntry(self.meds_frame, "e.g. cada 8 horas", width=20)
        
        e_nombre.grid(row=self.med_row_count, column=0, padx=2, pady=2)
        e_dosis.grid(row=self.med_row_count, column=1, padx=2, pady=2)
        e_freq.grid(row=self.med_row_count, column=2, padx=2, pady=2)
        
        ToolTip(e_nombre, "Seleccione o escriba el nombre del medicamento")
        ToolTip(e_dosis, "Dosis (ej: 500mg, 1 tableta)")
        ToolTip(e_freq, "Frecuencia (ej: cada 8 horas, 2 veces al día)")

        self.meds_entries.append((e_nombre, e_dosis, e_freq))
        self.med_row_count += 1
        if hasattr(self, "btn_remove_med"): self.update_remove_button_visibility()

    def remove_medicine_entry(self):
        if len(self.meds_entries) > 1:
            last = self.meds_entries.pop()
            for w in last: w.destroy()
            self.med_row_count -= 1
            self.update_remove_button_visibility()

    def update_remove_button_visibility(self):
        if len(self.meds_entries) <= 1: self.btn_remove_med.pack_forget()
        else: self.btn_remove_med.pack(side="left", padx=5)

    def on_patient_id_change(self, event=None):
        num = self.entry_num_afiliacion.get().strip()
        if not num or len(num) != 8:
            self.reset_patient_fields()
            return
        
        session = SessionLocal()
        try:
            perfil = session.query(PerfilPaciente).filter_by(num_afiliacion=num).first()
            if perfil:
                if not perfil.integridad_valida:
                    self.reset_patient_fields()
                    messagebox.showerror("Alerta", "Expediente alterado. Contacte al administrador.")
                    return
                self.fill_patient_data(perfil.usuario)
            else:
                self.reset_patient_fields()
        finally:
            session.close()

    def actualizar_pacientes(self):
        if messagebox.askyesno("Confirmar", "¿Descargar pacientes de Drive?"):
            if sync_patients_from_drive():
                messagebox.showinfo("Éxito", "Pacientes actualizados.")
            else:
                messagebox.showwarning("Alerta", "Hubo advertencias en la sincronización.")

    def buscar_paciente(self):
        self.show_patient_fields()
        self.on_patient_id_change()

    def show_patient_fields(self):
        if not self.patient_fields_visible:
            self.lbl_primer_nombre.grid(row=1, column=0, sticky="w"); self.entry_primer_nombre.grid(row=1, column=1, sticky="w")
            self.lbl_segundo_nombre.grid(row=2, column=0, sticky="w"); self.entry_segundo_nombre.grid(row=2, column=1, sticky="w")
            self.lbl_primer_apellido.grid(row=3, column=0, sticky="w"); self.entry_primer_apellido.grid(row=3, column=1, sticky="w")
            self.lbl_segundo_apellido.grid(row=4, column=0, sticky="w"); self.entry_segundo_apellido.grid(row=4, column=1, sticky="w")
            self.lbl_edad.grid(row=5, column=0, sticky="w"); self.entry_edad.grid(row=5, column=1, sticky="w")
            self.lbl_genero.grid(row=6, column=0, sticky="w"); self.entry_genero.grid(row=6, column=1, sticky="w")
            self.lbl_email.grid(row=7, column=0, sticky="w"); self.entry_email.grid(row=7, column=1, sticky="w")
            self.patient_fields_visible = True

    def reset_patient_fields(self):
        for e in [self.entry_primer_nombre, self.entry_segundo_nombre, self.entry_primer_apellido, self.entry_segundo_apellido, self.entry_edad, self.entry_email]:
            e.config(state="normal"); e.put_placeholder(); e.config(state="readonly")
        self.entry_genero.config(state="disabled")

    def fill_patient_data(self, u):
        def set_val(entry, val):
            entry.config(state="normal"); entry.delete(0, "end")
            if val: entry.insert(0, val); entry.config(foreground="black"); entry.has_placeholder = False
            entry.config(state="readonly")

        set_val(self.entry_primer_nombre, u.primer_nombre)
        set_val(self.entry_segundo_nombre, u.segundo_nombre)
        set_val(self.entry_primer_apellido, u.primer_apellido)
        set_val(self.entry_segundo_apellido, u.segundo_apellido)
        set_val(self.entry_edad, str(u.edad) if u.edad else "")
        set_val(self.entry_email, u.email_usuario)
        
        if u.genero:
            self.entry_genero.config(state="normal")
            self.entry_genero.set(u.genero)
            self.entry_genero.config(state="disabled")

    def load_medicamentos(self):
        s = SessionLocal()
        try: self.medicamento_names = [m.nombre for m in s.query(Medicamento).all()]
        except: self.medicamento_names = []
        finally: s.close()

    # --- LÓGICA: GENERAR RECETA LOCAL ---
    def generar_receta_local(self):
        num_afiliacion = self.entry_num_afiliacion.get().strip()
        cedula = self.entry_cedula.get().strip()
        diag = self.entry_diag.get().strip()
        
        if not num_afiliacion or len(num_afiliacion) != 8:
            messagebox.showerror("Error", "Falta número de afiliación válido.")
            return
        if not cedula or not diag:
            messagebox.showerror("Error", "Falta cédula o diagnóstico.")
            return

        medicamentos_ui = []
        for em, ed, ef in self.meds_entries:
            m, d, f = em.get().strip(), ed.get().strip(), ef.get().strip()
            if m and d and f:
                medicamentos_ui.append({'nombre': m, 'dosis': d, 'frecuencia': f})
        
        if not medicamentos_ui:
            messagebox.showerror("Error", "Agregue al menos un medicamento.")
            return

        paciente_nombre = f"{self.entry_primer_nombre.get()} {self.entry_primer_apellido.get()}"
        doc_nombre = f"{self.entry_medico_nombre.get()} {self.entry_medico_primer_apellido.get()}"

        datos_ui = {
            'num_afiliacion': num_afiliacion,
            'paciente_nombre': paciente_nombre,
            'doc_nombre': doc_nombre,
            'doc_cedula': cedula,
            'diagnostico': diag
        }

        # Llamada a receta_flow.py
        exito, mensaje = procesar_nueva_receta_local(datos_ui, medicamentos_ui)

        if exito:
            messagebox.showinfo("Éxito", f"{mensaje}\n\nReceta generada, validada y subida.")
            self.entry_diag.put_placeholder()
            for em, ed, ef in self.meds_entries:
                em.put_placeholder(); ed.put_placeholder(); ef.put_placeholder()
        else:
            messagebox.showerror("Error", f"Error al crear receta:\n{mensaje}")

    # --- LÓGICA: SINCRONIZAR ---
    def recuperar_recetas(self):
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, ">>> Sincronizando con Drive...\n")
        self.update_idletasks()

        buffer = io.StringIO()
        orig_stdout = sys.stdout
        sys.stdout = buffer

        try:
            sync_prescriptions()
        except Exception as e:
            print(f"Error sync: {e}")
        finally:
            sys.stdout = orig_stdout
        
        self.text_area.insert(tk.END, buffer.getvalue())
        self.text_area.insert(tk.END, "\n>>> Sincronización finalizada.\n")

        session = SessionLocal()
        try:
            recetas = session.query(RecetaLocal).order_by(RecetaLocal.fecha_creacion.desc()).all()
            if not recetas:
                self.text_area.insert(tk.END, "No hay recetas locales.\n")
                return

            self.text_area.insert(tk.END, f"\n=== {len(recetas)} Recetas en BD ===\n")
            for r in recetas:
                status = "✅ VÁLIDA" if r.integridad_valida else "❌ ALTERADA"
                self.text_area.insert(tk.END, f"FOLIO: {r.folio_web} | {r.fecha_creacion} | {status}\n")
                if r.integridad_valida:
                    pdf_path = f"pdfs_local/receta_{r.folio_web}.pdf"
                    try:
                        generar_pdf_receta_local(r, r.medicamentos, pdf_path)
                    except Exception as e:
                        self.text_area.insert(tk.END, f"Error PDF: {e}\n")
        finally:
            session.close()

# ==========================================
# PESTAÑA 2: IMPRESIÓN
# ==========================================

class MandarRecetasTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=10, pady=10, fill='x')
        
        ttk.Label(main_frame, text='Seleccionar Receta:').grid(row=0, column=0, sticky='w', pady=5)
        self.receta_combo = ttk.Combobox(main_frame, width=50, state='readonly')
        self.receta_combo.grid(row=0, column=1, sticky='w', padx=5)
        
        self.btn_refresh = ttk.Button(main_frame, text='Actualizar', command=self.load_recetas_locales)
        self.btn_refresh.grid(row=0, column=2, padx=5)
        
        self.btn_mandar = ttk.Button(main_frame, text='Imprimir', command=self.procesar_receta)
        self.btn_mandar.grid(row=1, column=1, pady=10, sticky='w')
        
        self.console_area = tk.Text(self, height=20)
        self.console_area.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.load_recetas_locales()

    def load_recetas_locales(self):
        session = SessionLocal()
        try:
            recetas = session.query(RecetaLocal).filter_by(integridad_valida=True).order_by(RecetaLocal.fecha_creacion.desc()).all()
            opciones = []
            self.recetas_map = {}
            for r in recetas:
                txt = f"Folio: {r.folio_web} - {r.num_afiliacion} - {r.fecha_creacion}"
                opciones.append(txt)
                self.recetas_map[txt] = r.id_receta
            self.receta_combo['values'] = opciones
            self.log(f"Cargadas {len(recetas)} recetas.")
        finally:
            session.close()

    def procesar_receta(self):
        sel = self.receta_combo.get()
        if not sel: return
        rid = self.recetas_map[sel]
        
        session = SessionLocal()
        try:
            r = session.query(RecetaLocal).get(rid)
            if not r: return

            self.log(f"Imprimiendo folio: {r.folio_web}...")
            pdf_dir = os.path.join(os.getcwd(), "pdfs_local")
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, f"receta_{r.folio_web}.pdf")
            
            generar_pdf_receta_local(r, r.medicamentos, pdf_path)
            
            exito, msg = enviar_a_impresora(pdf_path)
            self.log(f"{'✅' if exito else '❌'} {msg}")
            
            if exito:
                r.impresa = True
                session.commit()
        except Exception as e:
            self.log(f"Error: {e}")
        finally:
            session.close()

    def log(self, msg):
        self.console_area.insert(tk.END, f"{msg}\n")
        self.console_area.see(tk.END)

class AppRecetas(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('App Recetas')
        self.geometry('900x700')
        
        init_db()
        init_recetas_db()
        
        try:
            # sync_patients_from_drive() 
            pass
        except: pass
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.recetas_tab = RecetasTab(self.notebook)
        self.notebook.add(self.recetas_tab, text='Generar / Sincronizar')
        
        self.mandar_tab = MandarRecetasTab(self.notebook)
        self.notebook.add(self.mandar_tab, text='Impresión')

if __name__ == "__main__":
    app = AppRecetas()
    app.mainloop()