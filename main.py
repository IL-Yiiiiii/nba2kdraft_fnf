import copy, streamlit as st, pandas as pd

player_array = []
drafted_player_array = []
t1_array = []
if "compare_array" not in st.session_state:
    st.session_state.compare_array = []
if "compare_df" not in st.session_state:
    st.session_state.compare_df = pd.DataFrame()

class Player:
    def __init__(self, name, rating, primary_pos, secondary_pos, set, ht, wt, ins, mid, three, plk, itd, prd, reb, ath):
        self.name = name
        self.rating = rating
        self.primary_pos = primary_pos
        self.secondary_pos = secondary_pos
        self.set = set
        self.desc = ""
        self.pic = ""
        self.ht = ht
        self.wt = str(wt) + "lbs"
        self.ins = ins
        self.mid = mid
        self.three = three
        self.plk = plk
        self.itd = itd
        self.prd = prd
        self.reb = reb
        self.ath = ath
        self.ppg = -1
        self.rpg = -1
        self.apg = -1
        self.mpg = -1
        self.spg = -1
        self.bpg = -1
        self.fgp = -1
        self.three_p = -1
        self.ftp = -1
        self.compare = False

    def clone(self):
            return copy.deepcopy(self)

    def convert_positions(self):
        if self.secondary_pos == "":
            positions = self.primary_pos
        else:
            positions = self.primary_pos+"/"+self.secondary_pos
        return positions

    def to_dict(self):
        return {"Name": self.name,
        "Rating": self.rating,
        "Positions": self.convert_positions(),
        "Height":      self.ht,
        "Weight":      self.wt,
        "Inside Scoring":     self.ins,
        "Mid Range Shooting":     self.mid,
        "3PT Shooting":   self.three,
        "Playmaking":     self.plk,
        "Interior Defense":     self.itd,
        "Perimeter Defense":     self.prd,
        "Rebounding":     self.reb,
        "Athleticism":     self.ath,
        "PPG":     self.ppg,
        "RPG":     self.rpg,
        "APG":     self.apg,
        "MPG":     self.mpg,
        "SPG":     self.spg,
        "BPG":     self.bpg,
        "FG%":     self.fgp,
        "3P%": self.three_p,
        "FT%":     self.ftp,
    }

def load(file, array):
    try:
        with open(file) as f:
            for line in f:
                clean_line = line.strip()
                if not clean_line: continue  # Skip empty lines
                parts = clean_line.split(",")
                if len(parts) == 16:
                    n = parts[0].strip()
                    r = parts[1].strip()
                    pp = parts[2].strip()
                    sp = parts[3].strip()
                    se = parts[4].strip()
                    ht = parts[5].strip()
                    wt = parts[6].strip()
                    ins = parts[7].strip()
                    mid = parts[8].strip()
                    three = parts[9].strip()
                    plk = parts[10].strip()
                    pd = parts[11].strip()
                    itd  = parts[12].strip()
                    reb = parts[13].strip()
                    ath = parts[14].strip()
                array.append(Player(n, r, pp, sp, se, ht, wt, ins, mid, three, plk, pd, itd, reb, ath))
    except FileNotFoundError:
        print("File not found")

