import tkinter as tk
from tkinter import ttk
from tkinter import Canvas, Scrollbar
import json
from PIL import Image, ImageTk


with open('cooking.json', 'r') as file:
    cooking_data = json.load(file)

try:
    with open('pricing.json', 'r') as file:
        pricing_data = json.load(file)
except FileNotFoundError:
    pricing_data = {}
    with open('pricing.json', 'w') as file:
        json.dump(pricing_data, file)
try:
    with open('resale_pricing.json', 'r') as file:
        resale_pricing_data = json.load(file)
except FileNotFoundError:
    resale_pricing_data = {}
    with open('resale_pricing.json', 'w') as file:
        json.dump(resale_pricing_data, file)

def save_pricing():
    with open('pricing.json', 'w') as file:
        json.dump(pricing_data, file)
    with open('resale_pricing.json', 'w') as file:
        json.dump(resale_pricing_data, file)

def fetch_icon(image_path):
    img = Image.open(image_path) 
    img = img.resize((30, 30), Image.Resampling.LANCZOS)
    
    return ImageTk.PhotoImage(img)

all_item_ids = set(item['id'] for item in cooking_data['data']['items']['data'])
print(all_item_ids)


def calculate_craft_price(item_id):
    if item_id in pricing_data and pricing_data[item_id].strip():
        try:
            return float(pricing_data[item_id])
        except ValueError:
            return 0.0
    else:
        item_data = next((item for item in cooking_data['data']['items']['data'] if item['id'] == item_id), None)
        if not item_data:
            return 0.0

        total_price = 0.0
        for resource_item in item_data.get('attributes', {}).get('resources_items', []):
            if resource_item['items']['data']:
                resource_id = resource_item['items']['data'][0]['id']
                quantity = int(resource_item['amount'])
                
                total_price += calculate_craft_price(resource_id) * quantity
        return total_price




