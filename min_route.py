'''JSON Format Used: {
    "__lineasMetro__": true,
    "lineas": [
        [[st1_ofln1, 0], [st2_ofln1, dist_ofln1 + distToPrev], ....]
        [[st1_ofln2, 0], [st2_ofln2, dist_ofln2 + distToPrev], ....]
        ],
    "stNodes": [StNode1, stNode2, ...]
}
    stNodes are strings and at 'lineas', distaces can also be dist from stAt to
    first.
lineasMetro Format:
{'dictMetro': dictMetro {'lin': [stName -> stLn, stPosinLn]
                         'stNm': [Ln -> stNamesOfLine],
                         'stDist': [Ln -> stDistOfLine]}
 'stNodes': stNodes [stNodes -> ()]
 }
'''

import json
from collections import defaultdict
from functools import wraps


def lineas_metro_hook(obj):
    '''
    lineas_metro_hook
    -----------------
    Hook to the load function used to read the metro lines and returns
    the data in the lineasMetro format in which we have:
    - lin where it associates the stName to it's line and position in it,
          a station can have more than one line and position.
    - stNm and stDist we associate the lnNum to it's station names
        and distances
    - stNodes which are all the recognised nodes, which in the case of the
    Metro of Athens (l1, l2, l3) are:
            "Syntagma" - l2 - "Panepistimio"
                |l3|             |l2|
        "Monastiraki" - l1 - "Omonia" - l1 - "Victoria" - l1 -  "Attiki"
                                |l2|                              /l2/
                            "Metaxourghio"  - - - l2 - - - "Larissa Station"
    '''
    if '__lineasMetro__' in obj:
        dict_lin, dict_st_nm, dict_st_dist = defaultdict(lambda: None), {}, {}
        for n_lin, line in enumerate(obj['lineas'], 1):
            st_names = []
            distances = []
            for st_pos, st_data in enumerate(line):
                st_names.append(st_data[0])
                distances.append(st_data[1])
                if dict_lin[st_data[0]] is None:
                    dict_lin[st_data[0]] = (n_lin, st_pos)
                else:
                    dict_lin[st_data[0]] += (n_lin, st_pos)
            dict_st_nm[n_lin] = tuple(st_names)
            dict_st_dist[n_lin] = tuple(distances)
        st_nodes = defaultdict(None, {node: () for node in obj['stNodes']})
        return {'lin': dict_lin, 'stNm': dict_st_nm, 'stDist': dict_st_dist,
                'stNodes': st_nodes}
    return obj


def load_data(file_name):
    '''
    load_data
    ---------
    Loads the json file passed at the fileName path and stores
    it in the used format, described at lineas_metro_hook.'''
    with open(file_name, 'r', encoding="utf-8") as file:
        return json.load(file, object_hook=lineas_metro_hook)


def dist(distances, st_pos_1, st_pos_2):
    '''
    dist
    ----
    Returns the distance between two stations in the same line.'''
    return abs(distances[st_pos_1] - distances[st_pos_2])


def belongs_to(lin_intervals, pos_1, pos_2=-1):
    '''
    belongs
    -------
    Returns the value of the interval pos in lin_intervals pos_1 belongs to.
    If pos_2 is not -1, it only returns the value of the interval if both are
    in the same one. If not it returns -1.'''
    for i, int_val in enumerate(lin_intervals):
        is_pos_2_in_int = pos_2 == -1 or int_val[0] <= pos_2 <= int_val[1]
        if int_val[0] <= pos_1 <= int_val[1] and is_pos_2_in_int:
            return i
    return -1


def insert_sorted(list_val, val, comp):
    '''
    insert_sorted
    -------------
    Inserts into listVal the val in a position which we consider to be sorted
    by the condition comp.
    comp(val_1, val_2) has to be a comparator that returns a positive value
    if val_1 < val_2, 0 if val_1 = val_2 and negative if val_1 > val_2.
    Inserts from lowest comp value to highest.
    Ex. val_2 - val_1 / val_1 <= val_2
        val_1 - val_2 / val_1 >= val_2'''
    if len(list_val) == 0:
        list_val.append(val)
        return

    start, end, pos = 0, len(list_val) - 1, -1
    while pos == -1:
        if start != end:
            mid = int((start + end)/2)
            cmp = comp(val, list_val[mid])  # val <= listVal[mid]
            if cmp == 0:  # val_1 = val_2
                pos = mid
            elif cmp < 0:  # val_1 > val_2
                start = mid + 1
            elif cmp > 0:  # val_1 < val_2
                end = mid
        else:
            pos = start + 1 if comp(val, list_val[start]) < 0 else start
    list_val.insert(pos, val)


