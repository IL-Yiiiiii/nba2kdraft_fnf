import copy, streamlit as st, pandas as pd
import streamlit_authenticator as stauth
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=3000, limit=10000, key="draft_room_counter")
@st.cache_resource
def get_global_draft_store():
    return {
        "initialized": False,
        "player_array": [],
        "t1_array": [],
        "drafted_player_array": [],
        "drafted_t1_array": [],
        "all_teams": {}  # Structure: {"username_1": [player1, player2], "username_2": []}
    }
shared_draft = get_global_draft_store()

class Player:
    def __init__(self, name, rating, primary_pos, secondary_pos, set, ht, wt, ins, mid, three, plk, itd, prd, reb, ath, ppg, rpg, apg, mpg, spg, bpg, fgp, three_p, ftp):
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
        self.ppg = ppg
        self.rpg = rpg
        self.apg = apg
        self.mpg = mpg
        self.spg = spg
        self.bpg = bpg
        self.fgp = fgp
        self.three_p = three_p
        self.ftp = ftp
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
        "3PT Shooting":    self.three,
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
                if len(parts) == 24:
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
                    ppg = parts[15].strip()
                    rpg = parts[16].strip()
                    apg = parts[17].strip()
                    mpg = parts[18].strip()
                    spg = parts[19].strip()
                    bpg = parts[20].strip()
                    fgp = parts[21].strip()
                    thp = parts[22].strip()
                    ftp = parts[23].strip()
                    array.append(
                        Player(n, r, pp, sp, se, ht, wt, ins, mid, three, plk, pd, itd, reb, ath, ppg, rpg, apg, mpg,
                               spg, bpg, fgp, thp, ftp))
    except FileNotFoundError:
        print("File not found")