class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Crafting Efficiency Tool')
        self.geometry('800x600')

        self.tab_control = ttk.Notebook(self)

        self.materials_tab = ttk.Frame(self.tab_control)
        self.craft_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.materials_tab, text='Materials')
        self.tab_control.add(self.craft_tab, text='Crafts')
        self.craft_price_entries = {}
        self.tab_control.pack(expand=1, fill='both')
        self.image_references = []
        self.setup_materials_tab()
        self.setup_craft_tab() 
        

    def setup_materials_tab(self):
        
        basic_materials = []
        basic_materials_id = []

        for item in cooking_data['data']['items']['data']:
            for resource_item in item.get('attributes', {}).get('resources_items', []):
                if resource_item['items']['data']:
                    if resource_item['items']['data'][0]['id'] not in basic_materials_id:
                        if resource_item['items']['data'][0]['id'] not in all_item_ids:
                            basic_materials.append(resource_item)
                            basic_materials_id.append(resource_item['items']['data'][0]['id'])

        self.canvas = Canvas(self.materials_tab)
        self.scrollbar = Scrollbar(self.materials_tab, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        max_per_line = 6
        column_idx = 0
        row_idx = 0
        entry_width = 10  # Largura fixa para as caixas de preço

        padx = 6  # Espaçamento horizontal entre os widgets
        pady = 6  # Espaçamento vertical entre os widgets

        for idx, material in enumerate(basic_materials):
            if idx % max_per_line == 0 and idx != 0:
                column_idx = 0
                row_idx += 3

            icon_url = f".{material['items']['data'][0]['attributes']['image']['data']['attributes']['url']}"
            icon = fetch_icon(icon_url)

            if icon:
                self.image_references.append(icon)
                tk.Label(self.scrollable_frame, image=icon).grid(row=row_idx + 1, column=column_idx, padx=padx, pady=pady, sticky="ew")

            tk.Label(self.scrollable_frame, text=material['items']['data'][0]['attributes']['name']).grid(row=row_idx, column=column_idx, padx=padx, pady=pady, sticky="ew")

            price_var = tk.StringVar(value=pricing_data.get(material['items']['data'][0]['id'], ''))
            price_var.trace_add('write', lambda name, index, mode, sv=price_var, material_id=material['items']['data'][0]['id']: self.update_pricing(material_id, sv))

            price_entry = ttk.Entry(self.scrollable_frame, textvariable=price_var, width=entry_width)
            price_entry.grid(row=row_idx + 2, column=column_idx, padx=padx, pady=pady, sticky="ew")

            column_idx += 1


    def update_pricing(self, material_id, var):
        pricing_data[material_id] = var.get()
        save_pricing()
        self.refresh_craft_prices()
        #self.refresh_craft_tab_ui()

    def update_resale(self, material_id, var):
        resale_pricing_data[material_id] = var.get()
        save_pricing()
        self.refresh_craft_prices()

    def setup_craft_tab(self):
        self.canvas = Canvas(self.craft_tab)
        self.scrollbar = Scrollbar(self.craft_tab, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        crafts_by_level = {}
        for item in cooking_data['data']['items']['data']:
            level = item.get('attributes', {}).get('crafting_level_single', 'N/A')
            crafts_by_level.setdefault(level, []).append(item)

        row_idx = 0
        max_per_line = 4  # Ajuste conforme necessário para o layout desejado
        padx, pady = 6, 6

        for level, crafts in sorted(crafts_by_level.items(), key=lambda x: x[0]):
            ttk.Label(self.scrollable_frame, text=f"Crafting Level {level}", font=('Helvetica', 16, 'bold')).grid(row=row_idx, column=0, columnspan=max_per_line, pady=(pady*4, pady*2))
            row_idx += 1
            column_idx = 0

            for item in crafts:
                if column_idx == max_per_line:
                    column_idx = 0
                    row_idx += 6  # Aumenta para criar espaço para os elementos adicionais

                item_frame = tk.Frame(self.scrollable_frame, bg='#dddddd', relief='groove', borderwidth=2)
                item_frame.grid(row=row_idx, column=column_idx, padx=padx, pady=pady, sticky="ew")
                item_frame.grid_propagate(False)

                icon_url = f".{item['attributes']['image']['data']['attributes']['url']}"
                icon = fetch_icon(icon_url)

                if icon:
                    self.image_references.append(icon)
                    tk.Label(item_frame, image=icon, bg='#dddddd').pack(pady=pady, expand=True)

                tk.Label(item_frame, text=item['attributes']['name'], bg='#dddddd').pack(pady=(pady, 0), expand=True)

                craft_price = calculate_craft_price(item['id'])
                resale_price = float(resale_pricing_data.get(item['id'], '0'))
                resale_price_var = tk.StringVar(value=resale_pricing_data.get(item['id'], ''))
                resale_price_entry = ttk.Entry(item_frame, textvariable=resale_price_var)
                resale_price_entry.pack(pady=(pady, pady*2), expand=True)
                resale_price_var.trace_add('write', lambda name, index, mode, sv=resale_price_var, item_id=item['id']: self.update_resale(item_id, sv))
                quantity = 5  # Assumindo quantidade 1 para simplificar, ajuste conforme necessário
                profit = (resale_price * quantity) - float(craft_price)
                experience = float(item.get('attributes', {}).get('experience', 0))
                exp_cost = 0
                try:
                    exp_cost = profit / experience
                except:
                    pass

                tk.Label(item_frame, text=f"EXP: {experience}", bg='#dddddd').pack(pady=pady, expand=True)
                tk.Label(item_frame, text=f"Profit: {profit:.2f}", bg='#dddddd').pack(pady=pady, expand=True)
                tk.Label(item_frame, text=f"Exp Cost: {exp_cost:.2f}", bg='#dddddd').pack(pady=pady, expand=True)

                column_idx += 1
                if column_idx == max_per_line or item == crafts[-1]:
                    row_idx += 6  # Incrementa para a próxima linha de itens

            row_idx += 1  # Espaço extra após cada níve


    def refresh_craft_prices(self):
        for item in cooking_data['data']['items']['data']:
            if item['id'] not in all_item_ids:  # Check if it's a craft
                calculate_craft_price(item['id'])  # Recalculate craft prices

if __name__ == '__main__':
    app = Application()
    app.mainloop()