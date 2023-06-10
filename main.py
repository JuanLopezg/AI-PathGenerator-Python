import tkinter as tk
from PIL import ImageTk, Image
from min_route import MetAtenas


class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y


class Edge:
    def __init__(self, point: Point, v1: str, v2: str):
        self.point = point
        self.v1 = v1
        self.v2 = v2


# Station names to coordinates in background
stations = {
    # Line 1
    "Piraeus": Point(21, 648),
    "Faliro": Point(110, 638),
    "Moschato": Point(136, 615),
    "Kalithea": Point(158, 593),
    "Tavros": Point(180, 570),
    "Petralona": Point(203, 547),
    "Thissio": Point(213, 523),
    "Monastiraki": Point(213, 485),
    "Omonia": Point(213, 451),
    "Victoria": Point(213, 420),
    "Attiki": Point(176, 370),
    "Aghios Nikolaos": Point(194, 352),
    "Kato Patissia": Point(216, 331),
    "Aghios Eleftherios": Point(237, 309),
    "Ano Patissia": Point(257, 289),
    "Perissos": Point(275, 270),
    "Pefkakia": Point(295, 251),
    "Nea Ionia": Point(313, 232),
    "Iraklio": Point(331, 214),
    "Irini": Point(404, 206),
    "Neratziotissa": Point(432, 202),
    "Maroussi": Point(470, 166),
    "KAT": Point(502, 133),
    "Kifissia": Point(535, 101),
    # Line 2
    "Aghios Antonios": Point(113, 306),
    "Sepolia": Point(145, 338),
    "Larissa Station": Point(177, 404),
    "Metaxourghio": Point(177, 432),
    "Panepistimio": Point(232, 467),
    "Syntagma": Point(251, 485),
    "Akropoli": Point(253, 525),
    "Syngrou - Fix": Point(254, 554),
    "Neos Kosmos": Point(254, 585),
    "Aghios Ioanis": Point(254, 613),
    "Dafni": Point(254, 643),
    "Aghios Dimitrios Alexandros Panagoulis": Point(254, 673),
    # Line 3
    "Egaleo": Point(53, 401),
    "Eleonas": Point(96, 443),
    "Kerameikos": Point(128, 476),
    "Evangelismos": Point(316, 485),
    "Megaro Moussikis": Point(370, 475),
    "Ambelokipi": Point(388, 457),
    "Panormou": Point(405, 439),
    "Katehaki": Point(422, 421),
    "Ethniki Amyna": Point(439, 404),
    "Holargos": Point(458, 386),
    "Nomismatokopio": Point(475, 369),
    "Aghia Paraskevi": Point(493, 350),
    "Halandri": Point(510, 333),
    "Doukissis Plakentias": Point(539, 304),
    "Pallini": Point(588, 325),
    "Peania-Kantza": Point(588, 372),
    "Koropi": Point(588, 477),
    "Airport Eleftherios Venizelos": Point(650, 502),
    # SUBWAY
    # "Kifisias" : Point(466, 237),
    # "Pentelis" : Point(501, 272)
}

# edges between station nodes to simulate faults
edges = [
    Edge(Point(177, 390), "Attiki", "Larissa Station"),
    Edge(Point(199, 391), "Attiki", "Victoria"),
    Edge(Point(177, 419), "Larissa Station", "Metaxourghio"),
    Edge(Point(189, 449), "Metaxourghio", "Omonia"),
    Edge(Point(213, 435), "Victoria", "Omonia"),
    Edge(Point(213, 468), "Omonia", "Monastiraki"),
    Edge(Point(224, 460), "Omonia", "Panepistimio"),
    Edge(Point(230, 486), "Monastiraki", "Syntagma"),
    Edge(Point(241, 476), "Panepistimio", "Syntagma"),
]

metroAt = MetAtenas('lineasMetro.json')

# Canvas dimensions and colors
CANVAS_WIDTH = 710
CANVAS_HEIGHT = 778