def display_player(player):
    added_confirm = False
    added_already = False
    drafted_confirm = False
    drafted_already = False
    secondary = ""
    if player.secondary_pos != "":
        secondary = "/" + player.secondary_pos

    # Grab the logged-in username for roster mapping
    username = st.session_state.get("username", "Guest")

    with st.expander(f"***{player.name}*** [{player.rating} - {player.primary_pos}{secondary}]"):
        col_gap1, col_left, col_gap2, col_right, col_gap3 = st.columns([0.5, 5, 1, 7.5, 0.5])
        with col_left:
            if player.pic != "":
                st.image(player.pic)
            # Global check for draft mode
            if not shared_draft["draft_mode"]:
                if st.button("Undo draft player", key=f"undo_button_{player.name}"):
                    was_in_regular = any(p.name == player.name for p in shared_draft["drafted_player_array"])
                    was_in_t1 = any(p.name == player.name for p in shared_draft["drafted_t1_array"])

                    if was_in_regular:
                        shared_draft["player_array"].append(player.clone())
                        shared_draft["player_array"].sort(key=lambda x: int(x.rating), reverse=True)
                    elif was_in_t1:
                        shared_draft["t1_array"].append(player.clone())
                        shared_draft["t1_array"].sort(key=lambda x: int(x.rating), reverse=True)

                    # Remove from whichever team owned them globally
                    for team_owner in shared_draft["all_teams"]:
                        shared_draft["all_teams"][team_owner] = [p for p in shared_draft["all_teams"][team_owner] if
                                                                 p.name != player.name]

                    shared_draft["drafted_t1_array"] = [p for p in shared_draft["drafted_t1_array"] if
                                                        p.name != player.name]
                    shared_draft["drafted_player_array"] = [p for p in shared_draft["drafted_player_array"] if
                                                            p.name != player.name]

                    drafted_confirm = False
                    st.session_state.pending_toast = {"message": f"You have undrafted {player.name}!", "icon": "🚫"}
                    st.rerun()
        with col_right:
            st.subheader(f"Set: *{player.set}*")
            st.subheader(f"Height: *{player.ht}*")
            st.subheader(f"Weight: *{player.wt}*")
            st.write("")
            st.write(player.desc)
            col_compare, col_draft = st.columns([1, 1])
            with col_compare:
                if st.button("Compare Player", key=f"compare_button_{player.name}"):
                    already_added = any(p.name == player.name for p in st.session_state.compare_array)
                    if not already_added:
                        added_confirm = True
                        st.session_state.compare_array.append(player.clone())
                    else:
                        added_already = True
            with col_draft:
                if st.button("Draft Player", key=f"draft_button_{player.name}"):
                    # Check if already drafted globally by anyone
                    already_drafted = (any(p.name == player.name for p in shared_draft["drafted_player_array"]) or
                                       any(p.name == player.name for p in shared_draft["drafted_t1_array"]))

                    if not already_drafted:
                        in_regular = any(p.name == player.name for p in shared_draft["player_array"])
                        in_t1 = any(p.name == player.name for p in shared_draft["t1_array"])

                        if in_regular:
                            shared_draft["drafted_player_array"].append(player.clone())
                            shared_draft["player_array"] = [p for p in shared_draft["player_array"] if
                                                            p.name != player.name]
                        elif in_t1:
                            shared_draft["drafted_t1_array"].append(player.clone())
                            shared_draft["t1_array"] = [p for p in shared_draft["t1_array"] if p.name != player.name]

                        # Add to the active user's global team dictionary entry
                        if username not in shared_draft["all_teams"]:
                            shared_draft["all_teams"][username] = []
                        shared_draft["all_teams"][username].append(player.clone())
                        shared_draft["all_teams"][username].sort(key=lambda x: int(x.rating), reverse=True)

                        drafted_confirm = True
                    else:
                        drafted_already = True
        # HTML/Toast warning rendering remains the same...
        if added_confirm:
            st.markdown(
                f"<div style='background-color: #213d3b; padding: 10px; border-radius: 5px; color: #8afffd; text-align: center; font-style: italic;'>{player.name} added to compare!</div>",
                unsafe_allow_html=True)
            st.toast(f"{player.name} added to compare!", icon="⚖️")
        elif added_already:
            st.markdown(
                f"<div style='background-color: #3d421f; padding: 10px; border-radius: 5px; color: #ffff8a; text-align: center; font-style: italic;'>{player.name} already added to compare!</div>",
                unsafe_allow_html=True)
        if drafted_already:
            st.markdown(
                f"<div style='background-color: #421f1f; padding: 10px; border-radius: 5px; color: #ff8a8a; text-align: center; font-style: italic;'>{player.name} has already been drafted!</div>",
                unsafe_allow_html=True)
        elif drafted_confirm:
            st.session_state.pending_toast = {"message": f"You have drafted {player.name}!", "icon": "🤝"}
            st.rerun()

        # Attribute and Stats layout section remains unchanged below this...
        st.markdown("---")
        col_gap1, col_ats_title, col_gap2, col_stats_title1 = st.columns([0.6, 5.3, 1, 8])
        with col_ats_title:
            st.subheader(f"Attributes:")
        with col_gap2:
            st.markdown(
                """<div style="border-left: 2px solid #3c4044; height: 100%; min-height: 62px; margin: 0 auto; display: block; width: 2px;"></div>""",
                unsafe_allow_html=True)
        with col_stats_title1:
            st.subheader(f"Stats & Splits:")
        col_gap1, col_ats, col_gap2, col_stats1, col_stats2, col_stats3 = st.columns([1, 8, 2, 4, 4, 4])
        with col_ats:
            st.write(f"**Inside Scoring: {colour_grade(player.ins)}**")
            st.write(f"**Mid-Range Shooting: {colour_grade(player.mid)}**")
            st.write(f"**3PT Shooting: {colour_grade(player.three)}**")
            st.write(f"**Playmaking: {colour_grade(player.plk)}**")
            st.write(f"**Perimeter Defense: {colour_grade(player.prd)}**")
            st.write(f"**Interior Defense: {colour_grade(player.itd)}**")
            st.write(f"**Rebounding: {colour_grade(player.reb)}**")
            st.write(f"**Athleticism: {colour_grade(player.ath)}**")
        with col_gap2:
            st.markdown(
                """<div style="border-left: 2px solid #3c4044; height: 100%; min-height: 325px; margin: 0 auto; display: block; width: 2px;"></div>""",
                unsafe_allow_html=True)
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

def add_pics(filename, array):
    try:
        with open(filename) as p:
            for i in range(len(array)):
                pic = p.readline().strip()
                array[i].pic = "images/" + str(pic)
    except FileNotFoundError:
        print("File not found")

def colour_grade(grade):
    grade = str(grade)
    new = None
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
    for i in range(len(shared_draft["t1_array"])):
        display_player(shared_draft["t1_array"][i])