def display_player(player):
    added_confirm = False
    added_already = False
    secondary = ""
    if player.secondary_pos != "":
        secondary = "/" + player.secondary_pos
    with st.expander(f"***{player.name}*** [{player.rating} - {player.primary_pos}{secondary}]"):
        col_gap1, col_left, col_gap2, col_right = st.columns([1,5,1,10])
        with col_left:
            if player.pic != "":
                st.image(player.pic)
            if st.button("Compare Player", key=f"compare_button_{player.name}"):
                already_added = any(p.name == player.name for p in st.session_state.compare_array)
                if not already_added:
                    added_confirm = True
                    st.session_state.compare_array.append(player.clone())
                else:
                    added_already = True
        if added_confirm:
            st.markdown(
                f"""
                    <div style='background-color: #213d25; padding: 10px; border-radius: 5px; 
                    color: #68e27b; text-align: center; font-weight: italic;'>
                    {player.name} added to compare!</div>
                    """,
                unsafe_allow_html=True)
        elif added_already:
            st.markdown(
                f"""
                <div style='background-color: #3d421f; padding: 10px; border-radius: 5px; 
                            color: #ffff8a; text-align: center; font-weight: italic;'>
                 {player.name} already added to compare!
                </div>
                """,
                unsafe_allow_html=True)
        with col_right:
            st.subheader(f"Set: *{player.set}*")
            st.subheader(f"Height: *{player.ht}*")
            st.subheader(f"Weight: *{player.wt}*")
            st.write("")
            st.write(player.desc)
        st.markdown("---")
        col_gap1, col_ats_title, col_gap2, col_stats_title1 = st.columns([0.6, 5.3, 1, 8])
        with col_ats_title:
            st.subheader(f"Attributes:")
        with col_gap2:
            st.markdown("""
                              <div style="
                                  border-left: 2px solid #3c4044;
                                  height: 100%;
                                  min-height: 62px;
                                  margin: 0 auto;
                                  display: block;
                                  width: 2px;
                              "></div>
                          """, unsafe_allow_html=True)
        with col_stats_title1:
            st.subheader(f"Stats & Splits:")
        col_gap1, col_ats, col_gap2, col_stats1, col_stats2, col_stats3 = st.columns([1, 8, 2, 4, 4, 4])
        with col_ats:
            st.write(f"**Inside Scoring: {colour_grade(player.ins)}**")
            st.write(f"**Mid-Range Shooting: {colour_grade(player.mid)}**")
            st.write(f"**3PT Shooting: {colour_grade(player.three)}**")
            st.write(f"**Playmaking: {colour_grade(player.plk)}**")
            st.write(f"**Interior Defense: {colour_grade(player.itd)}**")
            st.write(f"**Perimeter Defense: {colour_grade(player.prd)}**")
            st.write(f"**Rebounding: {colour_grade(player.reb)}**")
            st.write(f"**Athleticism: {colour_grade(player.ath)}**")
        with col_gap2:
            st.markdown("""
                <div style="
                    border-left: 2px solid #3c4044;
                    height: 100%;
                    min-height: 325px;
                    margin: 0 auto;
                    display: block;
                    width: 2px;
                "></div>
            """, unsafe_allow_html=True)
        with col_stats1:
            st.metric(f"**PPG**", player.ppg)
            st.metric(f"**MPG**", player.mpg)
            st.metric(f"**FG%**", player.fgp)
        with col_stats2:
            st.metric(f"**RPG**", player.rpg)
            st.metric(f"**SPG**", player.spg)
            st.metric(f"**3P%**", player.three_p)
        with col_stats3:
            st.metric(f"**APG**", player.apg)
            st.metric(f"**BPG**", player.bpg)
            st.metric(f"**FT%**", player.ftp)

def load_to_df(array):
    st.session_state.compare_df = pd.DataFrame([obj.to_dict() for obj in array])

def add_desc(file, array):
    try:
        with open(file) as d:
            for i in range(len(array)):
                desc = d.readline().strip()
                array[i].desc = desc
    except FileNotFoundError:
        print("File not found")

def add_pics():
    try:
        with open("txt/tier1pics.txt") as p:
            for i in range(7):
                pic = p.readline().strip()
                t1_array[i].pic = "images/" + str(pic)
    except FileNotFoundError:
        print("File not found")

def colour_grade(grade):
    grade = str(grade)
    if grade == "S":
        new = f":violet[{grade}]"
    elif grade == "A+":
        new = f":blue[{grade}]"
    elif grade == "A" or grade == "A-":
        new = f":green[{grade}]"
    elif grade == "B+" or grade == "B" or grade == "B-":
        new = f":yellow[{grade}]"
    elif grade == "C+" or grade == "C" or grade == "C-":
        new = f":orange[{grade}]"
    elif grade == "D+" or grade == "D" or grade == "D-" or grade == "F":
        new = f":red[{grade}]"
    return new

def display_t1():
    for i in range(len(t1_array)):
        display_player(t1_array[i])

def check_playstyles(player, pstyle_choice):
    if pstyle_choice == "None":
        return True
    playstyles = player.desc
    parts = playstyles.split(",")
    if len(parts) == 3:
        pstyle1 = parts[0].strip()
        pstyle2 = parts[1].strip()
        pstyle3 = parts[2].strip()
        if pstyle1 == pstyle_choice or pstyle2 == pstyle_choice or pstyle3 == pstyle_choice:
            return True
    elif playstyles == 2:
        pstyle1 = parts[0].strip()
        pstyle2 = parts[1].strip()
        if pstyle1 == pstyle_choice or pstyle2 == pstyle_choice:
            return True
    if parts == pstyle_choice:
        return True

def make_attribute_dict():
    attribute_dict = {}
    try:
        with open("txt/attributes.txt") as f:
            for line in f:
                clean_line = line.strip()
                if not clean_line: continue  # Skip empty lines
                parts = clean_line.split(",")
                name = parts[0].strip()
                shortened = parts[1].strip()
                attribute_dict[name] = shortened
    except FileNotFoundError:
        print("File not found")
    return attribute_dict