ORIGIN_COLOR = "#55B309"
DEST_COLOR = "#2962DF"
FILL_COLOR = "#264DFF"
FAULT_COLOR = "#e60000"
FAULT_COLOR_OUTLINE = "#000000"
PATH_COLOR = '#E0A21B'
OUTPUT_BG_COLOR = '#8C8F86'
STATION_R = 10
POINT_RADIUS = 7
PATH_POINT_RADIUS = 5
FAULT_POINT_RADIUS = 6


def reset_buttons(button_id):  # 0 Origin, 1 Destination and 2 sim fault
    global is_selecting_origin
    global is_selecting_destination
    global is_selecting_fault
    if button_id in {0, 1} and is_selecting_fault:
        toggle_simulate_fault()
    if button_id in {1, 2} and is_selecting_origin:
        toggle_select_origin()
    if button_id in {0, 2} and is_selecting_destination:
        toggle_select_destination()


def toggle_select_origin():
    global is_selecting_origin
    reset_buttons(0)
    if is_selecting_origin:
        origin_button.config(text="Select origin")
    else:
        origin_button.config(text="Cancel")

    is_selecting_origin = not is_selecting_origin


def toggle_select_destination():
    global is_selecting_destination
    reset_buttons(1)
    if is_selecting_destination:
        destination_button.config(text="Select destination")
    else:
        destination_button.config(text="Cancel")
    is_selecting_destination = not is_selecting_destination


def toggle_simulate_fault():
    global canvas
    global simulate_fault_button
    global is_selecting_fault
    global is_fault_selected
    if is_fault_selected:
        simulate_fault_button.config(text="Simulate fault")
        canvas.delete("fault_point")
        # Resetting adyacencies
        metroAt.get_adyacencies(tuple(metroAt.st_nodes.keys()))
        is_fault_selected = False
    else:
        reset_buttons(2)
        if is_selecting_fault:
            canvas.delete("fault_point")
            simulate_fault_button.config(text="Simulate fault")
        else:
            for edge in edges:
                canvas.create_oval(edge.point.x - FAULT_POINT_RADIUS,
                                   edge.point.y - FAULT_POINT_RADIUS,
                                   edge.point.x + FAULT_POINT_RADIUS,
                                   edge.point.y + FAULT_POINT_RADIUS,
                                   fill=FAULT_COLOR,
                                   outline=FAULT_COLOR_OUTLINE,
                                   width=2, tags="fault_point")
            simulate_fault_button.config(text="Cancel")
        is_selecting_fault = not is_selecting_fault


def callback(event):
    global distance_label
    global time_label
    global is_selecting_origin
    global is_selecting_destination
    global is_selecting_fault
    global is_fault_selected
    global origin_station_name
    global is_origin_selected
    global is_destination_selected
    global destination_station_name
    global canvas
    global metroAt
    global simulate_fault_button
    global calculate_path_button

    if is_selecting_origin:
        canvas.delete("origin_station")
        origin_station_name = get_station_name(event.x, event.y)
        if origin_station_name is None:
            is_origin_selected = False
            origin_label.config(text="-----")
        else:
            station_point = stations[origin_station_name]
            canvas.create_oval(station_point.x - POINT_RADIUS,
                               station_point.y - POINT_RADIUS,
                               station_point.x + POINT_RADIUS,
                               station_point.y + POINT_RADIUS,
                               fill=ORIGIN_COLOR, tags="origin_station")
            origin_label.config(text=origin_station_name)
            is_origin_selected = True

        origin_button.config(text="Select origin")
        is_selecting_origin = False
    elif is_selecting_destination:
        canvas.delete("destination_station")
        destination_station_name = get_station_name(event.x, event.y)
        if destination_station_name is None:
            is_destination_selected = False
            destination_label.config(text="-----")
        else:
            station_point = stations[destination_station_name]
            canvas.create_oval(station_point.x - POINT_RADIUS,
                               station_point.y - POINT_RADIUS,
                               station_point.x + POINT_RADIUS,
                               station_point.y + POINT_RADIUS,
                               fill=DEST_COLOR, tags="destination_station")
            destination_label.config(text=destination_station_name)
            is_destination_selected = True

        destination_button.config(text="Select destination")
        is_selecting_destination = False
    elif is_selecting_fault:
        canvas.delete("fault_point")
        simulate_fault_button.config(text="Remove fault")
        for edge in edges:
            if abs(event.x - edge.point.x) <= 8 and abs(event.y - edge.point.y) <= 8:
                metroAt.break_line(edge.v1, edge.v2)
                canvas.create_oval(edge.point.x - FAULT_POINT_RADIUS,
                                   edge.point.y - FAULT_POINT_RADIUS,
                                   edge.point.x + FAULT_POINT_RADIUS,
                                   edge.point.y + FAULT_POINT_RADIUS,
                                   fill=FAULT_COLOR,
                                   outline=FAULT_COLOR_OUTLINE, 
                                   width=2, tags="fault_point")
        is_selecting_fault = False
        is_fault_selected = True

    if(is_destination_selected and is_origin_selected):
        calculate_path_button.config(state=tk.NORMAL)
    else:
        calculate_path_button.config(state=tk.DISABLED)


