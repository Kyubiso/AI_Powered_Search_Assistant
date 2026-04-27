import json
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont, ttk

import customtkinter as ctk


# --------------------------------------------------
# App configuration
# --------------------------------------------------

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

APP_TITLE = "Agent Assistant"
WINDOW_SIZE = "920x680"
MIN_SIZE = (760, 560)


# --------------------------------------------------
# Main application
# --------------------------------------------------

class AgentApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.is_loading = False
        self.output_box_visible = False
        self.sql_box_visible = False
        self.sql_details_visible = False
        self.current_sql_details = ""
        self.metrics_window = None
        self.metrics_text_box = None

        # Spinner state
        self._spinner_running = False
        self._spinner_frames = ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"]
        self._spinner_index = 0

        self._configure_window()
        self._build_ui()

    # --------------------------------------------------
    # Window setup
    # --------------------------------------------------

    def _configure_window(self):
        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(*MIN_SIZE)
        self.configure(fg_color=("#f5f3ff", "#1a1029"))

    # --------------------------------------------------
    # UI construction
    # --------------------------------------------------

    def _build_ui(self):
        self._build_header()
        self._build_input()
        self._build_output()
        self._build_sql_details()
        self._build_table()

    def _get_sql_anchor_widget(self):
        if self.output_box_visible:
            return self.output_box
        return self.loading_label

    def _build_header(self):
        ctk.CTkLabel(
            self,
            text="Agent Assistant",
            font=("Segoe UI", 26, "bold"),
            text_color=("#6d28d9", "#c4b5fd"),
        ).pack(pady=(24, 8))

        ctk.CTkLabel(
            self,
            text="Ask a question. The agents handle the rest.",
            font=("Segoe UI", 12),
            text_color=("#0f766e", "#5eead4"),
        ).pack(pady=(0, 18))

    def _build_input(self):
        self.input_box = ctk.CTkTextbox(
            self,
            height=110,
            font=("Segoe UI", 13),
            corner_radius=10,
        )
        self.input_box.pack(fill="x", padx=(140, 60))

        self.input_box.bind("<Control-Return>", lambda _: self.run_agents())

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(pady=16)

        self.ask_button = ctk.CTkButton(
            button_row,
            text="Ask",
            height=40,
            font=("Segoe UI", 14, "bold"),
            command=self.run_agents,
        )
        self.ask_button.pack(side="left", padx=(0, 12))

        self.metrics_button = ctk.CTkButton(
            button_row,
            text="Show Metrics",
            height=40,
            font=("Segoe UI", 14, "bold"),
            fg_color=("#0f766e", "#115e59"),
            hover_color=("#0d9488", "#134e4a"),
            command=self.show_metrics_window,
        )
        self.metrics_button.pack(side="left")

        self.loading_label = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 18, "bold"),
            text_color=("#0f766e", "#5eead4"),
        )
        self.loading_label.pack(pady=(0, 8))

    def _build_output(self):
        self.output_box = ctk.CTkTextbox(
            self,
            height=110,
            font=("Segoe UI", 13),
            state="disabled",
            corner_radius=10,
            fg_color=("#ccfbf1", "#99f6e4"),
            text_color=("#0f172a", "#0f172a"),
        )
        self.output_box.pack(fill="x", padx=(60, 140))
        self.output_box.pack_forget()

    def _build_sql_details(self):
        self.sql_button = ctk.CTkButton(
            self,
            text="Show SQL Query",
            height=34,
            font=("Segoe UI", 13, "bold"),
            command=self._toggle_sql_details,
        )
        self.sql_button.pack(pady=(0, 10))
        self.sql_button.pack_forget()

        self.sql_box = ctk.CTkTextbox(
            self,
            height=180,
            font=("Consolas", 12),
            state="disabled",
            corner_radius=10,
            fg_color=("#ede9fe", "#2a1842"),
            text_color=("#1f2937", "#f3f4f6"),
        )
        self.sql_box.pack(fill="x", padx=(60, 140))
        self.sql_box.pack_forget()

    def _build_table(self):
        self.table_frame = ctk.CTkFrame(self, corner_radius=10)
        self.table_frame.pack(fill="both", expand=True, padx=60, pady=(12, 20))
        self.table_frame.pack_forget()

        container = tk.Frame(self.table_frame)
        container.pack(fill="both", expand=True, padx=8, pady=8)

        self.table = ttk.Treeview(container, show="headings", height=14)
        self.table.grid(row=0, column=0, sticky="nsew")
        self.table.bind("<Double-1>", self._on_table_double_click)

        self._configure_table_style()
        self._add_table_scrollbars(container)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

    def _configure_table_style(self):
        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 13), rowheight=30)
        style.configure("Treeview.Heading", font=("Segoe UI", 13, "bold"))

    def _add_table_scrollbars(self, container):
        y_scroll = ttk.Scrollbar(container, orient="vertical", command=self.table.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")

        x_scroll = ttk.Scrollbar(container, orient="horizontal", command=self.table.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")

        self.table.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )

    # --------------------------------------------------
    # Spinner helpers
    # --------------------------------------------------

    def _start_spinner(self):
        self._spinner_running = True
        self._spinner_index = 0
        self._animate_spinner()

    def _stop_spinner(self):
        self._spinner_running = False
        self.loading_label.configure(text="")

    def _animate_spinner(self):
        if not self._spinner_running:
            return

        frame = self._spinner_frames[self._spinner_index]
        self.loading_label.configure(text=f"{frame} Running query…")

        self._spinner_index = (self._spinner_index + 1) % len(self._spinner_frames)
        self.after(120, self._animate_spinner)

    # --------------------------------------------------
    # Agent integration
    # --------------------------------------------------

    def _call_agents(self, query: str) -> dict:
        project_root = Path(__file__).resolve().parents[2]

        completed = subprocess.run(
            [sys.executable, "-m", "src.backend.pipeline.ask_database", query],
            capture_output=True,
            text=True,
            cwd=project_root,
            check=False,
        )

        if completed.stdout:
            sys.stdout.write(completed.stdout)
            sys.stdout.flush()

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            if completed.returncode != 0:
                return {
                    "text": completed.stderr.strip() or "Failed to run ask_database.",
                    "table": None,
                }
            return {"text": "ask_database returned invalid JSON.", "table": None}

        execution = payload.get("execution") or {}
        columns = execution.get("columns", [])
        rows = execution.get("rows", [])
        generated_sql = payload.get("generated_sql") or {}
        selected_dataset = payload.get("selected_dataset") or {}
        metrics = payload.get("metrics") or {}

        table = {"columns": columns, "rows": rows} if columns else None

        dataset_name = selected_dataset.get("dataset_name")

        validation = payload.get("validation") or {}
        text_parts = []
        if validation.get("is_valid") is False and validation.get("violations"):
            text_parts.append("Validation failed:")
            text_parts.extend(f"- {item}" for item in validation["violations"])

        sql_lines = []
        if dataset_name:
            sql_lines.append(f"Selected dataset: {dataset_name}")
        if generated_sql.get("chosen_dataset_name"):
            sql_lines.append(f"Chosen candidate: {generated_sql['chosen_dataset_name']}")
        if generated_sql.get("final_mode"):
            sql_lines.append(f"Final mode: {generated_sql['final_mode']}")
        if generated_sql.get("mode_decision"):
            sql_lines.append(f"Mode decision: {generated_sql['mode_decision']}")
        if generated_sql.get("explanation"):
            sql_lines.append(f"Explanation: {generated_sql['explanation']}")
        if metrics:
            sql_lines.extend(
                [
                    "",
                    "Metrics:",
                    f"Status: {metrics.get('status', 'unknown')}",
                    f"Total time (ms): {metrics.get('timings_ms', {}).get('total', 'n/a')}",
                    f"Retrieval time (ms): {metrics.get('timings_ms', {}).get('retrieval', 'n/a')}",
                    f"SQL generation time (ms): {metrics.get('timings_ms', {}).get('sql_generation', 'n/a')}",
                    "Candidate changed by model: "
                    f"{metrics.get('retrieval', {}).get('candidate_changed_by_model', False)}",
                    "Mode changed by model: "
                    f"{metrics.get('query_mode', {}).get('mode_changed_by_model', False)}",
                ]
            )
        if generated_sql.get("sql"):
            sql_lines.extend(["", "SQL:", generated_sql["sql"]])

        return {
            "text": "\n".join(text_parts),
            "table": table,
            "sql_details": "\n".join(sql_lines).strip(),
        }

    def _load_metrics_report(self) -> tuple[str, bool]:
        project_root = Path(__file__).resolve().parents[2]
        completed = subprocess.run(
            [sys.executable, "-m", "src.backend.pipeline.report_metrics"],
            capture_output=True,
            text=True,
            cwd=project_root,
            check=False,
        )

        if completed.returncode != 0:
            message = completed.stderr.strip() or "Failed to load aggregated metrics."
            return message, False

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            return "Aggregated metrics report returned invalid JSON.", False

        return json.dumps(payload, indent=2, ensure_ascii=False), True

    # --------------------------------------------------
    # Core logic
    # --------------------------------------------------

    def run_agents(self):
        if self.is_loading:
            return

        query = self.input_box.get("1.0", "end").strip()
        if not query:
            return

        self._set_loading_state(True)

        threading.Thread(
            target=self._run_agents_worker,
            args=(query,),
            daemon=True,
        ).start()

    def _run_agents_worker(self, query: str):
        result = self._call_agents(query)
        self.after(0, lambda: self._finish_run(result))

    def _finish_run(self, result: dict):
        self._set_loading_state(False)
        self._render_text(result.get("text", ""))
        self._render_sql_details(result.get("sql_details", ""))
        self._render_table(result.get("table"))

    def _set_loading_state(self, loading: bool):
        self.is_loading = loading
        state = "disabled" if loading else "normal"

        self.ask_button.configure(state=state)
        self.metrics_button.configure(state=state)
        self.input_box.configure(state=state)

        if loading:
            self.table.delete(*self.table.get_children())
            self.table_frame.pack_forget()
            self._render_sql_details("")
            self._start_spinner()
        else:
            self._stop_spinner()

    # --------------------------------------------------
    # Rendering helpers
    # --------------------------------------------------

    def _render_text(self, text: str):
        if text and not self.output_box_visible:
            self.output_box.pack(fill="x", padx=(60, 140))
            self.output_box_visible = True
        elif not text and self.output_box_visible:
            self.output_box.pack_forget()
            self.output_box_visible = False

        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("end", text)
        self.output_box.configure(state="disabled")

    def _render_sql_details(self, sql_details: str):
        self.current_sql_details = sql_details.strip()
        should_show_button = bool(self.current_sql_details)

        if should_show_button and not self.sql_box_visible:
            self.sql_button.configure(text="Show SQL Query")
            self.sql_button.pack(after=self._get_sql_anchor_widget(), pady=(0, 10))
            self.sql_box_visible = True
        elif not should_show_button and self.sql_box_visible:
            self.sql_button.pack_forget()
            self.sql_box_visible = False

        if not should_show_button:
            if self.sql_details_visible:
                self.sql_box.pack_forget()
                self.sql_details_visible = False
            self.sql_box.configure(state="normal")
            self.sql_box.delete("1.0", "end")
            self.sql_box.configure(state="disabled")
            return

        self.sql_box.configure(state="normal")
        self.sql_box.delete("1.0", "end")
        self.sql_box.insert("end", self.current_sql_details)
        self.sql_box.configure(state="disabled")

        if self.sql_details_visible:
            self.sql_box.pack(after=self.sql_button, fill="x", padx=(60, 140), pady=(0, 10))

    def _toggle_sql_details(self):
        if not self.current_sql_details:
            return

        if self.sql_details_visible:
            self.sql_box.pack_forget()
            self.sql_button.configure(text="Show SQL Query")
            self.sql_details_visible = False
            return

        self.sql_box.pack(after=self.sql_button, fill="x", padx=(60, 140), pady=(0, 10))
        self.sql_button.configure(text="Hide SQL Query")
        self.sql_details_visible = True

    def show_metrics_window(self):
        if self.metrics_window is not None and self.metrics_window.winfo_exists():
            self.metrics_window.deiconify()
            self.metrics_window.lift()
            self.metrics_window.focus()
            self.refresh_metrics_window()
            return

        self.metrics_window = ctk.CTkToplevel(self)
        self.metrics_window.title("Aggregated Metrics")
        self.metrics_window.geometry("820x560")
        self.metrics_window.minsize(640, 420)
        self.metrics_window.protocol("WM_DELETE_WINDOW", self._close_metrics_window)

        header = ctk.CTkFrame(self.metrics_window, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(14, 8))

        ctk.CTkLabel(
            header,
            text="Aggregated Metrics",
            font=("Segoe UI", 20, "bold"),
            text_color=("#0f766e", "#5eead4"),
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Refresh",
            width=110,
            command=self.refresh_metrics_window,
        ).pack(side="right")

        self.metrics_text_box = ctk.CTkTextbox(
            self.metrics_window,
            font=("Consolas", 12),
            wrap="none",
        )
        self.metrics_text_box.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.refresh_metrics_window()

    def refresh_metrics_window(self):
        if self.metrics_text_box is None:
            return

        metrics_text, success = self._load_metrics_report()
        self.metrics_text_box.configure(state="normal")
        self.metrics_text_box.delete("1.0", "end")
        self.metrics_text_box.insert("1.0", metrics_text)
        self.metrics_text_box.configure(state="disabled")

        if self.metrics_window is not None and self.metrics_window.winfo_exists():
            title = "Aggregated Metrics" if success else "Aggregated Metrics (Error)"
            self.metrics_window.title(title)

    def _close_metrics_window(self):
        if self.metrics_window is not None and self.metrics_window.winfo_exists():
            self.metrics_window.destroy()
        self.metrics_window = None
        self.metrics_text_box = None

    def _autosize_columns(self, rows, headings, max_width=420, min_width=100):
        measure = tkfont.Font(font=("Segoe UI", 13)).measure

        for col_index, heading in enumerate(headings):
            max_text_width = measure(str(heading))

            for row in rows:
                if col_index < len(row):
                    max_text_width = max(
                        max_text_width, measure(str(row[col_index]))
                    )

            width = max(min_width, min(max_width, max_text_width + 28))
            yield width

    def _render_table(self, table: dict | None):
        self.table.delete(*self.table.get_children())

        if not table:
            self.table_frame.pack_forget()
            return

        columns = list(map(str, table["columns"]))
        rows = table["rows"]

        column_ids = [f"col_{i}" for i in range(len(columns))]
        self.table.configure(columns=column_ids)

        widths = list(self._autosize_columns(rows, columns))

        for col_id, heading, width in zip(column_ids, columns, widths):
            self.table.heading(col_id, text=heading)
            self.table.column(
                col_id,
                anchor="w",
                width=width,
                minwidth=100,
                stretch=False,
            )

        for row in rows:
            self.table.insert("", "end", values=row)

        self.table_frame.pack(fill="both", expand=True, padx=60, pady=(12, 20))

    # --------------------------------------------------
    # Cell viewer
    # --------------------------------------------------

    def _on_table_double_click(self, event):
        if self.table.identify("region", event.x, event.y) != "cell":
            return

        row_id = self.table.identify_row(event.y)
        column_index = int(self.table.identify_column(event.x).replace("#", "")) - 1

        if not row_id:
            return

        values = self.table.item(row_id, "values")
        if not (0 <= column_index < len(values)):
            return

        column_id = self.table["columns"][column_index]
        heading = self.table.heading(column_id).get("text", column_id)

        self._show_cell_viewer(str(heading), str(values[column_index]))

    def _show_cell_viewer(self, column_name: str, value: str):
        viewer = ctk.CTkToplevel(self)
        viewer.title(f"Cell Value – {column_name}")
        viewer.geometry("900x500")
        viewer.minsize(600, 300)

        text_box = ctk.CTkTextbox(viewer, font=("Segoe UI", 13), wrap="word")
        text_box.pack(fill="both", expand=True, padx=14, pady=14)
        text_box.insert("1.0", value)
        text_box.configure(state="disabled")


if __name__ == "__main__":
    AgentApp().mainloop()