def move_to_graph(func):
    '''
    move_to_graph
    -------------
    Is a wrapper that surrounds min_cam from MetroAtenas. The wrapper
    ensures that the values that are passed to min_cam are nodes. To do so,
    it uses the intervals defined in MetroAtenas to move to the nearest
    node.
    The logic it uses can be sumed up as:
    - If both stations are nodes, then just do min_cam
    - If both stations are not nodes and are at the same line,
        check if both are in the same interval in the line and if they are
        then return the path between them.
    - If one or both are not nodes, call move_to_node to move to the
        nearest node. If the node they are at now is the same, then
        returns the travel path obtained, else, obtains the sum of the path
        with the start and the end.'''
    @wraps(func)
    def wrapper(*args, **kwargs):
        metro, st_from, st_to = args[0], args[1], args[2]
        if metro.transfer_line_time(0) < 0:  # Metro is closed
            return None
        ln_from, pos_from = 0, 0
        ln_to, pos_to = 0, 0
        if metro.st_nodes.get(st_from) is None:  # Checks if they are a nodes
            ln_from, pos_from = metro.st_lin[st_from]
        if metro.st_nodes.get(st_to) is None:
            ln_to, pos_to = metro.st_lin[st_to]

        # If both stations are not nodes and in the same line
        if ln_from == ln_to and ln_from != 0:
            if belongs_to(metro.st_intervals[ln_from], pos_from, pos_to) != -1:
                # Calculate the step and the path (without end station)
                step = 1 if pos_from < pos_to else -1
                path = metro.st_names[ln_from][pos_from:pos_to:step]
                distance = dist(metro.st_dist[ln_from], pos_from, pos_to)
                return {'path': path + (metro.st_names[ln_from][pos_to],),
                        'dist': distance,
                        'time': round(distance/metro.train_speed, 1),
                        'tmTrans': 0}
        # begin / end = (st_nm_path, dist_travelled, st_node_nm)
        begin = metro.move_to_node(ln_from, pos_from)
        tm_used = 0  # TODO
        if begin[2] is not None:  # If it has moved
            st_from = begin[2]
            tm_used = round(begin[1]/metro.train_speed, 1)
        end = metro.move_to_node(ln_to, pos_to)
        if end[2] is not None:
            st_to = end[2]
        if st_from == st_to:  # If both nodes are the same
            tm_transfer = 0
            # If they have come from different lines
            if ln_from != 0 and ln_to != 0 and ln_from != ln_to:
                tm_transfer = metro.transfer_line_time(tm_used)
                if tm_transfer < 0:
                    return None
            return {
                'path': begin[0] + (st_from, ) + end[0][::-1],
                'dist': begin[1] + end[1],
                'time': round((begin[1] + end[1])/metro.train_speed + tm_transfer, 1),
                'tmTrans': tm_transfer}
        # Intro modified args
        args = (metro, st_from, st_to, ln_from, ln_to, tm_used)
        path_in_graph = func(*args, **kwargs)
        if path_in_graph is None:
            return None
        tm_used = round(
            (begin[1] + path_in_graph['dist'] + end[1])/metro.train_speed, 1)
        tm_used += path_in_graph['tmTrans']
        return {'path': begin[0] + path_in_graph['path'] + end[0][::-1],
                'dist': begin[1] + path_in_graph['dist'] + end[1],
                'time': tm_used,
                'tmTrans': path_in_graph['tmTrans']}
    return wrapper