def get_station_name(x: int, y: int) -> str:
    for name, point in stations.items():
        if abs(x - point.x) <= STATION_R and abs(y - point.y) <= STATION_R:
            return name
    return None


def calculate_path():
    global canvas
    global distance_label
    global time_label
    global origin_button
    global destination_button
    global calculate_path_button
    global simulate_fault_button
    global day_menu
    global hour_menu
    global minute_menu
    global is_path_calculated
    global distance_label
    global time_label

    if is_path_calculated:
        is_path_calculated = False
        canvas.delete("path")

        origin_button.config(state=tk.NORMAL)
        destination_button.config(state=tk.NORMAL)
        simulate_fault_button.config(state=tk.NORMAL)
        day_menu.config(state=tk.NORMAL)
        hour_menu.config(state=tk.NORMAL)
        minute_menu.config(state=tk.NORMAL)
        speed_menu.config(state=tk.NORMAL)
        output_label.config(text="", bg='white')

        calculate_path_button.config(text="Calculate path")
    else:
        is_path_calculated = True
        origin_button.config(state=tk.DISABLED)
        destination_button.config(state=tk.DISABLED)
        simulate_fault_button.config(state=tk.DISABLED)
        day_menu.config(state=tk.DISABLED)
        hour_menu.config(state=tk.DISABLED)
        minute_menu.config(state=tk.DISABLED)
        speed_menu.config(state=tk.DISABLED)

        calculate_path_button.config(text="Change settings")
        metroAt.set_hour(day_var.get(), hour_var.get(), minute_var.get())
        metroAt.set_speed(speed_var.get())
        result = metroAt.min_cam(origin_station_name, destination_station_name)
        if result is None:
            output_label.config(text="Metro is closed or closes during journey",
                                fg='red',
                                bg=OUTPUT_BG_COLOR)
            return
        output_text = "Journey Complete:\n"
        output_text += f"Total Duration: {result['time']} mins\n"
        output_text += f"Waiting time for all line exchanges: {result['tmTrans']} mins\n"
        arr_tm = (int(i) for i in metroAt.get_time(result['time']))
        output_text += f"Arrival time: {day_options[next(arr_tm)]}, "
        output_text += f"{next(arr_tm)}h and {next(arr_tm)}min\n"
        output_text += f"Total Distance Travelled: {result['dist']} meters"

        output_label.config(text=output_text, fg=PATH_COLOR,
                            bg=OUTPUT_BG_COLOR)
        for name in result['path']:
            point = stations[name]
            canvas.create_oval(point.x - PATH_POINT_RADIUS,
                               point.y - PATH_POINT_RADIUS,
                               point.x + PATH_POINT_RADIUS,
                               point.y + PATH_POINT_RADIUS,
                               fill=PATH_COLOR, tags="path")