def check_playstyles(player, pstyle_choice):
    if pstyle_choice == "None":
        return True
    playstyles = player.desc
    parts = playstyles.split(",")
    if len(parts) == 5:
        pstyle1 = parts[0].strip()
        pstyle2 = parts[1].strip()
        pstyle3 = parts[2].strip()
        pstyle4 = parts[3].strip()
        pstyle5 = parts[4].strip()
        if pstyle1 == pstyle_choice or pstyle2 == pstyle_choice or pstyle3 == pstyle_choice or pstyle4 == pstyle_choice or pstyle5 == pstyle_choice:
            return True
    elif len(parts) == 4:
        pstyle1 = parts[0].strip()
        pstyle2 = parts[1].strip()
        pstyle3 = parts[2].strip()
        pstyle4 = parts[3].strip()
        if pstyle1 == pstyle_choice or pstyle2 == pstyle_choice or pstyle3 == pstyle_choice or pstyle4 == pstyle_choice:
            return True
    elif len(parts) == 3:
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
# --- LOCAL STORAGE (Individual User UI Views) ---
# These are unique to whoever is looking at the screen right now
if "compare_array" not in st.session_state:
    st.session_state.compare_array = []
if "compare_df" not in st.session_state:
    st.session_state.compare_df = pd.DataFrame()
if "pending_toast" in st.session_state:
    st.toast(st.session_state.pending_toast["message"], icon=st.session_state.pending_toast["icon"])
    del st.session_state.pending_toast

# --- GLOBAL STORAGE (Shared Across All Devices) ---
# This block runs EXACTLY ONCE when the first person boots up the website
if not shared_draft["initialized"]:
    # 1. Load available player pools from text files
    temp_players = []
    load("txt/players.txt", temp_players)
    add_desc("txt/players_desc.txt", temp_players)
    shared_draft["player_array"] = temp_players
    add_pics("txt/playerspics.txt", shared_draft["player_array"])
    temp_t1 = []
    load("txt/tier1.txt", temp_t1)
    add_desc("txt/tier1desc.txt", temp_t1)
    shared_draft["t1_array"] = temp_t1
    add_pics("txt/tier1pics.txt", shared_draft["t1_array"])
    # 2. Initialize empty global draft tracking lists
    shared_draft["drafted_player_array"] = []
    shared_draft["drafted_t1_array"] = []
    # 3. Initialize multi-user team rosters & draft mechanics
    shared_draft["all_teams"] = {}
    shared_draft["picks_made"] = 0
    shared_draft["draft_mode"] = False
    # Flip the master switch so the server remembers this data is ready
    shared_draft["initialized"] = True
# --------------------------------------
option = st.sidebar.selectbox("Menu", ["Home", "Guide", "Headliner Players", "Search Players", "Compare Players", "Teams", "Trade Hub", "Draft", "Results"])
if st.sidebar.button("***:rainbow[Send balloons!]***"):
    st.balloons()
if st.sidebar.button("***:rainbow[Send snowflakes!]***"):
    st.snow()
if st.sidebar.button("***:rainbow[Send stars!]***"):
    st.toast("Here's a star!", icon="⭐")
    youtube_url = "https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1"
    st.markdown(
        """
        <iframe width="560" height="315"
        src="https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1"
        frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
        """,
        unsafe_allow_html=True
    )
st.sidebar.write("------------")
st.sidebar.write("Draft Date: **TBC**")
st.sidebar.write("*Also credit to the NBA, Bleacher Report and others for photos please don't copyright me*")

col_logo, col_blank = st.columns(2)
with col_logo:
    st.image("images/Logo.png")