def check_attribute(player, attribute_choice, min_grade_choice, max_grade_choice, attribute_dict):
    if attribute_choice == "None":
        return True
    dict = attribute_dict
    attribute = str(dict[attribute_choice])
    grade_order = ["S", "A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"]
    if grade_order.index(min_grade_choice) >= grade_order.index(getattr(player, attribute)) and grade_order.index(max_grade_choice) <= grade_order.index(getattr(player, attribute)):
        return True

def check_position(player, pos_choice, sec_boolean):
    if pos_choice == None:
        return True
    if player.primary_pos == pos_choice:
        return True
    elif player.secondary_pos == pos_choice and sec_boolean == True:
        return True

def reset():
    st.session_state.pos_choice = None
    st.session_state.ps_choice = "None"
    st.session_state.a_choice = "None"
    st.session_state.sec_choice = False
    st.session_state.max_a_choice = "S"
    st.session_state.min_a_choice = "F"

#MAIN STARTS HERE
load("txt/tier1.txt", t1_array)
load("txt/players.txt", player_array)
add_desc("txt/tier1desc.txt",t1_array)
add_desc("txt/players_desc.txt", player_array)
option = st.sidebar.selectbox("Menu", ["Home", "Guide", "Tier 1 Players", "Search Players", "Compare Players", "Teams"])
if st.sidebar.button("***:rainbow[Send balloons!]***"):
    st.balloons()
if st.sidebar.button("***:rainbow[Send stars!]***"):
    youtube_url = "https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1"
    st.markdown(
        """
        <iframe width="560" height="315"
        src="https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1"
        frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
        """,
        unsafe_allow_html=True
    )

col_logo, col_blank = st.columns(2)
with col_logo:
    st.image("images/Logo.png")
if option == "Home":
    st.title("**:orange[Favourites]** *:red[&]* ***:blue[Future]***")
    st.write("Welcome to the draft website - Please use the sidebar to navigate to different features.")
    st.subheader("Your name: ")
    st.subheader("Your pick position: " )
    st.button("Trade pick position")
    st.subheader("Current Round/Pick: ")
    st.subheader("Your team: ")
    st.write("[Placeholder for team display]")
    st.button("Go to team")

elif option == "Guide":
    st.title("GUIDE:")
    st.subheader("About the players:")
    st.write("Players in sets 2020-2026 have their ratings based on potential.")
    st.write("MyTEAM Players have been adjusted to not be absolutely busted.")
    st.subheader("If rotations are automated:")
    st.write("Playoffs: 8 Man Rotation, Time towards bench - 35")
    st.write("Regular Season: 9 Man Rotation, Time towards bench - 50")
    st.subheader("Attribute and stat information:")
    st.write("***Stats included are from the regular season (rounded), all per game***: Points, Rebounds, Assists, Minutes, Steals, Blocks, Field Goal %, 3 Point %, Free Throw %")
    st.write(f"The grade **:violet[S]** indicates the attribute is in the range 95-99.")
    st.write("The rest of the grades are whatever 2K gives the player.")
    st.subheader("What is each attribute?")
    st.write("***Inside Scoring:*** **How well the player scores close to the basket; includes dunks, layups and post moves.**")
    st.write("***Mid-Range Shooting:*** **How well the player shoots from the middle distance (roughly 10-20 feet).**")
    st.write("***3-Point Shooting:*** **How well the player shoots from beyond the arc.**")
    st.write("***Playmaking:*** **How well the player creates scoring opportunities for teammates through passing and decision making.**")
    st.write("***Interior Defense:*** **How well the player defends inside the paint; includes shot blocking and stopping drives.**")
    st.write("***Perimeter Defense:*** **How well the player guards on the outside against shooters and ball handlers; includes contesting**")
    st.write("***Rebounding:*** **How well the player grabs missed shots on both ends.**")
    st.write("***Athleticism:*** **How physically gifted the player is in terms of speed, leaping ability and explosiveness.**")
    st.subheader("What is each playstyle?")
    st.write("***3-Level Scorer:*** **Can score at the rim, mid range and from three at a high level (A or above)**")
    st.write("***Sharpshooter:*** **Elite perimeter(3PT) shooter, floor spacer**")
    st.write("***Mid Range Assassin:*** **Elite pull up and mid range scorer**")
    st.write("***Crafty Finisher:*** **Elite touch and skill finisher; floaters, layups, finishing through contact**")
    st.write("***Explosive Finisher:*** **Elite athlete who finishes above the rim**")
    st.write("***Paint Beast:*** **Dominant interior scorer and rebounder**")
    st.write("***Stretch Big:*** **Big man who spaces the floor with shooting** (At least B+ in both defenses)")
    st.write("***Defensive Anchor:*** **Elite rim protector and interior defender**")
    st.write("***Perimeter Lockdown:*** **Elite on-ball perimeter defender**")
    st.write("***Versatile Defender:*** **Can guard multiple positions** (At least A- in both defenses)")
    st.write("***Two Way:*** **Elite on both ends**")
    st.write("***Two Way Unicorn:*** **UNIQUE two way talent at any position**")
    st.write("***Floor General:*** **Pass first orchestrator who controls tempo**")
    st.write("***Playmaking Maestro:*** **Scorer with elite secondary playmaking**")
    st.write("***Swiss Army Knife:*** **Does everything, no defined primary role**")

