import json
import ast
import re
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

# --------------------------------------------------
# App setup
# --------------------------------------------------

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")


class AgentApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Agent Assistant")
        self.geometry("920x680")
        self.minsize(760, 560)
        self.configure(fg_color=("#f5f3ff", "#1a1029"))

        self._build_ui()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def _build_ui(self):
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

        self.input_box = ctk.CTkTextbox(
            self,
            height=110,
            font=("Segoe UI", 13),
            corner_radius=10,
        )
        self.input_box.pack(fill="x", padx=(140, 60))

        ctk.CTkButton(
            self,
            text="Ask",
            height=40,
            font=("Segoe UI", 14, "bold"),
            command=self.run_agents,
        ).pack(pady=16)

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
        self.output_box_visible = False

        # ---- Table
        self.table_frame = ctk.CTkFrame(self, corner_radius=10)
        self.table_frame.pack(fill="both", expand=True, padx=60, pady=(12, 20))
        self.table_frame.pack_forget()

        container = tk.Frame(self.table_frame)
        container.pack(fill="both", expand=True, padx=8, pady=8)

        self.table = ttk.Treeview(container, show="headings", height=14)
        self.table.grid(row=0, column=0, sticky="nsew")

        table_style = ttk.Style()
        table_style.configure("Treeview", font=("Segoe UI", 13), rowheight=30)
        table_style.configure("Treeview.Heading", font=("Segoe UI", 14, "bold"))

        table_scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=self.table.yview
        )
        table_scrollbar.grid(
            row=0, column=1, sticky="ns"
        )

        table_scrollbar_x = ttk.Scrollbar(
            container, orient="horizontal", command=self.table.xview
        )
        table_scrollbar_x.grid(row=1, column=0, sticky="ew")

        self.table.configure(
            yscrollcommand=table_scrollbar.set,
            xscrollcommand=table_scrollbar_x.set,
        )
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

    # --------------------------------------------------
    # Mock agent layer (replace with real agents later)
    # --------------------------------------------------

    def _call_agents(self, query: str) -> dict:
        """
        Contract:
        {
            "text": str,
            "table": {"columns": [...], "rows": [...]} | None
        }
        """
        return {
            "text": "These drugs were identified based on your query.",
            "table": {
                "columns": ["Drug","Safety"],
                "rows": [
                    ["Carbamazepine", 100],
                    ["Sunitinib", 45],
                    ["Esmolol", 70],
                    ["Moxifloxacin", 89],
                    ["Octreotide", 50],
                    ["Eribulin", 60],
                    ["Carbamazepine", 100],
                    ["Sunitinib", 45],
                    ["Esmolol", 70],
                    ["Moxifloxacin", 89],
                    ["Octreotide", 50],
                    ["Eribulin", 60],
                ],
            },
        }

    # --------------------------------------------------
    # Core logic
    # --------------------------------------------------

    def run_agents(self):
        query = self.input_box.get("1.0", "end").strip()
        if not query:
            return

        result = self._call_agents(query)

        self._render_text(result.get("text", ""))
        self._render_table(result.get("table"))

    # --------------------------------------------------
    # Rendering
    # --------------------------------------------------

    def _render_text(self, text: str):
        if text and not self.output_box_visible:
            self.output_box.pack(fill="x", padx=(60, 140))
            self.output_box_visible = True
        if not text and self.output_box_visible:
            self.output_box.pack_forget()
            self.output_box_visible = False

        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("end", text)
        self.output_box.configure(state="disabled")

    def _render_table(self, table: dict | None):
        for row in self.table.get_children():
            self.table.delete(row)

        if not table:
            self.table_frame.pack_forget()
            return

        columns = table["columns"]
        rows = table["rows"]

        # reset table schema fully
        self.table["columns"] = ()
        self.table["columns"] = columns

        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, anchor="w", width=180, stretch=False)

        for row in rows:
            self.table.insert("", "end", values=row)

        self.table_frame.pack(fill="both", expand=True, padx=60, pady=(12, 20))


# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    AgentApp().mainloop()