if option == "Home":
    st.title("**:orange[Favourites]** *:red[&]* ***:blue[Future]***")
    st.write("Welcome to the draft website - Please use the sidebar to navigate to different features.")
    #Login part
    credentials = {"usernames": {}}
    for uname, info in st.secrets["credentials"]["usernames"].items():
        credentials["usernames"][uname] = {
            "name": info["name"],
            "password": info["password"],  # already hashed, see below
        }

    authenticator = stauth.Authenticate(
        credentials,
        st.secrets["cookie"]["name"],
        st.secrets["cookie"]["key"],
        st.secrets["cookie"]["expiry_days"],
        auto_hash=False,  # important: our passwords are already hashed, don't re-hash them
    )

    authenticator.login(location="main")

    auth_status = st.session_state.get("authentication_status")
    name = st.session_state.get("name")
    username = st.session_state.get("username")

    if auth_status:
        st.subheader(f"*Logged in as:* **{name}**")
        authenticator.logout("**LOG OUT**", "main")
        st.divider()
        if not shared_draft["draft_mode"]:
            st.subheader("**Website currently in pre-draft mode**")
            st.write("You can look at players and build teams")
        if name == "Isaac":
            if st.button("START DRAFT"):
                shared_draft["draft_mode"] = True
                st.rerun()
            if st.button("REVERT TO PRE-DRAFT MODE"):
                shared_draft["draft_mode"] = False
                st.rerun()
        if shared_draft["draft_mode"]:
            st.subheader("WEBSITE IS IN *DRAFT MODE*")
            st.subheader("Your pick position: ")
            st.button("Trade pick position")
            st.subheader("Current Round/Pick: ")
            st.subheader("Your team: ")
            st.write("[Placeholder for team display]")
            st.button("Go to team")

        # current_pick_team = get_whose_turn_it_is(st.session_state.get("picks_made", 0))
        # if username == current_pick_team:
        # st.success("It's your turn to pick!")
        # else:
        # st.info(f"Waiting on {current_pick_team} to pick...")

    elif auth_status is False:
        st.error("Username or password is incorrect")
    elif auth_status is None:
        st.warning("Please enter your username and password")
    # Login ends here

elif option == "Guide":
    st.title("***GUIDE***")
    st.subheader("If rotations are automated:")
    st.write("Playoffs: 8 Man Rotation, Time towards bench - 35")
    st.write("Regular Season: 9 Man Rotation, Time towards bench - 50")
    st.subheader("Attribute and stat information:")
    st.write("***Stats included are from the regular season (rounded), all per game***: Points, Rebounds, Assists, Minutes, Steals, Blocks, Field Goal %, 3 Point %, Free Throw %")
    st.write(f"The grade **:violet[S]** indicates that the player is top 3 for that attribute (out of players in the draft).")
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
    st.write("***3-Level Scorer:*** **Can score at the rim, mid range and from three at a high level (A- in all 3 types of scoring)**")
    st.write("***Sharpshooter:*** **Elite perimeter(3PT) shooter, floor spacer (A+/S 3PT)**")
    st.write("***Mid Range Assassin:*** **Elite pull up and mid range scorer (A+/S Mid Range)**")
    st.write("***Crafty Finisher:*** **Elite touch and skill finisher; floaters, layups, finishing through contact**")
    st.write("***Explosive Finisher:*** **Elite athlete who finishes above the rim**")
    st.write("***Paint Beast:*** **Dominant interior scorer and rebounder**")
    st.write("***Stretch Big:*** **Big man who spaces the floor with shooting**")
    st.write("***Defensive Anchor:*** **Elite rim protector and interior defender (A+/S Interior defense)**")
    st.write("***Perimeter Lockdown:*** **Elite on-ball perimeter defender (90+ Perimeter defense)**")
    st.write("***Versatile Defender:*** **Can guard multiple positions**")
    st.write("***Two Way:*** **Elite on both ends**")
    st.write("***Floor General:*** **Pass first orchestrator who controls tempo**")
    st.write("***Playmaking Maestro:*** **Scorer with elite secondary playmaking**")
    st.write("***Swiss Army Knife:*** **Does everything, no defined primary role**")
    st.subheader("Opposing Superteams (not really superteams they aren't that scary actually):")
    st.write("Celtics: Tatum + Giannis")
    st.write("Thunder: Shai + KD")
    st.write("Knicks: Brunson + Booker")
    st.write("Nuggets: Mitchell + Jokic")
    st.write("Wizards: Doncic + AD")

