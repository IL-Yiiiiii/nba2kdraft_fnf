import streamlit as st, pandas as pd, random, time
import streamlit_authenticator as stauth
from streamlit_autorefresh import st_autorefresh
import pickle
import base64
import requests
import uuid
from player import Player
from upstash_redis import Redis
import json

# Initialize Upstash Redis client
redis = Redis(
    url=st.secrets["redis"]["UPSTASH_REDIS_REST_URL"], 
    token=st.secrets["redis"]["UPSTASH_REDIS_REST_TOKEN"]
)

# --- CLOUD DATABASE SETUP ---
def load_draft_state():
    try:
        # 1. Pull the data from Upstash
        data_str = redis.get("shared_draft_state")
        
        # 2. If it's a completely new database, auto-initialize it with zero data!
        if not data_str:
            initial_state = {
                "draft_order": [],
                "current_pick": 0,
                "headliners_resolved": False,
                "all_teams": {},
                "pending_trades": [],
                "draft_log": []
            }
            redis.set("shared_draft_state", json.dumps(initial_state))
            return initial_state
            
        # 3. Return the active draft data
        return json.loads(data_str)
        
    except Exception as e:
        st.error(f"Database read error: {e}")
        return st.session_state.get("last_valid_draft_state", {})

def save_draft_state(state):
    try:
        # Push the updated draft layout up to Upstash
        redis.set("shared_draft_state", json.dumps(state))
        return True
    except Exception as e:
        st.error(f"Database write error: {e}")
        return False
        
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

saved_state = load_draft_state()

if saved_state is not None:
    shared_draft = saved_state
else:
    shared_draft = {
        "initialized": False,
        "player_array": [],
        "t1_array": [],
        "drafted_player_array": [],
        "drafted_t1_array": [],
        "all_teams": {},
        "headliner_picks": {},
        "draft_order": [],
        "headliners_resolved": False,
        "coin_flip_losers": [],
        "draft_history": [],
        "draft_mode": False
    }

