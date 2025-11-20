# gui.py - simple Tkinter interface with tabs
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from receta_xml import generar_xml_receta, parsear_xml_a_dict
from db import (
    SessionLocal,
    init_db,
    insertar_receta,
    Medicamento,
    buscar_paciente_por_codigo,
    Usuario,
    PerfilMedico,
    Receta,
    RecetaMedicamento,
    obtener_todas_recetas,
    obtener_receta_por_id,
    PerfilPaciente,
)
from drive_client import (
    obtener_servicio,
    subir_archivo_bytes,
    listar_archivos_en_carpeta,
    descargar_archivo,
)
from config import DRIVE_FOLDER_ID
from pdf_generator import generar_pdf_receta_completo
from email_sender import enviar_receta_por_email
from sync_patients import sync_patients_from_drive



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

class RecetasTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.load_medicamentos()
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Top frame for patient and doctor info
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", pady=(0, 10))

        # Patient Info Frame
        patient_frame = ttk.LabelFrame(
            top_frame, text="Información del Paciente", padding=10
        )
        patient_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ttk.Label(patient_frame, text="Núm. Afiliación:").grid(
            row=0, column=0, sticky="w"
        )
        self.entry_num_afiliacion = PlaceholderEntry(
            patient_frame, "e.g. 12345678", width=15
        )
        self.entry_num_afiliacion.grid(row=0, column=1, sticky="w")
        self.entry_num_afiliacion.bind("<FocusOut>", self.on_patient_id_change)
        self.entry_num_afiliacion.bind("<Return>", self.on_patient_id_change)
        ToolTip(
            self.entry_num_afiliacion,
            "Número de afiliación del paciente (8 dígitos)",
        )

        self.btn_buscar = ttk.Button(
            patient_frame, text="Buscar Paciente", command=self.buscar_paciente
        )
        self.btn_buscar.grid(row=0, column=2, sticky="w", padx=(10, 0))

        # 🔄 Botón para actualizar pacientes desde Drive
        self.btn_sync_pacientes = ttk.Button(
            patient_frame,
            text="Actualizar Pacientes",
            command=self.actualizar_pacientes,
        )
        self.btn_sync_pacientes.grid(row=0, column=3, sticky="w", padx=(10, 0))
        ToolTip(
            self.btn_sync_pacientes,
            "Descarga los pacientes desde Google Drive y actualiza la base local",
        )

        # Hidden patient fields (initially)
        self.lbl_primer_nombre = ttk.Label(patient_frame, text="Primer Nombre:")
        self.entry_primer_nombre = PlaceholderEntry(
            patient_frame, "e.g. Israel", width=20
        )
        ToolTip(self.entry_primer_nombre, "Primer nombre del paciente")

        self.lbl_segundo_nombre = ttk.Label(patient_frame, text="Segundo Nombre:")
        self.entry_segundo_nombre = PlaceholderEntry(
            patient_frame, "e.g. Antonio", width=20
        )
        ToolTip(
            self.entry_segundo_nombre,
            "Segundo nombre del paciente (opcional)",
        )

        self.lbl_primer_apellido = ttk.Label(patient_frame, text="Primer Apellido:")
        self.entry_primer_apellido = PlaceholderEntry(
            patient_frame, "e.g. Rivera", width=20
        )
        ToolTip(self.entry_primer_apellido, "Primer apellido del paciente")

        self.lbl_segundo_apellido = ttk.Label(
            patient_frame, text="Segundo Apellido:"
        )
        self.entry_segundo_apellido = PlaceholderEntry(
            patient_frame, "e.g. García", width=20
        )
        ToolTip(
            self.entry_segundo_apellido,
            "Segundo apellido del paciente (opcional)",
        )

        self.lbl_edad = ttk.Label(patient_frame, text="Edad:")
        self.entry_edad = PlaceholderEntry(patient_frame, "e.g. 35", width=10)
        ToolTip(self.entry_edad, "Edad del paciente en años (solo números)")

        self.lbl_genero = ttk.Label(patient_frame, text="Género:")
        self.entry_genero = PlaceholderCombobox(
            patient_frame,
            "Seleccionar",
            values=["F", "M", "X"],
            width=10,
            state="readonly",
        )
        ToolTip(
            self.entry_genero,
            "Seleccione el género del paciente (F=Femenino, M=Masculino, X=Otro)",
        )

        self.lbl_email = ttk.Label(patient_frame, text="Email:")
        self.entry_email = PlaceholderEntry(
            patient_frame, "e.g. israel@email.com", width=30
        )
        ToolTip(self.entry_email, "Correo electrónico del paciente")

        self.patient_fields_visible = False

        # Doctor Info Frame
        doctor_frame = ttk.LabelFrame(
            top_frame, text="Información del Doctor", padding=10
        )
        doctor_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        ttk.Label(doctor_frame, text="Nombre:").grid(
            row=0, column=0, sticky="w"
        )
        self.entry_medico_nombre = PlaceholderEntry(
            doctor_frame, "e.g. Ana", width=20
        )
        self.entry_medico_nombre.grid(row=0, column=1, sticky="w")
        ToolTip(self.entry_medico_nombre, "Nombre del médico")

        ttk.Label(doctor_frame, text="Primer Apellido:").grid(
            row=1, column=0, sticky="w"
        )
        self.entry_medico_primer_apellido = PlaceholderEntry(
            doctor_frame, "e.g. López", width=20
        )
        self.entry_medico_primer_apellido.grid(row=1, column=1, sticky="w")
        ToolTip(
            self.entry_medico_primer_apellido,
            "Primer apellido del médico",
        )

        ttk.Label(doctor_frame, text="Segundo Apellido:").grid(
            row=2, column=0, sticky="w"
        )
        self.entry_medico_segundo_apellido = PlaceholderEntry(
            doctor_frame, "e.g. García", width=20
        )
        self.entry_medico_segundo_apellido.grid(row=2, column=1, sticky="w")
        ToolTip(
            self.entry_medico_segundo_apellido,
            "Segundo apellido del médico (opcional)",
        )

        ttk.Label(doctor_frame, text="Cédula:").grid(
            row=3, column=0, sticky="w"
        )
        self.entry_cedula = PlaceholderEntry(
            doctor_frame, "e.g. 12345678", width=20
        )
        self.entry_cedula.grid(row=3, column=1, sticky="w")
        ToolTip(self.entry_cedula, "Cédula profesional del médico")

        # Prescription Frame
        prescription_frame = ttk.LabelFrame(
            main_frame, text="Receta Médica", padding=10
        )
        prescription_frame.pack(fill="both", expand=True)

        ttk.Label(prescription_frame, text="Diagnóstico:").grid(
            row=0, column=0, sticky="w"
        )
        self.entry_diag = PlaceholderEntry(
            prescription_frame,
            "e.g. Hipertensión arterial",
            width=40,
        )
        self.entry_diag.grid(row=0, column=1, sticky="w", pady=(0, 10))
        ToolTip(self.entry_diag, "Diagnóstico médico del paciente")

        # Medicine headers
        ttk.Label(prescription_frame, text="Medicamento").grid(
            row=1, column=0, sticky="w", padx=(0, 2)
        )
        ttk.Label(prescription_frame, text="Dósis").grid(
            row=1, column=1, sticky="w", padx=(110, 2)
        )
        ttk.Label(prescription_frame, text="Frecuencia").grid(
            row=1, column=2, sticky="w", padx=2
        )

        # Container for medicine entries
        self.meds_frame = ttk.Frame(prescription_frame)
        self.meds_frame.grid(
            row=2, column=0, columnspan=3, sticky="ew", pady=(5, 10)
        )

        self.meds_entries = []
        self.med_row_count = 0

        # Medicine buttons frame
        btn_med_frame = ttk.Frame(prescription_frame)
        btn_med_frame.grid(
            row=3, column=0, columnspan=3, sticky="ew"
        )

        self.btn_add_med = ttk.Button(
            btn_med_frame,
            text="Agregar medicamento",
            command=self.add_medicine_entry,
        )
        self.btn_add_med.pack(side="left", padx=5)

        self.btn_remove_med = ttk.Button(
            btn_med_frame,
            text="Quitar medicamento",
            command=self.remove_medicine_entry,
        )
        self.btn_remove_med.pack(side="left", padx=5)

        # Add first medicine entry
        self.add_medicine_entry()

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        self.btn_generar = ttk.Button(
            btn_frame, text="Generar receta", command=self.generar_receta
        )
        self.btn_generar.grid(row=0, column=0, padx=5)

        self.btn_recuperar = ttk.Button(
            btn_frame,
            text="Recuperar recetas",
            command=self.recuperar_recetas,
        )
        self.btn_recuperar.grid(row=0, column=1, padx=5)

        self.text_area = tk.Text(self, height=15)
        self.text_area.pack(fill="both", expand=True, padx=10, pady=10)

    def add_medicine_entry(self):
        e_nombre = PlaceholderEntry(
            self.meds_frame, "e.g. Paracetamol", width=23
        )
        e_dosis = PlaceholderEntry(self.meds_frame, "e.g. 500mg", width=15)
        e_freq = PlaceholderEntry(
            self.meds_frame, "e.g. cada 8 horas", width=20
        )

        e_nombre.grid(row=self.med_row_count, column=0, padx=2, pady=2)
        e_dosis.grid(row=self.med_row_count, column=1, padx=2, pady=2)
        e_freq.grid(row=self.med_row_count, column=2, padx=2, pady=2)

        ToolTip(
            e_nombre,
            "Seleccione o escriba el nombre del medicamento",
        )
        ToolTip(e_dosis, "Dosis (ej: 500mg, 1 tableta)")
        ToolTip(
            e_freq,
            "Frecuencia (ej: cada 8 horas, 2 veces al día)",
        )

        self.meds_entries.append((e_nombre, e_dosis, e_freq))
        self.med_row_count += 1
        if hasattr(self, "btn_remove_med"):
            self.update_remove_button_visibility()

    def remove_medicine_entry(self):
        if len(self.meds_entries) > 1:
            last_entry = self.meds_entries.pop()
            for widget in last_entry:
                widget.destroy()
            self.med_row_count -= 1
            self.update_remove_button_visibility()

    def update_remove_button_visibility(self):
        if len(self.meds_entries) <= 1:
            self.btn_remove_med.pack_forget()
        else:
            self.btn_remove_med.pack(side="left", padx=5)

    def on_patient_id_change(self, event=None):
        num_afiliacion = self.entry_num_afiliacion.get().strip()
        if not num_afiliacion or len(num_afiliacion) != 8:
            self.reset_patient_fields()
            return

        session = SessionLocal()
        try:
            perfil = (
                session.query(PerfilPaciente)
                .filter_by(num_afiliacion=num_afiliacion)
                .first()
            )

            if perfil:
                if not perfil.integridad_valida:
                    self.reset_patient_fields()
                    messagebox.showerror(
                        "Documento alterado",
                        (
                            "El expediente de este paciente fue alterado o no pasó "
                            "la verificación de integridad.\n"
                            "Contacte al administrador del sistema."
                        ),
                    )
                    return

                usuario = perfil.usuario
                self.fill_patient_data(usuario)
            else:
                self.reset_patient_fields()
                messagebox.showwarning(
                    "Paciente no encontrado",
                    (
                        "El Número de Afiliación que ha buscado no pertenece a un paciente "
                        "existente/activo. Intente nuevamente."
                    ),
                )
        except Exception as e:
            print(f"Error buscando paciente: {e}")
            self.reset_patient_fields()
            messagebox.showerror(
                "Error", f"Error al buscar paciente: {str(e)}"
            )
        finally:
            session.close()

    def next_field(self, next_widget):
        next_widget.focus_set()

    def focus_first_medicine(self):
        if self.meds_entries:
            self.meds_entries[0][0].focus_set()

    def actualizar_pacientes(self):
        """Ejecuta la sincronización de pacientes desde Google Drive."""
        try:
            res = messagebox.askyesno(
                "Actualizar pacientes",
                "Se descargarán y validarán los pacientes desde Google Drive.\n"
                "¿Desea continuar?",
            )
            if not res:
                return

            ok = sync_patients_from_drive()
            if ok:
                messagebox.showinfo(
                    "Actualización completa",
                    "Los pacientes se han actualizado correctamente desde Google Drive.",
                )
            else:
                messagebox.showwarning(
                    "Actualización con advertencias",
                    "La sincronización terminó con advertencias. Revise la consola/log del sistema.",
                )
        except Exception as e:
            print(f"Error al sincronizar pacientes: {e}")
            messagebox.showerror(
                "Error",
                f"Ocurrió un error al actualizar pacientes:\n{e}",
            )

    def buscar_paciente(self):
        num_afiliacion = self.entry_num_afiliacion.get().strip()
        if not num_afiliacion:
            messagebox.showwarning(
                "Advertencia", "Ingrese un número de afiliación"
            )
            return

        if len(num_afiliacion) != 8:
            messagebox.showwarning(
                "Advertencia",
                "El número de afiliación debe tener 8 dígitos",
            )
            return

        self.show_patient_fields()
        self.on_patient_id_change()

    def show_patient_fields(self):
        if not self.patient_fields_visible:
            self.lbl_primer_nombre.grid(row=1, column=0, sticky="w")
            self.entry_primer_nombre.grid(row=1, column=1, sticky="w")

            self.lbl_segundo_nombre.grid(row=2, column=0, sticky="w")
            self.entry_segundo_nombre.grid(row=2, column=1, sticky="w")

            self.lbl_primer_apellido.grid(row=3, column=0, sticky="w")
            self.entry_primer_apellido.grid(row=3, column=1, sticky="w")

            self.lbl_segundo_apellido.grid(row=4, column=0, sticky="w")
            self.entry_segundo_apellido.grid(row=4, column=1, sticky="w")

            self.lbl_edad.grid(row=5, column=0, sticky="w")
            self.entry_edad.grid(row=5, column=1, sticky="w")

            self.lbl_genero.grid(row=6, column=0, sticky="w")
            self.entry_genero.grid(row=6, column=1, sticky="w")

            self.lbl_email.grid(row=7, column=0, sticky="w")
            self.entry_email.grid(row=7, column=1, sticky="w")

            self.patient_fields_visible = True

    def reset_patient_fields(self):
        # Temporarily enable fields to clear and set placeholders
        self.entry_primer_nombre.config(state="normal")
        self.entry_segundo_nombre.config(state="normal")
        self.entry_primer_apellido.config(state="normal")
        self.entry_segundo_apellido.config(state="normal")
        self.entry_edad.config(state="normal")
        self.entry_genero.config(state="readonly")
        self.entry_email.config(state="normal")

        # Clear fields and set placeholders
        self.entry_primer_nombre.put_placeholder()
        self.entry_segundo_nombre.put_placeholder()
        self.entry_primer_apellido.put_placeholder()
        self.entry_segundo_apellido.put_placeholder()
        self.entry_edad.put_placeholder()
        self.entry_genero.put_placeholder()
        self.entry_email.put_placeholder()

        # Set all fields to read-only state
        self.entry_primer_nombre.config(state="readonly")
        self.entry_segundo_nombre.config(state="readonly")
        self.entry_primer_apellido.config(state="readonly")
        self.entry_segundo_apellido.config(state="readonly")
        self.entry_edad.config(state="readonly")
        self.entry_genero.config(state="disabled")
        self.entry_email.config(state="readonly")

    def fill_patient_data(self, usuario):
        # Enable fields temporarily to fill data
        self.entry_primer_nombre.config(state="normal")
        self.entry_segundo_nombre.config(state="normal")
        self.entry_primer_apellido.config(state="normal")
        self.entry_segundo_apellido.config(state="normal")
        self.entry_edad.config(state="normal")
        self.entry_genero.config(state="normal")
        self.entry_email.config(state="normal")

        # Clear and fill primer nombre
        self.entry_primer_nombre.delete(0, "end")
        self.entry_primer_nombre.insert(0, usuario.primer_nombre)
        self.entry_primer_nombre.config(foreground="black")
        self.entry_primer_nombre.has_placeholder = False

        # Clear and fill segundo nombre
        self.entry_segundo_nombre.delete(0, "end")
        if usuario.segundo_nombre:
            self.entry_segundo_nombre.insert(0, usuario.segundo_nombre)
        self.entry_segundo_nombre.config(foreground="black")
        self.entry_segundo_nombre.has_placeholder = False

        # Clear and fill primer apellido
        self.entry_primer_apellido.delete(0, "end")
        self.entry_primer_apellido.insert(0, usuario.primer_apellido)
        self.entry_primer_apellido.config(foreground="black")
        self.entry_primer_apellido.has_placeholder = False

        # Clear and fill segundo apellido
        self.entry_segundo_apellido.delete(0, "end")
        if usuario.segundo_apellido:
            self.entry_segundo_apellido.insert(0, usuario.segundo_apellido)
        self.entry_segundo_apellido.config(foreground="black")
        self.entry_segundo_apellido.has_placeholder = False

        # Clear and fill age
        self.entry_edad.delete(0, "end")
        if usuario.edad:
            self.entry_edad.insert(0, str(usuario.edad))
        self.entry_edad.config(foreground="black")
        self.entry_edad.has_placeholder = False

        # Clear and fill gender
        if usuario.genero:
            self.entry_genero.set(usuario.genero)
        self.entry_genero.config(foreground="black")
        self.entry_genero.has_placeholder = False

        # Clear and fill email
        self.entry_email.delete(0, "end")
        if usuario.email_usuario:
            self.entry_email.insert(0, usuario.email_usuario)
        self.entry_email.config(foreground="black")
        self.entry_email.has_placeholder = False

        # Set all fields back to readonly
        self.entry_primer_nombre.config(state="readonly")
        self.entry_segundo_nombre.config(state="readonly")
        self.entry_primer_apellido.config(state="readonly")
        self.entry_segundo_apellido.config(state="readonly")
        self.entry_edad.config(state="readonly")
        self.entry_genero.config(state="disabled")
        self.entry_email.config(state="readonly")

    def load_medicamentos(self):
        session = SessionLocal()
        try:
            medicamentos = session.query(Medicamento).all()
            self.medicamento_names = [med.nombre for med in medicamentos]
        except Exception:
            self.medicamento_names = []
        finally:
            session.close()

    def generar_receta(self):
        # Validaciones básicas
        num_afiliacion = self.entry_num_afiliacion.get().strip()
        if not num_afiliacion or len(num_afiliacion) != 8:
            messagebox.showerror(
                "Error",
                "Debe ingresar un número de afiliación válido de 8 dígitos",
            )
            return

        if not self.entry_diag.get():
            messagebox.showerror(
                "Error",
                "Debe ingresar un diagnóstico",
            )
            return

        if not self.entry_cedula.get():
            messagebox.showerror(
                "Error",
                "Debe ingresar la cédula del médico",
            )
            return

        # Construir lista de medicamentos a partir de las filas dinámicas
        medicamentos = []
        for en_med, en_dosis, en_freq in self.meds_entries:
            med = en_med.get().strip()
            dosis = en_dosis.get().strip()
            freq = en_freq.get().strip()
            if med or dosis or freq:
                if not (med and dosis and freq):
                    messagebox.showerror(
                        "Error",
                        "Todas las columnas (Medicamento, Dosis y Frecuencia) "
                        "deben estar llenas para cada fila.",
                    )
                    return
                medicamentos.append(
                    {
                        "medicamento": med,
                        "dosis": dosis,
                        "frecuencia": freq,
                    }
                )

        if not medicamentos:
            messagebox.showerror(
                "Error",
                "Debe agregar al menos un medicamento",
            )
            return

        session = SessionLocal()
        try:
            # ===================== PACIENTE =====================
            perfil = (
                session.query(PerfilPaciente)
                .filter_by(num_afiliacion=num_afiliacion)
                .first()
            )

            if not perfil:
                messagebox.showerror("Error", "Paciente no encontrado")
                return

            if not perfil.integridad_valida:
                messagebox.showerror(
                    "Documento alterado",
                    (
                        "El expediente de este paciente fue alterado o no pasó la "
                        "verificación de integridad.\n"
                        "No es posible generar recetas hasta que se solucione el problema."
                    ),
                )
                return

            usuario = perfil.usuario

            # ===================== MÉDICO =====================
            cedula = self.entry_cedula.get().strip()
            perfil_medico = (
                session.query(PerfilMedico)
                .filter_by(cedula_profesional=cedula)
                .first()
            )

            if not perfil_medico:
                usuario_medico = Usuario(
                    email_usuario=f"{cedula}@medico.com",
                    primer_nombre=self.entry_medico_nombre.get().strip(),
                    primer_apellido=self.entry_medico_primer_apellido.get().strip(),
                    segundo_apellido=self.entry_medico_segundo_apellido.get().strip(),
                    edad=35,
                    genero="M",
                    numero_telefono="0000000000",
                    es_staff=True,
                )
                session.add(usuario_medico)
                session.flush()

                perfil_medico = PerfilMedico(
                    id_usuario=usuario_medico.id_usuario,
                    cedula_profesional=cedula,
                )
                session.add(perfil_medico)
                session.flush()

            # ===================== RECETA =====================
            receta = Receta(
                paciente=usuario.id_usuario,
                medico=perfil_medico.id_medico,
                diagnostico=self.entry_diag.get(),
            )
            session.add(receta)
            session.flush()

            # ===================== MEDICAMENTOS =====================
            for med_data in medicamentos:
                medicamento = (
                    session.query(Medicamento)
                    .filter_by(nombre=med_data["medicamento"])
                    .first()
                )
                if not medicamento:
                    medicamento = Medicamento(nombre=med_data["medicamento"])
                    session.add(medicamento)
                    session.flush()

                rm = RecetaMedicamento(
                    receta_id=receta.id,
                    medicamento_id=medicamento.id,
                    dosis=med_data["dosis"],
                    frecuencia=med_data["frecuencia"],
                )
                session.add(rm)

            session.commit()
            messagebox.showinfo(
                "Éxito",
                f"Receta generada exitosamente (ID: {receta.id})",
            )

            # Limpiar algunos campos de la UI
            self.entry_diag.put_placeholder()
            for en_med, en_dosis, en_freq in self.meds_entries:
                en_med.put_placeholder()
                en_dosis.put_placeholder()
                en_freq.put_placeholder()

        except Exception as e:
            session.rollback()
            messagebox.showerror(
                "Error",
                f"Error al generar receta: {str(e)}",
            )
        finally:
            session.close()

    def recuperar_recetas(self):
        try:
            service = obtener_servicio()
            files = listar_archivos_en_carpeta(service, DRIVE_FOLDER_ID)
            if not files:
                messagebox.showinfo(
                    "Info",
                    "No se encontraron archivos XML en la carpeta.",
                )
                return
            for f in files:
                xml_bytes = descargar_archivo(service, f["id"])
                receta_dict = parsear_xml_a_dict(xml_bytes)
                self.text_area.insert(
                    tk.END, f"--- Archivo: {f['name']} ---\n"
                )
                self.text_area.insert(
                    tk.END, xml_bytes.decode("utf-8") + "\n\n"
                )
                session = SessionLocal()
                try:
                    insertar_receta(session, receta_dict)
                finally:
                    session.close()
            messagebox.showinfo(
                "Éxito",
                "Archivos recuperados e insertados en la base de datos.",
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))




class MandarRecetasTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=10, pady=10, fill='x')
        
        # Receta selection
        ttk.Label(main_frame, text='Seleccionar Receta:').grid(row=0, column=0, sticky='w', pady=5)
        
        self.receta_combo = ttk.Combobox(main_frame, width=50, state='readonly')
        self.receta_combo.grid(row=0, column=1, sticky='w', padx=5)
        
        # Refresh button
        self.btn_refresh = ttk.Button(main_frame, text='Actualizar Lista', command=self.load_recetas)
        self.btn_refresh.grid(row=0, column=2, padx=5)
        
        # Send button
        self.btn_mandar = ttk.Button(main_frame, text='Mandar Receta', command=self.mandar_receta)
        self.btn_mandar.grid(row=1, column=1, pady=10, sticky='w')
        
        # Console area
        ttk.Label(self, text='Consola:').pack(anchor='w', padx=10)
        self.console_area = tk.Text(self, height=20)
        self.console_area.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Load initial data
        self.load_recetas()

    def load_recetas(self):
        session = SessionLocal()
        try:
            recetas = obtener_todas_recetas(session)
            self.receta_combo['values'] = [f"ID: {r['id']} - {r['paciente']} - {r['diagnostico'][:30]}..." for r in recetas]
            self.recetas_data = {f"ID: {r['id']} - {r['paciente']} - {r['diagnostico'][:30]}...": r['id'] for r in recetas}
            self.log_message(f"Cargadas {len(recetas)} recetas")
        except Exception as e:
            self.log_message(f"Error cargando recetas: {str(e)}")
        finally:
            session.close()

    def mandar_receta(self):
        if not self.receta_combo.get():
            self.log_message("Error: Debe seleccionar una receta")
            return
            
        receta_id = self.recetas_data[self.receta_combo.get()]
        self.log_message(f"Procesando receta ID: {receta_id}")
        
        session = SessionLocal()
        try:
            receta_info = obtener_receta_por_id(session, receta_id)
            if not receta_info:
                self.log_message(f"Error: No se encontró la receta con ID {receta_id}")
                return
                
            self.log_message("=== INFORMACIÓN DE LA RECETA ===")
            self.log_message(f"ID: {receta_info['id']}")
            self.log_message(f"Paciente: {receta_info['paciente']['nombre']}")
            self.log_message(f"Email: {receta_info['paciente']['correo']}")
            self.log_message(f"Médico: {receta_info['medico']['nombre']}")
            self.log_message(f"Diagnóstico: {receta_info['diagnostico']}")
            self.log_message(f"Fecha: {receta_info['fecha']}")
            self.log_message("\nMedicamentos:")
            for med in receta_info['medicamentos']:
                self.log_message(f"- {med['medicina']} | {med['dosis']} | {med['frecuencia']}")
            
            # Generar PDF
            self.log_message("\n=== GENERANDO PDF ===")
            filepath, password = generar_pdf_receta_completo(receta_info)
            self.log_message(f"PDF generado: {filepath}")
            self.log_message(f"Contraseña generada: {password}")
            
            # Enviar por email
            self.log_message("\n=== ENVIANDO POR EMAIL ===")
            success, message = enviar_receta_por_email(receta_info, filepath, password)
            if success:
                self.log_message(f"✓ {message}")
                self.log_message("✓ PDF enviado al paciente")
                self.log_message("✓ Contraseña enviada por separado")
            else:
                self.log_message(f"✗ {message}")
            
            self.log_message("\n" + "="*50)
            
        except Exception as e:
            self.log_message(f"Error procesando receta: {str(e)}")
        finally:
            session.close()

    def log_message(self, message):
        self.console_area.insert(tk.END, f"{message}\n")
        self.console_area.see(tk.END)

class AppRecetas(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('App Recetas')
        self.geometry('900x600')
        
        # Initialize database
        init_db()
        
        # Sync with Google Drive first
        try:
            self.sync_with_drive()
        except:
            pass  # Continue without sync if it fails
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add Recetas tab
        self.recetas_tab = RecetasTab(self.notebook)
        self.notebook.add(self.recetas_tab, text='Generar Recetas')
        
        # Add Mandar Recetas tab
        self.mandar_tab = MandarRecetasTab(self.notebook)
        self.notebook.add(self.mandar_tab, text='Mandar Recetas')
    
    def sync_with_drive(self):
        try:
            from sync_patients import sync_patients_from_drive
            sync_patients_from_drive()
        except Exception as e:
            messagebox.showerror('Error de sincronización', f'No se pudo sincronizar con Google Drive: {str(e)}')