elif option == "Headliner Players":
    st.title("***HEADLINERS***")
    st.subheader("***NOTE:***")
    st.write("**The draft is in serpentine order - so in even rounds the 7th pick will go 1st, 6th go 2nd, and so on.**")
    st.write("**Example:** Round 1: 1,2,3,4,5,6,7 | Round 2: 7,6,5,4,3,2,1")
    st.write("*> Picking a 99 will get you a pick in the range* **4-7**.")
    st.write("*> Picking a 98 will get you a pick in the range* **1-3**.")
    st.write("> **CONTEST SYSTEM:** If multiple people pick a player the person who gets the player is decided by random and the person (or people) who did not get the player has to pick from the remaining headliners.")
    st.write("Also: The efficiencies are more normal in the playoffs, for example, 3PT shooting % for mid shooters falls to mid 30 percentages")
    st.header("*:green[UNDRAFTED]*")
    display_t1()
    st.header("*:red[DRAFTED]*")
    if shared_draft["drafted_t1_array"]:
        for i in range(len(shared_draft["drafted_t1_array"])):
            display_player(shared_draft["drafted_t1_array"][i])

elif option == "Search Players":
    st.title("*PLAYER SEARCH*")
    st.subheader("About the players:")
    st.write("Players in sets 2020-2026 have their ratings based on their projected primes.")
    st.write("Note: The efficiencies are more normal in the playoffs, for example, 3PT shooting % for mid shooters falls to mid 30 percentages")
    st.write("Also: Players who took a low volume of 3s (that shouldn't have) due to system profiency get put at 0 3P%")
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
    st.header("*:green[UNDRAFTED]*")
    for i in range(len(shared_draft["player_array"])):
        if check_playstyles(shared_draft["player_array"][i], playstyle_select) and check_attribute(
                shared_draft["player_array"][i], attribute_select, min_grade_select, max_grade_select,
                make_attribute_dict()) and check_position(shared_draft["player_array"][i], pos_filter, sec_allowed):
            display_player(shared_draft["player_array"][i])
    st.markdown("---")
    st.header("*:red[DRAFTED]*")
    if shared_draft["drafted_player_array"]:
        for i in range(len(shared_draft["drafted_player_array"])):
            display_player(shared_draft["drafted_player_array"][i])

elif option == "Compare Players":
    st.title("*COMPARE PLAYERS*")
    st.subheader("*Click on a player in 'Search Players' or 'Headliner Players' and click compare player to add here:*")
    if st.button(":yellow[Reset compare]", key="reset_compare"):
        st.session_state.compare_array = []
        st.rerun()
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
    st.dataframe(st.session_state.compare_df.T, width='stretch')

elif option == "Draft":
    st.title("*DRAFT*")

elif option == "Teams":
    st.title("*TEAMS*")
    st.subheader("*YOUR TEAM:*")

    username = st.session_state.get("username", "Guest")
    user_team = shared_draft["all_teams"].get(username, [])

    if user_team:
        st.write(f"Player Count: {len(user_team)}")
        for i in range(len(user_team)):
            display_player(user_team[i])
    else:
        st.write("You haven't drafted any players yet!")

    if not shared_draft["draft_mode"]:
        st.divider()
        st.subheader("*THIS PAGE WILL CHANGE IN DRAFT MODE!*")
    if shared_draft["draft_mode"]:
        st.divider()
        st.subheader("*OTHER TEAMS:*")

        # 1. Filter the dictionary to ONLY include opponents
        other_teams = {owner: roster for owner, roster in shared_draft["all_teams"].items() if owner != username}

        # 2. Check if the opponent list is empty
        if not other_teams:
            st.write("No one else has drafted any players yet!")
        else:
            # 3. Loop through the filtered opponents
            for team_owner, roster in other_teams.items():
                with st.expander(f"{team_owner.upper()[0] + team_owner[1:]}'s Team ({len(roster)} players)"):
                    if not roster:
                        st.write(f"*{team_owner} hasn't drafted anyone yet.*")
                    else:
                        for player in roster:
                            display_player(player)

elif option == "Trade Hub":
    st.title("*TRADE HUB*")
    if not shared_draft["draft_mode"]:
        st.subheader("**Will open in draft mode!**")

elif option == "Results":
    st.title("*RESULTS*")
    st.subheader("**< YEAR 1 >**")
    st.write("*WAITING!*")
    st.subheader("**< YEAR 2 >**")
    st.write("*WAITING!*")
    st.subheader("**< YEAR 3 >**")
    st.write("*WAITING!*")
    st.subheader("**< YEAR 4 >**")
    st.write("*WAITING!*")
    st.subheader("**< YEAR 5 >**")
    st.write("*WAITING!*")
    st.subheader("**< YEAR 6 >**")
    st.write("*WAITING!*")
    st.subheader("**< YEAR 7 >**")
    st.write("*WAITING!*")