def display_player(player):
    added_confirm = False
    added_already = False
    drafted_confirm = False
    drafted_already = False
    secondary = ""
    if player.secondary_pos != "":
        secondary = "/" + player.secondary_pos

    username = st.session_state.get("username", "Guest")

    with st.expander(f"***{player.name}*** [{player.rating} - {player.primary_pos}{secondary}]"):
        col_gap1, col_left, col_gap2, col_right, col_gap3 = st.columns([0.5, 5, 1, 7.5, 0.5])
        with col_left:
            if player.pic != "":
                st.image(player.pic)
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

                    for team_owner in shared_draft["all_teams"]:
                        shared_draft["all_teams"][team_owner] = [p for p in shared_draft["all_teams"][team_owner] if
                                                                 p.name != player.name]

                    shared_draft["drafted_t1_array"] = [p for p in shared_draft["drafted_t1_array"] if
                                                        p.name != player.name]
                    shared_draft["drafted_player_array"] = [p for p in shared_draft["drafted_player_array"] if
                                                            p.name != player.name]

                    drafted_confirm = False
                    save_draft_state(shared_draft)
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
                    already_drafted = (any(p.name == player.name for p in shared_draft["drafted_player_array"]) or
                                       any(p.name == player.name for p in shared_draft["drafted_t1_array"]))

                    if already_drafted:
                        drafted_already = True
                    else:
                        # --- PRE-DRAFT / PRACTICE MODE (Your Original Logic) ---
                        if not shared_draft["draft_mode"]:
                            in_regular = any(p.name == player.name for p in shared_draft["player_array"])
                            in_t1 = any(p.name == player.name for p in shared_draft["t1_array"])

                            if in_regular:
                                shared_draft["drafted_player_array"].append(player.clone())
                                shared_draft["player_array"] = [p for p in shared_draft["player_array"] if
                                                                p.name != player.name]
                            elif in_t1:
                                shared_draft["drafted_t1_array"].append(player.clone())
                                shared_draft["t1_array"] = [p for p in shared_draft["t1_array"] if
                                                            p.name != player.name]

                            # Add to the active user's global team dictionary entry
                            if username not in shared_draft["all_teams"]:
                                shared_draft["all_teams"][username] = []
                            shared_draft["all_teams"][username].append(player.clone())
                            shared_draft["all_teams"][username].sort(key=lambda x: int(x.rating), reverse=True)

                            drafted_confirm = True

                        # --- PHASE 1: BLIND HEADLINERS ---
                        elif shared_draft["draft_mode"] and not shared_draft["headliners_resolved"]:
                            in_t1 = any(p.name == player.name for p in shared_draft["t1_array"])

                            if not in_t1:
                                st.error("⚠️ The draft hasn't officially started yet! Go pick a Headliner first.")
                                st.stop()

                            # Register their blind choice
                            shared_draft["headliner_picks"][username] = player.name

                            # Clear them from the losers list if they are submitting a backup choice
                            if username in shared_draft.get("coin_flip_losers", []):
                                shared_draft["coin_flip_losers"].remove(username)

                            save_draft_state(shared_draft)  # 💾 ADD THIS LINE HERE!

                            st.session_state.pending_toast = {"message": f"🔒 Locked in choice: {player.name}!",
                                                              "icon": "🎯"}
                            st.rerun()

                         # --- PHASE 2: LIVE SERPENTINE DRAFT ---
                        elif shared_draft["draft_mode"] and shared_draft["headliners_resolved"]:
                            draft_order_list = shared_draft.get("draft_order", [])
                            total_teams = len(draft_order_list)

                            # Defensive Check: Is the order actually set up?
                            if total_teams == 0:
                                st.error("🚨 The Draft Order hasn't been set up yet! It's currently empty.")
                                st.stop()

                            # Safe turn calculation based on actual team count
                            current_pick_idx = len(shared_draft.get("draft_history", []))
                            curr_r = (current_pick_idx // total_teams) + 1
                            curr_p = (current_pick_idx % total_teams) + 1

                            # Serpentine math
                            if curr_r % 2 != 0:
                                current_owner = draft_order_list[curr_p - 1]
                            else:
                                current_owner = draft_order_list[total_teams - curr_p]

                            if username != current_owner:
                                st.error(f"⚠️ Out of turn! It is currently {current_owner.capitalize()}'s choice.")
                                st.stop()

                            # Process standard draft selection
                            in_regular = any(p.name == player.name for p in shared_draft["player_array"])
                            in_t1 = any(p.name == player.name for p in shared_draft["t1_array"])

                            if in_regular:
                                shared_draft["drafted_player_array"].append(player.clone())
                                shared_draft["player_array"] = [p for p in shared_draft["player_array"] if
                                                                p.name != player.name]
                            elif in_t1:
                                shared_draft["drafted_t1_array"].append(player.clone())
                                shared_draft["t1_array"] = [p for p in shared_draft["t1_array"] if
                                                            p.name != player.name]

                            if username not in shared_draft["all_teams"]:
                                shared_draft["all_teams"][username] = []
                            shared_draft["all_teams"][username].append(player.clone())
                            shared_draft["all_teams"][username].sort(key=lambda x: int(x.rating), reverse=True)

                            # Log onto progress timeline
                            if "draft_history" not in shared_draft:
                                shared_draft["draft_history"] = []
                            shared_draft["draft_history"].append(f"{player.name} ({player.rating} OVR)")

                            drafted_confirm = True

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
                    # Custom dynamic message depending on draft mode
                    if shared_draft["draft_mode"] and shared_draft["headliners_resolved"]:
                        msg = f"📢 {username.capitalize()} has drafted {player.name}!"
                    else:
                        msg = f"You have drafted {player.name}!"

                    st.session_state.pending_toast = {"message": msg, "icon": "🤝"}

                    # 💾 ONLY RERUN IF THE SAVE WAS SUCCESSFUL
                    if save_draft_state(shared_draft):
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
if not shared_draft.get("initialized", False):
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
option = st.sidebar.selectbox("Menu", ["Start", "Guide", "Headliner Players", "Search Players", "Compare Players", "Draft Room", "Teams", "Trade Hub", "Results"])
if shared_draft["draft_mode"]:
    username = st.session_state.get("username", "Guest")

# ==========================================
# GLOBAL ON-THE-CLOCK NOTIFICATION SYSTEM
# ==========================================
if shared_draft.get("draft_mode") and shared_draft.get("headliners_resolved"):
    history = shared_draft.get("draft_history", [])
    current_pick_idx = len(history)
    total_teams = 7
    total_rounds = 8

    # Ensure the draft isn't over yet
    if current_pick_idx < (total_teams * total_rounds):
        curr_r = (current_pick_idx // total_teams) + 1
        curr_p = (current_pick_idx % total_teams) + 1

        # Calculate current owner using your snake draft math
        if curr_r % 2 != 0:
            current_owner = shared_draft["draft_order"][curr_p - 1]
        else:
            current_owner = shared_draft["draft_order"][total_teams - curr_p]

        # If the viewer is the current owner, fire a toast!
        if username == current_owner:
            st.toast(f"🚨 YOU ARE ON THE CLOCK! (Round {curr_r}.{curr_p})", icon="⏰")

# ==========================================
if shared_draft.get("draft_mode"):
    if option == "Draft Room":
        st_autorefresh(interval=5000, limit=10000, key="draft_room_counter")
    else:
        st_autorefresh(interval=15000, limit=10000, key="global_counter")

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
if option == "Start":
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
            if st.button("DRAFT MODE"):
                shared_draft["draft_mode"] = True
                save_draft_state(shared_draft)
                st.rerun()
            if st.button("PRE-DRAFT MODE"):
                shared_draft["draft_mode"] = False
                save_draft_state(shared_draft)
                st.rerun()
            if st.button("⚠️ EMERGENCY RESET ENTIRE DRAFT"):
                # Re-initializes a fresh, clean slate dictionary
                empty_draft = {
                    "initialized": False,
                    "player_array": [],
                    "t1_array": [],
                    "drafted_player_array": [],
                    "drafted_t1_array": [],
                    "all_teams": {},
                    "headliner_picks": {},
                    "draft_order": [],
                    "headliners_resolved": False,
                    "coin_flip_losers": [],
                    "draft_history": [],
                    "draft_mode": False
                }
                # Forces the cloud to overwrite with this clean slate
                save_draft_state(empty_draft)
                st.write("Cloud database wiped. Restarting app...")
                st.rerun()
        if shared_draft["draft_mode"]:
            st.subheader("Website is in *DRAFT MODE*, please head to 'Draft Room'")

    elif auth_status is False:
        st.error("Username or password is incorrect")
    elif auth_status is None:
        st.warning("Please enter your username and password (only needed when draft starts)")
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

elif option == "Draft Room":

    st.title("*DRAFT ROOM*")
    if not shared_draft["draft_mode"]:
        st.warning("🚨 The draft has not started yet!")

    else:
        username = st.session_state.get("username", "Guest")

        # --- PHASE 1 DISPLAY: WAITING ON BLIND HEADLINERS ---
        if not shared_draft.get("headliners_resolved", False):
            st.subheader("🎯 Phase 1: Headliner Submission Status")

            if username in shared_draft.get("coin_flip_losers", []):
                st.error(
                    "❌ YOU LOST THE RANDOMIZER! Your choice was taken. Head back to the Headliners tab and pick a remaining player!")
            elif username in shared_draft.get("headliner_picks", {}):
                st.success(
                    f"✅ You have securely submitted your choice: **{shared_draft['headliner_picks'][username]}**")
            else:
                st.info("👋 Go to the **Headliners** tab and click 'Draft Player' on your top choice to begin!")

            st.divider()

            picks_count = len(shared_draft.get('headliner_picks', {}))
            st.markdown(f"**Submissions received:** `{picks_count} / 7`")

            for user, pick in shared_draft.get("headliner_picks", {}).items():
                if st.session_state.get("name") == "Isaac":
                    st.write(f"- **{user.capitalize()}** selected *{pick}*")
                else:
                    st.write(f"- **{user.capitalize()}** has locked in a choice.")

            if username.lower() == "isaac" and picks_count == 7:
                st.write("")
                if st.button("Resolve Contests & Generate Draft Order", type="primary"):

                    pick_counts = {}
                    for u, p_name in shared_draft["headliner_picks"].items():
                        if p_name not in pick_counts:
                            pick_counts[p_name] = []
                        pick_counts[p_name].append(u)

                    losers_this_round = []

                    for p_name, users in pick_counts.items():
                        winner = random.choice(users)
                        player_obj = next((p for p in shared_draft["t1_array"] if p.name == p_name), None)

                        if player_obj:
                            if winner not in shared_draft["all_teams"]:
                                shared_draft["all_teams"][winner] = []
                            shared_draft["all_teams"][winner].append(player_obj.clone())
                            shared_draft["drafted_t1_array"].append(player_obj.clone())
                            shared_draft["t1_array"] = [p for p in shared_draft["t1_array"] if p.name != p_name]

                        for u in users:
                            if u != winner:
                                losers_this_round.append(u)
                                del shared_draft["headliner_picks"][u]

                    if len(losers_this_round) > 0:
                        shared_draft["coin_flip_losers"] = losers_this_round
                        save_draft_state(shared_draft)
                    else:
                        shared_draft["headliners_resolved"] = True
                        pool_98 = []
                        pool_99 = []
                        pool_other = []

                        for u in shared_draft["headliner_picks"].keys():
                            roster = shared_draft["all_teams"].get(u, [])
                            if roster:
                                try:
                                    rating = int(roster[0].rating)
                                    if rating == 98:
                                        pool_98.append(u)
                                    elif rating == 99:
                                        pool_99.append(u)
                                    else:
                                        pool_other.append(u)
                                except ValueError:
                                    pool_other.append(u)
                            else:
                                pool_other.append(u)

                        random.shuffle(pool_98)
                        random.shuffle(pool_99)
                        random.shuffle(pool_other)

                        shared_draft["draft_order"] = pool_98 + pool_99 + pool_other
                        shared_draft["headliners_resolved"] = True
                        save_draft_state(shared_draft)
                    st.rerun()

        # PHASE 1.5: The Draft Order Waiting Room
        elif not shared_draft.get("order_locked", False):
            st.title("⚖️ DRAFT ORDER CONFIRMATION")
            st.warning(
                "⏳ **WAITING ROOM:** The Headliner draft is complete! Does anyone want to swap positions in the draft order?")

            st.markdown("### 🔄 Swap Draft Positions?")
            if username.capitalize() == "Isaac":
                col1, col2 = st.columns(2)
                with col1:
                    team_1 = st.selectbox("Select Team 1", shared_draft["draft_order"], format_func=lambda name: name.capitalize(), key="swap_1")
                with col2:
                    team_2 = st.selectbox("Select Team 2", shared_draft["draft_order"], format_func=lambda name: name.capitalize(), key="swap_2")

                if st.button("Confirm Position Swap"):
                    if team_1 == team_2:
                        st.error("🟥 You can't swap a team with themselves!")
                    else:
                        idx_1 = shared_draft["draft_order"].index(team_1)
                        idx_2 = shared_draft["draft_order"].index(team_2)

                        shared_draft["draft_order"][idx_1], shared_draft["draft_order"][idx_2] = \
                            shared_draft["draft_order"][idx_2], shared_draft["draft_order"][idx_1]

                        if save_draft_state(shared_draft):
                            st.success(f"🟩 {team_1.capitalize()} and {team_2.capitalize()} swapped spots!")
                            st.rerun()

            st.markdown("---")
            st.markdown("### Current Draft Order")
            for i, team in enumerate(shared_draft["draft_order"]):
                st.write(f"**Pick {i + 1}:** {team.capitalize()}")

            st.markdown("---")
            if username.capitalize() == "Isaac":
                if st.button("🔒 LOCK DRAFT ORDER & START MAIN DRAFT", type="primary"):
                    shared_draft["order_locked"] = True
                    if save_draft_state(shared_draft):
                        st.rerun()
            else:
                st.info("⏳ Waiting for the draft order to be confirmed...")

        # --- PHASE 2 DISPLAY: THE LIVE PROGRESS TIMELINE ---
        else:
            # Dynamic Pick Position and Current Pick
            if shared_draft["headliners_resolved"]:
                # 1. Find their pick position
                if username in shared_draft["draft_order"]:
                    pick_pos = shared_draft["draft_order"].index(username) + 1
                    st.subheader(f"Your pick position: **{pick_pos}**")
                else:
                    st.subheader(f"Your pick position: **N/A**")

                # 2. Calculate the current round and pick on the clock
                current_pick_idx = len(shared_draft.get("draft_history", []))
                curr_r = (current_pick_idx // 7) + 1
                curr_p = (current_pick_idx % 7) + 1
                st.subheader(f"Current Round/Pick: **{curr_r}.{curr_p}**")
            else:
                # Fallback text while Headliners are still being picked
                st.subheader("Your pick position: **TBD (Pending Headliners)**")
                st.subheader("Current Round/Pick: **Phase 1**")

            # Dynamic Team Overview
            st.subheader("*YOUR TEAM:*")

            username = st.session_state.get("username", "Guest")
            user_team = shared_draft["all_teams"].get(username, [])

            if user_team:
                for i in range(len(user_team)):
                    display_player(user_team[i])
            else:
                st.write("You haven't drafted any players yet!")
            st.divider()

            history = shared_draft.get("draft_history", [])
            current_pick_idx = len(history)

            total_teams = 7
            total_rounds = 8

            curr_r = (current_pick_idx // total_teams) + 1
            curr_p = (current_pick_idx % total_teams) + 1

            # 📢 NEW: GLOBAL RECENT PICK ANNOUNCEMENT
            if len(history) > 0:
                prev_idx = current_pick_idx - 1
                prev_r = (prev_idx // total_teams) + 1
                prev_p = (prev_idx % total_teams) + 1
                if prev_r % 2 != 0:
                    prev_owner = shared_draft["draft_order"][prev_p - 1]
                else:
                    prev_owner = shared_draft["draft_order"][total_teams - prev_p]

                st.warning(f"📢 **LATEST DRAFT PICK:** **{prev_owner.capitalize()}** selected **{history[-1]}**!")

            st.write("")

            if current_pick_idx < (total_teams * total_rounds):
                if curr_r % 2 != 0:
                    current_owner = shared_draft["draft_order"][curr_p - 1]
                else:
                    current_owner = shared_draft["draft_order"][total_teams - curr_p]

                st.info(f"⚡ **ON THE CLOCK:** Round {curr_r}.{curr_p} — **{current_owner.capitalize()}**")
                if username == current_owner:
                        # Trigger the pop-up notification
                    st.success("👉 IT IS YOUR TURN! Head to 'Search Players' to draft a player.")
            else:
                st.success("🎉 The draft is officially finished!")

            st.write("")
            with st.expander("👑 View Phase 1: Headliner Selections", expanded=False):
                for team_owner, roster in shared_draft["all_teams"].items():
                    if roster:
                        st.write(
                            f"- **{team_owner.capitalize()}** secured: *{roster[0].name} ({roster[0].rating} OVR)*")

            st.divider()
            st.subheader("📋 Draft Progress Board")

            for pick_num in range(total_rounds * total_teams):
                r = (pick_num // total_teams) + 1
                p = (pick_num % total_teams) + 1

                if r % 2 != 0:
                    owner = shared_draft["draft_order"][p - 1]
                else:
                    owner = shared_draft["draft_order"][total_teams - p]

                if pick_num < len(history):
                    st.write(f"🟢 **Round {r}.{p}** | **{owner.capitalize()}** ➔ *{history[pick_num]}*")
                elif pick_num == len(history):
                    st.markdown(f"🟠 **Round {r}.{p}** | **{owner.capitalize()}** ➔ `🤔 NOW PICKING...`")
                else:
                    st.write(f"⚪ Round {r}.{p} | {owner.capitalize()} ➔ ⏳ *Pending*")

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

        other_teams = {owner: roster for owner, roster in shared_draft["all_teams"].items() if owner != username}

        if not other_teams:
            st.write("No one else has drafted any players yet!")
        else:
            for team_owner, roster in other_teams.items():
                with st.expander(f"{team_owner.capitalize()}'s Team ({len(roster)} players)"):
                    if not roster:
                        st.write(f"*{team_owner.capitalize()} hasn't drafted anyone yet.*")
                    else:
                        for player in roster:
                            display_player(player)

elif option == "Trade Hub":
    st.title("*TRADE HUB*")

    if not shared_draft["draft_mode"]:
        st.subheader("**Will open in draft mode!**")
    else:
        st.subheader("PROPOSE TRADE:")
        other_team = st.selectbox(
            "Select other team",
            shared_draft.get("draft_order", []),
            format_func=lambda name: name.capitalize() if name else "",
            key="other_team"
        )
        if "trade_count" not in st.session_state:
            st.session_state.trade_count = 1
        players_to_give = []
        players_to_get = []
        for i in range(st.session_state.trade_count):
            st.write(f"**Player {i + 1}**")
            col1, col2 = st.columns(2)
            with col1:
                give_player = st.selectbox(
                    "Select Player you want to give",
                    shared_draft["all_teams"].get(username, []),
                    format_func=lambda player: player.name if player else "",
                    key=f"give_player_{i}"
                )
                players_to_give.append(give_player)
            with col2:
                get_player = st.selectbox(
                    "Select Player you want to get",
                    shared_draft["all_teams"].get(other_team, []),
                    format_func=lambda player: player.name if player else "",
                    key=f"get_player_{i}"
                )
                players_to_get.append(get_player)
        col_add, col_remove, col_propose = st.columns(3)
        with col_add:
            if st.button("Add another player"):
                st.session_state.trade_count += 1
                st.rerun()
        with col_remove:
            if st.button("Remove player") and st.session_state.trade_count > 1:
                st.session_state.trade_count -= 1
                st.rerun()
        with col_propose:
            if st.button("Propose trade"):
                # 🛡️ 1. Extract player names to safely check for duplicates
                current_giving_names = [p.name for p in players_to_give if p]
                current_getting_names = [p.name for p in players_to_get if p]

                is_duplicate = False
                for existing_trade in shared_draft.get("pending_trades", []):
                    existing_giving_names = [p.name for p in existing_trade.get("giving", []) if p]
                    existing_getting_names = [p.name for p in existing_trade.get("getting", []) if p]

                    if (existing_trade.get("from_team") == username and
                            existing_trade.get("to_team") == other_team and
                            existing_giving_names == current_giving_names and
                            existing_getting_names == current_getting_names and
                            existing_trade.get("status") == "pending"):
                        is_duplicate = True
                        break

                if is_duplicate:
                    st.error("⚠️ You already proposed this exact trade. Wait for them to respond!")
                else:
                    # 🛡️ 2. Create the trade with a guaranteed unique ID
                    trade_proposal = {
                        "id": str(uuid.uuid4()),
                        "from_team": username,
                        "to_team": other_team,
                        "giving": players_to_give,
                        "getting": players_to_get,
                        "status": "pending"
                    }

                    if "pending_trades" not in shared_draft:
                        shared_draft["pending_trades"] = []

                    shared_draft["pending_trades"].append(trade_proposal)

                    if save_draft_state(shared_draft):
                        # 🛠️ 3. Use a toast and a tiny sleep timer so it actually renders!
                        st.toast(f"✅ Trade successfully sent to {other_team.capitalize()}!")
                        st.session_state.trade_count = 1
                        time.sleep(3)
                        st.rerun()
        st.divider()
        st.subheader("📬 TRADES RECEIVED")

        # Pull the list of trades safely
        pending_trades = shared_draft.get("pending_trades", [])

        # Filter for active trades sent specifically to the logged-in user
        incoming_offers = [t for t in pending_trades if t.get("to_team") == username and t.get("status") == "pending"]

        if not incoming_offers:
            st.info("Your inbox is clear. No pending trade offers right now.")
        else:
            for idx, trade in enumerate(incoming_offers):
                from_team = trade.get("from_team", "Unknown Team")

                with st.container(border=True):
                    st.markdown(f"### 🫱 Over from **{from_team.capitalize()}**")

                    col_receive, col_send = st.columns(2)
                    with col_receive:
                        st.success("🟢 **You Will Receive:**")
                        for p in trade.get("giving", []):
                            if p:
                                display_player(p)

                    with col_send:
                        st.error("🔴 **You Will Give Up:**")
                        for p in trade.get("getting", []):
                            if p:
                                display_player(p)

                    st.write("")
                    col_accept, col_decline = st.columns(2)

                    with col_accept:
                        # Using trade.get("id") as the ultimate key
                        unique_key = trade.get("id", f"backup_{idx}")
                        if st.button("🤝 Accept Trade", key=f"accept_{unique_key}", use_container_width=True):
                            # Fetch current rosters
                            my_roster = shared_draft["all_teams"].get(username, [])
                            their_roster = shared_draft["all_teams"].get(from_team, [])

                            # Extract names to target for swapping
                            items_i_lose = [p.name for p in trade.get("getting", []) if p]
                            items_i_gain = [p.name for p in trade.get("giving", []) if p]

                            # Execute the multi-player roster swap
                            new_my_roster = [p for p in my_roster if p.name not in items_i_lose] + [p for p in
                                                                                                    their_roster if
                                                                                                    p.name in items_i_gain]
                            new_their_roster = [p for p in their_roster if p.name not in items_i_gain] + [p for p in
                                                                                                          my_roster if
                                                                                                          p.name in items_i_lose]
                            # 🧹 NEW: Re-sort both rosters by rating (highest to lowest) before saving
                            new_my_roster.sort(key=lambda p: p.rating, reverse=True)
                            new_their_roster.sort(key=lambda p: p.rating, reverse=True)

                            # Save back to database
                            shared_draft["all_teams"][username] = new_my_roster
                            shared_draft["all_teams"][from_team] = new_their_roster

                            # Mark this trade as resolved
                            trade["status"] = "accepted"

                            if save_draft_state(shared_draft):
                                st.toast("🎉 Trade successful! Your rosters have been updated.")
                                time.sleep(3)
                                st.rerun()

                    with col_decline:
                        unique_key = trade.get("id", f"backup_{idx}")
                        if st.button("❌ Decline", key=f"decline_{unique_key}", use_container_width=True):
                            trade["status"] = "declined"
                            if save_draft_state(shared_draft):
                                st.toast(f"❌ Declined offer from {from_team.capitalize()}.")
                                time.sleep(3)
                                st.rerun()

        st.divider()
        st.subheader("📜 TRADE HISTORY")

        # Pull all trades safely
        all_trades = shared_draft.get("pending_trades", [])

        # Filter for trades that are no longer pending
        resolved_trades = [t for t in all_trades if t.get("status") in ["accepted", "declined"]]

        if not resolved_trades:
            st.info("No trades have been completed yet.")
        else:
            # Reverse the list so the newest trades show up at the top
            for trade in reversed(resolved_trades):
                status = trade.get("status", "unknown")
                status_icon = "✅" if status == "accepted" else "❌"
                from_t = trade.get("from_team", "Unknown").capitalize()
                to_t = trade.get("to_team", "Unknown").capitalize()

                # Use an expander to keep the UI clean if there are a ton of trades
                with st.expander(f"{status_icon} {from_t} & {to_t} ({status.capitalize()})"):

                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        st.write(f"**{from_t}** traded away:")
                        for p in trade.get("giving", []):
                            if p:
                                st.write(f"- {p.name}")

                    with col_t2:
                        st.write(f"**{to_t}** traded away:")
                        for p in trade.get("getting", []):
                            if p:
                                st.write(f"- {p.name}")

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
