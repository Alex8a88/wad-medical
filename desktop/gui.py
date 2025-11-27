import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import io
from datetime import datetime

# Importaciones de Base de Datos
from db import (
    SessionLocal,
    init_db,
    Medicamento,
    PerfilPaciente,
    Usuario,
    PerfilMedico
)
# Importamos los NUEVOS modelos y funciones de recetas
from db_recetas_models import RecetaLocal, MedicamentoRecetaLocal, init_recetas_db
from sync_prescriptions import sync_prescriptions

# Importaciones de Drive y Configuración
from config import DRIVE_FOLDER_ID_RECETAS, DRIVE_FOLDER_ID_PACIENTES 
from sync_patients import sync_patients_from_drive

# Importaciones de Utilidades
from pdf_generator import generar_pdf_receta_local
from printer_utils import enviar_a_impresora

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

        self.btn_recuperar = ttk.Button(
            btn_frame,
            text="Sincronizar y Ver Recetas",
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

    def recuperar_recetas(self):
        """
        Sincroniza recetas desde Drive y luego las muestra/imprime.
        CAPTURAMOS LA CONSOLA para mostrar lo que pasa.
        """
        try:
            # Limpiar área de texto
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, ">>> Iniciando proceso de sincronización...\n")
            self.update_idletasks()

            # --- CAPTURAR SALIDA DE CONSOLA (STDOUT) ---
            buffer = io.StringIO()
            original_stdout = sys.stdout
            sys.stdout = buffer # Redirigir prints a nuestra variable buffer

            try:
                # 1. Ejecutar sincronización
                sync_prescriptions()
            except Exception as e:
                print(f"\n❌ Error crítico durante la sincronización: {e}")
            finally:
                # Restaurar consola normal
                sys.stdout = original_stdout
            
            # Mostrar lo capturado en la GUI
            log_output = buffer.getvalue()
            self.text_area.insert(tk.END, log_output)
            self.text_area.insert(tk.END, "\n>>> Fin del proceso de sincronización.\n")
            # -------------------------------------------
            
            # 2. Leer de la Base de Datos local
            session = SessionLocal()
            try:
                recetas = session.query(RecetaLocal).order_by(RecetaLocal.fecha_creacion.desc()).all()
                
                if not recetas:
                    self.text_area.insert(tk.END, "\n[INFO] No hay recetas registradas en la base de datos local.\n")
                    return

                self.text_area.insert(tk.END, f"\n=== RESUMEN: {len(recetas)} recetas en BD local ===\n")

                for receta in recetas:
                    estado_integridad = "✅ VÁLIDA" if receta.integridad_valida else "❌ ALTERADA"
                    self.text_area.insert(tk.END, f"FOLIO: {receta.folio_web}\n")
                    self.text_area.insert(tk.END, f"FECHA: {receta.fecha_creacion}\n")
                    self.text_area.insert(tk.END, f"PACIENTE: {receta.num_afiliacion}\n")
                    self.text_area.insert(tk.END, f"INTEGRIDAD: {estado_integridad}\n")
                    
                    if not receta.integridad_valida:
                        self.text_area.insert(tk.END, "⚠️ ESTA RECETA NO SE PUEDE PROCESAR POR SEGURIDAD.\n")
                    else:
                        # Generar PDF Localmente si es válida
                        pdf_path = f"pdfs_local/receta_{receta.folio_web}.pdf"
                        try:
                            # Pasamos los medicamentos de la relación
                            generar_pdf_receta_local(receta, receta.medicamentos, pdf_path)
                            self.text_area.insert(tk.END, f"📄 PDF Generado: {pdf_path}\n")
                        except Exception as pdf_err:
                            self.text_area.insert(tk.END, f"❌ Error generando PDF: {pdf_err}\n")

                    self.text_area.insert(tk.END, "-"*30 + "\n")

            finally:
                session.close()

            messagebox.showinfo("Proceso Finalizado", "Revise el área de texto para ver los resultados.")

        except Exception as e:
            messagebox.showerror("Error", f"Error general: {str(e)}")


class MandarRecetasTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=10, pady=10, fill='x')
        
        # Receta selection
        ttk.Label(main_frame, text='Seleccionar Receta Local:').grid(row=0, column=0, sticky='w', pady=5)
        
        self.receta_combo = ttk.Combobox(main_frame, width=50, state='readonly')
        self.receta_combo.grid(row=0, column=1, sticky='w', padx=5)
        
        # Refresh button
        self.btn_refresh = ttk.Button(main_frame, text='Actualizar Lista', command=self.load_recetas_locales)
        self.btn_refresh.grid(row=0, column=2, padx=5)
        
        # Send button (Simulado para impresión o reenvío)
        self.btn_mandar = ttk.Button(main_frame, text='Imprimir / Procesar', command=self.procesar_receta)
        self.btn_mandar.grid(row=1, column=1, pady=10, sticky='w')
        
        # Console area
        ttk.Label(self, text='Estado:').pack(anchor='w', padx=10)
        self.console_area = tk.Text(self, height=20)
        self.console_area.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Load initial data
        self.load_recetas_locales()

    def load_recetas_locales(self):
        session = SessionLocal()
        try:
            # Cargamos recetas locales validadas
            recetas = session.query(RecetaLocal).filter_by(integridad_valida=True).all()
            
            opciones = []
            self.recetas_map = {}
            
            for r in recetas:
                texto = f"Folio: {r.folio_web} - {r.num_afiliacion} - {r.fecha_creacion}"
                opciones.append(texto)
                self.recetas_map[texto] = r.id_receta
                
            self.receta_combo['values'] = opciones
            self.log_message(f"Cargadas {len(recetas)} recetas locales válidas.")
        except Exception as e:
            self.log_message(f"Error cargando recetas: {str(e)}")
        finally:
            session.close()

    def procesar_receta(self):
        seleccion = self.receta_combo.get()
        if not seleccion:
            self.log_message("Error: Debe seleccionar una receta")
            return
            
        try:
            # Obtener ID del mapa
            receta_id = self.recetas_map[seleccion]
        except KeyError:
            self.log_message("Error: Seleccione una receta válida de la lista.")
            return

        self.log_message(f"Procesando receta local ID: {receta_id}")
        
        session = SessionLocal()
        try:
            receta = session.query(RecetaLocal).get(receta_id)
            if not receta:
                self.log_message("Error: Receta no encontrada en BD.")
                return
            
            self.log_message("=== INFORMACIÓN DE LA RECETA ===")
            self.log_message(f"Folio: {receta.folio_web}")
            self.log_message(f"Paciente: {receta.num_afiliacion}")
            self.log_message(f"Médico: {receta.nombre_doctor}")
            
            # 1. Generar el PDF Localmente (para asegurar que existe)
            # Creamos carpeta si no existe
            pdf_dir = os.path.join(os.getcwd(), "pdfs_local")
            os.makedirs(pdf_dir, exist_ok=True)
            
            pdf_name = f"receta_{receta.folio_web}.pdf"
            pdf_path = os.path.join(pdf_dir, pdf_name)
            
            self.log_message(f"Generando PDF en: {pdf_path}")
            
            # Usamos la función de generación (pasando la receta y sus medicamentos)
            generar_pdf_receta_local(receta, receta.medicamentos, pdf_path)
            
            self.log_message("✅ PDF Generado correctamente.")
            
            # 2. IMPRESIÓN REAL (El cambio importante)
            self.log_message("🖨️ Iniciando servicio de impresión de Windows...")
            
            exito, mensaje = enviar_a_impresora(pdf_path)
            
            if exito:
                self.log_message(f"✅ ÉXITO: {mensaje}")
                self.log_message(">> Revisa tu impresora predeterminada.")
                
                # Marcar como impresa en base de datos
                receta.impresa = True
                session.commit()
            else:
                self.log_message(f"❌ ERROR DE IMPRESIÓN: {mensaje}")
            
            self.log_message("\n" + "="*50)
            
        except Exception as e:
            self.log_message(f"Error procesando: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            session.close()

    def log_message(self, message):
        self.console_area.insert(tk.END, f"{message}\n")
        self.console_area.see(tk.END)

class AppRecetas(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('App Recetas')
        self.geometry('900x700')
        
        # Initialize database tables (Pacientes y Recetas)
        init_db()
        init_recetas_db()
        
        # Sync with Google Drive first (Patients)
        try:
            # Opcional: Sincronizar al inicio
            # sync_patients_from_drive()
            pass
        except:
            pass 
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add Recetas tab
        self.recetas_tab = RecetasTab(self.notebook)
        self.notebook.add(self.recetas_tab, text='Sincronización y Consulta')
        
        # Add Mandar Recetas tab (Ahora enfocado a Impresión Local)
        self.mandar_tab = MandarRecetasTab(self.notebook)
        self.notebook.add(self.mandar_tab, text='Impresión / Historial')
    
    def sync_with_drive(self):
        try:
            from sync_patients import sync_patients_from_drive
            sync_patients_from_drive()
        except Exception as e:
            messagebox.showerror('Error de sincronización', f'No se pudo sincronizar con Google Drive: {str(e)}')

if __name__ == "__main__":
    app = AppRecetas()
    app.mainloop()