class MetAtenas:
    '''
    MetAtenas
    ---------
    The class MetAtenas contains all the operations needed for the creation of
    the map of the Metro of Athens and the calculation of min_cam between
    stations.'''
    day_val = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
               "Friday": 4, "Saturday": 5, "Sunday": 6}

    def __init__(self, met_data):
        lineas_metro_data = load_data(met_data)
        self.st_lin = lineas_metro_data['lin']
        self.st_names = lineas_metro_data['stNm']
        self.st_dist = lineas_metro_data['stDist']
        # Average train speed is 80 km/h, we store the speed in m/min
        self.train_speed = round(80*1000/60, 2)
        self.start_travel_time = (0, 12, 0)
        # Heuristic values for line_travel_cost and line_transfer_cost
        # set at get_adyacencies
        # By default we set, 1, if minimum_travel_time is lower than one
        # we change these values
        self.min_node_dist = 1
        # We load the station nodes, and then we introduce their adyacencies
        self.st_nodes = lineas_metro_data['stNodes']
        self.st_nodes = self.get_adyacencies(tuple(self.st_nodes.keys()))
        self.st_intervals = self.get_intervals()

    def get_adyacencies(self, node_names) -> dict:
        '''
        get_adyacencies
        ---------------
        Returns a dictionary with all the adyacencies each node_name has. We
        only consider adyacencies between nodes.
        '''
        # Declare the dictionaries we will be using
        st_nodes = self.st_nodes
        # We use as min_dist start value the distance travelled in 1 minute
        min_dist = self.train_speed
        # The dictionary we will return
        adyacencies = {}
        for st_name in node_names:
            st_data = self.st_lin[st_name]
            ady = []
            distance = 0
            for i in range(0, len(st_data), 2):
                # Line of the station and pos in the line
                lin, pos = st_data[i: i + 2]
                # Names and distances as st_lin
                ln_nm, ln_dist = self.st_names[lin], self.st_dist[lin]
                lenln = len(ln_nm)
                # If the prevSt is a node then append
                if pos != 0 and st_nodes.get(ln_nm[pos - 1]) is not None:
                    distance = dist(ln_dist, pos - 1, pos)
                    min_dist = min(min_dist, distance/self.train_speed)
                    ady.append((ln_nm[pos - 1], lin, distance))
                # If the nextSt is a node then append
                if pos < lenln and st_nodes.get(ln_nm[pos + 1]) is not None:
                    distance = dist(ln_dist, pos + 1, pos)
                    min_dist = min(min_dist, distance/self.train_speed)
                    ady.append((ln_nm[pos + 1], lin, distance))
            adyacencies[st_name] = tuple(ady)
            self.min_node_dist = min_dist
        return adyacencies

    def get_intervals(self) -> dict:
        '''
        get_intervals
        -------------
        All the stations that are not nodes are put into intervals, associated
        to their lines. In the case of the Athenas Metro, the only intervals
        we can find are at the start of the line or the end.'''
        st_intervals = {}
        # Read all metro lines
        for num_ln in self.st_names.keys():
            line_names, line_intervals = self.st_names[num_ln], []
            # start = -1 means we haven't found yet the start of the interval
            start, step, read_a_node, len_lin = -1, 0, False, len(line_names)
            for pos, name in enumerate(line_names):
                is_a_node = self.st_nodes.get(name) is not None
                if start == -1 and not is_a_node:
                    start = pos
                    step = 1 if not read_a_node else -1
                elif start != -1 and (is_a_node or pos == len_lin - 1):
                    # If it was an interval between a two nodes
                    step = 0 if read_a_node and is_a_node else step
                    # If station is not last, then the previous one is the last
                    last_st = pos - 1 if pos < len_lin - 1 else pos
                    line_intervals.append((start, last_st, step))
                    read_a_node, start = False, -1
                else:
                    read_a_node = is_a_node or read_a_node
            st_intervals[num_ln] = tuple(line_intervals)
        return st_intervals

    def move_to_node(self, st_line, st_pos):
        '''
        move_to_node
        ------------
        Returns the station names the interval covers between the stPos
        and the end of the interval.
        The way it covers the interval is codified in the step. If step is 1,
        then it's a start interval, if it's a -1 an end interval.
        Step cannot be 0 for the Athenas metro, as we haven't defined
        any middle intervals, which would need to be covered both ways
        and added both to the calculations.
        If it's a node, return ((), 0, None)'''
        if st_line != 0:
            st_nm, st_dist = self.st_names[st_line], self.st_dist[st_line]
            st_from_int = belongs_to(self.st_intervals[st_line], st_pos)
            st_interval = self.st_intervals[st_line][st_from_int]
            step = st_interval[2]
            pos_nd = st_interval[1] + 1 if step == 1 else st_interval[0] - 1
            return(st_nm[st_pos:pos_nd:step], dist(st_dist, st_pos, pos_nd),
                   st_nm[pos_nd])
        return ((), 0, None)

    def break_line(self, st_from, st_to):
        '''
        break_line
        ----------
        Breaks the line between two station nodes. To fix the line either call
        get_adyacencies(tuple(st_nodes.keys())) and assign it to st_nodes and
        fix all the lines.'''
        if any(self.st_nodes.get(st) is None for st in (st_from, st_to)):
            print("Invalid stations")
            return
        self.st_nodes[st_from] = tuple(ady_vals
                                       for ady_vals in self.st_nodes[st_from]
                                       if ady_vals[0] != st_to)
        self.st_nodes[st_to] = tuple(ady_vals
                                     for ady_vals in self.st_nodes[st_to]
                                     if ady_vals[0] != st_from)

    def get_time(self, time_used):
        '''
        get_time
        --------
        Returns day, hours and minutes from the timeAt if time_used had passed.
        time_used is in minutes.'''
        day, hour, minutes = self.start_travel_time
        minutes += time_used
        n_min = minutes % 60
        hour += (minutes - n_min)/60
        n_hour = hour % 24
        day += (hour - n_hour)/24 % 7
        return (day, n_hour, n_min)

    def transfer_line_time(self, time_used):
        '''
        transfer_line_time
        ------------------
        Default function to obtain the average time spent in transfer in a
        transfer station. If the metro is closed at that time, returns -1.'''
        day, hour, mint = self.get_time(time_used)
        tm_trans = -1
        if hour < 5:
            if hour == 0 and mint < 30:
                tm_trans = 12
            elif day in {5, 6} and hour < 2:
                tm_trans = 15
        elif 5 <= hour < 9:
            met_open = hour > 5 or mint >= 30
            # 5:30 / 10m -> 9 / 3m
            tm_trans = 10 + ((hour - 5)*60 + mint)*(-1/30) if met_open else -1
        elif hour < 12:
            tm_trans = 3
        elif hour < 15:
            # 12:00 / 3min -> 15:00 / 5min
            tm_trans = 3 + ((hour - 12)*60 + mint)*(1/90)
        elif hour < 17:
            # 15:00 / 5min -> 17:00 / 4min
            tm_trans = 5 + ((hour - 15)*60 + mint)*(-1/120)
        elif hour < 20:
            tm_trans = 4
        elif hour < 22:
            # 20:00 / 4min -> 22:00 / 10min
            tm_trans = 4 + ((hour - 20)*60 + mint)*(1/20)
        else:
            tm_trans = 10
        return round(tm_trans, 1)

    def set_hour(self, day, hour, minute):
        self.start_travel_time = (self.day_val[day], hour, minute)

    def set_speed(self, speed):
        self.train_speed = round(speed*1000/60, 2)

    def heuristic_costs(self, st_name, st_lin=0):
        '''
        heuristic_costs
        ---------------
        Heuristic used to calculate a simulated distance in minutes between the
        stNode and all the other stNodes.
        Traveling between nodes of the same line accrues the travelCost (1).
        In a transfer station if you change lines, you accrue the exchangeCost
        (2).
        We find the min_cost to all the nodes using a modified Dijkstra
        algorithm.'''
        travel_cost = self.min_node_dist/self.train_speed
        exch_cost = travel_cost*3
        # visited where we store the permanent labels and stack_nodes were we
        # store the temporary ones
        visited = defaultdict(None)
        # node_in_stack = (stNode_Nm, node_cost, node_at_Ln)
        stack_nodes = [(st_name, 0, st_lin)]

        def comp(st_1, st_2):
            return st_1[1] - st_2[1]  # st_1 >= st_2
        # We don't modify the temp labels, we only check if it already has a
        # permanent one.
        while len(stack_nodes) != 0:
            # 0 -> stNodeNm / 1 -> node_cost / 2 -> node_at_Ln
            node_top = stack_nodes.pop()
            val_visited = visited.get(node_top[0])
            # Node already visited
            if val_visited is not None and val_visited != node_top[1]:
                continue
            # Add permanent label
            visited[node_top[0]] = node_top[1]
            # Get all adyacents
            adyacencies = self.st_nodes[node_top[0]]
            for ady_values in adyacencies:
                # ady = (nxt_st_name, through_line, nxt_st_dixt)
                # Adyacent already visited
                if visited.get(ady_values[0]) is not None:
                    continue
                node_in_ln = node_top[2] in {0, ady_values[1]}
                n_cost = travel_cost if node_in_ln else exch_cost
                insert_sorted(stack_nodes, (ady_values[0],
                                            node_top[1] + n_cost,
                                            ady_values[1]), comp)
        return visited

    @move_to_graph
    def min_cam(self, st_from, st_to, lin_from=0, lin_to=0, tm_used=0):
        '''
        min_cam
        -------
        Applies the A* algorithm to the nodes we have defined in st_nodes.
        The g(x) is the approximated time needed to cover the distance between
        st_from to station x. h(x) is the approximated time needed calculated
        at heuristic_costs.
        st_from is the start station and st_to the end.
        lin_from and lin_to indicates the lines we have to use
            (chosen at move_to_graph)
        tm_used is the time that has already passed (example, moving from
            st_from to the nearest station node)
        Returns a dictionary with 'path', 'dist' and 'tm_trans'
        '''
        h_vals = self.heuristic_costs(st_to, st_lin=lin_to)
        # stNodeVals=(  st_at, st_from,dist_trav,    ln_at,tm_trans, nd_cost)
        open_stck = [(st_from, st_from,        0, lin_from,       0,       0)]
        visited = defaultdict(None)

        def comp(node_vals_1, node_vals_2):
            # f_cost_1 >=  f_cost_2
            return node_vals_1[-1] - node_vals_2[-1]

        # In open_stck there can be two instances of the same node. Of these
        # instances we only count the lowest one, that is the first to be
        # extracted from open_stck. After we have added one of these to visited
        # we ignore the other ones.
        while len(open_stck) != 0 and open_stck[-1][0] != st_to:
            st_at, st_from, st_dist, at_ln, tm_trans, cost = open_stck.pop()
            if visited.get(st_at) is not None:
                continue
            visited[st_at] = st_from
            adyacencies = self.st_nodes[st_at]
            for nxt_st_nm, through_ln, nxt_st_dist in adyacencies:
                # Node has already been visited
                if visited.get(nxt_st_nm) is not None:
                    continue
                # Total time used travelling the total distance (g1(x))
                tt_tm = round((st_dist + nxt_st_dist)/self.train_speed, 1)
                # Next transfer time
                nxt_trans_tm = 0
                if at_ln not in {0, through_ln}:
                    time = self.transfer_line_time(round(tt_tm + tm_trans
                                                         + tm_used, 1))
                    if time > 0:
                        nxt_trans_tm += time
                    else:
                        continue
                # If we are at the st_to, and we are not in lin_to
                if nxt_st_nm == st_to and lin_to not in {0, through_ln}:
                    time = self.transfer_line_time(round(tt_tm + nxt_trans_tm + tm_used, 1))
                    if time > 0:
                        nxt_trans_tm += time
                    else:
                        continue
                # f(x) = g(x) + h(x) (g(x) = g1(x) + g2(x))
                # g2(x) = nxt_trans_tm + tm_trans
                node_cost = nxt_trans_tm + tm_trans + tt_tm + h_vals[nxt_st_nm]
                insert_sorted(open_stck, (nxt_st_nm, st_at, st_dist + nxt_st_dist,
                                          through_ln, nxt_trans_tm + tm_trans,
                                          node_cost), comp)
        if len(open_stck) == 0:
            return None
        node_info = open_stck.pop()
        path = [node_info[0]]
        st_prev = node_info[1]
        while visited[st_prev] != st_prev:
            path.insert(0, st_prev)
            st_prev = visited[st_prev]
        path.insert(0, st_prev)
        return {'path': tuple(path), 'dist': node_info[2],
                'tmTrans': node_info[4]}


if __name__ == '__main__':
    metroAt = MetAtenas('lineasMetro.json')
    a = metroAt.min_cam("Sepolia", "Omonia")