window = tk.Tk()
# window = tk.Toplevel()
window.title("Path Visualizer")
is_selecting_origin = False
is_selecting_destination = False
is_selecting_fault = False

is_origin_selected = False
is_destination_selected = False
is_fault_selected = False
is_path_calculated = False
origin_station_name = ""
destination_station_name = ""

button_panel = tk.Frame(master=window, bg="white")

# Origin button
origin_label = tk.Label(master=button_panel, text="------", fg=ORIGIN_COLOR,
                        bg="white")
origin_button = tk.Button(
    master=button_panel,
    text="Select origin",
    width=25,
    height=2,
    highlightbackground=ORIGIN_COLOR,
    command=toggle_select_origin
)

# Destination button
destination_label = tk.Label(master=button_panel, text="------", fg=DEST_COLOR,
                             bg='white')
destination_button = tk.Button(
    master=button_panel,
    text="Select destination",
    width=25,
    height=2,
    highlightbackground=DEST_COLOR,
    command=toggle_select_destination
)

# Fault Selection button
simulate_fault_button = tk.Button(
    master=button_panel,
    text="Simulate fault",
    width=25,
    height=2,
    highlightbackground=FAULT_COLOR,
    command=toggle_simulate_fault
)

# Calculate Path button
calculate_path_button = tk.Button(
    master=button_panel,
    text="Calculate path",
    width=25,
    height=2,
    highlightbackground=PATH_COLOR,
    command=calculate_path,
    state=tk.DISABLED
)

# Time drop down menu set up
day_options = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
)
time_panel = tk.Frame(master=button_panel, bg='white')
time_panel_label = tk.Label(master=time_panel, text="Select departing time:",
                            bg='white')

# Set inputs for the time
day_var = tk.StringVar(time_panel)
hour_var = tk.IntVar(time_panel)
minute_var = tk.IntVar(time_panel)
day_var.set("Monday")
hour_var.set(0)
minute_var.set(0)
# Create and pack the menus
day_menu = tk.OptionMenu(time_panel, day_var, *day_options)
hour_menu = tk.OptionMenu(time_panel,
                          hour_var,
                          *(i for i in range(0, 24)))
minute_menu = tk.OptionMenu(time_panel,
                            minute_var,
                            *(i for i in range(0, 60)))
time_panel_label.pack(side=tk.LEFT)
day_menu.pack(side=tk.LEFT)
hour_menu.pack(side=tk.LEFT)
minute_menu.pack(side=tk.LEFT)

# Speed menu
speed_panel = tk.Frame(master=button_panel, bg='white')
speed_label = tk.Label(master=speed_panel, text="Train Speed(km/h):",
                       bg='white')
speed_var = tk.IntVar()
speed_var.set(80)
speed_menu = tk.OptionMenu(speed_panel,
                           speed_var,
                           *("{:3d}".format(i*10) for i in range(1, 11)))
speed_label.pack(side=tk.LEFT)
speed_menu.pack(side=tk.LEFT)

# Distance and time used output
output_label = tk.Label(master=button_panel, text="", bg='white')


origin_label.pack(side=tk.TOP)
origin_button.pack(side=tk.TOP)
destination_label.pack(side=tk.TOP)
destination_button.pack(side=tk.TOP)
simulate_fault_button.pack(side=tk.TOP, pady=15)
time_panel_label.pack(side=tk.TOP)
time_panel.pack(side=tk.TOP, pady=15)
speed_panel.pack(side=tk.TOP)

calculate_path_button.pack(side=tk.BOTTOM, pady=15)
output_label.pack(side=tk.BOTTOM)

button_panel.pack(side=tk.LEFT, fill=tk.Y)
canvas = tk.Canvas(window, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
canvas.bind("<Button-1>", callback)
canvas.pack(side=tk.RIGHT)
img = ImageTk.PhotoImage(Image.open("metro_background.jpg"))
canvas.create_image(0, 0, anchor=tk.NW, image=img)
window.mainloop()