elif option == "Tier 1 Players":
    st.header("***Tier 1 Players:***")
    add_pics()
    display_t1()

elif option == "Search Players":
    st.header("*Player Search:*")
    col_pos, col_attribute = st.columns([6,8])
    with col_pos:
        playstyle_select = st.selectbox("Playstyle Filter:",
                     ["None", "3-Level Scorer", "Sharpshooter", "Mid Range Assassin", "Crafty Finisher", "Explosive Finisher",
                      "Paint Beast", "Stretch Big", "Defensive Anchor", "Perimeter Lockdown",
                      "Versatile Defender", "Two Way", "Floor General",
                      "Playmaking Maestro", "Swiss Army Knife"], key="ps_choice")
        pos_filter = st.segmented_control("Position Filter:", ["PG", "SG", "SF", "PF", "C"], key="pos_choice")
        sec_allowed = st.toggle("Allow secondary position", key="sec_choice")
        st.button("***:yellow[RESET FILTERS]***", on_click=reset)
    with col_attribute:
        attribute_select = st.selectbox("Attribute Filter:", ["None","Inside Scoring", "Mid-Range Shooting", "3-Point Shooting", "Playmaking", "Interior Defense", "Perimeter Defense", "Rebounding", "Athleticism"], key="a_choice")
        max_grade_select = st.select_slider("Max Attribute Grade:",["S", "A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"], key="max_a_choice")
        min_grade_select = st.select_slider("Min Attribute Grade:",["F", "D-", "D", "D+", "C-", "C", "C+", "B-", "B", "B+", "A-", "A", "A+", "S"], key="min_a_choice")
    st.markdown("---")
    st.subheader("*:green[UNDRAFTED:]*")
    for i in range(len(player_array)):
        if check_playstyles(player_array[i], playstyle_select) and check_attribute(player_array[i], attribute_select, min_grade_select, max_grade_select, make_attribute_dict()) and check_position(player_array[i], pos_filter, sec_allowed):
            display_player(player_array[i])
    st.markdown("---")
    st.subheader("*:red[DRAFTED:]*")

elif option == "Compare Players":
    st.header("*Compare Players:*")
    if st.button(":yellow[Reset compare]", key="reset_compare"):
        st.session_state.compare_array = []
        st.rerun()
    st.subheader("*Click on a player and click compare player to add here:*")
    st.markdown("""
        <style>
            div[data-testid="column"] {
                padding: 0px;
            }
            div[data-testid="stButton"] button {
                width: 100%;
            }
        </style>
    """, unsafe_allow_html=True)
    if st.session_state.compare_array:
        player_names = [p.name for p in st.session_state.compare_array]
        #col_remove_select, col_remove_button = st.columns([6,6], vertical_alignment="bottom")
        #with col_remove_select:
            #player_remove = st.selectbox("Remove player:", player_names)
        #with col_remove_button:
            #if st.button(":red[Remove]"):
                #st.session_state.compare_array = [p for p in st.session_state.compare_array if p.name != player_remove]
                #st.rerun()

        n = len(st.session_state.compare_array)

        # Match the ratio to your df's row-label vs data columns
        col_widths = [1.5] + [1] * n
        cols = st.columns(col_widths)

        with cols[0]:
            st.write("")  # empty space for row label column

        for i, player in enumerate(st.session_state.compare_array):
            with cols[i + 1]:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.compare_array.pop(i)
                    st.rerun()

    load_to_df(st.session_state.compare_array)
    st.dataframe(st.session_state.compare_df.T, use_container_width=True)

elif option == "Teams":
    st.header("*Teams:*")
